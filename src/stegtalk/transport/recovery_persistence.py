from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
import json


class RecoveryDisposition(StrEnum):
    QUEUED = "QUEUED"
    RESUMED = "RESUMED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


@dataclass(frozen=True)
class RecoverySnapshot:
    message_id: str
    disposition: RecoveryDisposition
    total_chunks: int
    acknowledged_chunks: tuple[int, ...]
    last_confirmed_custody_hash: str
    custody_spend_count: int
    queued_at: datetime
    expires_at: datetime
    restored_adapter: str | None = None
    previous_receipt_hash: str | None = None


@dataclass(frozen=True)
class RecoveryReceipt:
    snapshot_hash: str
    previous_receipt_hash: str | None
    disposition: RecoveryDisposition
    receipt_hash: str
    delivery_claimed: bool = False
    execution_authority_granted: bool = False


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=lambda item: item.isoformat())


def _hash(value: object) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def validate_snapshot(snapshot: RecoverySnapshot) -> None:
    if not snapshot.message_id:
        raise ValueError("message_id is required")
    if snapshot.total_chunks <= 0:
        raise ValueError("total_chunks must be positive")
    if snapshot.custody_spend_count < 1:
        raise ValueError("custody_spend_count must be positive")
    unique = tuple(sorted(set(snapshot.acknowledged_chunks)))
    if unique != snapshot.acknowledged_chunks:
        raise ValueError("acknowledged_chunks must be unique and sorted")
    if any(index < 0 or index >= snapshot.total_chunks for index in unique):
        raise ValueError("acknowledged chunk out of range")
    if snapshot.expires_at <= snapshot.queued_at:
        raise ValueError("expiry must follow queue time")


def make_recovery_receipt(snapshot: RecoverySnapshot) -> RecoveryReceipt:
    validate_snapshot(snapshot)
    snapshot_hash = _hash(asdict(snapshot))
    payload = {
        "snapshot_hash": snapshot_hash,
        "previous_receipt_hash": snapshot.previous_receipt_hash,
        "disposition": snapshot.disposition,
        "delivery_claimed": False,
        "execution_authority_granted": False,
    }
    return RecoveryReceipt(snapshot_hash, snapshot.previous_receipt_hash, snapshot.disposition, _hash(payload))


def verify_recovery_receipt(snapshot: RecoverySnapshot, receipt: RecoveryReceipt) -> bool:
    if receipt.delivery_claimed or receipt.execution_authority_granted:
        return False
    return make_recovery_receipt(snapshot) == receipt


def serialize_snapshot(snapshot: RecoverySnapshot) -> str:
    validate_snapshot(snapshot)
    payload = asdict(snapshot)
    payload["disposition"] = snapshot.disposition.value
    payload["queued_at"] = snapshot.queued_at.isoformat()
    payload["expires_at"] = snapshot.expires_at.isoformat()
    return _canonical(payload)


def reconstruct_snapshot(payload: str) -> RecoverySnapshot:
    raw = json.loads(payload)
    snapshot = RecoverySnapshot(
        message_id=raw["message_id"],
        disposition=RecoveryDisposition(raw["disposition"]),
        total_chunks=int(raw["total_chunks"]),
        acknowledged_chunks=tuple(int(item) for item in raw["acknowledged_chunks"]),
        last_confirmed_custody_hash=raw["last_confirmed_custody_hash"],
        custody_spend_count=int(raw["custody_spend_count"]),
        queued_at=datetime.fromisoformat(raw["queued_at"]),
        expires_at=datetime.fromisoformat(raw["expires_at"]),
        restored_adapter=raw.get("restored_adapter"),
        previous_receipt_hash=raw.get("previous_receipt_hash"),
    )
    validate_snapshot(snapshot)
    return snapshot


def missing_chunks(snapshot: RecoverySnapshot) -> tuple[int, ...]:
    validate_snapshot(snapshot)
    acknowledged = set(snapshot.acknowledged_chunks)
    return tuple(index for index in range(snapshot.total_chunks) if index not in acknowledged)


def resume_snapshot(snapshot: RecoverySnapshot, *, adapter: str, now: datetime) -> RecoverySnapshot:
    validate_snapshot(snapshot)
    if snapshot.disposition is not RecoveryDisposition.QUEUED:
        raise ValueError("only queued recovery may resume")
    if now >= snapshot.expires_at:
        raise ValueError("recovery expired")
    if not adapter:
        raise ValueError("restored adapter is required")
    receipt = make_recovery_receipt(snapshot)
    return replace(snapshot, disposition=RecoveryDisposition.RESUMED, restored_adapter=adapter, previous_receipt_hash=receipt.receipt_hash)


def expire_snapshot(snapshot: RecoverySnapshot, *, now: datetime) -> RecoverySnapshot:
    validate_snapshot(snapshot)
    if now < snapshot.expires_at:
        raise ValueError("recovery has not expired")
    receipt = make_recovery_receipt(snapshot)
    return replace(snapshot, disposition=RecoveryDisposition.EXPIRED, previous_receipt_hash=receipt.receipt_hash)


def cancel_snapshot(snapshot: RecoverySnapshot) -> RecoverySnapshot:
    validate_snapshot(snapshot)
    if snapshot.disposition is not RecoveryDisposition.QUEUED:
        raise ValueError("only queued recovery may be canceled")
    receipt = make_recovery_receipt(snapshot)
    return replace(snapshot, disposition=RecoveryDisposition.CANCELED, previous_receipt_hash=receipt.receipt_hash)
