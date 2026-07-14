import json

import pytest

from stegtalk.entity_runtime import create_entity_card, stable_hash
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import rotate_managed_checkpoint
from stegtalk.mobile_shell_session_recovery_receipt import (
    inspect_recovery_receipts,
    recover_session_with_receipt,
    restore_recovery_receipts,
)


def _shell(entity_id="rigel"):
    return create_mobile_shell(identity_card=create_entity_card(entity_id=entity_id, display_name=entity_id.title(), entity_type="human", purpose="local operator"))


def test_recovery_receipt_records_newest_generation(tmp_path):
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    recovered, receipt = recover_session_with_receipt(store_root=tmp_path, session_id="primary")
    assert recovered["generation"] == 1
    assert receipt["result"] == "recovered"
    assert receipt["fallback_used"] is False
    assert receipt["selected_generation"] == 1
    assert "shell" not in receipt
    assert inspect_recovery_receipts(store_root=tmp_path, session_id="primary")["receipt_count"] == 1


def test_recovery_receipt_records_automatic_fallback(tmp_path):
    for _ in range(2):
        rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary", retention=3)
    path = tmp_path / "mobile_shell_session_checkpoint_history" / "primary.json"
    history = json.loads(path.read_text(encoding="utf-8"))
    history["entries"][-1]["entry_hash"] = "sha256:damaged"
    history["history_hash"] = stable_hash({key: value for key, value in history.items() if key != "history_hash"})
    path.write_text(json.dumps(history), encoding="utf-8")

    recovered, receipt = recover_session_with_receipt(store_root=tmp_path, session_id="primary")
    assert recovered["generation"] == 1
    assert receipt["fallback_used"] is True
    assert receipt["selected_generation"] == 1
    assert receipt["rejected_generations"][0]["generation"] == 2


def test_failed_recovery_is_receipted_without_manual_work(tmp_path):
    recovered, receipt = recover_session_with_receipt(store_root=tmp_path, session_id="missing")
    assert recovered is None
    assert receipt["result"] == "failed"
    assert receipt["reason"]
    assert restore_recovery_receipts(store_root=tmp_path, session_id="missing")[0]["id"] == receipt["id"]


def test_recovery_receipt_history_detects_tampering(tmp_path):
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    recover_session_with_receipt(store_root=tmp_path, session_id="primary")
    path = tmp_path / "mobile_shell_session_recovery_receipts" / "primary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["receipts"][0]["selected_generation"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="history integrity"):
        restore_recovery_receipts(store_root=tmp_path, session_id="primary")


def test_recovery_receipts_chain_automatically(tmp_path):
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    _, first = recover_session_with_receipt(store_root=tmp_path, session_id="primary")
    _, second = recover_session_with_receipt(store_root=tmp_path, session_id="primary")
    assert second["previous_chain_head"] == first["receipt_chain_head"]
    assert inspect_recovery_receipts(store_root=tmp_path, session_id="primary")["chain_head"] == second["receipt_chain_head"]
