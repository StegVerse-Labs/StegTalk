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
KV recovery/extension host: IMPLEMENTED
KV portable execution store: IMPLEMENTED
Connected KnowledgeVault _System/Execution backing layout: CREATED AND VERIFIED
Source-level KV persistence/restart reconstruction: VALIDATED
Connected-KV integration validation receipt: PRESENT UNDER _System/Execution/Receipts
Live bearer-generated attempt persisted/reconstructed through connected KV: NOT PROVEN
Physical edge restart/device replacement after real dispatch: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-031 — Cross-Edge Best-Admissible Capability Resolver

Goal: let the messenger surface express communication posture/constraints while StegTalk deterministically selects the most capable currently admissible outbound path across admitted user edges.

```text
Resolver source: IMPLEMENTED
Edge capability advertisement contract: IMPLEMENTED
Advertisement freshness/expiry gate: IMPLEMENTED
Attestation requirement: IMPLEMENTED
Recipient KNOWN/UNKNOWN/UNREACHABLE states: IMPLEMENTED
Unknown-recipient safe-fallback requirement: IMPLEMENTED
Hard constraints before scoring: IMPLEMENTED
Relay/store-forward/locality/emergency constraints: IMPLEMENTED
Remote-edge denial enforcement: IMPLEMENTED
Current-edge identity requirement under remote denial: IMPLEMENTED
Multidimensional deterministic scoring: IMPLEMENTED
Single-primary-edge default: IMPLEMENTED
Explicit multipath authorization: IMPLEMENTED
Ordered fallback set: IMPLEMENTED
Ambiguous-after-dispatch fallback block: IMPLEMENTED
Confirmed-side-effect-absence fallback gate: IMPLEMENTED
Execution lease primitive: IMPLEMENTED
Hash-bound selection receipt: IMPLEMENTED
StegWhisper v0.2 posture contract: IMPLEMENTED
KnowledgeVault selection receipt/store integration: IMPLEMENTED
SDK conformance demonstration: VALIDATED
Pinned StegTalk + KnowledgeVault source integration: VALIDATED
Full StegWhisper -> StegTalk -> KnowledgeVault source integration: VALIDATED
Physical/live edge advertisements and bearer execution: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## Observed validation evidence

### SDK conformance demonstration

`StegVerse-org/StegVerse-SDK` now contains a non-authorizing communication-edge demonstrator.

```text
PR #54
Communication Edge SDK Demo Validation
workflow run 32602726148
Python 3.9  SUCCESS
Python 3.11 SUCCESS
Python 3.12 SUCCESS
```

It demonstrated deterministic edge scoring, native StegTalk-over-SMS selection under AUTO, remote-edge denial, unknown-recipient safe fallback, fail-closed unattested paths, ambiguity suppression, and exact ordered fallback while explicitly remaining `sdk_simulation_only` and non-authorizing.

### Pinned real StegTalk + KnowledgeVault source integration

```text
StegVerse-org/StegVerse-SDK PR #55
workflow run 32602863793
Python 3.9  SUCCESS
Python 3.11 SUCCESS
Python 3.12 SUCCESS

StegTalk source exercised:
2361d13ea09818f17aef5239ebf4771a161a0dc7

