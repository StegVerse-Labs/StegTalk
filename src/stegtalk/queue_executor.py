from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stegtalk.managed_completion import next_pending_task


def summarize_queue(queue: dict[str, Any]) -> dict[str, Any]:
    tasks = queue.get("tasks", [])
    complete = [task for task in tasks if task.get("status") == "complete"]
    ready = [task for task in tasks if task.get("status") == "ready"]
    pending = [task for task in tasks if task.get("status") == "pending"]
    return {
        "task_count": len(tasks),
        "complete_count": len(complete),
        "ready_count": len(ready),
        "pending_count": len(pending),
        "next_task": next_pending_task(queue),
        "production_ready": False,
    }


def mark_task(queue: dict[str, Any], task_id: str, status: str) -> dict[str, Any]:
    allowed = {"pending", "ready", "complete", "blocked"}
    if status not in allowed:
        raise ValueError(f"status must be one of {sorted(allowed)}")
    updated = json.loads(json.dumps(queue))
    for task in updated.get("tasks", []):
        if task.get("id") == task_id:
            task["status"] = status
            return updated
    raise KeyError(f"task not found: {task_id}")


def load_queue(root: Path) -> dict[str, Any]:
    return json.loads((root / "STEGTALK_TASK_QUEUE.json").read_text(encoding="utf-8"))


def verify_queue_execution(root: Path) -> dict[str, Any]:
    queue = load_queue(root)
    summary = summarize_queue(queue)
    if queue.get("production_ready") is not False:
        raise AssertionError("queue must keep production_ready false")
    if summary["task_count"] < 1:
        raise AssertionError("queue must contain tasks")
    return summary
