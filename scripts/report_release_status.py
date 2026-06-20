from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_PATH = ROOT / "STEGTALK_ACTIVATION_STATE.json"
REVIEW_PATH = ROOT / "STEGTALK_LOCAL_PROTOTYPE_REVIEW.json"


def build_release_status() -> dict:
    activation = json.loads(ACTIVATION_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    missing_activation = [path for path in activation["required_files"] if not (ROOT / path).exists()]
    missing_review = [path for path in review["evidence_files"] + review["test_files"] if not (ROOT / path).exists()]
    local_ready = activation["local_runtime_ready"] and review["local_candidate_ready"] and not missing_activation and not missing_review
    status = {
        "schema_version": "1.0.0",
        "status_type": "stegtalk_release_status",
        "repo": "StegVerse-Labs/StegTalk",
        "activation_target": activation["activation_target"],
        "local_candidate_ready": local_ready,
        "production_ready": False,
        "completed_stages": activation["completed_stages"],
        "remaining_stages": review["remaining_work"],
        "missing_activation_files": missing_activation,
        "missing_review_files": missing_review,
        "next_task": "managed_release_handoff",
    }
    if activation["production_ready"] or review["production_ready"]:
        raise AssertionError("release status cannot report production readiness from local prototype artifacts")
    if missing_activation or missing_review:
        raise AssertionError("release status evidence is incomplete")
    return status


def main() -> None:
    print(json.dumps(build_release_status(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
