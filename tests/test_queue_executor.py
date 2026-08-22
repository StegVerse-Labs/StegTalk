from pathlib import Path

from stegtalk.queue_executor import load_queue, mark_task, summarize_queue, verify_queue_execution

ROOT = Path(__file__).resolve().parents[1]


def test_queue_summary_reports_current_local_queue():
    queue = load_queue(ROOT)
    summary = summarize_queue(queue)
    assert summary["task_count"] == len(queue["tasks"])
    assert summary["production_ready"] is False
    assert summary["next_task"] is None
    assert summary["complete_count"] == sum(task["status"] == "complete" for task in queue["tasks"])
    assert summary["pending_count"] == sum(task["status"] == "pending" for task in queue["tasks"])


def test_mark_task_updates_status_without_mutating_original():
    queue = load_queue(ROOT)
    updated = mark_task(queue, "ST-001", "ready")
    assert updated != queue
    assert any(task["id"] == "ST-001" and task["status"] == "ready" for task in updated["tasks"])


def test_queue_execution_verifies():
    queue = load_queue(ROOT)
    summary = verify_queue_execution(ROOT)
    assert summary["production_ready"] is False
    assert summary["task_count"] == len(queue["tasks"])
    assert summary["next_task"] is None
