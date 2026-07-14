#!/usr/bin/env python3
"""Verify AURI-L1 service packaging and fail-closed health behavior."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stegtalk.auri.containment import ContainmentState, quarantine_provider
from stegtalk.auri.runtime import AuriRuntime
from stegtalk.auri.service import AuriService

MANIFEST = ROOT / "auri" / "deployment" / "service-manifest.json"


def provider(prompt, context):
    return f"proposal for {context['action']}: {prompt}"


def request():
    return {
        "session": {
            "session_id": "session:service:verification",
            "user_entity_id": "stegverse:user:authorized",
            "authenticated": True,
        },
        "instruction": "Prepare a reversible repository change",
        "target": "StegVerse-Labs/StegTalk",
        "action": "prepare_repository_change",
        "policy_ref": "policy:auri-l1",
        "delegation_ref": "delegation:advisory-only",
        "rollback_ref": "git:revert",
    }


def verify():
    manifest = json.loads(MANIFEST.read_text())
    if manifest["deployment_status"] != "packaged_not_live":
        raise ValueError("service manifest must not claim live deployment")
    if manifest["request_contract"]["execution_authority"] is not False:
        raise ValueError("AURI-L1 service cannot have execution authority")

    service = AuriService(AuriRuntime(provider, "provider:verification"))
    health = service.health()
    if health.status != "ready" or not health.ready_for_advisory_requests:
        raise ValueError("healthy reference service did not report ready")
    if health.execution_authority is not False or len(health.health_sha256) != 64:
        raise ValueError("health boundary is not hash-addressed advisory-only")

    result = service.submit(request())
    if result.execution_performed is not False:
        raise ValueError("service performed execution")

    quarantined = AuriService(
        AuriRuntime(provider, "provider:verification"),
        containment=quarantine_provider(ContainmentState(), "provider.failure"),
    )
    if quarantined.health().status != "fail_closed":
        raise ValueError("quarantined service did not fail closed")
    try:
        quarantined.submit(request())
    except PermissionError:
        pass
    else:
        raise ValueError("quarantined service accepted a request")

    return {
        "result": "PASS",
        "scope": "AURI-L1 deployment-neutral service boundary",
        "packaged": True,
        "live_deployment_verified": False,
        "health_hash_verified": True,
        "advisory_request_verified": True,
        "no_execution_verified": True,
        "quarantine_fail_closed_verified": True,
        "next_task": "live deployment evidence or automated local service activation",
    }


if __name__ == "__main__":
    try:
        report = verify()
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        raise SystemExit(1)
    print(json.dumps(report, indent=2, sort_keys=True))
