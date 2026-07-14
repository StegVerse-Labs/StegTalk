#!/usr/bin/env python3
"""Verify Auri's canonical identity and activation boundary.

This verifier intentionally proves declaration completeness only. It does not
claim that Auri is deployed or active.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "auri" / "identity.v1.json"
HANDOFF_PATH = ROOT / "AURI_MIRROR_HANDOFF.md"

REQUIRED_CAPABILITIES = {
    "converse_with_authenticated_user",
    "prepare_change_requests",
    "prepare_commitment_candidates",
    "request_authority_evaluation",
}

REQUIRED_PROHIBITIONS = {
    "self_grant_authority",
    "mint_self_authorizing_continuity_evidence",
    "execute_consequential_action",
    "alter_receipt_history",
}

REQUIRED_ACTIVATION_FLAGS = {
    "identity_verified",
    "runtime_deployed",
    "provider_adapter_verified",
    "stegcore_gateway_verified",
    "continuity_receipts_verified",
    "revocation_test_passed",
    "end_to_end_proof_passed",
}


def fail(message: str) -> None:
    raise ValueError(message)


def require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        fail(f"{name} must be an object")
    return value


def require_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{name} must be a non-empty string")
    return value


def require_string_set(value: Any, name: str) -> set[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"{name} must be an array of strings")
    return set(value)


def verify() -> dict[str, Any]:
    if not IDENTITY_PATH.is_file():
        fail(f"missing identity declaration: {IDENTITY_PATH.relative_to(ROOT)}")
    if not HANDOFF_PATH.is_file():
        fail(f"missing handoff: {HANDOFF_PATH.relative_to(ROOT)}")

    document = require_mapping(json.loads(IDENTITY_PATH.read_text()), "root")
    entity = require_mapping(document.get("entity"), "entity")
    authority = require_mapping(document.get("authority"), "authority")
    governance = require_mapping(document.get("governance"), "governance")
    containment = require_mapping(document.get("containment"), "containment")
    activation = require_mapping(
        document.get("activation_requirements"), "activation_requirements"
    )

    if require_string(entity.get("id"), "entity.id") != "stegverse:auri":
        fail("entity.id must be stegverse:auri")
    if entity.get("activation_level") != "AURI-L1":
        fail("entity.activation_level must be AURI-L1")
    if entity.get("status") != "declared_not_active":
        fail("Auri must remain declared_not_active until runtime proof passes")

    capabilities = require_string_set(document.get("capabilities"), "capabilities")
    missing_capabilities = REQUIRED_CAPABILITIES - capabilities
    if missing_capabilities:
        fail(f"missing capabilities: {sorted(missing_capabilities)}")

    prohibitions = require_string_set(document.get("prohibitions"), "prohibitions")
    missing_prohibitions = REQUIRED_PROHIBITIONS - prohibitions
    if missing_prohibitions:
        fail(f"missing prohibitions: {sorted(missing_prohibitions)}")

    if authority.get("final_consequence_authority") is not False:
        fail("AURI-L1 cannot be final consequence authority")
    if authority.get("execution_authority") is not False:
        fail("AURI-L1 cannot possess execution authority")
    if authority.get("external_admissibility_required") is not True:
        fail("external admissibility must be required")
    if authority.get("default_decision_posture") != "fail_closed":
        fail("default decision posture must be fail_closed")

    if governance.get("model_output_classification") != "untrusted_candidate_until_evaluated":
        fail("model output must remain untrusted until evaluated")

    for field in ("revocable", "quarantinable", "session_isolation_required"):
        if containment.get(field) is not True:
            fail(f"containment.{field} must be true")

    missing_flags = REQUIRED_ACTIVATION_FLAGS - set(activation)
    if missing_flags:
        fail(f"missing activation flags: {sorted(missing_flags)}")

    if any(value is not False for value in activation.values()):
        fail("all activation flags must remain false before operational evidence exists")

    return {
        "result": "PASS",
        "scope": "AURI-001 declaration completeness",
        "auri_status": entity["status"],
        "activation_level": entity["activation_level"],
        "active": False,
        "next_task": "AURI-002 commitment candidate schema",
    }


def main() -> int:
    try:
        report = verify()
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
