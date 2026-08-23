from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, MutableMapping, Protocol

from .cross_edge_resolver import CapabilityResolutionError, Lease, issue_execution_lease, resolve_cross_edge_path
from .edge_runtime import (
    EdgeExecutionReceipt,
    EdgeExecutionRequest,
    EdgeExecutor,
    EdgeRuntimeError,
    execute_selected_edge,
    next_runtime_action,
    receipt_as_record,
)
from .entity_runtime import JsonObject, stable_hash, utc_now
from .serial_modem import SerialCandidate
from .sovereign_sms_journal import SovereignSmsJournal
from .sovereign_sms_runtime import SovereignSmsSession


class RuntimeExecutionError(RuntimeError):
    pass


class ExecutionStore(Protocol):
    def append_attempt(self, attempt_id: str, record: dict[str, Any]) -> Path: ...
    def append_receipt(self, receipt_stream_id: str, record: dict[str, Any]) -> Path: ...
    def append_recovery(self, attempt_id: str, record: dict[str, Any]) -> Path: ...
    def read_stream(self, category: str, stream_id: str) -> list[dict[str, Any]]: ...


def _read_json(path: str | Path) -> JsonObject:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeExecutionError(f"expected JSON object: {path}")
    return value


def _read_json_list(path: str | Path) -> list[JsonObject]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise RuntimeExecutionError(f"expected JSON array of objects: {path}")
    return value


def load_knowledge_vault_store(vault_root: str | Path) -> ExecutionStore:
    """Load the canonical KnowledgeVault store instead of duplicating its contract."""

    try:
        from execution.vault_store import KnowledgeVaultExecutionStore
    except ImportError as exc:
        raise RuntimeExecutionError(
            "KnowledgeVault execution store is unavailable; install or expose "
            "StegVerse-Labs/continuity-vault-kit before running a live attempt"
        ) from exc
    store = KnowledgeVaultExecutionStore(vault_root)
    store.initialize()
    return store


def prepare_runtime_attempt(
    *,
    attempt_id: str,
    posture: str,
    edge_advertisements: list[JsonObject],
    recipient: JsonObject,
    constraints: JsonObject,
    store: ExecutionStore,
    lease_seconds: int = 120,
    now: datetime | None = None,
) -> tuple[JsonObject, JsonObject, Lease, JsonObject]:
    """Run ST-031 once and durably persist selection + lease before ST-032 dispatch."""

    if not attempt_id or any(part in attempt_id for part in ("/", "\\", "..")):
        raise RuntimeExecutionError("attempt_id must be a safe single path component")
    if lease_seconds < 1:
        raise RuntimeExecutionError("lease_seconds must be positive")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    selection = resolve_cross_edge_path(
        attempt_id=attempt_id,
        posture=posture,
        edge_advertisements=edge_advertisements,
        recipient=recipient,
        constraints=constraints,
        now=current,
    )
    expires = (current + timedelta(seconds=lease_seconds)).isoformat().replace("+00:00", "Z")
    lease = issue_execution_lease(
        attempt_id=attempt_id,
        selection_receipt=selection,
        lease_epoch=1,
        expires_at=expires,
        now=current,
    )
    lease_record: JsonObject = {
        "schema_version": "0.1",
        "type": "ST031_EXECUTION_LEASE",
        **asdict(lease),
        "selection_sha256": selection["selection_sha256"],
        "dispatch_authorized_by_receipt": False,
        "delivery_proven": False,
        "production_active": False,
        "recorded_at": current.isoformat().replace("+00:00", "Z"),
    }
    attempt: JsonObject = {
        "schema_version": "0.1",
        "type": "STEGTALK_RUNTIME_ATTEMPT",
        "attempt_id": attempt_id,
        "state": "SELECTED_NOT_DISPATCHED",
        "posture": posture,
        "selected_edge_id": selection["selected_edge_id"],
        "selected_bearer": selection["selected_bearer"],
        "selection_sha256": selection["selection_sha256"],
        "lease_sha256": stable_hash(lease_record),
        "edge_advertisement_count": len(edge_advertisements),
        "physical_bearer_execution_proven": False,
        "delivery_proven": False,
        "production_active": False,
        "recorded_at": current.isoformat().replace("+00:00", "Z"),
    }
    store.append_attempt(attempt_id, attempt)
    store.append_receipt(attempt_id, selection)
    store.append_receipt(attempt_id, lease_record)
    return attempt, selection, lease, lease_record


