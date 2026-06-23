from scripts.report_wiki_staging_install import build_install_report


def test_wiki_staging_install_manifest_has_no_missing_sources():
    report = build_install_report()
    assert report["ok"] is True
    assert report["target_repo_status"] == "not_found"
    assert report["copy_count"] == 10
    assert report["missing_sources"] == []
    assert report["manual_tasks_remaining"] == []
