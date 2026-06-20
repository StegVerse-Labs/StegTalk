from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF_PATH = ROOT / "STEGTALK_RELEASE_HANDOFF.json"


def evaluate_handoff() -> dict:
    handoff = json.loads(HANDOFF_PATH.read_text(encoding="utf-8"))
    if handoff["production_ready"] is True:
        raise AssertionError("release handoff cannot mark production_ready")
    return {
        "ok": handoff["handoff_condition_met"],
        "local_candidate_ready": handoff["local_candidate_ready"],
        "production_ready": handoff["production_ready"],
        "next_build_lane": handoff["next_build_lane"],
        "completed_lane_count": len(handoff["completed_local_lanes"]),
    }


def main() -> None:
    print(json.dumps(evaluate_handoff(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