def load_runtime_binding(*, store: ExecutionStore, attempt_id: str) -> tuple[JsonObject, Lease, JsonObject]:
    """Reconstruct ST-031 selection + lease from the connected KV receipt stream."""

    records = store.read_stream("Receipts", attempt_id)
    selections = [record for record in records if record.get("receipt_type") == "CROSS_EDGE_SELECTION"]
    leases = [record for record in records if record.get("type") == "ST031_EXECUTION_LEASE"]
    if not selections or not leases:
        raise RuntimeExecutionError("KnowledgeVault has no complete ST-031 selection/lease binding for attempt")
    selection = selections[-1]
    lease_record = leases[-1]
    if lease_record.get("attempt_id") != attempt_id:
        raise RuntimeExecutionError("persisted lease attempt mismatch")
    if lease_record.get("selection_sha256") != selection.get("selection_sha256"):
        raise RuntimeExecutionError("persisted lease selection hash mismatch")
    if lease_record.get("edge_id") != selection.get("selected_edge_id"):
        raise RuntimeExecutionError("persisted lease edge mismatch")
    lease = Lease(
        attempt_id=str(lease_record["attempt_id"]),
        edge_id=str(lease_record["edge_id"]),
        lease_epoch=int(lease_record["lease_epoch"]),
        expires_at=str(lease_record["expires_at"]),
    )
    return selection, lease, lease_record


def _durable_execution_cache(*, store: ExecutionStore, attempt_id: str) -> MutableMapping[str, EdgeExecutionReceipt]:
    cache: dict[str, EdgeExecutionReceipt] = {}
    for record in store.read_stream("Receipts", attempt_id):
        if record.get("receipt_type") != "EDGE_EXECUTION":
            continue
        receipt = EdgeExecutionReceipt(**record)
        receipt_as_record(receipt)
        prior = cache.get(receipt.idempotency_key)
        if prior is not None and prior.receipt_sha256 != receipt.receipt_sha256:
            raise RuntimeExecutionError("KnowledgeVault contains conflicting execution receipts for idempotency key")
        cache[receipt.idempotency_key] = receipt
    return cache


def execute_persisted_selected_edge(
    *,
    selection_receipt: JsonObject,
    lease: Lease,
    request: EdgeExecutionRequest,
    executors: Mapping[str, EdgeExecutor],
    store: ExecutionStore,
    next_fallback_index: int = 0,
) -> tuple[EdgeExecutionReceipt, JsonObject, bool]:
    """Execute through ST-032 with KV-backed restart/idempotency reconstruction."""

    cache = _durable_execution_cache(store=store, attempt_id=request.attempt_id)
    replayed_from_kv = request.idempotency_key in cache
    if not replayed_from_kv:
        store.append_attempt(
            request.attempt_id,
            {
                "type": "ST032_DISPATCH_PENDING",
                "attempt_id": request.attempt_id,
                "selection_sha256": request.selection_sha256,
                "edge_id": request.edge_id,
                "bearer": request.bearer,
                "idempotency_key": request.idempotency_key,
                "lease_epoch": request.lease_epoch,
                "delivery_proven": False,
                "production_active": False,
                "recorded_at": utc_now(),
            },
        )

    receipt = execute_selected_edge(
        selection_receipt=selection_receipt,
        lease=lease,
        request=request,
        executors=executors,
        execution_cache=cache,
    )
    action = next_runtime_action(
        selection_receipt=selection_receipt,
        receipt=receipt,
        next_fallback_index=next_fallback_index,
    )
    if replayed_from_kv:
        return receipt, action, True

    receipt_record = receipt_as_record(receipt)
    store.append_receipt(request.attempt_id, receipt_record)
    store.append_attempt(
        request.attempt_id,
        {
            "type": "ST032_EXECUTION_TRANSITION",
            "attempt_id": request.attempt_id,
            "selection_sha256": request.selection_sha256,
            "edge_id": request.edge_id,
            "bearer": request.bearer,
            "idempotency_key": request.idempotency_key,
            "dispatch_state": receipt.dispatch_state,
            "outcome": receipt.outcome,
            "execution_receipt_sha256": receipt.receipt_sha256,
            "next_action": action,
            "delivery_proven": receipt.outcome in {"DELIVERED", "ACKNOWLEDGED", "EXECUTED"},
            "production_active": False,
            "recorded_at": utc_now(),
        },
    )
    if action["action"] == "VERIFY_EXTERNALLY":
        store.append_recovery(
            request.attempt_id,
            {
                "type": "STEGTALK_EXTERNAL_VERIFICATION_REQUIRED",
                "attempt_id": request.attempt_id,
                "selection_sha256": request.selection_sha256,
                "execution_receipt_sha256": receipt.receipt_sha256,
                "reason": action["reason"],
                "recorded_at": utc_now(),
            },
        )
    return receipt, action, False


