# Auri Activation Mirror Handoff

## Target

```text
Organization: StegVerse-Labs
Primary repository: StegTalk
Supporting repositories: StegCore, Continuity / StegID, StegAgents
Goal: activate Auri as a governed, receipt-bearing AURI-L1 advisory entity
```

## Source of truth

This document is the current handoff and task source of truth. Auri is not active merely because a model uses its name. Activation requires persistent identity, enforceable authority boundaries, runtime evidence, external admissibility, revocation, reconstructable receipts, and verified live deployment.

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
- AURI-007 end-to-end activation proof: BLOCKED AT LIVE DEPLOYMENT EVIDENCE
  - Reference verifier: `scripts/verify_auri_end_to_end.py`
  - Service boundary: `src/stegtalk/auri/service.py`
  - Service tests: `tests/test_auri_service.py`
  - Service manifest: `auri/deployment/service-manifest.json`
  - Service verifier: `scripts/verify_auri_service_boundary.py`
  - Result boundary: the runtime is packaged behind a provider-neutral, hosting-neutral, hash-addressed health and advisory interface; no live persistent deployment is claimed.

## Deployment-neutral package

The package exposes:

- hash-addressed health state;
- authenticated advisory request intake;
- immutable AURI-L1 no-execution posture;
- provider-neutral runtime binding;
- hosting-neutral manifest;
- quarantine-driven fail-closed health;
- no silent conversion of package readiness into live activation.

## Current activation state

```text
state: packaged_awaiting_live_deployment_evidence
active: false
completed: AURI-001 through AURI-006
current: AURI-007
service_packaged: true
runtime_deployed: false
end_to_end_proof_passed: false
```

Canonical state: `auri/activation-state.json`.

## Current claim

```text
AURI-007 — live deployment evidence and final activation receipt
```

## Known manual blocker

```text
Code: deployment.target_or_credentials.required
```

A live persistent runtime cannot be truthfully deployed or independently health-checked without an authorized hosting target and a non-interactive deployment credential path. Neither may be presumed, embedded, or fabricated. Automated work resumes when those become available.

This blocker does not require redesign or code scaffolding. The deployment-neutral service boundary, manifest, tests, and verifier are installed.

## Resume condition

```text
authorized deployment target + non-interactive credential path
```

After the resume condition exists, the automated continuation is:

1. deploy the packaged AURI-L1 service;
2. capture live health evidence;
3. exercise advisory allow/deny/defer without execution;
4. exercise quarantine and revocation;
5. preserve cross-repository receipts;
6. issue the final activation receipt;
7. set `runtime_deployed`, `end_to_end_proof_passed`, and `active` true only when independently supported.

## Email monitoring

Auri Repo Watch must now run daily because the only remaining activation blocker requires an authorized external deployment target or credential path. It should return to higher-frequency monitoring only when the blocker is removed.

## Next integration candidate after activation

```text
AURI-L1-STEGTALK-INTEGRATION — bind the active Auri service to authenticated StegTalk sessions without expanding execution authority
```

## Archive readiness

All unique decisions, artifacts, progress, and the deployment blocker are durably represented here, in committed files, sub-handoffs, verifiers, state, and evidence. The complete thread is ready for archiving without any additional part of the thread needed to move forward.
