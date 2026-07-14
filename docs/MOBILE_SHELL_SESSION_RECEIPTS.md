# Mobile-Shell Session Receipt Chain

This lane records local persistent-session events without granting execution or network authority.

## Automated entry points

- `persist_session_with_receipt(...)`
- `restore_session_with_receipt(...)`

Both functions update the receipt chain automatically. Callers do not construct receipts, carry forward chain heads, classify integrity failures, or replay the chain manually.

## Recorded events

- `persist`
- `restore`
- `rejection`
- `integrity_failure`

Each receipt is local-only, non-production, and non-authorizing. It carries hashes and reasons but no message payload.

## Fail-closed behavior

Receipt replay rejects:

- previous-chain-head discontinuity;
- receipt identity drift;
- receipt-chain-head drift;
- unsupported event or receipt types;
- any receipt that claims production, non-local, or authorizing status.

## Authority boundary

A receipt is evidence that an event occurred or was rejected. It does not authorize the event, elevate the shell, enable networking, or create downstream mutation authority.
