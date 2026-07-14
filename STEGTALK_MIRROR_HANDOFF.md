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
- validation-install repair artifact and test

## Current Priority

Repair and verify the two observed validation failures before any downstream propagation or release-status advancement. Preserve `production_ready: false` and the queue-only downstream posture until pull-request workflow evidence is green.

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

## Validation Repair

Artifact: `STEGTALK_VALIDATION_REPAIR.json`
Test: `tests/test_validation_repair.py`
Branch: `repair-validation-install`
Manual tasks required: none
New workflows added: false

Observed failures:

1. `StegTalk Managed Completion`, run `29304441633`, failed at `Install test/runtime support` because `0.0.0-managed-completion` was not a PEP 440-compliant project version.
2. `device-continuity`, run `29304441639`, reached both validators successfully and failed at `Run Device Continuity tests` because the existing workflow did not install `pytest`.

Installed repairs:

- `pyproject.toml` now uses `0.0.0+managed.completion`.
- The existing `.github/workflows/device-continuity.yml` installs `pytest` before running its two tests.

Verification remains fail-closed at `PENDING_PULL_REQUEST_WORKFLOW_EVIDENCE` until the pull-request runs prove:

- `StegTalk Managed Completion`: PASS
- `device-continuity`: PASS
- `Test Readiness`: PASS

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

## Build Rule

Before continuing any StegTalk repo task, check this file first and treat it as the current handoff and task source of truth.

## Next Integration Candidate

Inspect the pull-request workflow evidence for the validation repair. Merge only after all three required checks pass. After merge, recheck destination handoffs and propagate `verified_non_production_local_prototype` only when the immediate destination handoff authorizes mutation, preserving `production_ready: false` in every destination artifact.
