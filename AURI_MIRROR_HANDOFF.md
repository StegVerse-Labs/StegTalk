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

## Existing foundation

StegTalk Entity Runtime v1 already establishes that:

- Auri is an identity distinct from a provider, model, endpoint, device, repository, or storage location.
- Auri may create, interpret, or route Change Requests.
- Auri must not silently execute consequence.
- Authority evaluation remains external to Auri.

Canonical reference:

```text
docs/STEGTALK_ENTITY_RUNTIME_V1.md
```

## Activation level

Initial target:

```text
AURI-L1 — governed advisory entity
```

AURI-L1 may:

- converse with an authenticated user;
- interpret approved context;
- create structured change requests and commitment candidates;
- request readiness and authority evaluation;
- explain allow, deny, defer, blocked, and not-ready results;
- emit signed or hash-addressed advisory receipts.

AURI-L1 may not:

- grant itself authority;
- mint continuity evidence used to authorize itself;
- alter its own identity declaration, policy, delegation, or receipt history;
- execute consequential actions;
- represent a user without an explicit relationship contract;
- treat model output as verified fact without evidence classification.

## Active task chain

### AURI-001 — Canonical identity package

Status: IN PROGRESS

Deliverables:

```text
auri/identity.v1.json
auri/authority-boundary.v1.json
auri/activation-state.json
```

Completion criteria:

- stable entity identifier;
- provider-independent identity;
- declared capabilities and prohibitions;
- revocation and quarantine fields;
- explicit AURI-L1 status.

Verification:

```text
python scripts/verify_auri_activation.py
```

### AURI-002 — Commitment candidate schema

Status: QUEUED

Deliverables:

```text
auri/schemas/commitment-candidate.schema.json
auri/examples/commitment-candidate.valid.json
auri/examples/commitment-candidate.denied.json
```

### AURI-003 — Runtime adapter

Status: QUEUED

Deliverables:

```text
src/stegtalk/auri/
```

Required modules:

- provider-neutral model adapter;
- structured proposal output;
- evidence classification;
- session identity binding;
- no-execution default.

### AURI-004 — StegCore gateway

Status: QUEUED

Destination:

```text
StegVerse-Labs/StegCore
```

Required modules:

- Auri actor declaration intake;
- readiness evaluation request;
- authority evaluation request;
- commit-time equality check;
- allow / deny / defer receipt handling.

### AURI-005 — Continuity receipts

Status: QUEUED

Destination:

```text
Continuity / StegID receipt-governance layer
```

Required artifacts:

- interaction provenance receipt;
- advisory-output receipt;
- authority-decision reference;
- execution non-occurrence or execution reference;
- revocation receipt.

### AURI-006 — Containment and recovery

Status: QUEUED

Required controls:

- provider disablement;
- credential revocation;
- session quarantine;
- known-good identity state;
- rollback and recovery verification;
- fail-closed behavior.

### AURI-007 — End-to-end activation proof

Status: QUEUED

Proof sequence:

1. authenticate Auri identity;
2. create a valid advisory change request;
3. deny a request missing authority;
4. allow a properly authorized reversible candidate without executing it at AURI-L1;
5. produce reconstructable receipts;
6. revoke Auri;
7. verify subsequent requests fail closed.

## Email notification monitoring

Email notifications involving Auri activation repositories are monitored outside this repository through the user-authorized scheduler.

Search scope should include notifications mentioning:

```text
Auri
StegVerse-Labs/StegTalk
StegVerse-Labs/StegCore
StegVerse-Labs/StegAgents
Continuity
StegID
AURI_MIRROR_HANDOFF
AURI-001 through AURI-007
```

The monitor may triage and act on safe repository work supported by available authority. It must not silently approve financial, legal, identity, deployment, or other consequence-bearing actions.

## Non-overlap statement

Parallel sessions must claim a specific AURI task identifier before mutation and must not modify the same file concurrently.

Current claim:

```text
AURI-001 — canonical identity package
```

## Next integration candidate

```text
AURI-002 — commitment candidate schema
```

## Archive readiness

This conversation may be archived once all unique decisions are represented in this handoff, committed files, task records, receipts, or email-monitor automation. Remaining repository incompleteness alone is not a reason to retain the conversation.
