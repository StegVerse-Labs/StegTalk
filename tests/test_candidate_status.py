import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_status_is_verified_non_production_and_lists_targets():
    status = json.loads((ROOT / "STEGTALK_CANDIDATE_STATUS.json").read_text(encoding="utf-8"))
    assert status["candidate_status"] == "verified_non_production_local_prototype"
    assert status["candidate_marker"] == "v0.1.0-local-prototype-candidate"
    assert status["production_ready"] is False
    assert "account_ready" in status["required_ready_flags"]
    assert status["remaining_internal_tasks"] == []
    assert "propagate_verified_candidate_status" in status["remaining_ecosystem_tasks"]
    assert "StegVerse-Labs/Site" in status["external_update_targets"]
    assert "GCAT-BCAT-Engine/Publisher" in status["external_update_targets"]
