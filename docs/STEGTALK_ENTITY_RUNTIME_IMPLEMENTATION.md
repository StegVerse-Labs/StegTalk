# StegTalk Entity Runtime Implementation

## Assumptions

- StegTalk is local-first.
- GitHub is a mirror/distribution location, not the canonical runtime.
- This implementation is a minimal runtime slice, not production secure messaging.
- Auri may route and explain changes, but should not silently execute consequence.

## Done Definition

This implementation pass is done when the repo contains:

- a local-first runtime module,
- scoped interaction helpers,
- a schema bundle,
- a StegWeather example,
- a runnable demo trace builder,
- tests covering create, recognize, rely, publish, revoke, fork, scoped messaging, feed visibility, attention, compensation, and contributor split receipts.

## Installed Files

```text
src/stegtalk/entity_runtime.py
src/stegtalk/entity_interactions.py
src/stegtalk/entity_runtime_exports.py
schemas/entity-runtime.schema.json
examples/stegweather_entity_runtime_demo.json
scripts/run_entity_runtime_demo.py
tests/test_entity_runtime.py
tests/test_entity_interactions.py
tests/test_entity_runtime_demo.py
```

## Runtime Flow

```text
Create Entity
→ Recognize Entity
→ Rely on Entity
→ Generate Receipts
→ Publish Entity
→ Build Discovery Record
→ Send Scoped Message
→ Create Feed Item
→ Explain Visibility
→ Create Attention Receipt
→ Settle Compensation
→ Settle Contributor Splits
→ Revoke Reliance
→ Fork Entity
```

## Demo Command

```bash
python scripts/run_entity_runtime_demo.py
```

The command writes:

```text
examples/stegweather_runtime_trace.json
```

That generated trace is intentionally not committed by default because receipt identifiers include runtime timestamps.

## Boundary

This does not claim:

- production cryptography,
- production token settlement,
- production public discovery,
- production governance authority,
- production messaging transport.

It does establish the first runnable local model for the entity-native StegTalk architecture.
