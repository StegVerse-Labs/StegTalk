import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_status_is_non_production_and_lists_targets():
    status = json.loads((ROOT / "STEGTALK_CANDIDATE_STATUS.json").read_text(encoding="utf-8"))
    assert status["candidate_status"] == "non_production_local_prototype_candidate"
    assert status["production_ready"] is False
    assert "account_ready" in status["required_ready_flags"]
    assert "tag_or_release_candidate_marker" in status["remaining_internal_tasks"]
    assert "StegVerse-Labs/Site" in status["external_update_targets"]
    assert "GCAT-BCAT-Engine/Publisher" in status["external_update_targets"]
