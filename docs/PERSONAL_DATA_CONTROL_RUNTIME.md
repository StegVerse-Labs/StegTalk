# StegTalk Personal Data Control Runtime

StegTalk must provide a machine-observable path for a participant to control account, session, device, local-store, routing-metadata, receipt, and processor-linked personal data.

A privacy promise is not an activated runtime capability. The lifecycle must expose deterministic states, exact storage scopes, executable local actions, processor-propagation state, appeal state, and completion receipts.

## Required lifecycle

```text
NOT_REQUESTED
RECEIVED
IDENTITY_VERIFICATION_REQUIRED
VERIFIED
PROCESSING_RESTRICTED
INVENTORY_COMPLETE
DELETION_IN_PROGRESS
PROCESSOR_PROPAGATION_PENDING
COMPLETED
PARTIALLY_DENIED
DENIED
APPEAL_OPEN
CHANNEL_FAILED
```

## Required data scopes

```text
account_profile
identity_and_device_bindings
session_state
contact_and_routing_metadata
local_inbox
local_store
message_receipts
recovery_checkpoints
recovery_policy_receipts
analytics_and_diagnostics
processor_copies
```

## Completion rule

A request is not complete until the runtime produces a receipt identifying:

- request identifier;
- authenticated subject binding;
- scopes inventoried;
- scopes deleted;
- scopes retained and their basis;
- processor propagation state;
- appeal availability;
- completion timestamp;
- receipt hash.

No external task is permitted. Missing remote confirmation is represented as a state transition, not a development blocker. Repository-local validation and repair continue independently.
