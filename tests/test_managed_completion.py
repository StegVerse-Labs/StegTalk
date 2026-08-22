from pathlib import Path

from stegtalk.managed_completion import load_queue, next_pending_task, build_management_state, verify_management_state

ROOT = Path(__file__).resolve().parents[1]


def test_managed_queue_has_no_unclaimed_pending_repository_task():
    queue = load_queue(ROOT)
    assert next_pending_task(queue) is None
    tasks = {item["id"]: item for item in queue["tasks"]}
    assert tasks["ST-026"]["status"] == "complete"
    assert tasks["ST-029"]["claim_state"] == "OPEN"
    assert tasks["ST-030"]["claim_state"] == "OPEN"
    assert tasks["ST-029"]["live_activation"] is False
    assert tasks["ST-030"]["live_kv_backing_proof"] is False
    assert "KnowledgeVault" in queue["next_integration_goal"]


def test_management_state_is_capable_not_production_ready():
    queue = load_queue(ROOT)
    state = build_management_state(queue)
    assert state["managed_completion_capable"] is True
    assert state["production_ready"] is False
    assert state["open_task_count"] == 0


def test_required_management_files_exist():
    state = verify_management_state(ROOT)
    assert state["managed_completion_capable"] is True
