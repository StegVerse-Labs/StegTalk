from stegtalk.transport.active_transfer import (
    ActiveTransfer,
    ActiveTransferState,
    begin_reselection,
    fail_no_alternate,
    pause_for_adapter_loss,
    provenance_hash,
    resume_on_alternate,
    verify_no_duplicate_custody_spend,
)


def transfer():
    return ActiveTransfer(
        message_id="msg-demo-001",
        state=ActiveTransferState.ACTIVE,
        active_bearer_id="wifi-peer-1",
        adapter_receipt_hash="a" * 64,
        observation_provenance_hash="b" * 64,
        last_confirmed_custody_hash="c" * 64,
    )


def test_pause_reselect_resume_preserves_custody_boundary():
    original = transfer()
    paused = pause_for_adapter_loss(original, adapter_kind="wifi_peer")
    selecting = begin_reselection(paused)
    resumed = resume_on_alternate(
        selecting,
        alternate_bearer_id="ble-peer-1",
        provenance=provenance_hash(adapter_receipt_hash="d" * 64, source_event_hashes=("e" * 64,)),
    )
    assert resumed.state is ActiveTransferState.RESUMED
    assert resumed.invalidated_adapter == "wifi_peer"
    assert verify_no_duplicate_custody_spend(original, resumed)


def test_no_alternate_path_keeps_last_confirmed_boundary():
    original = transfer()
    terminal = fail_no_alternate(begin_reselection(pause_for_adapter_loss(original, adapter_kind="wifi_peer")))
    assert terminal.state is ActiveTransferState.NO_ALTERNATE_PATH
    assert verify_no_duplicate_custody_spend(original, terminal)


def test_cannot_switch_without_pause_and_reselection():
    try:
        resume_on_alternate(transfer(), alternate_bearer_id="ble-peer-1", provenance="x" * 64)
    except ValueError as exc:
        assert "reselecting" in str(exc)
    else:
        raise AssertionError("expected fail-closed transition")
