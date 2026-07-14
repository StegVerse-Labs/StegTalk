# Auri Activation Mirror Handoff

## Target

```text
Organization: StegVerse-Labs
Primary repository: StegTalk
Supporting repositories: StegCore, Continuity / StegID, StegAgents
Goal: activate Auri as a governed, receipt-bearing AURI-L1 advisory entity
```

## Source of truth

This document is the current handoff and task source of truth. Auri is not active merely because a model uses its name. Activation requires persistent identity, enforceable authority boundaries, runtime evidence, external admissibility, revocation, reconstructable receipts, and verified deployment.

## Operating rule

Progression is automation-first. Manual tasks must be eliminated through workflows, validators, receipts, and machine-readable handoffs wherever possible. If no further progress can occur without a user-performed action, record the blocker and reduce monitoring to daily.

## Task status

- AURI-001 canonical identity package: COMPLETE
- AURI-002 commitment candidate schema: COMPLETE
- AURI-003 provider-neutral advisory runtime: COMPLETE
- AURI-004 StegCore gateway: COMPLETE
  - Handoff: `StegVerse-Labs/StegCore/AURI_GATEWAY_MIRROR_HANDOFF.md`
  - Evidence: `StegVerse-Labs/StegCore/evidence/auri-gateway-verification.json`
- AURI-005 Continuity receipts: COMPLETE
  - Handoff: `StegVerse-Labs/Continuity/AURI_RECEIPTS_MIRROR_HANDOFF.md`
  - Evidence: `StegVerse-Labs/Continuity/evidence/auri-receipts-verification.json`
- AURI-006 containment and recovery: COMPLETE
  - Runtime: `src/stegtalk/auri/containment.py`
  - Tests: `tests/test_auri_containment.py`
  - Verifier: `scripts/verify_auri_containment.py`
  - Evidence: `evidence/auri-containment-verification.json`
- AURI-007 end-to-end activation proof: IN PROGRESS
  - Reference verifier: `scripts/verify_auri_end_to_end.py`
  - Current result boundary: reference runtime can prove identity, advisory generation, missing-authority denial, external allow-without-execution representation, receipt references, revocation, and post-revocation fail-closed behavior.
  - Deployment is not yet verified; Auri remains inactive.

## Current activation state

```text
state: activation_proof_in_progress
active: false
completed: AURI-001 through AURI-006
current: AURI-007
runtime_deployed: false
end_to_end_proof_passed: false
```

Canonical state: `auri/activation-state.json`.

## Current claim

```text
AURI-007 — end-to-end activation proof and deployment boundary
```

## Known manual blockers

```text
None currently. Deployment credentials or an external hosting target must not be presumed; first build an automated deployment-neutral verification workflow.
```

## Next integration candidate

```text
AURI-L1-DEPLOYMENT — automated deployment-neutral runtime packaging, health evidence, and activation receipt
```

## Email monitoring

Auri Repo Watch remains hourly while automated progress is possible. It changes to daily after verified completion or when only a manual user action remains.

## Archive readiness

All decisions through AURI-006 and the AURI-007 reference-proof boundary are durably represented here, in committed files, sub-handoffs, verifiers, and evidence. The thread is not required for continuation.
