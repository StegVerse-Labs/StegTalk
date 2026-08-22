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

## ST-031 — Cross-Edge Best-Admissible Capability Resolver

Goal: allow the messenger surface to express the communication outcome/posture while StegTalk deterministically selects the most capable currently admissible outbound path across all admitted user edges.

```text
Resolver source: IMPLEMENTED
Edge capability advertisement contract: IMPLEMENTED
Advertisement freshness/expiry gate: IMPLEMENTED
Attestation requirement: IMPLEMENTED
Recipient capability states KNOWN/UNKNOWN/UNREACHABLE: IMPLEMENTED
Unknown recipient safe-fallback requirement: IMPLEMENTED
Hard constraints before scoring: IMPLEMENTED
Messenger relay/store-forward constraints: IMPLEMENTED
Remote-edge denial enforcement: IMPLEMENTED
Current-edge identity required when remote execution denied: IMPLEMENTED
Multidimensional deterministic scoring: IMPLEMENTED
Single-primary-edge default: IMPLEMENTED
Explicit multipath authorization flag: IMPLEMENTED
Ordered fallback set: IMPLEMENTED
Ambiguous-after-dispatch fallback block: IMPLEMENTED
Confirmed-side-effect-absence fallback gate: IMPLEMENTED
Execution lease primitive: IMPLEMENTED
Hash-bound selection receipt: IMPLEMENTED
Dedicated tests: IMPLEMENTED
Dedicated CI lane: INSTALLED
StegWhisper v0.2 messenger posture contract: IMPLEMENTED
KnowledgeVault canonical selection-receipt schema/test: IMPLEMENTED
Observed CI: PENDING
Live cross-edge advertisements/selection: NOT PROVEN
Live KV selection-receipt persistence: NOT PROVEN
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

StegWhisper:
network_preferences/adapter.py
schemas/network-preference.schema.json
fixtures/network-preferences/scenarios.json
tests/test_network_preferences.py
docs/STEGWHISPER_NETWORK_PREFERENCES.md

KnowledgeVault:
schemas/cross-edge-selection-receipt.schema.json
tests/test_cross_edge_selection_receipt.py
CROSS_EDGE_SELECTION_MIRROR_HANDOFF.md
```

### Messenger / resolver boundary

The messenger surface selects a posture and hard constraints, never a networking interface:

```text
AUTO
MOST_PRIVATE
FASTEST
LOWEST_COST
LOWEST_ENERGY
LOCAL_ONLY
EMERGENCY_RESILIENT
```

StegWhisper v0.2 also makes these policy choices explicit:

```text
cross_edge_policy.scope = ALL_ADMITTED_EDGES
remote_edge_execution_authorized = true | false
multipath_authorized = true | false
```

StegTalk then:

```text
1. reads current admitted edge advertisements;
2. rejects expired or unattested advertisements;
3. evaluates recipient capability state;
4. eliminates paths violating hard constraints;
5. enforces remote-edge, relay, store-forward, locality, emergency, and metric constraints;
6. scores only remaining paths;
7. deterministically selects one primary edge + bearer;
8. records ordered fallback candidates;
9. emits a hash-bound selection receipt;
10. leases the selected edge for the attempt;
11. prevents fallback after ambiguous dispatch until external verification resolves side-effect uncertainty.
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
energy
metadata minimization
```

Postures alter weights but never loosen hard authority, identity, locality, relay, expiry, recipient compatibility, or explicit cross-edge policy.

### Recipient discovery state

Recipient capability is never silently guessed:

```text
KNOWN       -> use advertised accepted bearers
UNKNOWN     -> only explicitly safe fallback bearers may be used
UNREACHABLE -> no admissible path
```

### Cross-edge authority / race boundary

```text
KnowledgeVault = durable intent, attempt, selection receipt, replay, reconstruction authority
StegTalk       = admissibility, scoring, bearer/edge selection and delivery truth
Messenger      = desired communication posture + user constraints
Edge device    = ephemeral capability advertisement + execution
```

One edge is primary by default. Multipath requires explicit authorization. When remote-edge execution is denied, the resolver requires a current-edge identity and excludes every other edge even when it scores higher. An execution lease binds an attempt to the selected edge/lease epoch; capability alone never grants execution authority.

### Fallback invariant

```text
DELIVERED / ACKNOWLEDGED / EXECUTED -> STOP
INDETERMINATE / timeout-after-dispatch -> VERIFY_EXTERNALLY
FAILED without confirmed side-effect absence -> VERIFY_EXTERNALLY
FAILED with confirmed side-effect absence -> next ordered fallback may execute
```

This preserves the KnowledgeVault recovery invariant that uncertainty never becomes permission to duplicate a side effect.

### Selection evidence

KnowledgeVault now has a canonical `cross-edge-selection-receipt` schema and executable receipt-stream round-trip test. Each receipt binds:

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

The connected KnowledgeVault already has `_System/Execution/Receipts/`; the remaining proof is an actual ST-031 receipt written to and reconstructed from that live surface.

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

## Validation boundary

- `.github/workflows/sovereign-sms.yml` covers ST-029/ST-030 software lanes.
- `.github/workflows/cross-edge-resolution.yml` covers ST-031 compilation/tests.
- StegWhisper `.github/workflows/network-preferences.yml` covers v0.2 messenger posture tests.
- KnowledgeVault `.github/workflows/execution-recovery.yml` now covers selection-receipt persistence tests.
- Combined-status endpoints returned no surfaced statuses for the current heads; validation remains pending rather than claimed green.

## Required continuation

1. Observe ST-031, StegWhisper preference, and KnowledgeVault recovery CI and repair any failure.
2. Pass a real StegWhisper v0.2 posture/constraint packet into ST-031.
3. Persist the resulting ST-031 selection receipt + lease into the actual connected KnowledgeVault execution surface.
4. Feed real capability advertisements from at least two admitted edges and prove deterministic selection.
5. Prove recipient UNKNOWN restricts selection to explicitly safe fallback rather than guessing compatibility.
6. Prove remote-edge denial keeps execution on the current edge even when another edge scores higher.
7. Dispatch through one selected edge, induce a confirmed pre-side-effect failure, and prove ordered fallback occurs once.
8. Induce ambiguous post-dispatch state and prove fallback is suppressed pending verification.
9. Restart/replace the selected edge and prove KnowledgeVault reconstructs attempt/selection/lease state without duplicate dispatch.
10. Exercise ST-029 physical modem/SIM as one ST-031 edge and prove outbound/inbound/report correlation into KV.
11. Only after observed live proof mark ST-029/ST-030/ST-031 activated as applicable.

## Archive posture

DO NOT archive as complete. Source/schema/tests/CI and the cross-repo ownership contracts are implemented, but live cross-edge capability advertisements, live KV receipt/lease persistence, fallback observation, physical transport proof, and production activation remain open.

## Percentages

```text
ST-029 software slice: 100% implemented; goal activation remains 74%
ST-030 software/host slice: 100% implemented; goal activation remains 52%
ST-031 bounded software/cross-repo contract slice: 100% implemented; goal activation: 58%
Developed active ST-029/ST-030/ST-031 artifacts vs placeholders: 28 developed / 0 placeholder artifacts
```
