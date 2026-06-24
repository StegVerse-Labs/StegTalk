from scripts.report_wiki_target_blocker import build_blocker_report


def test_wiki_target_blocker_is_explicit_and_manual_inventory_free():
    report = build_blocker_report()
    assert report["ok"] is True
    assert report["current_status"] == "target_repo_not_found"
    assert report["open_check_count"] == 1
    assert report["open_checks"][0]["id"] == "SW-001"
    assert report["manual_inventory_required"] is False
    assert report["manual_tasks_remaining"] == []
