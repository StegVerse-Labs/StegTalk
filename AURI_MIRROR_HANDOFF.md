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

Progression is automation-first. Repository-side and adjacent-integration manual tasks are eliminated through workflows, validators, receipts, canonical intake paths, dormant evidence-gated bindings, and machine-readable handoffs. External authorization and infrastructure evidence are conditions, not repository tasks, and may not be presumed or fabricated.

## Core activation task status

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
  - Verifier: `scripts/verify_auri_containment.py`
  - Evidence: `evidence/auri-containment-verification.json`
- AURI-007 end-to-end activation proof: WAITING ON EXTERNAL AUTHORIZATION EVIDENCE

## Deployment and proof automation

Installed artifacts include:

```text
src/stegtalk/auri/service.py
src/stegtalk/auri/http_service.py
src/stegtalk/auri/__main__.py
Dockerfile.auri
auri/deployment/service-manifest.json
auri/deployment/deployment-contract.json
scripts/verify_auri_deployment_package.py
.github/workflows/auri-package-smoke.yml
evidence/auri-deployment-package.json
scripts/probe_auri_live_service.py
.github/workflows/auri-live-proof.yml
.github/workflows/auri-authorization-intake.yml
auri/authorization/README.md
auri/schemas/provider-binding.schema.json
auri/schemas/deployment-authorization.schema.json
scripts/verify_auri_activation_inputs.py
auri/schemas/activation-receipt.schema.json
scripts/build_auri_activation_receipt.py
scripts/finalize_auri_activation_state.py
evidence/auri-activation-gate-hardening.json
```

The package provides fail-closed startup, provider-neutral binding, standard-library HTTP health and advisory endpoints, non-root OCI packaging, credential-free smoke verification, canonical authorization intake, host-agnostic live probing, deterministic activation receipt construction, guarded active-state finalization, and automatic evidence commits only after every gate passes.

Default container startup is fail-closed. `AURI_PROVIDER_MODE=reference_echo` is limited to packaging and interface smoke verification and may never serve as production activation evidence.

Canonical authorization intake paths:

```text
auri/authorization/provider-binding.json
auri/authorization/deployment-authorization.json
```

When valid records arrive, the repository detects and verifies them automatically and dispatches live proof without manual workflow triggering, variable copying, or activation-state editing.

## Adjacent goal 1 — StegTalk session integration

Status:

```text
COMPLETE — INSTALLED DORMANT UNTIL CANONICAL ACTIVATION
```

Artifacts:

```text
src/stegtalk/auri/session_binding.py
auri/schemas/session-binding-receipt.schema.json
scripts/verify_auri_stegtalk_session_binding.py
.github/workflows/auri-stegtalk-integration.yml
```

The binding requires active canonical AURI-L1 state, activation receipt reference, authenticated session, device attestation, explicit relationship contract, valid session identity, and healthy containment. It emits a hash-addressed binding receipt and never grants or performs execution.

## Adjacent goal 2 — StegAgents proposal orchestration

Status:

```text
COMPLETE — REGISTERED DISABLED AND DORMANT UNTIL CANONICAL ACTIVATION
```

Authoritative sub-handoff:

```text
StegVerse-Labs/StegAgents/AURI_ORCHESTRATION_MIRROR_HANDOFF.md
```

Evidence:

```text
StegVerse-Labs/StegAgents/evidence/auri-orchestration-verification.json
```

The StegAgents registry now contains a disabled `Auri-L1-Advisory` entity. Proposal creation requires canonical activation evidence, activation receipt, warrant, pinned policy bundle, and relationship contract. Outputs remain proposal-only; StegCore and Continuity evidence remain external; execution authority remains false.

## Current activation state

```text
state: repository_and_adjacent_automation_complete_awaiting_external_authorization_evidence
active: false
completed: AURI-001 through AURI-006
current: AURI-007
manual_tasks_required: false
runtime_deployed: false
end_to_end_proof_passed: false
stegtalk_session_binding_installed: true
stegagents_orchestration_installed: true
```

Canonical state: `auri/activation-state.json`.

## External condition

```text
Code: deployment.authorization_evidence.pending
```

No repository-side or adjacent-integration manual action remains. Live activation waits for canonical externally authorized provider-binding and deployment-authorization records, a reachable persistent target, and a non-interactive credential path. None may be presumed, embedded, or fabricated.

## Automatic continuation

When authorized evidence becomes available, the repository automatically:

1. detects and verifies canonical authorization records;
2. deploys or confirms the OCI-packaged AURI-L1 service through the authorized path;
3. probes persistent live health;
4. verifies advisory allow, deny, and defer without execution;
5. verifies quarantine and revocation;
6. preserves StegCore and Continuity evidence;
7. builds and validates the final activation receipt;
8. runs the guarded state finalizer;
9. commits live evidence and changes `runtime_deployed`, `end_to_end_proof_passed`, and `active` only when independently supported;
10. enables the dormant StegTalk session and StegAgents proposal boundaries through canonical evidence rather than manual toggles.

## Monitoring

Auri Repo Watch remains daily because progression depends only on external authorization or deployment evidence. It resumes active processing when that evidence appears and does not repeatedly report the unchanged condition.

## Adjacent goal closure

```text
No further repository-controlled adjacent goals have been identified.
```

The remaining work is owned by an external future condition and its installed automatic continuation path. Repository incompleteness, pending deployment evidence, or future monitoring are not reasons to retain this conversation.

## Archive readiness

All unique decisions, artifacts, automation, adjacent integrations, validation rules, continuation paths, and the remaining external condition are durably represented in committed handoffs, state, evidence, schemas, workflows, and code. No future action requires access to this conversation. This session should be archived now.
