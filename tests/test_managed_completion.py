from pathlib import Path

from stegtalk.managed_completion import load_queue, next_pending_task, build_management_state, verify_management_state

ROOT = Path(__file__).resolve().parents[1]


def test_next_pending_task_selects_highest_priority_pending():
    queue = load_queue(ROOT)
    task = next_pending_task(queue)
    assert task is not None
    assert task["id"] == "ST-001"


def test_management_state_is_capable_not_production_ready():
    queue = load_queue(ROOT)
    state = build_management_state(queue)
    assert state["managed_completion_capable"] is True
    assert state["production_ready"] is False
    assert state["open_task_count"] >= 1


def test_required_management_files_exist():
    state = verify_management_state(ROOT)
    assert state["managed_completion_capable"] is True
