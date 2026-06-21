from scripts.report_release_status import build_release_status


def test_release_status_reports_ready_lanes_not_production():
    status = build_release_status()
    assert status["local_candidate_ready"] is True
    assert status["public_discovery_ready"] is True
    assert status["shell_ready"] is True
    assert status["production_ready"] is False
    assert status["missing_activation_files"] == []
    assert status["missing_review_files"] == []
    assert status["missing_discovery_files"] == []
    assert status["missing_shell_files"] == []
