# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active tasks: ST-029, ST-030, ST-031
Durable continuity host: KnowledgeVault / StegVerse-Labs/continuity-vault-kit
Messenger surface authority: communication posture / constraints
Final bearer admissibility + selection authority: StegTalk
Device role: EPHEMERAL_TRANSPORT_EDGE
Cloud messaging dependency: none
SMS aggregator dependency: none
```

## ST-029 — Sovereign Direct-Modem SMS

Goal: bidirectional ordinary SMS without a cloud messaging provider.

```text
Software slice: IMPLEMENTED
Dedicated CI lane: INSTALLED
Serial discovery/POSIX binding: IMPLEMENTED
SIM + registration gate: IMPLEMENTED
Fresh registration immediately before send: IMPLEMENTED
Local hash-chained journal/restart/dedupe: IMPLEMENTED
UCS-2 multipart PDU: IMPLEMENTED
+CDS delivery-report ingestion: IMPLEMENTED
Physical modem/SIM proof: NOT PROVEN
Live outbound/inbound/report proof: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-030 — KnowledgeVault-Hosted Communication Extension

Goal: keep durable personal communication authority, attempt state, replay, and recovery in KnowledgeVault while devices remain replaceable execution edges.

```text
KV extension request/binding: IMPLEMENTED
KV recovery/extension host: IMPLEMENTED IN SOURCE
KV portable execution store: IMPLEMENTED IN SOURCE
Connected KnowledgeVault _System/Execution backing layout: CREATED AND VERIFIED
Live communication attempt persisted/reconstructed through KV: NOT PROVEN
Edge restart/device replacement proof: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

Connected KnowledgeVault backing layout:

```text
_System/Execution/
    Attempts/
    Extensions/
    Receipts/
    Recovery/
```

## ST-031 — Cross-Edge Best-Admissible Capability Resolver

Goal: allow the messenger surface to express the communication outcome/posture while StegTalk deterministically selects the most capable currently admissible outbound path across all admitted user edges.

```text
Resolver source: IMPLEMENTED
Edge capability advertisement contract: IMPLEMENTED
Advertisement freshness/expiry gate: IMPLEMENTED
Attestation requirement: IMPLEMENTED
Recipient capability states KNOWN/UNKNOWN/UNREACHABLE: IMPLEMENTED
Hard constraints before scoring: IMPLEMENTED
Multidimensional deterministic scoring: IMPLEMENTED
Single-primary-edge default: IMPLEMENTED
Explicit remote-edge policy: IMPLEMENTED
Explicit multipath authorization flag: IMPLEMENTED
Ordered fallback set: IMPLEMENTED
Ambiguous-after-dispatch fallback block: IMPLEMENTED
Confirmed-side-effect-absence fallback gate: IMPLEMENTED
Execution lease primitive: IMPLEMENTED
Hash-bound selection receipt: IMPLEMENTED
Dedicated tests: IMPLEMENTED
Dedicated CI lane: INSTALLED
Observed CI: PENDING
Live cross-edge advertisements/selection: NOT PROVEN
KV selection-receipt persistence: NOT PROVEN
Live edge lease/failover/reconstruction: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

ST-031 artifacts:

```text
src/stegtalk/cross_edge_resolver.py
schemas/cross-edge-capability.schema.json
tests/test_cross_edge_resolver.py
.github/workflows/cross-edge-resolution.yml
STEGTALK_TASK_QUEUE.json
```

### Messenger / resolver boundary

The messenger surface does not directly select a network interface. It selects a posture and hard constraints:

```text
AUTO
MOST_PRIVATE
FASTEST
LOWEST_COST
LOWEST_ENERGY
LOCAL_ONLY
EMERGENCY_RESILIENT
```

StegTalk then:

```text
1. reads current admitted edge advertisements;
2. rejects expired or unattested advertisements;
3. evaluates recipient capability state;
4. eliminates paths violating hard constraints;
5. scores only remaining paths;
6. deterministically selects one primary edge + bearer;
7. records ordered fallback candidates;
8. emits a hash-bound selection receipt;
9. leases the selected edge for the attempt;
10. prevents fallback after ambiguous dispatch until external verification resolves side-effect uncertainty.
```

### "Most capable" vector

The resolver scores admissible candidates across normalized dimensions:

```text
security
privacy
recipient compatibility
reliability
receipt quality
bidirectionality
resilience
latency
bandwidth
cost
ergy
metadata minimization
```

