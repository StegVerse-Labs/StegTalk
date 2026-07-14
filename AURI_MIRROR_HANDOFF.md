# Auri Activation Mirror Handoff

## Target

```text
Organization: StegVerse-Labs
Primary repository: StegTalk
Supporting repositories: StegCore, Continuity / StegID, StegAgents
Goal: activate Auri as a governed, receipt-bearing AURI-L1 advisory entity
```

## Source of truth

This document is the current handoff and task source of truth. Auri is not active merely because a model uses its name. Activation requires persistent identity, enforceable authority boundaries, runtime evidence, external admissibility, revocation, reconstructable receipts, verified live deployment, canonical authorization evidence, and a final activation receipt.

## Operating rule

Progression is automation-first. Repository-side manual tasks are eliminated through workflows, validators, receipts, canonical intake paths, and machine-readable handoffs. External authorization and infrastructure evidence are conditions, not repository tasks, and may not be presumed or fabricated.

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
- AURI-007 end-to-end activation proof: WAITING ON EXTERNAL AUTHORIZATION EVIDENCE
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
  - Live probe: `scripts/probe_auri_live_service.py`
  - Gated live-proof workflow: `.github/workflows/auri-live-proof.yml`
  - Automatic authorization intake: `.github/workflows/auri-authorization-intake.yml`
  - Canonical intake path: `auri/authorization/`
  - Provider binding schema: `auri/schemas/provider-binding.schema.json`
  - Deployment authorization schema: `auri/schemas/deployment-authorization.schema.json`
  - Authorization verifier: `scripts/verify_auri_activation_inputs.py`
  - Activation receipt schema: `auri/schemas/activation-receipt.schema.json`
  - Activation receipt builder: `scripts/build_auri_activation_receipt.py`
  - Evidence-gated state finalizer: `scripts/finalize_auri_activation_state.py`
  - Gate-hardening evidence: `evidence/auri-activation-gate-hardening.json`

## Deployment and proof package

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
- host-agnostic live health probing;
- canonical provider-binding authorization;
- canonical deployment-target authorization;
- matching credential-reference validation;
- automatic detection of canonical authorization records;
- automatic live-proof dispatch after authorization verification;
- gated cross-repository evidence checks;
- deterministic activation receipt construction;
- evidence-gated active-state finalization;
- automated commit of activation evidence only after all gates pass;
- explicit separation between reference smoke mode and live activation.

Default container startup is fail-closed. `AURI_PROVIDER_MODE=reference_echo` exists only for automated packaging and interface smoke verification and may never be used as production activation evidence.

The canonical authorization intake paths are:

```text
auri/authorization/provider-binding.json
auri/authorization/deployment-authorization.json
```

When both records are committed, the intake workflow verifies them and dispatches the live-proof workflow automatically. No person must trigger the workflow, copy evidence into repository variables, or edit activation state manually.

## Current activation state

```text
state: repository_automation_complete_awaiting_external_authorization_evidence
active: false
completed: AURI-001 through AURI-006
current: AURI-007
service_packaged: true
oci_packaged: true
live_proof_automation_installed: true
authorization_document_schemas_installed: true
authorization_input_verifier_installed: true
authorization_intake_automation_installed: true
evidence_gated_state_finalizer_installed: true
manual_tasks_required: false
runtime_deployed: false
end_to_end_proof_passed: false
```

Canonical state: `auri/activation-state.json`.

## Current claim

```text
AURI-007 — externally authorized live deployment evidence and final activation receipt
```

## External condition

```text
Code: deployment.authorization_evidence.pending
```

No repository-side manual action remains. Live activation waits for canonical externally authorized provider-binding and deployment-authorization records, a reachable persistent target, and a non-interactive credential path. None may be presumed, embedded, or fabricated.

## Automatic continuation

When canonical authorization records and authorized deployment evidence become available, the repository automatically:

1. detects the canonical records;
2. verifies provider and deployment authorization;
3. dispatches live proof;
4. deploys or confirms the OCI-packaged AURI-L1 service through the authorized path;
5. probes live health;
6. verifies advisory allow, deny, and defer without execution;
7. verifies quarantine and revocation;
8. preserves cross-repository receipts;
9. builds and validates the final activation receipt;
10. runs the guarded state finalizer;
11. commits live evidence and sets `runtime_deployed`, `end_to_end_proof_passed`, and `active` true only when independently supported.

## Email monitoring

Auri Repo Watch remains daily because progression now depends only on external authorization or deployment evidence. It resumes active processing when that evidence appears and does not repeatedly report the unchanged condition.

## Next integration candidate after activation

```text
AURI-L1-STEGTALK-INTEGRATION — bind the active Auri service to authenticated StegTalk sessions without expanding execution authority
```

## Archive readiness

All repository-side tasks, automation, handoffs, validation rules, continuation paths, and the remaining external condition are durably represented in committed records. No future action requires access to this conversation. This session may be archived now.
