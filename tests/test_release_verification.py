import json
from pathlib import Path

from scripts.verify_release_candidate import build_release_verification

ROOT = Path(__file__).resolve().parents[1]


def test_release_verification_is_fail_closed_and_propagation_ready():
    verification = build_release_verification()
    assert verification["candidate_status"] == "verified_non_production_local_prototype"
    assert verification["production_ready"] is False
    assert verification["device_continuity_handoff_valid"] is True
    assert verification["device_continuity_receipt_valid"] is True
    assert verification["destination_validation_workflow_installed"] is True
    assert verification["propagation_ready"] is True
    assert len(verification["propagation_targets"]) == 4


def test_committed_release_verification_matches_builder():
    expected = build_release_verification()
    actual = json.loads((ROOT / "STEGTALK_RELEASE_VERIFICATION.json").read_text(encoding="utf-8"))
    assert actual == expected
