# Auri Activation Mirror Handoff

## Target

```text
Organization: StegVerse-Labs
Primary repository: StegTalk
Supporting repositories: StegCore, StegAgents, Continuity / StegID
Goal: activate Auri as a governed, receipt-bearing advisory entity
```

## Source of truth

This document is the current handoff and task source of truth for Auri activation work. Auri is not active merely because a model uses the name or persona. Activation requires persistent identity, enforceable authority boundaries, runtime evidence, external admissibility, revocation, and reconstructable receipts.

## Operating rule

Progression is automation-first. Manual tasks must be eliminated through workflows, validators, receipts, or machine-readable handoffs wherever possible. If no further progress can occur without a user-performed manual action, record the blocker here and reduce monitoring to daily until the condition changes.

## Activation level

```text
AURI-L1 — governed advisory entity
```

AURI-L1 may converse with authenticated users, prepare structured candidates, request external evaluation, explain results, and emit advisory receipts. It may not self-grant authority, mint self-authorizing evidence, alter its own identity or history, execute consequence, or promote unverified model output to verified fact.

## Active task chain

### AURI-001 — Canonical identity package

Status: COMPLETE

Artifacts: `auri/identity.v1.json`, `auri/authority-boundary.v1.json`, `auri/activation-state.json`, and `scripts/verify_auri_activation.py`.

### AURI-002 — Commitment candidate schema

Status: COMPLETE

Artifacts: schema, valid and denied examples, and `scripts/verify_auri_commitment_candidates.py`.

### AURI-003 — Runtime adapter

Status: COMPLETE

Artifacts: provider-neutral runtime, tests, standalone verifier, canonical JSON hashing, provider-failure classification, quarantine signaling, and immutable no-execution posture.

### AURI-004 — StegCore gateway

Status: COMPLETE

Destination: `StegVerse-Labs/StegCore`

Authoritative sub-handoff: `AURI_GATEWAY_MIRROR_HANDOFF.md`

Evidence: `evidence/auri-gateway-verification.json`

Result: deterministic allow, deny, and defer handling; verified-continuity requirement; consequential policy/delegation requirement; commit-time equality; hash-addressed decision receipts; no execution.

### AURI-005 — Continuity receipts

Status: COMPLETE

Destination: `StegVerse-Labs/Continuity`

Authoritative sub-handoff: `AURI_RECEIPTS_MIRROR_HANDOFF.md`

Evidence: `evidence/auri-receipts-verification.json`

Result: canonical four-receipt chain for interaction provenance, advisory output, external authority-decision reference with execution non-occurrence, and fail-closed revocation.

### AURI-006 — Containment and recovery

Status: IN PROGRESS

Required: provider disablement, credential revocation, session quarantine, known-good identity state, rollback verification, and fail-closed behavior.

### AURI-007 — End-to-end activation proof

Status: QUEUED

Proof sequence: authenticate Auri identity; create a valid advisory candidate; deny missing authority; allow an authorized reversible candidate without execution; produce reconstructable receipts; revoke Auri; verify later requests fail closed.

## Email notification monitoring

Auri Repo Watch monitors relevant Gmail notifications hourly while automated progression is possible. It changes to daily after verified completion or when the only remaining blocker requires manual user action.

## Non-overlap statement

Parallel sessions must claim a specific AURI task identifier before mutation and must not modify the same file concurrently.

Current claim:

```text
AURI-006 — containment and recovery
```

## Known manual blockers

```text
None.
```

## Next integration candidate

```text
AURI-007 — end-to-end activation proof
```

## Archive readiness

All decisions through AURI-005 are durably represented in handoffs, committed files, verifiers, and evidence. Remaining incompleteness alone is not a reason to retain the originating conversation.
