#!/usr/bin/env python3
"""Verify the credential-free AURI-L1 deployment package.

This proves packaging and fail-closed deployment defaults. It does not claim a
live deployment or activate Auri.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require_file(path: str) -> str:
    target = ROOT / path
    if not target.is_file():
        raise ValueError(f"missing required file: {path}")
    return target.read_text(encoding="utf-8")


def verify() -> dict[str, object]:
    contract = json.loads(require_file("auri/deployment/deployment-contract.json"))
    dockerfile = require_file("Dockerfile.auri")
    http_service = require_file("src/stegtalk/auri/http_service.py")
    entrypoint = require_file("src/stegtalk/auri/__main__.py")
    workflow = require_file(".github/workflows/auri-package-smoke.yml")

    if contract.get("entity_id") != "stegverse:auri":
        raise ValueError("deployment contract entity mismatch")
    if contract.get("activation_level") != "AURI-L1":
        raise ValueError("deployment contract activation level mismatch")
    posture = contract.get("default_posture", {})
    if posture.get("provider_mode") != "disabled":
        raise ValueError("default provider mode must be disabled")
    if posture.get("fail_closed") is not True:
        raise ValueError("default deployment posture must fail closed")
    if posture.get("execution_authority") is not False:
        raise ValueError("AURI-L1 deployment cannot have execution authority")

    required_live = set(contract.get("live_activation_requires", []))
    expected_live = {
        "authorized_hosting_target",
        "non_interactive_deployment_credential_path",
        "persistent_live_health_observation",
        "final_activation_receipt",
    }
    if not expected_live.issubset(required_live):
        raise ValueError("live activation evidence requirements are incomplete")

    for token in (
        "AURI_PROVIDER_MODE=disabled",
        "USER 65532:65532",
        'CMD ["python", "-m", "stegtalk.auri"]',
    ):
        if token not in dockerfile:
            raise ValueError(f"Dockerfile missing invariant: {token}")

    for token in (
        'provider_mode = os.getenv("AURI_PROVIDER_MODE", "disabled")',
        '"deployment.provider_not_configured"',
        'if self.path == "/health"',
        'if self.path != "/advisory"',
        '"execution_performed": False',
    ):
        if token not in http_service:
            raise ValueError(f"HTTP service missing invariant: {token}")

    if "serve()" not in entrypoint:
        raise ValueError("module entrypoint does not start the service")
    if "Build fail-closed OCI image" not in workflow:
        raise ValueError("package workflow does not build the OCI image")
    if "Verify fail-closed default health" not in workflow:
        raise ValueError("package workflow does not probe fail-closed health")
    if "Verify reference smoke mode" not in workflow:
        raise ValueError("package workflow does not probe the reference interface")

    return {
        "result": "PASS",
        "scope": "AURI-L1 credential-free deployment package",
        "oci_packaged": True,
        "fail_closed_default_verified": True,
        "reference_smoke_distinguished_from_live": True,
        "execution_authority": False,
        "live_deployment_verified": False,
        "active": False,
        "remaining_blocker": "deployment.target_or_credentials.required",
    }


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
