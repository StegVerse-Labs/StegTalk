from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_validation_repair_is_fail_closed_and_automatic() -> None:
    repair = json.loads((ROOT / "STEGTALK_VALIDATION_REPAIR.json").read_text(encoding="utf-8"))

    assert repair["repo"] == "StegVerse-Labs/StegTalk"
    assert repair["production_ready"] is False
    assert repair["manual_tasks_required"] == []
    assert repair["workflow_policy"]["new_workflows_added"] is False
    assert repair["verification_state"] == "PENDING_MANAGED_COMPLETION_RERUN"

    failures = repair["observed_failures"]
    assert any(entry["run_id"] == 29304441633 for entry in failures)
    assert any(entry["run_id"] == 29304441639 for entry in failures)
    assert any(entry["run_id"] == 29304803059 for entry in failures)

    passes = {entry["workflow"]: entry for entry in repair["observed_passes"]}
    assert passes["device-continuity"]["result"] == "PASS"
    assert passes["Test Readiness"]["result"] == "PASS"


def test_project_version_is_pep440_compatible() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.0.0+managed.completion"' in pyproject
    assert 'version = "0.0.0-managed-completion"' not in pyproject


def test_device_continuity_workflow_installs_pytest() -> None:
    workflow = (ROOT / ".github" / "workflows" / "device-continuity.yml").read_text(encoding="utf-8")
    assert "python -m pip install pytest" in workflow
    assert "python -m pytest tests/test_device_continuity_handoff.py tests/test_device_continuity_receipt.py" in workflow
