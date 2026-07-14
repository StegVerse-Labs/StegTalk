#!/usr/bin/env python3
"""Finalize Auri activation state only from validated live evidence.

The script never deploys services or grants execution authority. It updates a supplied
state file only after all required evidence documents independently assert PASS and the
activation receipt is canonical.
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path
from typing import Any


def canonical_sha256(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def require_pass(document: dict[str, Any], label: str) -> None:
    if document.get("result") != "PASS":
        raise ValueError(f"{label} evidence is not PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--activation-inputs", type=Path, required=True)
    parser.add_argument("--live-health", type=Path, required=True)
    parser.add_argument("--activation-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        state = load(args.state)
        inputs = load(args.activation_inputs)
        health = load(args.live_health)
        receipt = load(args.activation_receipt)
        require_pass(inputs, "activation input")
        require_pass(health, "live health")
        if receipt.get("auri_entity_id") != "stegverse:auri" or receipt.get("activation_level") != "AURI-L1":
            raise ValueError("activation receipt identity is invalid")
        if receipt.get("active") is not True or receipt.get("execution_authority") is not False:
            raise ValueError("activation receipt posture is invalid")
        claimed = receipt.get("receipt_sha256")
        body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        if not isinstance(claimed, str) or canonical_sha256(body) != claimed:
            raise ValueError("activation receipt hash is invalid")
        gates = state.setdefault("activation_gates", {})
        for gate in (
            "identity_verified", "commitment_schema_verified", "service_packaged",
            "oci_packaged", "provider_adapter_verified", "stegcore_gateway_verified",
            "continuity_receipts_verified", "containment_verified", "revocation_test_passed",
        ):
            if gates.get(gate) is not True:
                raise ValueError(f"pre-existing gate is not verified: {gate}")
        gates["runtime_deployed"] = True
        gates["end_to_end_proof_passed"] = True
        state.update({
            "state": "active_AURI-L1_advisory",
            "active": True,
            "manual_tasks_required": False,
            "completed_tasks": [f"AURI-{index:03d}" for index in range(1, 8)],
            "current_task": None,
            "next_task": "AURI-L1-STEGTALK-INTEGRATION",
            "manual_blocker": None,
        })
        state.setdefault("evidence", {}).update({
            "activation_inputs": str(args.activation_inputs),
            "live_health": str(args.live_health),
            "activation_receipt": str(args.activation_receipt),
        })
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
        report = {"result": "PASS", "active": True, "execution_authority": False, "output": str(args.output)}
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        report = {"result": "FAIL", "active": False, "error": str(exc)}
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
