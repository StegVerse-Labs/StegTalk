import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_checkpoint_rotation_handoff_requires_no_manual_work():
    handoff = json.loads((ROOT / "STEGTALK_SESSION_CHECKPOINT_ROTATION_HANDOFF.json").read_text(encoding="utf-8"))
    assert handoff["current_goal"] == "mobile_shell_session_checkpoint_rotation"
    assert handoff["manual_tasks_required"] == []
    assert handoff["production_ready"] is False
    assert handoff["new_workflows_added"] is False
    assert handoff["downstream_mutation_authorized"] is False
