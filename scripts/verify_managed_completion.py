import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "STEGTALK_MANAGED_COMPLETION.md",
    "STEGTALK_TASK_QUEUE.json",
    "src/stegtalk/__init__.py",
    "src/stegtalk/entity_runtime.py",
    "src/stegtalk/entity_interactions.py",
    "src/stegtalk/entity_runtime_exports.py",
    "schemas/entity-runtime.schema.json",
    "examples/stegweather_entity_runtime_demo.json",
    "scripts/run_entity_runtime_demo.py",
    "tests/test_entity_runtime.py",
    "tests/test_entity_interactions.py",
    "tests/test_entity_runtime_demo.py",
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
