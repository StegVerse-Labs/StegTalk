# Account Runtime

## Purpose

The account runtime describes StegTalk local account profile and account session behavior.

## Runtime Behavior

The account path should identify:

- account id
- display name
- owner entity
- linked entities
- profile hash
- shell state hash
- active view
- session events
- session hash

## StegTalk Ownership

StegTalk owns local account profile creation, linked-entity records, account session creation, session event recording, and account/session summaries.

## Overlap

StegGuardian owns guardian, recovery, device trust, account federation, and protective boundary interpretation. Admissibility owns standing checks for account, guardian, recovery, federation, and execution actions.

## Boundary

Account readiness does not imply external login authority, production identity, cross-device recovery, public account federation, or production guardian enforcement.
