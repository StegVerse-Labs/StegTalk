from stegtalk.transport.recovery_runtime import (
    AckKey,
    DeviceContinuity,
    demonstrate_crash_restart,
    make_slot,
    select_recovery_slot,
    sign_ack_set,
    verify_ack_set,
)


def test_single_valid_slot_survives_and_dual_corruption_fails():
    continuity = DeviceContinuity("device-hash", 3, 5)
    valid = make_slot(slot_name="A", generation=6, snapshot_hash="snapshot-6", previous_slot_hash="slot-5")
    torn = valid.__class__("B", 7, "snapshot-7", valid.slot_hash, "tampered")
    assert select_recovery_slot((valid, torn), continuity) == valid

    broken = valid.__class__("A", 6, "snapshot-6", "slot-5", "tampered")
    result = demonstrate_crash_restart(
        slots=(broken, torn),
        continuity=continuity,
        total_chunks=3,
        acknowledgement_receipt=sign_ack_set(
            message_id="m1",
            custody_hash="c1",
            store_generation=6,
            acknowledged_chunks=(0,),
            key=AckKey("k1", b"secret", 1),
        ),
        keys=(AckKey("k1", b"secret", 1),),
    )
    assert result.reconstruction_failed is True


def test_replay_is_blocked_by_device_continuity_generation():
    continuity = DeviceContinuity("device-hash", 3, 8)
    stale = make_slot(slot_name="A", generation=7, snapshot_hash="snapshot-7", previous_slot_hash=None)
    result = demonstrate_crash_restart(
        slots=(stale,),
        continuity=continuity,
        total_chunks=2,
        acknowledgement_receipt=sign_ack_set(
            message_id="m1",
            custody_hash="c1",
            store_generation=7,
            acknowledged_chunks=(0,),
            key=AckKey("k1", b"secret", 1),
        ),
        keys=(AckKey("k1", b"secret", 1),),
    )
    assert result.replay_blocked is True
    assert result.reconstruction_failed is True


def test_key_rotation_preserves_old_confirmations_and_new_key_signs_new_generation():
    old = AckKey("old", b"old-secret", 1, retired_after_generation=6)
    new = AckKey("new", b"new-secret", 7)
    old_receipt = sign_ack_set(
        message_id="m1",
        custody_hash="c1",
        store_generation=6,
        acknowledged_chunks=(0, 2),
        key=old,
    )
    new_receipt = sign_ack_set(
        message_id="m1",
        custody_hash="c1",
        store_generation=7,
        acknowledged_chunks=(0, 2, 3),
        key=new,
    )
    assert verify_ack_set(old_receipt, (old, new)) is True
    assert verify_ack_set(new_receipt, (old, new)) is True


def test_end_to_end_crash_restart_selects_latest_slot_and_only_missing_chunks():
    key = AckKey("current", b"secret", 7)
    receipt = sign_ack_set(
        message_id="m1",
        custody_hash="custody-1",
        store_generation=8,
        acknowledged_chunks=(0, 1, 3),
        key=key,
    )
    older = make_slot(slot_name="A", generation=7, snapshot_hash="snapshot-7", previous_slot_hash=None)
    latest = make_slot(slot_name="B", generation=8, snapshot_hash="snapshot-8", previous_slot_hash=older.slot_hash)
    result = demonstrate_crash_restart(
        slots=(older, latest),
        continuity=DeviceContinuity("device-hash", 3, 7),
        total_chunks=5,
        acknowledgement_receipt=receipt,
        keys=(key,),
    )
    assert result.selected_slot == "B"
    assert result.selected_generation == 8
    assert result.missing_chunks == (2, 4)
    assert result.reconstruction_failed is False
