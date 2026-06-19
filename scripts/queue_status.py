import json
from pathlib import Path

from stegtalk.queue_executor import verify_queue_execution

ROOT = Path(__file__).resolve().parents[1]
summary = verify_queue_execution(ROOT)
print(json.dumps({
    "ok": True,
    "queue_execution_capable": True,
    "production_ready": False,
    "summary": summary,
}, indent=2))
