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

The ST-032 continuation now directly uses the canonical `KnowledgeVaultExecutionStore` rather than reimplementing its append-only hashing, secret-rejection, or recovery semantics. Selection, lease, dispatch-pending state, execution receipts, execution transitions, and external-verification recovery records therefore share one durable interface.

```text
ST-032 -> KnowledgeVault execution-store source binding: IMPLEMENTED
KV-backed ST-032 idempotency reconstruction after process restart: VALIDATED
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

Canonical coordinator implementation:

```text
src/stegtalk/edge_runtime.py
tests/test_edge_runtime.py
.github/workflows/edge-runtime.yml
```

KnowledgeVault persistence / physical-edge integration layer under PR #32:

```text
src/stegtalk/physical_edge_runtime.py
runtime/cross-edge-physical-runtime.v1.json
tests/test_physical_edge_runtime.py
.github/workflows/cross-edge-resolution.yml
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
INDETERMINATE / TIMEOUT_AFTER_DISPATCH / UNKNOWN_AFTER_DISPATCH -> VERIFY_EXTERNALLY
FAILED without confirmed side-effect absence -> VERIFY_EXTERNALLY
FAILED with confirmed absence -> exact ordered fallback may execute
```

Uncertainty never becomes permission to duplicate a side effect.

A `LOOPBACK_TEST` executor exists solely to exercise real callable dispatch/receipt/fallback plumbing in CI. It is not a physical/network delivery claim, does not grant authority, and must never be advertised as a production bearer.

The KV persistence layer reconstructs prior `EDGE_EXECUTION` receipts from the connected execution-store receipt stream and supplies them back to ST-032 as the idempotency cache. A restarted process therefore returns the same persisted receipt for the same idempotency key and exact execution binding without invoking the edge executor again. Conflicting persisted receipts for one idempotency key fail closed.

The first real bearer adapter is bounded to ST-029: a selected `sms` advertisement must carry an admitted `capabilities.modem_path`; the adapter then calls the existing `SovereignSmsSession` through ST-032. Modem submission returns `INDETERMINATE`, not `DELIVERED`, until independent delivery evidence such as `+CDS` is observed. Consequently the safe next action after submission is `VERIFY_EXTERNALLY`, not automatic fallback.

Observed ST-032 coordinator validation:

```text
StegTalk PR #30
Edge Runtime Validation run 32608123831
Python 3.11 SUCCESS
Python 3.12 SUCCESS
Test Readiness run 32608123844 SUCCESS
device-continuity run 32608123828 SUCCESS
```

Observed PR #32 KV-persistence validation before this handoff update:

```text
StegTalk Cross-Edge Resolution run 32608380148: SUCCESS
  compile resolver/runtime harness: SUCCESS
  resolver + KV-persisted runtime tests: SUCCESS
Test Readiness run 32608380146: SUCCESS
device-continuity run 32608380164: SUCCESS
Managed Completion run 32608380174: implementation tests SUCCESS; mirror-handoff assertion exposed the missing explicit uncertainty invariant now restored above
```

An initial ST-032 Python 3.9 matrix leg failed before tests because the StegTalk package declares `requires-python >=3.11`; the ST-032 workflow was corrected to the actual repository support boundary rather than weakening or misrepresenting the package contract.

ST-032 now has source-level durable execution-stream and restart-idempotency integration. It still does not prove connected-vault live bearer execution or physical/network delivery.

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

PR #32 proves the source path that will write and reconstruct ST-032 execution receipts through that canonical store. Its CI tests use a deterministic store double and therefore do not manufacture a live connected-vault bearer receipt.

## Required continuation

The highest-value next work is now physical/runtime rather than another execution-coordinator layer:

1. install and admit an actual non-loopback IP/local edge adapter under ST-032, while preserving ST-031 selection authority;
2. advertise at least two actual admitted device edges and let ST-031 select one;
3. originate a real bearer-generated attempt against the connected KnowledgeVault and persist selection + lease + dispatch + execution evidence through the canonical execution store;
4. execute the selected real bearer and append delivery evidence into connected KV;
5. restart/replace the selected edge and reconstruct the attempt from connected KV without duplicate dispatch;
6. exercise ST-029 modem/SIM outbound, `+CDS` delivery report, inbound correlation, and multipart partial-failure semantics on physical hardware;
7. only after those proofs mark applicable ST-029/ST-030/ST-031/ST-032 runtime activation complete.

## Archive posture

DO NOT archive as fully activated. ST-032 closes the source-level selection-to-execution coordinator, and PR #32 adds source-level KnowledgeVault persistence plus restart/idempotency reconstruction. Actual admitted device edges, connected-KV live execution, physical/network delivery, edge replacement proof, and production activation remain open.
