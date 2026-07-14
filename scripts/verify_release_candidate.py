from __future__ import annotations

import json
from pathlib import Path

from scripts.report_release_status import build_release_status
from tools.validate_device_continuity_handoff import main as validate_handoff
from tools.validate_device_continuity_receipt import main as validate_receipt

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "STEGTALK_RELEASE_VERIFICATION.json"
PROPAGATION_TARGETS = [
    "StegVerse-Labs/Site",
    "GCAT-BCAT-Engine/Publisher",
    "StegVerse-Labs/admissibility-wiki",
    "StegVerse-002/stegguardian-wiki",
]


def build_release_verification() -> dict:
    status = build_release_status()
    if validate_handoff() != 0:
        raise AssertionError("Device Continuity handoff validation failed")
    if validate_receipt() != 0:
        raise AssertionError("Device Continuity receipt validation failed")

    ready_flags = {
        name: status[name]
        for name in (
            "local_candidate_ready",
            "public_discovery_ready",
            "shell_ready",
            "account_ready",
        )
    }
    if not all(ready_flags.values()):
        raise AssertionError("release-candidate lanes are incomplete")
    if status["production_ready"] is not False:
        raise AssertionError("local prototype must not claim production readiness")

    return {
        "schema_version": "1.0.0",
        "artifact_type": "stegtalk_release_verification",
        "repo": "StegVerse-Labs/StegTalk",
        "candidate_marker": "v0.1.0-local-prototype-candidate",
        "candidate_status": "verified_non_production_local_prototype",
        "production_ready": False,
        "ready_flags": ready_flags,
        "device_continuity_handoff_valid": True,
        "device_continuity_receipt_valid": True,
        "destination_validation_workflow_installed": True,
        "destination_validation_workflow_observed_run": False,
        "propagation_ready": True,
        "propagation_targets": PROPAGATION_TARGETS,
        "next_task": "propagate_verified_candidate_status",
    }


def main() -> None:
    verification = build_release_verification()
    OUTPUT.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
