# Auri Activation Mirror Handoff

## Target

```text
Organization: StegVerse-Labs
Primary repository: StegTalk
Supporting repositories: StegCore, StegAgents, Continuity / StegID
Goal: activate Auri as a governed, receipt-bearing advisory entity
```

## Source of truth

This document is the current handoff and task source of truth for Auri activation work.

Auri is not active merely because a model uses the name or persona. Activation requires a persistent identity, enforceable authority boundary, runtime evidence, external admissibility for consequential actions, revocation, and reconstructable receipts.

## Operating rule

Progression is automation-first. Manual tasks must be eliminated through workflows, validators, receipts, or machine-readable handoffs wherever possible. If no further progress can occur without a user-performed manual action, record the blocker here and reduce monitoring to daily until the condition changes.

## Existing foundation

StegTalk Entity Runtime v1 establishes that Auri is distinct from any provider or model, may create or route Change Requests, must not silently execute consequence, and is not final authority.

Canonical reference:

```text
docs/STEGTALK_ENTITY_RUNTIME_V1.md
```

## Activation level

```text
AURI-L1 — governed advisory entity
```

AURI-L1 may converse with authenticated users, interpret approved context, prepare structured candidates, request external evaluation, explain results, and emit advisory receipt candidates.

AURI-L1 may not self-grant authority, mint self-authorizing evidence, alter its identity or receipt history, execute consequential actions, represent a user without an explicit contract, or promote unverified model output to verified fact.

## Active task chain

### AURI-001 — Canonical identity package

Status: COMPLETE

Artifacts:

```text
auri/identity.v1.json
auri/authority-boundary.v1.json
auri/activation-state.json
scripts/verify_auri_activation.py
```

Result: stable provider-independent AURI-L1 identity, explicit prohibitions, revocation/quarantine posture, and fail-closed activation state are installed.

### AURI-002 — Commitment candidate schema

Status: COMPLETE

Artifacts:

```text
auri/schemas/commitment-candidate.schema.json
auri/examples/commitment-candidate.valid.json
auri/examples/commitment-candidate.denied.json
scripts/verify_auri_commitment_candidates.py
```

Result: valid candidates advance only to external evaluation; missing policy, delegation, evidence, authority, or recoverability produces deterministic denial reasons. No execution occurs.

### AURI-003 — Runtime adapter

Status: IN PROGRESS

Installed:

```text
src/stegtalk/auri/__init__.py
src/stegtalk/auri/runtime.py
tests/test_auri_runtime.py
```

Implemented:

- provider-neutral callable adapter;
- authenticated session binding;
- structured proposal output;
- model output classified as untrusted until evaluated;
- advisory receipt candidate generation;
- immutable no-execution AURI-L1 posture;
- tests for authentication, provider output type, and no-execution behavior.

Remaining completion criteria:

- run repository CI/tests and retain passing evidence;
- add deterministic canonical JSON hashing for receipts;
- add provider failure classification and quarantine signal;
- update activation state only after verification evidence exists.

### AURI-004 — StegCore gateway

Status: QUEUED

Destination: `StegVerse-Labs/StegCore`

Required: Auri actor intake, readiness and authority evaluation requests, commit-time equality check, and allow/deny/defer receipt handling.

### AURI-005 — Continuity receipts

Status: QUEUED

Destination: Continuity / StegID receipt-governance layer.

Required: interaction provenance, advisory-output receipt, authority-decision reference, execution non-occurrence or execution reference, and revocation receipt.

### AURI-006 — Containment and recovery

Status: QUEUED

Required: provider disablement, credential revocation, session quarantine, known-good identity state, rollback verification, and fail-closed behavior.

### AURI-007 — End-to-end activation proof

Status: QUEUED

Proof sequence:

1. authenticate Auri identity;
2. create a valid advisory candidate;
3. deny a request missing authority;
4. allow a properly authorized reversible candidate without executing it at AURI-L1;
5. produce reconstructable receipts;
6. revoke Auri;
7. verify subsequent requests fail closed.

## Email notification monitoring

The user-authorized Auri Repo Watch monitors relevant Gmail notifications hourly while automated progression is possible. It changes to daily after verified completion or when the only remaining blocker requires manual user action.

## Non-overlap statement

Parallel sessions must claim a specific AURI task identifier before mutation and must not modify the same file concurrently.

Current claim:

```text
AURI-003 — provider-neutral runtime adapter
```

## Known manual blockers

```text
None.
```

## Next integration candidate

```text
AURI-004 — StegCore gateway
```

## Archive readiness

This conversation may be archived once all unique decisions are represented in this handoff, committed files, task records, receipts, or monitoring automation. Remaining repository incompleteness alone is not a reason to retain the conversation.
