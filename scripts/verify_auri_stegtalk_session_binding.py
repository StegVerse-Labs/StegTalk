#!/usr/bin/env python3
"""Verify activation-gated AURI-L1 binding to StegTalk sessions."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stegtalk.auri.containment import ContainmentState
from stegtalk.auri.runtime import AuriRuntime, canonical_sha256
from stegtalk.auri.service import AuriService
from stegtalk.auri.session_binding import AuriStegTalkBinding, StegTalkSessionContext


def provider(prompt, context):
    return f"advisory:{context['action']}:{prompt}"


def context(**overrides):
    values = {
        "session_id": "session:stegtalk:auri:001",
        "user_entity_id": "stegverse:user:authorized",
        "authenticated": True,
        "device_attested": True,
        "relationship_contract_ref": "contract:auri-advisory:001",
        "activation_receipt_ref": "evidence/auri-activation-receipt.json",
    }
    values.update(overrides)
    return StegTalkSessionContext(**values)


def verify():
    service = AuriService(AuriRuntime(provider, "provider:verified-non-reference"), containment=ContainmentState())

    inactive = AuriStegTalkBinding(service, {"active": False, "activation_level": "AURI-L1"})
    inactive_result = inactive.bind(context())
    if inactive_result.bound or inactive_result.reason_code != "auri.activation.inactive":
        raise ValueError("inactive Auri did not fail closed")

    active_state = {"active": True, "activation_level": "AURI-L1"}
    binding = AuriStegTalkBinding(service, active_state)

    for invalid, reason in [
        (context(authenticated=False), "session.authentication.required"),
        (context(device_attested=False), "session.device_attestation.required"),
        (context(relationship_contract_ref=None), "session.relationship_contract.required"),
        (context(activation_receipt_ref=None), "auri.activation_receipt.missing"),
    ]:
        result = binding.bind(invalid)
        if result.bound or result.reason_code != reason:
            raise ValueError(f"expected {reason}")

    valid = binding.bind(context())
    if not valid.bound or valid.reason_code != "ok":
        raise ValueError("valid session did not bind")
    receipt = dict(valid.binding_receipt)
    digest = receipt.pop("receipt_sha256")
    if digest != canonical_sha256(receipt):
        raise ValueError("binding receipt hash mismatch")
    if receipt["execution_authority"] is not False or receipt["execution_performed"] is not False:
        raise ValueError("binding expanded execution authority")

    proposal = binding.submit_advisory(
        context(),
        {
            "instruction": "Explain the requested reversible change",
            "target": "StegVerse-Labs/StegTalk",
            "action": "prepare_repository_change",
            "policy_ref": "policy:auri-l1",
            "delegation_ref": "delegation:advisory-only",
            "rollback_ref": "git:revert",
        },
    )
    if proposal.execution_performed is not False:
        raise ValueError("session-bound advisory executed")

    return {
        "result": "PASS",
        "scope": "AURI-L1 StegTalk session integration boundary",
        "inactive_fail_closed_verified": True,
        "authentication_required": True,
        "device_attestation_required": True,
        "relationship_contract_required": True,
        "activation_receipt_required": True,
        "binding_receipt_hash_verified": True,
        "no_execution_verified": True,
        "integration_status": "installed_dormant_until_activation",
    }


def main():
    try:
        report = verify()
    except (KeyError, TypeError, ValueError, PermissionError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
