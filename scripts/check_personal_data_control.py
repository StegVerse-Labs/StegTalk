#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "docs/PERSONAL_DATA_CONTROL_RUNTIME.md"
SCHEMA = ROOT / "schemas/personal-data-control.schema.json"
RUNTIME = ROOT / "runtime/personal-data-control.v1.json"
TEST = ROOT / "tests/test_personal_data_control.py"
WORKFLOW = ROOT / ".github/workflows/ci.yml"
HANDOFF = ROOT / "STEGTALK_MIRROR_HANDOFF.md"
QUEUE = ROOT / "STEGTALK_TASK_QUEUE.json"

REQUIRED_STATES = {
    "NOT_REQUESTED", "RECEIVED", "IDENTITY_VERIFICATION_REQUIRED", "VERIFIED",
    "PROCESSING_RESTRICTED", "INVENTORY_COMPLETE", "DELETION_IN_PROGRESS",
    "PROCESSOR_PROPAGATION_PENDING", "COMPLETED", "PARTIALLY_DENIED", "DENIED",
    "APPEAL_OPEN", "CHANNEL_FAILED",
}
REQUIRED_SCOPES = {
    "account_profile", "identity_and_device_bindings", "session_state",
    "contact_and_routing_metadata", "local_inbox", "local_store",
    "message_receipts", "recovery_checkpoints", "recovery_policy_receipts",
    "analytics_and_diagnostics", "processor_copies",
}


def main() -> int:
    failures: list[str] = []
    for path in (STANDARD, SCHEMA, RUNTIME, TEST, WORKFLOW, HANDOFF, QUEUE):
        if not path.is_file():
            failures.append(f"missing {path.relative_to(ROOT)}")
    if failures:
        print("STEGTALK_PERSONAL_DATA_CONTROL=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    data = json.loads(RUNTIME.read_text(encoding="utf-8"))
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    workflow = WORKFLOW.read_text(encoding="utf-8")

    if data.get("state") != "ACTIVATED_AND_CI_BOUND":
        failures.append("runtime state is not ACTIVATED_AND_CI_BOUND")
    if data.get("external_tasks_required") is not False:
        failures.append("external_tasks_required must be false")
    if data.get("authority_granted") is not False:
        failures.append("authority_granted must be false")
    if REQUIRED_STATES - set(data.get("lifecycle_states", [])):
        failures.append("runtime lifecycle states incomplete")
    if REQUIRED_SCOPES - set(data.get("data_scopes", [])):
        failures.append("runtime data scopes incomplete")

    task = data.get("task", {})
    for path in task.get("implementation_locations", []) + task.get("verification_locations", []):
        if not (ROOT / path).is_file():
            failures.append(f"task location missing: {path}")
    queue_task = next((item for item in queue.get("tasks", []) if item.get("id") == "ST-026"), None)
    if not queue_task or queue_task.get("status") != "complete":
        failures.append("ST-026 is not complete in STEGTALK_TASK_QUEUE.json")
    if "python scripts/check_personal_data_control.py" not in workflow:
        failures.append("validator is not bound into CI")

    # Historical completion is machine-owned by the structured runtime and task
    # queue above. The current mirror handoff may legitimately advance to a new
    # active task (currently ST-029), so validation must not require stale prose
    # markers from ST-026 to remain in the handoff forever.

    if failures:
        print("STEGTALK_PERSONAL_DATA_CONTROL=FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("STEGTALK_PERSONAL_DATA_CONTROL=PASS")
    print("STEGTALK_PERSONAL_DATA_CONTROL_EXTERNAL_TASKS=false")
    print("STEGTALK_PERSONAL_DATA_CONTROL_AUTHORITY=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
