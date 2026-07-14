import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_session_receipt_handoff_is_automatic_and_fail_closed():
    handoff = json.loads(
        (ROOT / "STEGTALK_SESSION_RECEIPT_HANDOFF.json").read_text(encoding="utf-8")
    )
    assert handoff["current_goal"] == "mobile_shell_session_receipt_chain"
    assert handoff["production_ready"] is False
    assert handoff["manual_tasks_required"] == []
    assert handoff["new_workflows_added"] is False
    assert handoff["downstream_mutation_authorized"] is False
    assert handoff["post_merge_goal"] == "mobile_shell_session_receipt_persistence"
