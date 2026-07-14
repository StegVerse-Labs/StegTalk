# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

## Current Build State

The repo is a verified non-production local prototype candidate with the following built lanes:

- entity runtime
- message envelope
- contact routing
- local inbox projection
- local persistence
- boundary module
- activation readiness
- local prototype review
- release status
- public discovery record/index/search/demo
- shell plan/state/actions/demo/review
- account model/session
- Device Continuity Layer handoff boundary
- Device Continuity Layer destination validation
- Device Continuity Layer destination receipt
- Device Continuity Layer validation workflow
- release-candidate verification artifact and test
- destination-handoff propagation posture and test
- validation-install repair artifact and tests

## Current Priority

Complete pull-request validation repair and merge only after the managed-completion rerun passes. Preserve `production_ready: false` and the queue-only downstream posture.

## Local Candidate Verification Complete

Destination: `StegVerse-Labs/StegTalk`

- `STEGTALK_RELEASE_HANDOFF.json`
- `STEGTALK_CANDIDATE_STATUS.json`
- `STEGTALK_LOCAL_CANDIDATE.json`
- `STEGTALK_RELEASE_VERIFICATION.json`
- `scripts/verify_release_candidate.py`
- `tests/test_release_verification.py`

Candidate marker: `v0.1.0-local-prototype-candidate`
Status: `verified_non_production_local_prototype`
Production ready: `false`

## Validation Repair

Artifact: `STEGTALK_VALIDATION_REPAIR.json`
Tests: `tests/test_validation_repair.py`, `tests/test_managed_completion.py`
Branch: `repair-validation-install`
Manual tasks required: none
New workflows added: false

Observed and repaired failures:

1. `StegTalk Managed Completion`, run `29304441633`, failed at editable installation because the project version was not PEP 440 compliant. `pyproject.toml` now uses `0.0.0+managed.completion`.
2. `device-continuity`, run `29304441639`, failed because `pytest` was not installed. The existing workflow now installs `pytest`.
3. `StegTalk Managed Completion`, run `29304803059`, passed installation and management-state commands, then failed because `tests/test_managed_completion.py` still expected `ST-001`. The test now derives the highest-priority pending task from the queue and confirms `ST-025`.

Observed passes after the first repair:

- `device-continuity`, run `29304803099`: PASS
- `Test Readiness`, run `29304803088`: PASS

Verification state: `PENDING_MANAGED_COMPLETION_RERUN`

Required merge evidence:

- `StegTalk Managed Completion`: PASS
- `device-continuity`: PASS
- `Test Readiness`: PASS

## Device Continuity Install Complete

Source: `StegVerse-Labs/device-continuity-layer`
Destination: `StegVerse-Labs/StegTalk`
Candidate tag: `v0.1.0-offline-baseline`
Status: installed as non-authorizing handoff payload

Installed files:

- `docs/device-continuity-layer.md`
- `contracts/device-continuity-handoff.contract.md`
- `fixtures/device-continuity/stegtalk-device-continuity-handoff.json`
- `fixtures/device-continuity/fixture-ble-button-stegtalk-001.receipt.json`
- `receipts/device-continuity/stegtalk-device-continuity-receipt.json`
- `tools/validate_device_continuity_handoff.py`
- `tools/validate_device_continuity_receipt.py`
- `tests/test_device_continuity_handoff.py`
- `tests/test_device_continuity_receipt.py`
- `.github/workflows/device-continuity.yml`

## Propagation Posture

Artifact: `STEGTALK_PROPAGATION_POSTURE.json`
Authority posture: `QUEUE_ONLY_NO_DOWNSTREAM_MUTATION`
Manual tasks required: none

Destination review results:

- `StegVerse-Labs/Site`: `DEFER_ACTIVE_GOAL`
- `GCAT-BCAT-Engine/Publisher`: `QUEUE_AFTER_CURRENT_PRIORITY`
- `StegVerse-Labs/admissibility-wiki`: `QUEUE_PENDING_CANONICAL_VALIDATION`
- `StegVerse-002/stegguardian-wiki`: `DEFER_ACTIVE_VALIDATION`

No downstream repo was mutated because each destination handoff currently preserves another active gate or workstream.

## Managed Queue

The current queue source of truth identifies `ST-025` (`State`) as the only pending task. Its parent plan is `STEGTALK_MOBILE_SHELL_PLAN.json`, whose declared next task is `build_mobile_shell_state`.

## Build Rule

Before continuing any StegTalk repo task, check this file first and treat it as the current handoff and task source of truth.

## Next Integration Candidate

Inspect the updated pull-request workflow evidence. Merge only after all three required checks pass. Then complete `ST-025` by building the mobile-shell state from `STEGTALK_MOBILE_SHELL_PLAN.json`, and only afterward recheck downstream handoffs for authorized propagation.
