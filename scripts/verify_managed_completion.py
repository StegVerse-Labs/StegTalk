import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "STEGTALK_MANAGED_COMPLETION.md",
    "STEGTALK_TASK_QUEUE.json",
    "src/stegtalk/__init__.py",
    ".github/workflows/ci.yml",
]

missing = [path for path in REQUIRED if not (ROOT / path).exists()]
queue = json.loads((ROOT / "STEGTALK_TASK_QUEUE.json").read_text(encoding="utf-8"))
assert queue["production_ready"] is False
assert not missing, f"missing managed completion files: {missing}"
print(json.dumps({
    "ok": True,
    "managed_completion_capable": True,
    "production_ready": False,
    "required_files": REQUIRED,
    "task_count": len(queue["tasks"]),
}, indent=2))
