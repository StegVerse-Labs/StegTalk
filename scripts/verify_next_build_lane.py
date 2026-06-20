from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANE_PATH = ROOT / "STEGTALK_NEXT_BUILD_LANE.json"


def evaluate_lane() -> dict:
    lane = json.loads(LANE_PATH.read_text(encoding="utf-8"))
    if lane["production_ready"] is True:
        raise AssertionError("next build lane cannot mark production_ready")
    return {
        "ok": True,
        "selected_lane": lane["selected_lane"],
        "deferred_lane": lane["deferred_lane"],
        "next_task": lane["next_task"],
        "production_ready": lane["production_ready"],
    }


def main() -> None:
    print(json.dumps(evaluate_lane(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
