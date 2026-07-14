import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_session_receipt_state_eliminates_manual_chain_tasks():
    state = json.loads(
        (ROOT / "STEGTALK_MOBILE_SHELL_SESSION_RECEIPT_STATE.json").read_text(encoding="utf-8")
    )
    assert state["goal"] == "mobile_shell_session_receipt_chain"
    assert state["production_ready"] is False
    assert state["local_only"] is True
    assert state["authorizing"] is False
    assert state["manual_tasks_remaining"] == []
    assert state["new_workflows_added"] is False
    assert state["failure_posture"] == {
        "authority_escalation": "REJECT_AND_RECEIPT",
        "integrity_failure": "REJECT_AND_RECEIPT",
        "missing_session": "REJECT_AND_RECEIPT",
        "chain_discontinuity": "FAIL_CLOSED",
    }
