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
    "src/stegtalk/message_envelope.py",
    "src/stegtalk/contact_routing.py",
    "src/stegtalk/local_inbox.py",
    "src/stegtalk/local_store.py",
    "schemas/entity-runtime.schema.json",
    "schemas/message-envelope.schema.json",
    "examples/stegweather_entity_runtime_demo.json",
    "examples/stegtalk_message_envelope_demo.json",
    "examples/contact_routing_demo.json",
    "examples/local_inbox_projection_demo.json",
    "examples/local_store_demo.json",
    "scripts/run_entity_runtime_demo.py",
    "scripts/run_message_envelope_demo.py",
    "scripts/run_contact_routing_demo.py",
    "scripts/run_local_inbox_demo.py",
    "scripts/run_local_store_demo.py",
    "tests/test_entity_runtime.py",
    "tests/test_entity_interactions.py",
    "tests/test_entity_runtime_demo.py",
    "tests/test_message_envelope.py",
    "tests/test_contact_routing.py",
    "tests/test_local_inbox.py",
    "tests/test_local_store.py",
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
