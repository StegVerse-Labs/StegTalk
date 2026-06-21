from scripts.verify_release_handoff import evaluate_handoff


def test_release_handoff_names_next_lane_without_production_claim():
    result = evaluate_handoff()
    assert result["ok"] is True
    assert result["local_candidate_ready"] is True
    assert result["production_ready"] is False
    assert result["next_build_lane"] == "account_model"
    assert result["completed_lane_count"] >= 18
