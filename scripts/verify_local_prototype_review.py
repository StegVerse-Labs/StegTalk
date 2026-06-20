from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_PATH = ROOT / "STEGTALK_LOCAL_PROTOTYPE_REVIEW.json"


def evaluate_review() -> dict:
    review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    missing = [path for path in review["evidence_files"] + review["test_files"] if not (ROOT / path).exists()]
    if review["production_ready"] is True:
        raise AssertionError("local prototype review cannot mark production_ready")
    if missing:
        raise AssertionError(f"missing review evidence: {missing}")
    return {
        "ok": True,
        "local_candidate_ready": review["local_candidate_ready"],
        "production_ready": review["production_ready"],
        "next_task": review["next_task"],
        "missing_review_evidence": missing,
    }


def main() -> None:
    print(json.dumps(evaluate_review(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
