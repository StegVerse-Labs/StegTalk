from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Literal

from ..entity_runtime import JsonObject, stable_hash, utc_now
from .failover import FailoverPlan, next_failover_bearer

AttemptResult = Literal["PENDING", "SUCCEEDED", "FAILED", "CANCELED"]
CustodyState = Literal[
    "CREATED",
    "QUEUED",
    "ATTEMPTING",
    "RELAYED",
    "RECONSTRUCTED",
    "DELIVERED",
    "ACKNOWLEDGED",
    "CANCELED",
    "FAILED",
]

TERMINAL_STATES = {"ACKNOWLEDGED", "CANCELED", "FAILED"}
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "CREATED": {"QUEUED", "CANCELED", "FAILED"},
    "QUEUED": {"ATTEMPTING", "CANCELED", "FAILED"},
    "ATTEMPTING": {"QUEUED", "RELAYED", "RECONSTRUCTED", "DELIVERED", "CANCELED", "FAILED"},
    "RELAYED": {"QUEUED", "RECONSTRUCTED", "DELIVERED", "CANCELED", "FAILED"},
    "RECONSTRUCTED": {"DELIVERED", "ACKNOWLEDGED", "FAILED"},
    "DELIVERED": {"ACKNOWLEDGED"},
    "ACKNOWLEDGED": set(),
    "CANCELED": set(),
    "FAILED": set(),
}


@dataclass(frozen=True)
class TransportAttempt:
    attempt_number: int
    bearer_id: str
    result: AttemptResult = "PENDING"
    failure_code: str | None = None


@dataclass(frozen=True)
class TransportCustody:
    message_id: str
    state: CustodyState
    active_bearer_id: str | None
    attempts: tuple[TransportAttempt, ...]
    failed_bearer_ids: tuple[str, ...]
    previous_state_hash: str | None = None


def create_custody(message_id: str) -> TransportCustody:
    if not message_id.strip():
        raise ValueError("message_id is required")
    return TransportCustody(
        message_id=message_id,
        state="CREATED",
        active_bearer_id=None,
        attempts=(),
        failed_bearer_ids=(),
    )


def transition_custody(
    custody: TransportCustody,
    new_state: CustodyState,
    *,
    active_bearer_id: str | None = None,
) -> TransportCustody:
    if new_state not in _ALLOWED_TRANSITIONS[custody.state]:
        raise ValueError(f"inadmissible custody transition: {custody.state}->{new_state}")
    return replace(
        custody,
        state=new_state,
        active_bearer_id=active_bearer_id,
        previous_state_hash=stable_hash(asdict(custody)),
    )


def start_next_attempt(custody: TransportCustody, plan: FailoverPlan) -> TransportCustody:
    if custody.state in TERMINAL_STATES:
        raise ValueError("terminal custody cannot start another attempt")
    bearer_id = next_failover_bearer(plan, failed_bearer_ids=set(custody.failed_bearer_ids))
    if bearer_id is None:
        return transition_custody(custody, "FAILED")
    attempt = TransportAttempt(attempt_number=len(custody.attempts) + 1, bearer_id=bearer_id)
    queued = custody if custody.state == "QUEUED" else transition_custody(custody, "QUEUED")
    return replace(
        transition_custody(queued, "ATTEMPTING", active_bearer_id=bearer_id),
        attempts=queued.attempts + (attempt,),
    )


def record_attempt_failure(
    custody: TransportCustody,
    *,
    failure_code: str,
) -> TransportCustody:
    if custody.state != "ATTEMPTING" or not custody.attempts:
        raise ValueError("no active attempt")
    if not failure_code.strip():
        raise ValueError("failure_code is required")
    current = custody.attempts[-1]
    failed = replace(current, result="FAILED", failure_code=failure_code)
    failed_ids = tuple(sorted(set(custody.failed_bearer_ids) | {current.bearer_id}))
    updated = replace(custody, attempts=custody.attempts[:-1] + (failed,), failed_bearer_ids=failed_ids)
    return transition_custody(updated, "QUEUED")


def record_attempt_success(
    custody: TransportCustody,
    *,
    resulting_state: Literal["RELAYED", "RECONSTRUCTED", "DELIVERED"],
) -> TransportCustody:
    if custody.state != "ATTEMPTING" or not custody.attempts:
        raise ValueError("no active attempt")
    current = custody.attempts[-1]
    succeeded = replace(current, result="SUCCEEDED")
    updated = replace(custody, attempts=custody.attempts[:-1] + (succeeded,))
    return transition_custody(updated, resulting_state, active_bearer_id=current.bearer_id)


def cancel_custody(custody: TransportCustody) -> TransportCustody:
    if custody.state in TERMINAL_STATES or custody.state in {"DELIVERED", "RECONSTRUCTED"}:
        raise ValueError("custody can no longer be canceled")
    attempts = custody.attempts
    if custody.state == "ATTEMPTING" and attempts:
        attempts = attempts[:-1] + (replace(attempts[-1], result="CANCELED"),)
        custody = replace(custody, attempts=attempts)
    return transition_custody(custody, "CANCELED")


def build_attempt_receipt(custody: TransportCustody, *, previous_receipt_hash: str | None = None) -> JsonObject:
    receipt: JsonObject = {
        "schema_version": "0.1.0",
        "receipt_type": "stegtalk_transport_attempt_state",
        "message_id": custody.message_id,
        "custody_hash": stable_hash(asdict(custody)),
        "state": custody.state,
        "active_bearer_id": custody.active_bearer_id,
        "attempt_count": len(custody.attempts),
        "failed_bearer_ids": list(custody.failed_bearer_ids),
        "previous_receipt_hash": previous_receipt_hash,
        "authority": {
            "delivery_claim_only": True,
            "execution_authority_granted": False,
        },
        "created_at": utc_now(),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def verify_attempt_receipt(
    receipt: JsonObject,
    custody: TransportCustody,
    *,
    expected_previous_receipt_hash: str | None = None,
) -> bool:
    if receipt.get("receipt_type") != "stegtalk_transport_attempt_state":
        return False
    if receipt.get("previous_receipt_hash") != expected_previous_receipt_hash:
        return False
    if receipt.get("custody_hash") != stable_hash(asdict(custody)):
        return False
    authority = receipt.get("authority", {})
    if authority.get("delivery_claim_only") is not True:
        return False
    if authority.get("execution_authority_granted") is not False:
        return False
    stored_hash = receipt.get("receipt_hash")
    unhashed = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return stored_hash == stable_hash(unhashed)
