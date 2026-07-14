from scripts.verify_activation_readiness import evaluate_activation


def test_activation_readiness_reports_local_runtime_ready_not_production():
    result = evaluate_activation()
    assert result["ok"] is True
    assert result["local_runtime_ready"] is True
    assert result["production_ready"] is False
    assert result["missing_required_files"] == []
    assert "adapter_boundary" in result["completed_stages"]
    assert result["remaining_stages"] == ["release_candidate_review"]
