from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Literal

TransferState = Literal[
    "OFFERED",
    "ACCEPTED",
    "CONFIRMED",
    "EXPIRED",
    "ROLLED_BACK",
    "RELEASED",
]


@dataclass(frozen=True)
class CustodyTransfer:
    transfer_id: str
    message_id: str
    upstream_peer_id: str
    downstream_peer_id: str
    offered_at: str
    expires_at: str
    state: TransferState = "OFFERED"
    accepted_at: str | None = None
    confirmed_at: str | None = None
    released_at: str | None = None
    copy_budget_decremented: bool = False
    upstream_retains_payload: bool = True
    previous_state_hash: str | None = None
    reason: str | None = None


_ALLOWED: dict[TransferState, set[TransferState]] = {
    "OFFERED": {"ACCEPTED", "EXPIRED", "ROLLED_BACK"},
    "ACCEPTED": {"CONFIRMED", "EXPIRED", "ROLLED_BACK"},
    "CONFIRMED": {"RELEASED"},
    "EXPIRED": set(),
    "ROLLED_BACK": set(),
    "RELEASED": set(),
}


def create_transfer(
    *,
    transfer_id: str,
    message_id: str,
    upstream_peer_id: str,
    downstream_peer_id: str,
    offered_at: str,
    expires_at: str,
) -> CustodyTransfer:
    if not all(value.strip() for value in (transfer_id, message_id, upstream_peer_id, downstream_peer_id)):
        raise ValueError("transfer and peer identifiers are required")
    if upstream_peer_id == downstream_peer_id:
        raise ValueError("upstream and downstream peers must differ")
    if _parse(expires_at) <= _parse(offered_at):
        raise ValueError("expires_at must be after offered_at")
    return CustodyTransfer(
        transfer_id=transfer_id,
        message_id=message_id,
        upstream_peer_id=upstream_peer_id,
        downstream_peer_id=downstream_peer_id,
        offered_at=offered_at,
        expires_at=expires_at,
    )


def accept_transfer(transfer: CustodyTransfer, *, accepted_at: str, state_hash: str) -> CustodyTransfer:
    _require_transition(transfer, "ACCEPTED")
    _require_before_expiry(transfer, accepted_at)
    return replace(
        transfer,
        state="ACCEPTED",
        accepted_at=accepted_at,
        previous_state_hash=state_hash,
        upstream_retains_payload=True,
        copy_budget_decremented=False,
    )


def confirm_transfer(transfer: CustodyTransfer, *, confirmed_at: str, state_hash: str) -> CustodyTransfer:
    _require_transition(transfer, "CONFIRMED")
    _require_before_expiry(transfer, confirmed_at)
    return replace(
        transfer,
        state="CONFIRMED",
        confirmed_at=confirmed_at,
        previous_state_hash=state_hash,
        upstream_retains_payload=True,
        copy_budget_decremented=True,
    )


def release_upstream(transfer: CustodyTransfer, *, released_at: str, state_hash: str) -> CustodyTransfer:
    _require_transition(transfer, "RELEASED")
    return replace(
        transfer,
        state="RELEASED",
        released_at=released_at,
        previous_state_hash=state_hash,
        upstream_retains_payload=False,
    )


def expire_transfer(transfer: CustodyTransfer, *, observed_at: str, state_hash: str) -> CustodyTransfer:
    _require_transition(transfer, "EXPIRED")
    if _parse(observed_at) < _parse(transfer.expires_at):
        raise ValueError("transfer is not expired")
    return replace(
        transfer,
        state="EXPIRED",
        previous_state_hash=state_hash,
        reason="acceptance_or_confirmation_timeout",
        upstream_retains_payload=True,
        copy_budget_decremented=False,
    )


def rollback_transfer(transfer: CustodyTransfer, *, reason: str, state_hash: str) -> CustodyTransfer:
    _require_transition(transfer, "ROLLED_BACK")
    if not reason.strip():
        raise ValueError("rollback reason is required")
    return replace(
        transfer,
        state="ROLLED_BACK",
        previous_state_hash=state_hash,
        reason=reason,
        upstream_retains_payload=True,
        copy_budget_decremented=False,
    )


def deletion_eligible(transfer: CustodyTransfer) -> bool:
    return (
        transfer.state == "RELEASED"
        and transfer.copy_budget_decremented
        and not transfer.upstream_retains_payload
        and transfer.confirmed_at is not None
    )


def _require_transition(transfer: CustodyTransfer, target: TransferState) -> None:
    if target not in _ALLOWED[transfer.state]:
        raise ValueError(f"invalid custody transition: {transfer.state} -> {target}")


def _require_before_expiry(transfer: CustodyTransfer, timestamp: str) -> None:
    if _parse(timestamp) > _parse(transfer.expires_at):
        raise ValueError("custody transfer validity window expired")


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
