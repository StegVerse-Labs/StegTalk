from datetime import datetime, timedelta, timezone

import pytest

from stegtalk.transport.recovery_persistence import (
    RecoveryDisposition,
    RecoverySnapshot,
    cancel_snapshot,
    expire_snapshot,
    make_recovery_receipt,
    missing_chunks,
    reconstruct_snapshot,
    resume_snapshot,
    serialize_snapshot,
    verify_recovery_receipt,
)


def queued() -> RecoverySnapshot:
    now = datetime(2026, 7, 16, tzinfo=timezone.utc)
    return RecoverySnapshot(
        message_id="msg-demo-001",
        disposition=RecoveryDisposition.QUEUED,
        total_chunks=10,
        acknowledged_chunks=(0, 1, 2, 4, 7),
        last_confirmed_custody_hash="a" * 64,
        custody_spend_count=1,
        queued_at=now,
        expires_at=now + timedelta(minutes=5),
    )


def test_snapshot_round_trip_is_deterministic() -> None:
    original = queued()
    assert reconstruct_snapshot(serialize_snapshot(original)) == original


def test_sparse_retransmission_only_returns_missing_chunks() -> None:
    assert missing_chunks(queued()) == (3, 5, 6, 8, 9)


def test_resume_preserves_custody_and_chains_receipt() -> None:
    original = queued()
    first = make_recovery_receipt(original)
    resumed = resume_snapshot(original, adapter="ble", now=original.queued_at + timedelta(seconds=30))
    assert resumed.previous_receipt_hash == first.receipt_hash
    assert resumed.last_confirmed_custody_hash == original.last_confirmed_custody_hash
    assert resumed.custody_spend_count == 1
    assert missing_chunks(resumed) == missing_chunks(original)


def test_expiry_and_cancel_create_terminal_chained_snapshots() -> None:
    original = queued()
    expired = expire_snapshot(original, now=original.expires_at)
    canceled = cancel_snapshot(original)
    assert expired.disposition is RecoveryDisposition.EXPIRED
    assert canceled.disposition is RecoveryDisposition.CANCELED
    assert expired.previous_receipt_hash
    assert canceled.previous_receipt_hash


def test_receipt_rejects_snapshot_tampering_and_authority_escalation() -> None:
    original = queued()
    receipt = make_recovery_receipt(original)
    assert verify_recovery_receipt(original, receipt)
    altered = RecoverySnapshot(**{**original.__dict__, "acknowledged_chunks": (0, 1)})
    assert not verify_recovery_receipt(altered, receipt)
    escalated = type(receipt)(**{**receipt.__dict__, "execution_authority_granted": True})
    assert not verify_recovery_receipt(original, escalated)


def test_invalid_bitmap_and_late_resume_fail_closed() -> None:
    original = queued()
    duplicate = RecoverySnapshot(**{**original.__dict__, "acknowledged_chunks": (0, 0)})
    with pytest.raises(ValueError):
        serialize_snapshot(duplicate)
    with pytest.raises(ValueError):
        resume_snapshot(original, adapter="ble", now=original.expires_at)
