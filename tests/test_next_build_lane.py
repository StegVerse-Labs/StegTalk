from scripts.verify_next_build_lane import evaluate_lane


def test_next_build_lane_selects_public_discovery():
    result = evaluate_lane()
    assert result["ok"] is True
    assert result["selected_lane"] == "public_discovery"
    assert result["deferred_lane"] == "mobile_shell"
    assert result["next_task"] == "build_public_discovery_record_runtime"
    assert result["production_ready"] is False
