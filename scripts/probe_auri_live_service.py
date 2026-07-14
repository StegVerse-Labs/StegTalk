#!/usr/bin/env python3
"""Probe a deployed AURI-L1 service and emit activation evidence without secrets."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fetch_json(url: str, timeout: float) -> dict[str, object]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError(f"unexpected HTTP status: {response.status}")
        value = json.loads(response.read().decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("health response must be a JSON object")
    return value


def verify_health(value: dict[str, object]) -> None:
    if value.get("entity_id") != "stegverse:auri":
        raise ValueError("unexpected entity_id")
    if value.get("activation_level") != "AURI-L1":
        raise ValueError("unexpected activation_level")
    if value.get("execution_authority") is not False:
        raise ValueError("AURI-L1 execution authority must remain false")
    if value.get("ready_for_advisory_requests") is not True:
        raise ValueError("service is not ready for advisory requests")
    if value.get("containment_fail_closed") is not False:
        raise ValueError("service reports fail-closed containment")
    supplied = value.get("health_sha256")
    body = {key: item for key, item in value.items() if key != "health_sha256"}
    if supplied != canonical_sha256(body):
        raise ValueError("health hash mismatch")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--output")
    args = parser.parse_args()
    health_url = args.base_url.rstrip("/") + "/health"
    try:
        health = fetch_json(health_url, args.timeout)
        verify_health(health)
        evidence_body = {
            "schema_version": "1.0.0",
            "evidence_type": "auri_live_health_probe",
            "entity_id": "stegverse:auri",
            "activation_level": "AURI-L1",
            "service_url": args.base_url.rstrip("/"),
            "health_url": health_url,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "health": health,
            "execution_performed": False,
            "result": "PASS",
        }
        evidence = {**evidence_body, "evidence_sha256": canonical_sha256(evidence_body)}
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(rendered)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
