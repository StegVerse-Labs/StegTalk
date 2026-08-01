import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "runtime/personal-data-control.v1.json"


def test_personal_data_control_runtime_is_non_halting_and_located():
    data = json.loads(RUNTIME.read_text(encoding="utf-8"))
    assert data["state"] == "ACTIVATED_AND_CI_BOUND"
    assert data["external_tasks_required"] is False
    assert data["authority_granted"] is False
    assert data["non_halting_policy"]["external_response_is_evidence_not_dependency"] is True
    assert data["non_halting_policy"]["repository_repair_continues"] is True
    task = data["task"]
    assert task["id"] == "ST-026"
    assert task["status"] == "complete"
    for path in task["implementation_locations"] + task["verification_locations"]:
        assert (ROOT / path).is_file(), path
