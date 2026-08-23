# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active tasks: ST-029, ST-030, ST-031, ST-032
Durable continuity host: KnowledgeVault / StegVerse-Labs/continuity-vault-kit
Messenger surface authority: communication posture / constraints
Final bearer admissibility + selection authority: StegTalk ST-031
Selected-edge execution coordinator: StegTalk ST-032
Device role: EPHEMERAL_TRANSPORT_EDGE
Cloud messaging dependency: none
SMS aggregator dependency: none
```

## ST-029 — Sovereign Direct-Modem SMS

Software source remains implemented for serial/modem discovery, SIM/readiness/registration gating, fresh pre-send registration, hash-chained local journal/restart/dedupe, UCS-2 multipart PDU submission, and +CDS delivery-report ingestion.

```text
Physical modem/SIM proof: NOT PROVEN
Live outbound/inbound/report proof: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-030 — KnowledgeVault-Hosted Communication Extension

KnowledgeVault extension binding, recovery host, portable execution store, and connected `_System/Execution/{Attempts,Extensions,Receipts,Recovery}` structure are implemented. Source-level persistence/restart reconstruction has been validated, and the connected vault contains the durable ST031 integration validation receipt.

```text
Live bearer-generated attempt persisted/reconstructed through connected KV: NOT PROVEN
Physical edge restart/device replacement after real dispatch: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-031 — Cross-Edge Best-Admissible Capability Resolver

ST-031 is implemented and source-integrated with StegWhisper v0.2 and KnowledgeVault. It enforces expiring/attested edge advertisements, KNOWN/UNKNOWN/UNREACHABLE recipient capability, hard constraints before scoring, remote-edge denial, deterministic multidimensional scoring, one primary edge by default, ordered fallback, execution lease issuance, and hash-bound selection receipts.

Validated evidence retained:

```text
SDK demo PR #54 / run 32602726148: Python 3.9/3.11/3.12 SUCCESS
SDK pinned StegTalk+KV PR #55 / run 32602863793: Python 3.9/3.11/3.12 SUCCESS
StegWhisper -> StegTalk -> KV PR #15 / run 32602979304: SUCCESS
```

```text
Physical/live edge advertisements and bearer execution: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-032 — Bounded Edge Runtime Orchestrator

Goal: bridge an already-admitted ST-031 selection + lease to exactly one edge executor without moving selection authority or durable continuity authority into the edge runtime.

Implemented:

```text
src/stegtalk/edge_runtime.py
tests/test_edge_runtime.py
.github/workflows/edge-runtime.yml
```

Runtime invariants:

```text
selection attempt/hash/edge/bearer must match exactly
lease attempt/edge/epoch must match exactly
edge runtime does not select a bearer
payload_ref and idempotency_key required
same idempotency key + same binding returns cached receipt without redispatch
same idempotency key + changed binding fails closed
execution receipt is hash-bound
ambiguous dispatch cannot claim side-effect absence
successful execution cannot claim side-effect absence
ambiguous outcome -> VERIFY_EXTERNALLY
FAILED without confirmed side-effect absence -> VERIFY_EXTERNALLY
FAILED with confirmed absence -> exact ordered fallback may execute
```

A `LOOPBACK_TEST` executor exists solely to exercise real callable dispatch/receipt/fallback plumbing in CI. It is not a physical/network delivery claim, does not grant authority, and must never be advertised as a production bearer.

Observed ST-032 validation:

```text
StegTalk PR #30
Edge Runtime Validation run 32608123831
Python 3.11 SUCCESS
Python 3.12 SUCCESS
Test Readiness run 32608123844 SUCCESS
device-continuity run 32608123828 SUCCESS
```

An initial Python 3.9 matrix leg failed before tests because the StegTalk package declares `requires-python >=3.11`; the ST-032 workflow was corrected to the actual repository support boundary rather than weakening or misrepresenting the package contract.

ST-032 currently proves bounded runtime dispatch mechanics with a test executor. It does not prove physical/network bearer execution.

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
StegTalk ST-032
    | exact binding + dispatch + execution receipt
    v
EPHEMERAL_TRANSPORT_EDGE
    |
    +--> ST-029 SMS modem
    +--> native StegTalk/IP
    +--> Wi-Fi / Wi-Fi Direct
    +--> Bluetooth/local
    +--> admitted relay/store-forward
    +--> other admitted bearer adapters
    |
    v
recipient
    |
    v
receipts/evidence -> KnowledgeVault
```

```text
KnowledgeVault = durable continuity/recovery authority
StegTalk ST-031 = bearer/admissibility/selection authority
StegTalk ST-032 = bounded selected-edge execution coordinator
StegWhisper = posture/consent/presentation surface
Edge device = ephemeral execution capability
SDK = non-authorizing demonstration/conformance boundary
```

## Connected KnowledgeVault evidence

The connected KnowledgeVault contains `_System/Execution/{Attempts,Extensions,Receipts,Recovery}` and the validation document `ST031_Communication_Integration_Validation_2026-08-22` under Receipts. That document is validation evidence, not a production execution receipt from a live bearer transaction.

## Required continuation

The highest-value next work is now narrower:

1. bind ST-032 execution receipts and state transitions directly into `KnowledgeVaultExecutionStore` so one runtime attempt produces selection + lease + dispatch + execution/recovery records through one durable interface;
2. prove that combined runtime stream reconstructs after process restart with no duplicate dispatch;
3. replace `LOOPBACK_TEST` with actual admitted edge adapters, beginning with the strongest available IP/local edge and ST-029 modem/SIM;
4. advertise at least two actual admitted device edges and let ST-031 select one;
5. execute the selected real bearer and append delivery evidence into connected KV;
6. restart/replace the selected edge and reconstruct from connected KV without duplicate dispatch;
7. exercise ST-029 outbound, delivery report, inbound correlation, and multipart partial-failure semantics on physical modem/SIM;
8. only then mark applicable runtime activation complete.

## Archive posture

DO NOT archive as fully activated. ST-032 closes the previously missing source-level selection-to-execution coordinator and is CI validated, but connected-KV live execution, actual admitted device edges, physical/network delivery, and production activation remain open.
