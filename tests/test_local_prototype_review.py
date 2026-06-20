from scripts.verify_local_prototype_review import evaluate_review


def test_local_prototype_review_is_candidate_ready_not_production():
    result = evaluate_review()
    assert result["ok"] is True
    assert result["local_candidate_ready"] is True
    assert result["production_ready"] is False
    assert result["missing_review_evidence"] == []
    assert result["next_task"] == "build_release_status_verifier"
