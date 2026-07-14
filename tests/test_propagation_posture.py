import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_propagation_posture_is_queue_only_and_non_production():
    posture = json.loads((ROOT / "STEGTALK_PROPAGATION_POSTURE.json").read_text(encoding="utf-8"))
    assert posture["source_status"] == "verified_non_production_local_prototype"
    assert posture["production_ready"] is False
    assert posture["authority_posture"] == "QUEUE_ONLY_NO_DOWNSTREAM_MUTATION"
    assert posture["manual_tasks_required"] == []
    assert len(posture["destinations"]) == 4
    assert all(item["handoff_reviewed"] is True for item in posture["destinations"])
    assert all(item["result"] != "MUTATE_NOW" for item in posture["destinations"])
