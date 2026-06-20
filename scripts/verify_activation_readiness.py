from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "STEGTALK_ACTIVATION_STATE.json"


def evaluate_activation() -> dict:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    missing = [path for path in state["required_files"] if not (ROOT / path).exists()]
    stage_ready = not missing and state["local_runtime_ready"] is True
    result = {
        "ok": stage_ready,
        "activation_target": state["activation_target"],
        "production_ready": state["production_ready"],
        "local_runtime_ready": stage_ready,
        "completed_stages": state["completed_stages"],
        "remaining_stages": state["remaining_stages"],
        "missing_required_files": missing,
    }
    if result["production_ready"] is True:
        raise AssertionError("activation verifier cannot mark this prototype production_ready")
    if missing:
        raise AssertionError(f"missing activation files: {missing}")
    return result


def main() -> None:
    print(json.dumps(evaluate_activation(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
