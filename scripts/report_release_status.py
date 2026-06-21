from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_PATH = ROOT / "STEGTALK_ACTIVATION_STATE.json"
REVIEW_PATH = ROOT / "STEGTALK_LOCAL_PROTOTYPE_REVIEW.json"
DISCOVERY_FILES = [
    "src/stegtalk/public_discovery.py",
    "src/stegtalk/discovery_index.py",
    "scripts/run_discovery_demo.py",
    "tests/test_public_discovery.py",
    "tests/test_discovery_index.py",
    "tests/test_discovery_demo.py",
]
SHELL_FILES = [
    "STEGTALK_MOBILE_SHELL_PLAN.json",
    "STEGTALK_SHELL_REVIEW.json",
    "src/stegtalk/shell_state.py",
    "src/stegtalk/shell_actions.py",
    "scripts/run_shell_demo.py",
    "tests/test_shell_state.py",
    "tests/test_shell_actions.py",
    "tests/test_shell_demo.py",
    "tests/test_shell_review.py",
]


def build_release_status() -> dict:
    activation = json.loads(ACTIVATION_PATH.read_text(encoding="utf-8"))
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    missing_activation = [path for path in activation["required_files"] if not (ROOT / path).exists()]
    missing_review = [path for path in review["evidence_files"] + review["test_files"] if not (ROOT / path).exists()]
    missing_discovery = [path for path in DISCOVERY_FILES if not (ROOT / path).exists()]
    missing_shell = [path for path in SHELL_FILES if not (ROOT / path).exists()]
    local_ready = activation["local_runtime_ready"] and review["local_candidate_ready"] and not missing_activation and not missing_review
    discovery_ready = not missing_discovery
    shell_ready = not missing_shell
    status = {
        "schema_version": "1.2.0",
        "status_type": "stegtalk_release_status",
        "repo": "StegVerse-Labs/StegTalk",
        "activation_target": activation["activation_target"],
        "local_candidate_ready": local_ready,
        "public_discovery_ready": discovery_ready,
        "shell_ready": shell_ready,
        "production_ready": False,
        "completed_stages": activation["completed_stages"] + ["public_discovery", "shell_lane"],
        "remaining_stages": [stage for stage in review["remaining_work"] if stage not in {"public_discovery", "mobile_shell"}],
        "missing_activation_files": missing_activation,
        "missing_review_files": missing_review,
        "missing_discovery_files": missing_discovery,
        "missing_shell_files": missing_shell,
        "next_task": "refresh_release_handoff_after_shell",
    }
    if activation["production_ready"] or review["production_ready"]:
        raise AssertionError("release status cannot report production readiness from local prototype artifacts")
    if missing_activation or missing_review or missing_discovery or missing_shell:
        raise AssertionError("release status evidence is incomplete")
    return status


def main() -> None:
    print(json.dumps(build_release_status(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
