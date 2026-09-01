from stegtalk.transport.atomic_recovery_store import (
    ReplayLedger,
    choose_committed_slot,
    detect_torn_write,
    make_envelope,
)
from stegtalk.transport.chunk_acknowledgements import (
    make_chunk_acknowledgement,
    verified_acknowledged_chunks,
)


def test_atomic_slots_choose_highest_valid_generation_and_detect_torn_write():
    first = make_envelope(generation=1, payload='{"message_id":"m1"}', previous_envelope_hash=None)
    second = make_envelope(generation=2, payload='{"message_id":"m1","state":"queued"}', previous_envelope_hash=first.envelope_hash)
    assert choose_committed_slot(slot_a=first, slot_b=second) == second
    torn = make_envelope(generation=3, payload='{"message_id":"m1","state":"resumed"}', previous_envelope_hash="wrong")
    assert detect_torn_write(committed=second, candidate=torn)


def test_replay_ledger_rejects_same_or_older_generation():
    ledger = ReplayLedger({})
    first = make_envelope(generation=4, payload='{"message_id":"m1"}', previous_envelope_hash=None)
    ledger.accept(message_id="m1", envelope=first)
    try:
        ledger.accept(message_id="m1", envelope=first)
    except ValueError as exc:
        assert "replay" in str(exc)
    else:
        raise AssertionError("replayed snapshot was accepted")


def test_chunk_acknowledgements_are_bound_to_message_and_custody():
    key = b"test-only-key"
    valid = make_chunk_acknowledgement(message_id="m1", chunk_index=2, custody_hash="custody-a", key=key)
    wrong_custody = make_chunk_acknowledgement(message_id="m1", chunk_index=3, custody_hash="custody-b", key=key)
    wrong_message = make_chunk_acknowledgement(message_id="m2", chunk_index=4, custody_hash="custody-a", key=key)
    assert verified_acknowledged_chunks((valid, wrong_custody, wrong_message), key=key, message_id="m1", custody_hash="custody-a") == (2,)
