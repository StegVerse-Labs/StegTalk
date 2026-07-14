import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_session_receipt_build_complete_waits_only_for_ci():
    state = json.loads(
        (ROOT / "STEGTALK_SESSION_RECEIPT_BUILD_COMPLETE.json").read_text(encoding="utf-8")
    )
    assert state["build_state"] == "COMPLETE_PENDING_CI"
    assert state["manual_tasks_required"] == []
    assert state["new_workflows_added"] is False
    assert state["merge_condition"] == "all_required_ci_pass"
