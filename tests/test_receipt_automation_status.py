import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_receipt_automation_status_has_no_remaining_manual_tasks():
    status = json.loads(
        (ROOT / "STEGTALK_RECEIPT_AUTOMATION_STATUS.json").read_text(encoding="utf-8")
    )
    assert status["goal"] == "eliminate_manual_session_receipt_tasks"
    assert status["manual_tasks_before"]
    assert status["manual_tasks_after"] == []
    assert status["production_ready"] is False
    assert status["local_only"] is True
    assert status["authorizing"] is False
    assert status["new_workflows_added"] is False
