# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

## Current Build State

The repository is a verified non-production local prototype candidate with completed entity, messaging, routing, inbox, persistence, boundary, activation, discovery, shell, account/session, Device Continuity, release-candidate, validation-repair, mobile-shell, persistent session, receipt-chain, receipt persistence, managed-checkpoint, checkpoint-rotation, recovery-receipt, deterministic recovery-policy, and personal-data-control lanes.

Production ready: `false`
Manual tasks required: none
External tasks required: none

## Current Priority

Bind the personal-data control lifecycle to executable account/session deletion operations and signed completion receipts while preserving local-only, non-authorizing, fail-closed operation.

## Completed Local Prototype Queue

`STEGTALK_TASK_QUEUE.json` records `ST-001` through `ST-026` complete. Open task count: `0`.

## Personal Data Control Layer

```text
State: ACTIVATED_AND_CI_BOUND
Task: ST-026
Repository: StegVerse-Labs/StegTalk
External tasks: false
Authority granted: false
```

Installed locations:

```text
docs/PERSONAL_DATA_CONTROL_RUNTIME.md
schemas/personal-data-control.schema.json
runtime/personal-data-control.v1.json
scripts/check_personal_data_control.py
tests/test_personal_data_control.py
STEGTALK_TASK_QUEUE.json
.github/workflows/ci.yml
```

Task completion contract:

```text
Task object: runtime/personal-data-control.v1.json#/task
Validator: python scripts/check_personal_data_control.py
Success marker: STEGTALK_PERSONAL_DATA_CONTROL=PASS
Durable observer: .github/workflows/ci.yml
Status: complete
```

No external task, external actor, or unlocated session ownership is permitted. Missing controller or processor responses are represented as `CHANNEL_FAILED` or `PROCESSOR_PROPAGATION_PENDING`; they do not halt repository development.

## Non-halting continuation

```text
repository change
-> StegTalk CI runs
-> validator reports PASS or exact failed path/predicate
-> repository-local repair proceeds
-> queue and handoff remain authoritative
```

## Next Goal Declared

Next goal: `personal_data_control_executable_account_session_operations`

Required implementation locations:

```text
src/stegtalk/account_session.py
src/stegtalk/local_store.py
src/stegtalk/mobile_shell_session.py
receipts/personal-data-control/
```

Required behavior:

- authenticated request intake;
- deterministic scope inventory;
- local processing restriction;
- deletion of eligible local account/session data;
- explicit retained-data basis;
- processor-propagation tracking;
- appeal state;
- hash-bound completion receipt;
- no manual request-state transcription.

## Propagation Posture

Artifact: `STEGTALK_PROPAGATION_POSTURE.json`
Authority posture: `QUEUE_ONLY_NO_DOWNSTREAM_MUTATION`

No downstream mutation is currently authorized.

## Build Rule

Before continuing any StegTalk task, check this file first and treat it as the current source of truth.

## Authority boundary

```text
CI PASS != legal compliance adjudication
local deletion != processor deletion
request receipt != deletion completion
privacy claim != verified enforcement
```
