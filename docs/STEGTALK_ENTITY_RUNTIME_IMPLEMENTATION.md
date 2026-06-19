# StegTalk Entity Runtime Implementation

## Assumptions

- StegTalk is local-first.
- GitHub is a mirror/distribution location, not the canonical runtime.
- This implementation is a minimal runtime slice, not production secure messaging.
- Auri may route and explain changes, but should not silently execute consequence.

## Done Definition

This implementation pass is done when the repo contains:

- a local-first runtime module,
- a schema bundle,
- a StegWeather example,
- tests covering create, recognize, rely, publish, revoke, and fork.

## Installed Files

```text
src/stegtalk/entity_runtime.py
schemas/entity-runtime.schema.json
examples/stegweather_entity_runtime_demo.json
tests/test_entity_runtime.py
```

## Runtime Flow

```text
Create Entity
→ Recognize Entity
→ Rely on Entity
→ Generate Receipts
→ Publish Entity
→ Build Discovery Record
→ Revoke Reliance
→ Fork Entity
```

## Boundary

This does not claim:

- production cryptography,
- production token settlement,
- production public discovery,
- production governance authority,
- production messaging transport.

It does establish the first runnable local model for the entity-native StegTalk architecture.
