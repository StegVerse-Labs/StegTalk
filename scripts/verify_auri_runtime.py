#!/usr/bin/env python3
"""Verify AURI-003 runtime invariants without external services."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stegtalk.auri import AuriProviderError, AuriRuntime, AuriSession, canonical_sha256


def fail(message: str) -> None:
    raise ValueError(message)


def verify() -> dict[str, object]:
    session = AuriSession(
        session_id="verification-session",
        user_entity_id="stegverse:user:verifier",
        authenticated=True,
        relationship_contract_ref="contract:auri-verification",
    )
    runtime = AuriRuntime(
        lambda prompt, context: f"{context['action']}::{prompt}",
        "deterministic-verification-provider",
    )
    result = runtime.propose(
        session=session,
        instruction="Prepare an advisory-only reversible candidate",
        target="StegVerse-Labs/StegTalk",
        action="verify_auri_runtime",
        evidence_refs=["auri/identity.v1.json", "auri/authority-boundary.v1.json"],
        policy_ref="policy:auri-l1",
        delegation_ref="delegation:advisory-only",
        consequential=False,
        reversible=True,
        rollback_ref="git:revert",
    )

    if result.execution_performed is not False:
        fail("AURI-L1 must never report execution")
    if result.candidate["auri_posture"]["execution_authority"] is not False:
        fail("AURI-L1 execution authority must remain false")
    if result.advisory_receipt["candidate_sha256"] != canonical_sha256(result.candidate):
        fail("candidate receipt hash is not canonical")
    if result.advisory_receipt["authority_decision_ref"] is not None:
        fail("runtime must not invent an authority decision")

    failing = AuriRuntime(lambda _prompt, _context: (_ for _ in ()).throw(TimeoutError("test")), "failing-provider")
    try:
        failing.propose(
            session=session,
            instruction="Prepare an advisory candidate",
            target="StegVerse-Labs/StegTalk",
            action="provider_failure_test",
        )
    except AuriProviderError as exc:
        if not exc.quarantine_required:
            fail("provider failures must require quarantine")
        if exc.receipt.get("execution_performed") is not False:
            fail("provider failure must not execute")
        if exc.receipt.get("retry_performed") is not False:
            fail("provider failure must not silently retry")
    else:
        fail("provider failure did not fail closed")

    return {
        "result": "PASS",
        "scope": "AURI-003 provider-neutral advisory runtime",
        "provider_adapter_verified": True,
        "canonical_receipts_verified": True,
        "provider_quarantine_signal_verified": True,
        "execution_performed": False,
        "next_task": "AURI-004 StegCore gateway",
    }


def main() -> int:
    try:
        report = verify()
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
