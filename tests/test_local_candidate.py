import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_local_candidate_marker_is_non_production():
    marker = json.loads((ROOT / "STEGTALK_LOCAL_CANDIDATE.json").read_text(encoding="utf-8"))
    assert marker["production_ready"] is False
    assert marker["source_handoff"] == "STEGTALK_MIRROR_HANDOFF.md"
    assert marker["source_status"] == "STEGTALK_CANDIDATE_STATUS.json"
    assert len(marker["next_targets"]) == 4
