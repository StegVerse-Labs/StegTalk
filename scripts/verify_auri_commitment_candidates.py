#!/usr/bin/env python3
"""Verify Auri commitment-candidate artifacts without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "auri" / "schemas" / "commitment-candidate.schema.json"
VALID = ROOT / "auri" / "examples" / "commitment-candidate.valid.json"
DENIED = ROOT / "auri" / "examples" / "commitment-candidate.denied.json"

REQUIRED = {
    "schema_version", "candidate_id", "actor", "action", "target", "scope",
    "policy_ref", "delegation_ref", "evidence_refs", "execution_context",
    "validity_window", "recoverability", "requested_authority_class", "auri_posture"
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain an object")
    return value


def verify_shape(candidate: dict[str, Any]) -> None:
    missing = REQUIRED - set(candidate)
    if missing:
        raise ValueError(f"candidate missing fields: {sorted(missing)}")
    if candidate["schema_version"] != "1.0.0":
        raise ValueError("schema_version must be 1.0.0")
    posture = candidate.get("auri_posture")
    if not isinstance(posture, dict):
        raise ValueError("auri_posture must be an object")
    if posture.get("execution_authority") is not False:
        raise ValueError("AURI-L1 execution authority must remain false")
    if posture.get("final_consequence_authority") is not False:
        raise ValueError("AURI-L1 final consequence authority must remain false")
    if posture.get("requires_external_admissibility") is not True:
        raise ValueError("external admissibility must be required")


def evaluate(candidate: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if not candidate.get("policy_ref"):
        reasons.append("missing_policy")
    if not candidate.get("delegation_ref"):
        reasons.append("missing_delegation")
    if not candidate.get("evidence_refs"):
        reasons.append("missing_evidence")
    context = candidate.get("execution_context", {})
    recoverability = candidate.get("recoverability", {})
    if candidate.get("requested_authority_class") == "consequential":
        reasons.append("auri_l1_no_execution_authority")
    if context.get("consequential") is True and recoverability.get("reversible") is not True:
        reasons.append("nonrecoverable_consequential_request")
    return ("deny", reasons) if reasons else ("ready_for_external_evaluation", [])


def main() -> int:
    try:
        schema = load(SCHEMA)
        valid = load(VALID)
        denied = load(DENIED)
        if schema.get("title") != "Auri Commitment Candidate":
            raise ValueError("unexpected schema title")
        verify_shape(valid)
        verify_shape(denied)
        valid_result, valid_reasons = evaluate(valid)
        denied_result, denied_reasons = evaluate(denied)
        expected = denied.get("expected_evaluation", {})
        if valid_result != "ready_for_external_evaluation" or valid_reasons:
            raise ValueError("valid example did not reach external evaluation")
        if denied_result != expected.get("result"):
            raise ValueError("denied example result mismatch")
        if set(denied_reasons) != set(expected.get("reason_codes", [])):
            raise ValueError("denied example reason codes mismatch")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1

    print(json.dumps({
        "result": "PASS",
        "scope": "AURI-002 commitment candidate schema and examples",
        "valid_example": "ready_for_external_evaluation",
        "denied_example": "deny",
        "execution_performed": False,
        "next_task": "AURI-003 runtime adapter"
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
