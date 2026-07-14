import json
from copy import deepcopy

import pytest

from stegtalk.entity_runtime import create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint import create_managed_checkpoint, inspect_managed_checkpoint, restore_managed_checkpoint


def _shell():
    return create_mobile_shell(identity_card=create_entity_card(entity_id="rigel", display_name="Rigel", entity_type="human", purpose="local operator"))


def test_managed_checkpoint_round_trip_is_one_call(tmp_path):
    result = create_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    restored = restore_managed_checkpoint(store_root=tmp_path, session_id="primary")
    assert result["manual_tasks_required"] == []
    assert restored["verified"] is True
    assert restored["shell"]["user_entity"] == "rigel"
    assert len(restored["receipt_chain"]) == 1


def test_managed_checkpoint_inspection_is_payload_free(tmp_path):
    create_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    inspection = inspect_managed_checkpoint(store_root=tmp_path, session_id="primary")
    assert inspection["verified"] is True
    assert inspection["receipt_count"] == 1
    assert "shell" not in inspection
    assert inspection["authorizing"] is False


def test_managed_checkpoint_rejects_partial_state(tmp_path):
    create_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    (tmp_path / "mobile_shell_session_receipt_chains" / "primary.json").unlink()
    with pytest.raises(FileNotFoundError):
        restore_managed_checkpoint(store_root=tmp_path, session_id="primary")


def test_managed_checkpoint_rejects_checkpoint_tampering(tmp_path):
    create_managed_checkpoint(store_root=tmp_path, shell=_shell(), session_id="primary")
    path = tmp_path / "mobile_shell_session_checkpoints" / "primary.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["record"]["user_entity"] = "other"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="wrapper integrity"):
        restore_managed_checkpoint(store_root=tmp_path, session_id="primary")


def test_managed_checkpoint_rejects_stale_session_state(tmp_path):
    shell = _shell()
    create_managed_checkpoint(store_root=tmp_path, shell=shell, session_id="primary")
    changed = deepcopy(shell)
    changed["shell_state"]["active_view"] = "contacts"
    changed["mobile_shell_hash"] = "sha256:changed"
    from stegtalk.mobile_shell_session import persist_mobile_shell_session
    persist_mobile_shell_session(store_root=tmp_path, shell=changed, session_id="primary")
    with pytest.raises(ValueError, match="integrity check failed|shell hash mismatch|session record drift"):
        restore_managed_checkpoint(store_root=tmp_path, session_id="primary")
