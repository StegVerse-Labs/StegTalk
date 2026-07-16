from datetime import datetime, timedelta, timezone

import pytest

from stegtalk.transport.recovery_queue import (
    RecoveryState,
    mark_permission_restored,
    next_chunk_index,
    queue_after_path_exhaustion,
    refresh_recovery_state,
    resume_from_confirmed_chunk,
    verify_recovery_continuity,
)


NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def make_entry():
    return queue_after_path_exhaustion(
        message_id="msg-demo-001",
        now=NOW,
        expires_at=NOW + timedelta(minutes=10),
        invalidated_adapters=("wifi_peer", "ble", "wifi_peer"),
        last_confirmed_chunk_index=7,
        last_confirmed_custody_hash="custody-hash-001",
    )


def test_simultaneous_adapter_loss_is_deduplicated_and_queued():
    entry = make_entry()
    assert entry.state is RecoveryState.QUEUED
    assert entry.invalidated_adapters == ("ble", "wifi_peer")


def test_permission_restoration_resumes_from_next_confirmed_chunk():
    queued = make_entry()
    ready = mark_permission_restored(queued, adapter_kind="ble", now=NOW + timedelta(minutes=1))
    resumed = resume_from_confirmed_chunk(ready, bearer_id="ble:peer-hash", now=NOW + timedelta(minutes=2))
    assert resumed.state is RecoveryState.RESUMED
    assert next_chunk_index(resumed) == 8
    assert verify_recovery_continuity(queued, resumed)


def test_recovery_expiry_is_terminal_and_cannot_resume():
    queued = make_entry()
    expired = refresh_recovery_state(queued, now=NOW + timedelta(minutes=10))
    assert expired.state is RecoveryState.EXPIRED
    assert mark_permission_restored(expired, adapter_kind="ble", now=NOW + timedelta(minutes=11)).state is RecoveryState.EXPIRED


def test_unrelated_permission_restoration_is_rejected():
    with pytest.raises(ValueError, match="not part"):
        mark_permission_restored(make_entry(), adapter_kind="satellite_gateway", now=NOW + timedelta(minutes=1))


def test_resume_requires_permission_restoration():
    with pytest.raises(ValueError, match="permission restoration"):
        resume_from_confirmed_chunk(make_entry(), bearer_id="ble:peer", now=NOW + timedelta(minutes=1))


def test_invalid_queue_inputs_fail_closed():
    with pytest.raises(ValueError, match="at least one"):
        queue_after_path_exhaustion(
            message_id="msg-demo-001",
            now=NOW,
            expires_at=NOW + timedelta(minutes=1),
            invalidated_adapters=(),
            last_confirmed_chunk_index=0,
            last_confirmed_custody_hash="hash",
        )
