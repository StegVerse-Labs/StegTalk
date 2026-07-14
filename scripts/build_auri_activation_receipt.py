#!/usr/bin/env python3
"""Build a deterministic AURI-L1 activation receipt candidate from verified evidence refs."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployment-target-ref", required=True)
    parser.add_argument("--service-health-ref", required=True)
    parser.add_argument("--provider-binding-ref", required=True)
    parser.add_argument("--stegcore-decision-evidence-ref", required=True)
    parser.add_argument("--continuity-receipt-chain-ref", required=True)
    parser.add_argument("--containment-test-ref", required=True)
    parser.add_argument("--revocation-test-ref", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    refs = vars(args)
    missing = [name for name, value in refs.items() if name != "output" and not str(value).strip()]
    if missing:
        raise SystemExit("missing required references: " + ", ".join(sorted(missing)))

    body = {
        "schema_version": "1.0.0",
        "receipt_type": "auri_activation",
        "entity_id": "stegverse:auri",
        "activation_level": "AURI-L1",
        "deployment_target_ref": args.deployment_target_ref,
        "service_health_ref": args.service_health_ref,
        "provider_binding_ref": args.provider_binding_ref,
        "stegcore_decision_evidence_ref": args.stegcore_decision_evidence_ref,
        "continuity_receipt_chain_ref": args.continuity_receipt_chain_ref,
        "containment_test_ref": args.containment_test_ref,
        "revocation_test_ref": args.revocation_test_ref,
        "execution_authority": False,
        "active": True,
        "issued_at": datetime.now(timezone.utc).isoformat(),
    }
    receipt = {**body, "receipt_sha256": canonical_sha256(body)}
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
