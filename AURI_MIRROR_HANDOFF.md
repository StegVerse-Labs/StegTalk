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

Progression is automation-first. Manual tasks must be eliminated through workflows, validators, receipts, and machine-readable handoffs wherever possible. If no further progress can occur without a user-performed action, record the blocker and keep monitoring daily.

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
  - HTTP adapter: `src/stegtalk/auri/http_service.py`
  - Module entrypoint: `src/stegtalk/auri/__main__.py`
  - OCI package: `Dockerfile.auri`
  - Service manifest: `auri/deployment/service-manifest.json`
  - Deployment contract: `auri/deployment/deployment-contract.json`
  - Package verifier: `scripts/verify_auri_deployment_package.py`
  - Credential-free smoke workflow: `.github/workflows/auri-package-smoke.yml`
  - Package evidence: `evidence/auri-deployment-package.json`

## Deployment-neutral package

The package now exposes:

- hash-addressed health state;
- authenticated advisory request intake;
- immutable AURI-L1 no-execution posture;
- provider-neutral runtime binding;
- hosting-neutral manifest and deployment contract;
- fail-closed default provider mode;
- standard-library HTTP health and advisory endpoints;
- non-root OCI container packaging;
- credential-free automated image build and smoke probes;
- explicit separation between reference smoke mode and live activation.

Default container startup is fail-closed. `AURI_PROVIDER_MODE=reference_echo` exists only for automated packaging and interface smoke verification and may never be used as production activation evidence.

## Current activation state

```text
state: oci_packaged_awaiting_live_deployment_evidence
active: false
completed: AURI-001 through AURI-006
current: AURI-007
service_packaged: true
oci_packaged: true
credential_free_smoke_workflow_installed: true
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

All credential-free build, packaging, verification-contract, and smoke-workflow work is installed. A live persistent runtime still cannot be truthfully deployed or independently health-checked without an authorized hosting target and a non-interactive deployment credential path. Neither may be presumed, embedded, or fabricated.

## Resume condition

```text
authorized deployment target + non-interactive credential path
```

After the resume condition exists, the automated continuation is:

1. bind a non-reference provider adapter;
2. deploy the OCI-packaged AURI-L1 service;
3. capture persistent live health evidence;
4. exercise advisory allow, deny, and defer without execution;
5. exercise quarantine and revocation;
6. preserve cross-repository receipts;
7. issue the final activation receipt;
8. set `runtime_deployed`, `end_to_end_proof_passed`, and `active` true only when independently supported.

## Email monitoring

Auri Repo Watch remains daily because the only remaining activation blocker requires authorized external deployment infrastructure or credentials. It should return to higher-frequency monitoring only when the blocker is removed.

## Next integration candidate after activation

```text
AURI-L1-STEGTALK-INTEGRATION — bind the active Auri service to authenticated StegTalk sessions without expanding execution authority
```

## Archive readiness

All unique decisions, artifacts, progress, and the deployment blocker are durably represented here, in committed files, sub-handoffs, verifiers, state, and evidence. The complete thread is ready for archiving without any additional part of the thread needed to move forward.
