import json

import pytest

from stegtalk.entity_runtime import create_entity_card, stable_hash
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import inspect_checkpoint_history, restore_latest_valid_checkpoint, rotate_managed_checkpoint


def _shell(view: str = "home"):
    shell = create_mobile_shell(identity_card=create_entity_card(entity_id="rigel", display_name="Rigel", entity_type="human", purpose="local operator"))
    shell["shell_state"]["active_view"] = view
    shell["mobile_shell_hash"] = stable_hash({key: value for key, value in shell.items() if key != "mobile_shell_hash"})
    return shell


def test_rotation_retains_bounded_history_and_restores_latest(tmp_path):
    for view in ("home", "contacts", "inbox", "discovery"):
        rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(view), session_id="primary", retention=3)
    assert inspect_checkpoint_history(store_root=tmp_path, session_id="primary")["retained_generations"] == [2, 3, 4]
    restored = restore_latest_valid_checkpoint(store_root=tmp_path, session_id="primary")
    assert restored["generation"] == 4
    assert restored["fallback_used"] is False


def test_rotation_falls_back_from_corrupt_latest_entry(tmp_path):
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell("home"), session_id="primary")
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell("contacts"), session_id="primary")
    path = tmp_path / "mobile_shell_session_checkpoint_history" / "primary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["entries"][-1]["shell"]["shell_state"]["active_view"] = "tampered"
    data["history_hash"] = stable_hash({key: value for key, value in data.items() if key != "history_hash"})
    path.write_text(json.dumps(data), encoding="utf-8")
    restored = restore_latest_valid_checkpoint(store_root=tmp_path, session_id="primary")
    assert restored["generation"] == 1
    assert restored["fallback_used"] is True
    assert restored["rejected_generations"][0]["generation"] == 2


def test_rotation_rejects_history_tampering_and_invalid_inputs(tmp_path):
    rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    path = tmp_path / "mobile_shell_session_checkpoint_history" / "primary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["retention"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="history integrity"):
        restore_latest_valid_checkpoint(store_root=tmp_path, session_id="primary")
    with pytest.raises(ValueError, match="retention"):
        rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="other", retention=0)
    with pytest.raises(ValueError, match="unsupported characters"):
        rotate_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="../escape")
