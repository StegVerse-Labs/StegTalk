from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, Mapping, MutableMapping, Optional

from .cross_edge_resolver import Lease, fallback_action
from .entity_runtime import JsonObject, stable_hash


class EdgeRuntimeError(ValueError):
    pass


TERMINAL_RESULTS = {"DELIVERED", "ACKNOWLEDGED", "EXECUTED", "FAILED", "INDETERMINATE", "TIMEOUT_AFTER_DISPATCH", "UNKNOWN_AFTER_DISPATCH"}


@dataclass(frozen=True)
class EdgeExecutionRequest:
    attempt_id: str
    selection_sha256: str
    edge_id: str
    bearer: str
    payload_ref: str
    idempotency_key: str
    lease_epoch: int


@dataclass(frozen=True)
class EdgeExecutionReceipt:
    receipt_type: str
    attempt_id: str
    selection_sha256: str
    edge_id: str
    bearer: str
    idempotency_key: str
    lease_epoch: int
    dispatch_state: str
    outcome: str
    side_effect_absence_confirmed: bool
    observed_at: str
    receipt_sha256: str


EdgeExecutor = Callable[[EdgeExecutionRequest], Mapping[str, object]]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_without_receipt(value: Mapping[str, object]) -> str:
    encoded = dict(value)
    encoded.pop("receipt_sha256", None)
    return stable_hash(encoded)


def validate_execution_request(*, selection_receipt: JsonObject, lease: Lease, request: EdgeExecutionRequest) -> None:
    if request.attempt_id != selection_receipt.get("attempt_id"):
        raise EdgeRuntimeError("execution request attempt does not match selection")
    if request.selection_sha256 != selection_receipt.get("selection_sha256"):
        raise EdgeRuntimeError("execution request selection hash mismatch")
    if request.edge_id != selection_receipt.get("selected_edge_id"):
        raise EdgeRuntimeError("execution request edge does not match selected edge")
    if request.bearer != selection_receipt.get("selected_bearer"):
        raise EdgeRuntimeError("execution request bearer does not match selected bearer")
    if lease.attempt_id != request.attempt_id or lease.edge_id != request.edge_id:
        raise EdgeRuntimeError("execution lease does not bind selected attempt and edge")
    if lease.lease_epoch != request.lease_epoch:
        raise EdgeRuntimeError("execution request lease epoch mismatch")
    if not request.payload_ref:
        raise EdgeRuntimeError("payload_ref is required")
    if not request.idempotency_key:
        raise EdgeRuntimeError("idempotency_key is required")


def execute_selected_edge(
    *,
    selection_receipt: JsonObject,
    lease: Lease,
    request: EdgeExecutionRequest,
    executors: Mapping[str, EdgeExecutor],
    execution_cache: Optional[MutableMapping[str, EdgeExecutionReceipt]] = None,
) -> EdgeExecutionReceipt:
    """Execute exactly the selected edge/bearer under an already-issued lease.

    The runtime never selects a bearer and never broadens authority. The optional
    cache is an ephemeral idempotency aid only; durable continuity belongs in KV.
    """

    validate_execution_request(selection_receipt=selection_receipt, lease=lease, request=request)
    cache = execution_cache if execution_cache is not None else {}
    cached = cache.get(request.idempotency_key)
    if cached is not None:
        if (
            cached.selection_sha256 != request.selection_sha256
            or cached.edge_id != request.edge_id
            or cached.bearer != request.bearer
            or cached.lease_epoch != request.lease_epoch
        ):
            raise EdgeRuntimeError("idempotency key reused with different execution binding")
        return cached

    executor = executors.get(request.edge_id)
    if executor is None:
        raise EdgeRuntimeError("selected edge executor is unavailable")

    raw = dict(executor(request))
    outcome = str(raw.get("outcome") or "")
    if outcome not in TERMINAL_RESULTS:
        raise EdgeRuntimeError("edge executor returned unsupported outcome")
    dispatch_state = str(raw.get("dispatch_state") or "")
    if dispatch_state not in {"NOT_DISPATCHED", "DISPATCHED", "OBSERVED"}:
        raise EdgeRuntimeError("edge executor returned invalid dispatch_state")

    side_effect_absence_confirmed = bool(raw.get("side_effect_absence_confirmed", False))
    if outcome in {"INDETERMINATE", "TIMEOUT_AFTER_DISPATCH", "UNKNOWN_AFTER_DISPATCH"} and side_effect_absence_confirmed:
        raise EdgeRuntimeError("ambiguous dispatch cannot confirm side-effect absence")
    if outcome in {"DELIVERED", "ACKNOWLEDGED", "EXECUTED"} and side_effect_absence_confirmed:
        raise EdgeRuntimeError("successful execution cannot confirm side-effect absence")

    receipt_body: Dict[str, object] = {
        "receipt_type": "EDGE_EXECUTION",
        "attempt_id": request.attempt_id,
        "selection_sha256": request.selection_sha256,
        "edge_id": request.edge_id,
        "bearer": request.bearer,
        "idempotency_key": request.idempotency_key,
        "lease_epoch": request.lease_epoch,
        "dispatch_state": dispatch_state,
        "outcome": outcome,
        "side_effect_absence_confirmed": side_effect_absence_confirmed,
        "observed_at": str(raw.get("observed_at") or _utc_now()),
    }
    receipt_body["receipt_sha256"] = _hash_without_receipt(receipt_body)
    receipt = EdgeExecutionReceipt(**receipt_body)  # type: ignore[arg-type]
    cache[request.idempotency_key] = receipt
    return receipt


def next_runtime_action(*, selection_receipt: JsonObject, receipt: EdgeExecutionReceipt, next_fallback_index: int = 0) -> JsonObject:
    return fallback_action(
        outcome=receipt.outcome,
        selection_receipt=selection_receipt,
        next_fallback_index=next_fallback_index,
        side_effect_absence_confirmed=receipt.side_effect_absence_confirmed,
    )


def receipt_as_record(receipt: EdgeExecutionReceipt) -> JsonObject:
    record = asdict(receipt)
    expected = record.pop("receipt_sha256")
    if _hash_without_receipt(record) != expected:
        raise EdgeRuntimeError("edge execution receipt hash mismatch")
    record["receipt_sha256"] = expected
    return record


def loopback_test_executor(*, outcome: str = "DELIVERED", side_effect_absence_confirmed: bool = False) -> EdgeExecutor:
    """Return a real callable executor for CI/runtime plumbing tests only.

    LOOPBACK_TEST proves dispatch orchestration and receipt semantics but is not a
    physical/network delivery claim and must never be advertised as production.
    """

    def _execute(request: EdgeExecutionRequest) -> Mapping[str, object]:
        return {
            "dispatch_state": "OBSERVED" if outcome in {"DELIVERED", "ACKNOWLEDGED", "EXECUTED"} else "DISPATCHED",
            "outcome": outcome,
            "side_effect_absence_confirmed": side_effect_absence_confirmed,
            "observed_at": _utc_now(),
            "loopback_test_only": True,
            "request_hash": stable_hash(asdict(request)),
        }

    return _execute
