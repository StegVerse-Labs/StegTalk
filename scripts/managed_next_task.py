import json
from pathlib import Path

from stegtalk.managed_completion import load_queue, next_pending_task, build_management_state

ROOT = Path(__file__).resolve().parents[1]
queue = load_queue(ROOT)
state = build_management_state(queue)
task = next_pending_task(queue)

print(json.dumps({
    "ok": True,
    "managed_completion_capable": True,
    "production_ready": False,
    "next_task": task,
    "state": state,
}, indent=2))
