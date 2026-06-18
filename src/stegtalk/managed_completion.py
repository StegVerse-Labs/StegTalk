from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
QUEUE_PATH = ROOT / "STEGTALK_TASK_QUEUE.json"
STATE_PATH = ROOT / "STEGTALK_MANAGEMENT_STATE.json"


def load_queue(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / "STEGTALK_TASK_QUEUE.json").read_text(encoding="utf-8"))


def next_pending_task(queue: dict[str, Any]) -> dict[str, Any] | None:
    pending = [task for task in queue.get("tasks", []) if task.get("status") == "pending"]
    if not pending:
        return None
    return sorted(pending, key=lambda task: task.get("priority", 999))[0]


def build_management_state(queue: dict[str, Any]) -> dict[str, Any]:
    task = next_pending_task(queue)
    return {
        "schema_version": "1.1.0",
        "state_type": "stegtalk_managed_completion_state",
        "repo": queue.get("repo"),
        "branch": queue.get("branch"),
        "production_ready": False,
        "managed_completion_capable": True,
        "next_task": task,
        "open_task_count": len([t for t in queue.get("tasks", []) if t.get("status") == "pending"]),
    }


def verify_management_state(root: Path = ROOT) -> dict[str, Any]:
    queue = load_queue(root)
    state = build_management_state(queue)
    required = [
        "STEGTALK_MANAGED_COMPLETION.md",
        "STEGTALK_TASK_QUEUE.json",
        "STEGTALK_MANAGEMENT_STATE.json",
        "src/stegtalk/__init__.py",
        "src/stegtalk/managed_completion.py",
        ".github/workflows/ci.yml",
        "scripts/verify_managed_completion.py",
        "scripts/managed_next_task.py",
    ]
    missing = [path for path in required if not (root / path).exists()]
    if queue.get("production_ready") is not False:
        raise AssertionError("queue must keep production_ready false")
    if missing:
        raise AssertionError(f"missing required management files: {missing}")
    return state
