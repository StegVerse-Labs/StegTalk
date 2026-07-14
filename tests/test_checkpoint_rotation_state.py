import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_checkpoint_rotation_state_is_fail_closed_and_automatic():
    state = json.loads((ROOT / "STEGTALK_MOBILE_SHELL_SESSION_CHECKPOINT_ROTATION_STATE.json").read_text(encoding="utf-8"))
    assert state["goal"] == "mobile_shell_session_checkpoint_rotation"
    assert state["manual_tasks_remaining"] == []
    assert state["production_ready"] is False
    assert state["local_only"] is True
    assert state["authorizing"] is False
    assert state["new_workflows_added"] is False
    assert state["default_retention"] == 3
