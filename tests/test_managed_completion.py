from pathlib import Path

from stegtalk.managed_completion import load_queue, next_pending_task, build_management_state, verify_management_state

ROOT = Path(__file__).resolve().parents[1]


def test_managed_queue_has_no_pending_local_prototype_tasks():
    queue = load_queue(ROOT)
    assert next_pending_task(queue) is None
    assert all(item["status"] == "complete" for item in queue["tasks"])
    assert queue["next_integration_goal"] == "mobile_shell_persistent_session_boundary"


def test_management_state_is_capable_not_production_ready():
    queue = load_queue(ROOT)
    state = build_management_state(queue)
    assert state["managed_completion_capable"] is True
    assert state["production_ready"] is False
    assert state["open_task_count"] == 0


def test_required_management_files_exist():
    state = verify_management_state(ROOT)
    assert state["managed_completion_capable"] is True