def sovereign_sms_executor(
    *,
    edge_advertisements: list[JsonObject],
    envelope: JsonObject,
    to_number: str,
    store: ExecutionStore,
    journal_path: str | Path,
    allow_plaintext_external: bool = False,
) -> EdgeExecutor:
    """Expose ST-029 as an ST-032 executor without claiming delivery at submission."""

    advertisements = {str(ad.get("edge_id")): ad for ad in edge_advertisements}

    def _execute(request: EdgeExecutionRequest) -> Mapping[str, object]:
        if request.bearer != "sms":
            raise EdgeRuntimeError("ST-029 executor received non-SMS bearer")
        selected = advertisements.get(request.edge_id)
        if selected is None:
            raise EdgeRuntimeError("selected SMS edge advertisement is unavailable")
        modem_path = (selected.get("capabilities") or {}).get("modem_path")
        if not isinstance(modem_path, str) or not modem_path:
            raise EdgeRuntimeError("selected SMS edge lacks capabilities.modem_path")

        journal = SovereignSmsJournal(journal_path)
        candidate = SerialCandidate(path=modem_path, family="st032-selected")
        with SovereignSmsSession(candidate, journal=journal) as session:
            result, transport_receipt, session_receipt = session.send(
                envelope=envelope,
                to_number=to_number,
                allow_plaintext_external=allow_plaintext_external,
            )
        store.append_receipt(request.attempt_id, transport_receipt)
        store.append_receipt(request.attempt_id, session_receipt)
        store.append_receipt(
            request.attempt_id,
            {
                "type": "ST029_MODEM_SUBMISSION_EVIDENCE",
                "attempt_id": request.attempt_id,
                "selection_sha256": request.selection_sha256,
                "edge_id": request.edge_id,
                "modem_path": modem_path,
                "modem_reference": result.reference,
                "delivery_proven": False,
                "production_active": False,
                "recorded_at": utc_now(),
            },
        )
        return {
            "dispatch_state": "DISPATCHED",
            "outcome": "INDETERMINATE",
            "side_effect_absence_confirmed": False,
            "observed_at": utc_now(),
        }

    return _execute


def _write_stdout(value: JsonObject) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m stegtalk.physical_edge_runtime",
        description="ST-030/ST-031/ST-032 connected-KnowledgeVault runtime harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="persist ST-031 selection + lease before dispatch")
    prepare.add_argument("--attempt-id", required=True)
    prepare.add_argument("--posture", default="AUTO")
    prepare.add_argument("--edges", required=True)
    prepare.add_argument("--recipient", required=True)
    prepare.add_argument("--constraints", required=True)
    prepare.add_argument("--vault-root", required=True)
    prepare.add_argument("--lease-seconds", type=int, default=120)

    sms = sub.add_parser("sms-send", help="run the selected SMS edge through ST-032 -> ST-029")
    sms.add_argument("--attempt-id", required=True)
    sms.add_argument("--posture", default="AUTO")
    sms.add_argument("--edges", required=True)
    sms.add_argument("--recipient", required=True)
    sms.add_argument("--constraints", required=True)
    sms.add_argument("--vault-root", required=True)
    sms.add_argument("--envelope", required=True)
    sms.add_argument("--to", required=True)
    sms.add_argument("--journal", required=True)
    sms.add_argument("--payload-ref", required=True)
    sms.add_argument("--idempotency-key", required=True)
    sms.add_argument("--lease-seconds", type=int, default=120)
    sms.add_argument("--resume", action="store_true", help="reconstruct selection/lease/execution cache from KV")
    sms.add_argument("--allow-plaintext-external", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    store = load_knowledge_vault_store(args.vault_root)
    edges = _read_json_list(args.edges)
    if args.command == "prepare":
        attempt, selection, lease, lease_record = prepare_runtime_attempt(
            attempt_id=args.attempt_id,
            posture=args.posture,
            edge_advertisements=edges,
            recipient=_read_json(args.recipient),
            constraints=_read_json(args.constraints),
            store=store,
            lease_seconds=args.lease_seconds,
        )
        _write_stdout({"attempt": attempt, "selection": selection, "lease": lease_record})
        return 0

    if args.command == "sms-send":
        if args.resume:
            selection, lease, lease_record = load_runtime_binding(store=store, attempt_id=args.attempt_id)
            attempt = {"attempt_id": args.attempt_id, "state": "RECONSTRUCTED_FROM_KV"}
        else:
            attempt, selection, lease, lease_record = prepare_runtime_attempt(
                attempt_id=args.attempt_id,
                posture=args.posture,
                edge_advertisements=edges,
                recipient=_read_json(args.recipient),
                constraints=_read_json(args.constraints),
                store=store,
                lease_seconds=args.lease_seconds,
            )
        request = EdgeExecutionRequest(
            attempt_id=args.attempt_id,
            selection_sha256=str(selection["selection_sha256"]),
            edge_id=str(selection["selected_edge_id"]),
            bearer=str(selection["selected_bearer"]),
            payload_ref=args.payload_ref,
            idempotency_key=args.idempotency_key,
            lease_epoch=lease.lease_epoch,
        )
        executor = sovereign_sms_executor(
            edge_advertisements=edges,
            envelope=_read_json(args.envelope),
            to_number=args.to,
            store=store,
            journal_path=args.journal,
            allow_plaintext_external=args.allow_plaintext_external,
        )
        receipt, action, replayed = execute_persisted_selected_edge(
            selection_receipt=selection,
            lease=lease,
            request=request,
            executors={request.edge_id: executor},
            store=store,
        )
        _write_stdout(
            {
                "attempt": attempt,
                "selection": selection,
                "lease": lease_record,
                "execution": receipt_as_record(receipt),
                "next_action": action,
                "replayed_from_knowledge_vault": replayed,
            }
        )
        return 0
    raise RuntimeExecutionError("unsupported runtime command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeExecutionError, CapabilityResolutionError, EdgeRuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