Postures alter weights but never loosen hard authority, identity, locality, relay, expiry, or recipient-compatibility constraints.

### Recipient discovery state

Recipient capability is never silently guessed:

```text
KNOWN       -> use advertised accepted bearers
UNKNOWN     -> only explicitly safe fallback bearers may be used
UNREACHABLE -> no admissible path
```

### Cross-edge authority / race boundary

```text
KnowledgeVault = durable intent, attempt, receipt, replay, reconstruction authority
StegTalk       = admissibility, scoring, bearer/edge selection and delivery truth
Messenger      = desired communication posture + user constraints
Edge device    = ephemeral capability advertisement + execution
```

One edge is primary by default. Multipath requires explicit authorization. An execution lease binds an attempt to the selected edge/lease epoch; stale or competing workers may not infer execution authority from capability alone.

### Fallback invariant

Fallback is a new transport execution and is not permitted merely because the primary path timed out.

```text
DELIVERED / ACKNOWLEDGED / EXECUTED -> STOP
INDETERMINATE / timeout-after-dispatch -> VERIFY_EXTERNALLY
FAILED without confirmed side-effect absence -> VERIFY_EXTERNALLY
FAILED with confirmed side-effect absence -> next ordered fallback may execute
```

This preserves the KnowledgeVault recovery invariant that uncertainty never becomes permission to duplicate a side effect.

### Selection evidence

Each selection receipt contains or binds:

```text
attempt_id
policy_version
posture
recipient_state
candidate_set_sha256
selected_edge_id
selected_bearer
primary score + component vector
fallback order
excluded paths + reasons
selected advertisement hash
decision timestamp
multipath authorization state
remote-edge execution policy
selection_sha256
```

The receipt is intended to be persisted in the KnowledgeVault receipt stream so route choice is replayable and reconstructable rather than hidden runtime behavior.

## Combined authority topology

```text
Messenger surface
  | posture + constraints
  v
KnowledgeVault durable attempt
  |
  v
StegTalk ST-031 cross-edge resolver
  | admissibility + deterministic selection + lease
  v
Selected EPHEMERAL_TRANSPORT_EDGE
  |
  +--> ST-029 SMS modem
  +--> StegTalk IP
  +--> Wi-Fi / Wi-Fi Direct
  +--> Bluetooth / local paths
  +--> relay / store-forward when separately admissible
  +--> other admitted bearers
  |
  v
recipient
  |
  v
receipts/evidence -> KnowledgeVault
```

Edge invariant:

```text
device_authority = false
device_continuity_authority = false
vault_continuity_authority = true
capability advertisement != execution authority
selection != delivery
workflow pass != runtime proof
```

## Validation boundary

- `.github/workflows/sovereign-sms.yml` covers ST-029/ST-030 software lanes.
- `.github/workflows/cross-edge-resolution.yml` covers ST-031 compilation and resolver tests.
- Available status endpoints have not yet surfaced observed success for these new heads; validation remains pending rather than claimed green.

## Required continuation

1. Observe ST-031 CI and repair any failure.
2. Extend the messenger preference surface to emit the ST-031 posture/constraint vocabulary without assuming bearer authority.
3. Persist ST-031 selection receipts + leases in the actual KnowledgeVault execution surface.
4. Feed real edge advertisements from at least two admitted edges and prove deterministic selection.
5. Prove recipient UNKNOWN state restricts selection to safe fallback rather than guessing compatibility.
6. Dispatch through one selected edge, induce a confirmed pre-side-effect failure, and prove ordered fallback occurs once.
7. Induce ambiguous post-dispatch state and prove fallback is suppressed pending verification.
8. Restart/replace the selected edge and prove KnowledgeVault reconstructs the attempt and lease state without duplicate dispatch.
9. Exercise ST-029 physical modem/SIM as one ST-031 edge and prove outbound/inbound/report correlation into KV.
10. Only after observed live proof mark ST-029/ST-030/ST-031 activated as applicable.

## Archive posture

DO NOT archive as complete. ST-031 is now implemented in source/tests/CI, but live cross-edge capability advertisements, KV selection persistence, leasing, fallback behavior, physical transport proof, and production activation remain open.

## Percentages

```text
ST-029 software slice: 100% implemented; goal activation remains 74%
ST-030 software/host slice: 100% implemented; goal activation remains 52%
ST-031 software slice: 100% implemented for bounded resolver contract; goal activation: 45%
Developed active ST-029/ST-030/ST-031 artifacts vs placeholders: 25 developed / 0 placeholder artifacts
```
