from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_validation_repair_is_green_and_automatic() -> None:
    repair = json.loads((ROOT / "STEGTALK_VALIDATION_REPAIR.json").read_text(encoding="utf-8"))

    assert repair["repo"] == "StegVerse-Labs/StegTalk"
    assert repair["production_ready"] is False
    assert repair["manual_tasks_required"] == []
    assert repair["workflow_policy"]["new_workflows_added"] is False
    assert repair["verification_state"] == "VERIFIED_GREEN"

    failures = repair["observed_failures"]
    for run_id in (29304441633, 29304441639, 29304803059, 29304883307, 29305018795):
        assert any(entry["run_id"] == run_id for entry in failures)

    passes = {entry["workflow"]: entry for entry in repair["final_observed_passes"]}
    assert passes["StegTalk Managed Completion"]["run_id"] == 29305087620
    assert passes["device-continuity"]["run_id"] == 29305087641
    assert passes["Test Readiness"]["run_id"] == 29305087611
    assert all(entry["result"] == "PASS" for entry in passes.values())


def test_project_version_is_pep440_compatible() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.0.0+managed.completion"' in pyproject
    assert 'version = "0.0.0-managed-completion"' not in pyproject


def test_device_continuity_workflow_installs_pytest() -> None:
    workflow = (ROOT / ".github" / "workflows" / "device-continuity.yml").read_text(encoding="utf-8")
    assert "python -m pip install pytest" in workflow
    assert "python -m pytest tests/test_device_continuity_handoff.py tests/test_device_continuity_receipt.py" in workflow


def test_managed_completion_workflow_has_diagnostic_lanes() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "Run entity runtime tests" in workflow
    assert "Run messaging runtime tests" in workflow
    assert "Run local-state runtime tests" in workflow
    assert "Run release-state tests" in workflow
