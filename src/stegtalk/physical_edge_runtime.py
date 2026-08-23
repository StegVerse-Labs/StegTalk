from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from .cross_edge_resolver import (
    CapabilityResolutionError,
    fallback_action,
    issue_execution_lease,
    resolve_cross_edge_path,
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
    """Load the canonical KnowledgeVault filesystem store when installed.

    The continuity-vault-kit source/package must be present in the runtime's Python
    environment. StegTalk intentionally does not reimplement the KV execution-store
    hashing, secret rejection, or append-only persistence contract.
    """

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
) -> tuple[JsonObject, JsonObject, JsonObject]:
    """Resolve one real-advertisement candidate set and persist selection before dispatch."""

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
    return attempt, selection, lease_record


def record_runtime_outcome(
    *,
    attempt_id: str,
    selection_receipt: JsonObject,
    outcome: str,
    store: ExecutionStore,
    side_effect_absence_confirmed: bool = False,
    next_fallback_index: int = 0,
    evidence: JsonObject | None = None,
) -> JsonObject:
    """Persist delivery truth and compute the only safe next action.

    This function does not dispatch a fallback. It records the resolver's decision so
    ambiguous delivery can never silently become permission to duplicate a message.
    """

    action = fallback_action(
        outcome=outcome,
        selection_receipt=selection_receipt,
        next_fallback_index=next_fallback_index,
        side_effect_absence_confirmed=side_effect_absence_confirmed,
    )
    record: JsonObject = {
        "schema_version": "0.1",
        "type": "STEGTALK_RUNTIME_OUTCOME",
        "attempt_id": attempt_id,
        "outcome": outcome,
        "selection_sha256": selection_receipt.get("selection_sha256"),
        "side_effect_absence_confirmed": side_effect_absence_confirmed,
        "next_action": action,
        "delivery_proven": outcome in {"DELIVERED", "ACKNOWLEDGED", "EXECUTED"},
        "production_active": False,
        "evidence": evidence or {},
        "recorded_at": utc_now(),
    }
    store.append_attempt(attempt_id, record)
    store.append_receipt(attempt_id, record)
    if action["action"] == "VERIFY_EXTERNALLY":
        store.append_recovery(
            attempt_id,
            {
                "type": "STEGTALK_EXTERNAL_VERIFICATION_REQUIRED",
                "attempt_id": attempt_id,
                "selection_sha256": selection_receipt.get("selection_sha256"),
                "reason": action["reason"],
                "recorded_at": utc_now(),
            },
        )
    return record


def dispatch_selected_sms(
    *,
    attempt_id: str,
    selection_receipt: JsonObject,
    edge_advertisements: list[JsonObject],
    envelope: JsonObject,
    to_number: str,
    store: ExecutionStore,
    journal_path: str | Path,
    allow_plaintext_external: bool = False,
) -> JsonObject:
    """Bind an ST-031-selected SMS edge to the existing ST-029 live modem session."""

    if selection_receipt.get("selected_bearer") != "sms":
        raise RuntimeExecutionError("selected bearer is not sms; refusing modem dispatch")
    edge_id = selection_receipt.get("selected_edge_id")
    selected = next((ad for ad in edge_advertisements if ad.get("edge_id") == edge_id), None)
    if selected is None:
        raise RuntimeExecutionError("selected edge advertisement is unavailable")
    capabilities = selected.get("capabilities") or {}
    modem_path = capabilities.get("modem_path")
    if not isinstance(modem_path, str) or not modem_path:
        raise RuntimeExecutionError("selected SMS edge lacks capabilities.modem_path")

    journal = SovereignSmsJournal(journal_path)
    candidate = SerialCandidate(path=modem_path, family="st031-selected")
    with SovereignSmsSession(candidate, journal=journal) as session:
        result, transport_receipt, session_receipt = session.send(
            envelope=envelope,
            to_number=to_number,
            allow_plaintext_external=allow_plaintext_external,
        )

    dispatch: JsonObject = {
        "schema_version": "0.1",
        "type": "STEGTALK_ST029_DISPATCH",
        "attempt_id": attempt_id,
        "selection_sha256": selection_receipt.get("selection_sha256"),
        "selected_edge_id": edge_id,
        "selected_bearer": "sms",
        "modem_path": modem_path,
        "modem_reference": result.reference,
        "transport_receipt_hash": stable_hash(transport_receipt),
        "session_receipt_hash": stable_hash(session_receipt),
        "state": "DISPATCHED_DELIVERY_UNPROVEN",
        "delivery_proven": False,
        "production_active": False,
        "recorded_at": utc_now(),
    }
    store.append_attempt(attempt_id, dispatch)
    store.append_receipt(attempt_id, transport_receipt)
    store.append_receipt(attempt_id, session_receipt)
    store.append_receipt(attempt_id, dispatch)
    return dispatch


def _write_stdout(value: JsonObject) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m stegtalk.physical_edge_runtime",
        description="ST-030/ST-031 connected-KnowledgeVault physical-edge runtime harness",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare", help="persist selection + lease before any dispatch")
    prepare.add_argument("--attempt-id", required=True)
    prepare.add_argument("--posture", default="AUTO")
    prepare.add_argument("--edges", required=True, help="JSON array of admitted edge advertisements")
    prepare.add_argument("--recipient", required=True, help="recipient capability JSON object")
    prepare.add_argument("--constraints", required=True, help="resolver constraints JSON object")
    prepare.add_argument("--vault-root", required=True)
    prepare.add_argument("--lease-seconds", type=int, default=120)

    sms = sub.add_parser("sms-send", help="select, persist, then dispatch only if selected bearer is sms")
    sms.add_argument("--attempt-id", required=True)
    sms.add_argument("--posture", default="AUTO")
    sms.add_argument("--edges", required=True)
    sms.add_argument("--recipient", required=True)
    sms.add_argument("--constraints", required=True)
    sms.add_argument("--vault-root", required=True)
    sms.add_argument("--envelope", required=True)
    sms.add_argument("--to", required=True)
    sms.add_argument("--journal", required=True)
    sms.add_argument("--lease-seconds", type=int, default=120)
    sms.add_argument("--allow-plaintext-external", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    store = load_knowledge_vault_store(args.vault_root)
    edges = _read_json_list(args.edges)
    recipient = _read_json(args.recipient)
    constraints = _read_json(args.constraints)
    attempt, selection, lease = prepare_runtime_attempt(
        attempt_id=args.attempt_id,
        posture=args.posture,
        edge_advertisements=edges,
        recipient=recipient,
        constraints=constraints,
        store=store,
        lease_seconds=args.lease_seconds,
    )
    if args.command == "prepare":
        _write_stdout({"attempt": attempt, "selection": selection, "lease": lease})
        return 0
    if args.command == "sms-send":
        dispatch = dispatch_selected_sms(
            attempt_id=args.attempt_id,
            selection_receipt=selection,
            edge_advertisements=edges,
            envelope=_read_json(args.envelope),
            to_number=args.to,
            store=store,
            journal_path=args.journal,
            allow_plaintext_external=args.allow_plaintext_external,
        )
        _write_stdout({"attempt": attempt, "selection": selection, "lease": lease, "dispatch": dispatch})
        return 0
    raise RuntimeExecutionError("unsupported runtime command")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeExecutionError, CapabilityResolutionError) as exc:
        raise SystemExit(str(exc)) from exc
