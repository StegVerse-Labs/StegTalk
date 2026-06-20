import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_shell_review_references_existing_files():
    review = json.loads((ROOT / "STEGTALK_SHELL_REVIEW.json").read_text(encoding="utf-8"))
    assert review["production_ready"] is False
    assert review["shell_ready"] is True
    assert review["next_task"] == "refresh_release_status_after_shell"
    assert all((ROOT / path).exists() for path in review["completed_shell_files"])
