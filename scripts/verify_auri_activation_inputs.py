#!/usr/bin/env python3
"""Verify externally supplied AURI-L1 provider and deployment authorizations.

This verifier does not deploy Auri and cannot activate it. It validates canonical,
non-reference inputs before the live-proof workflow may proceed.
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


def verify_hash(document: dict[str, Any], field: str) -> None:
    claimed = document.get(field)
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise ValueError(f"{field} must be a sha256 hex string")
    body = {key: value for key, value in document.items() if key != field}
    if canonical_sha256(body) != claimed:
        raise ValueError(f"{field} does not match canonical document")


def verify_provider(document: dict[str, Any]) -> None:
    required = ("binding_id", "provider_id", "provider_mode", "credential_ref", "authorized_by")
    if document.get("auri_entity_id") != "stegverse:auri" or document.get("activation_level") != "AURI-L1":
        raise ValueError("provider binding identity or level is invalid")
    if document.get("provider_mode") in {None, "", "reference_echo"} or document.get("reference_only") is not False:
        raise ValueError("provider binding must be non-reference")
    if document.get("scope") != "advisory_only" or document.get("execution_authority") is not False:
        raise ValueError("provider binding exceeds AURI-L1 authority")
    if document.get("revocable") is not True:
        raise ValueError("provider binding must be revocable")
    if any(not isinstance(document.get(field), str) or not document[field].strip() for field in required):
        raise ValueError("provider binding required fields are missing")
    verify_hash(document, "binding_sha256")


def verify_deployment(document: dict[str, Any]) -> None:
    required = ("authorization_id", "target_id", "base_url", "credential_ref", "authorized_by")
    if document.get("auri_entity_id") != "stegverse:auri":
        raise ValueError("deployment authorization identity is invalid")
    if not str(document.get("base_url", "")).startswith("https://"):
        raise ValueError("deployment base_url must use https")
    if document.get("authorized_scope") != "AURI-L1-advisory-only":
        raise ValueError("deployment scope is invalid")
    if document.get("persistent_runtime") is not True or document.get("reference_environment") is not False:
        raise ValueError("deployment must be persistent and non-reference")
    if document.get("execution_authority") is not False or document.get("revocable") is not True:
        raise ValueError("deployment authority boundary is invalid")
    if any(not isinstance(document.get(field), str) or not document[field].strip() for field in required):
        raise ValueError("deployment authorization required fields are missing")
    verify_hash(document, "authorization_sha256")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider-binding", type=Path, required=True)
    parser.add_argument("--deployment-authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        provider = load(args.provider_binding)
        deployment = load(args.deployment_authorization)
        verify_provider(provider)
        verify_deployment(deployment)
        if provider["credential_ref"] != deployment["credential_ref"]:
            raise ValueError("provider and deployment credential references do not match")
        report = {
            "result": "PASS",
            "scope": "AURI-L1 authorized activation inputs",
            "provider_binding_id": provider["binding_id"],
            "deployment_authorization_id": deployment["authorization_id"],
            "deployment_target": deployment["base_url"],
            "execution_authority": False,
            "activation_performed": False,
        }
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        report = {"result": "FAIL", "error": str(exc), "activation_performed": False}

    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(text, end="")
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