KnowledgeVault source exercised:
35e6d7ad881e0dea60ba191c49dfd4fba86e3fd7
```

The workflow imported and executed the real `stegtalk.cross_edge_resolver` and real `execution.vault_store`. It selected `stegtalk-ip` over SMS, retained SMS as fallback, issued a lease, persisted the actual ST-031 receipt and attempt/lease state through the KV store, reopened a fresh store, and reconstructed that state after restart. Ambiguous post-dispatch state returned `VERIFY_EXTERNALLY`; confirmed no-side-effect failure returned `TRY_FALLBACK` to the exact ordered edge.

Observed selection hash:

```text
sha256:bcb923d56e548582f1bd303bf647bc958994197ca68cc6e402b3326d8dc48efc
```

### Full StegWhisper -> StegTalk -> KnowledgeVault source integration

```text
StegVerse-Labs/StegWhisper PR #15
merged commit 4baf51a57100cb942b7aa8855f60e2995c9eb386
Network Preference Validation run 32602979304
SUCCESS
```

This proof used the real StegWhisper v0.2 preference adapter, the pinned real ST-031 resolver, and the pinned real KV execution store. It proved posture propagation, edge selection, remote-edge denial, selection/lease persistence, restart reconstruction, ambiguity suppression, and confirmed-safe fallback.

## Connected KnowledgeVault evidence

The connected KnowledgeVault contains:

```text
_System/Execution/
    Attempts/
    Extensions/
    Receipts/
    Recovery/
```

The durable validation receipt `ST031_Communication_Integration_Validation_2026-08-22` is now located under `_System/Execution/Receipts`. It records the validated commits, workflow runs, selection hash, authority boundary, and remaining runtime proof.

This document is validation evidence. It is not classified as a production execution receipt from a live bearer transaction.

## Messenger / resolver boundary

The messenger surface selects posture and constraints, never a network interface:

```text
AUTO
MOST_PRIVATE
FASTEST
LOWEST_COST
LOWEST_ENERGY
LOCAL_ONLY
EMERGENCY_RESILIENT
```

StegTalk reads current admitted edge advertisements, rejects expired/unattested candidates, evaluates recipient capability, eliminates hard-constraint violations, scores remaining paths, deterministically selects one primary edge/bearer, records fallbacks, emits the selection receipt, and leases the selected edge.

## Capability vector

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

## Fallback invariant

```text
DELIVERED / ACKNOWLEDGED / EXECUTED -> STOP
INDETERMINATE / TIMEOUT_AFTER_DISPATCH / UNKNOWN_AFTER_DISPATCH -> VERIFY_EXTERNALLY
FAILED without confirmed side-effect absence -> VERIFY_EXTERNALLY
FAILED with confirmed side-effect absence -> next ordered fallback may execute
```

Uncertainty never becomes permission to duplicate a side effect.

## Authority topology

```text
Messenger / StegWhisper
    | posture + constraints
    v
KnowledgeVault durable attempt/continuity
    |
    v
StegTalk ST-031
    | admissibility + scoring + selection + lease
    v
EPHEMERAL_TRANSPORT_EDGE
    |
    +--> ST-029 SMS modem
    +--> native StegTalk/IP
    +--> Wi-Fi / Wi-Fi Direct
    +--> Bluetooth/local
    +--> admitted relay/store-forward
    +--> other admitted bearers
    |
    v
recipient
    |
    v
receipts/evidence -> KnowledgeVault
```

```text
KnowledgeVault = durable continuity/recovery authority
StegTalk = bearer/admissibility/selection/delivery-truth authority
StegWhisper = messenger posture/consent/presentation surface
Edge device = ephemeral execution capability
SDK = non-authorizing demonstration/conformance boundary
```

## Required continuation

The source/software integration is now tested. Remaining activation work is runtime/physical:

1. originate an actual running communication attempt against the connected KnowledgeVault;
2. persist its runtime ST-031 selection receipt and lease into the connected KV execution streams;
3. advertise at least two actual admitted device edges;
4. execute through the selected real bearer and append delivery evidence;
5. restart/replace that edge and reconstruct the live attempt from connected KV without duplicate dispatch;
6. exercise ST-029 modem/SIM as an actual SMS edge and prove outbound, delivery report, and inbound correlation;
7. only after those proofs mark applicable ST-029/ST-030/ST-031 runtime activation complete.

## Archive posture

DO NOT archive as fully activated. The cross-repo source integration and SDK demonstration are implemented and observed passing; physical/network execution and connected-vault live-attempt proof remain open.
