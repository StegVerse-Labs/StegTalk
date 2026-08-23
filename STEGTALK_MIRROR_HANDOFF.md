# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active tasks: ST-029, ST-030, ST-031, ST-032, ST-033
Durable continuity host: KnowledgeVault / StegVerse-Labs/continuity-vault-kit
Messenger surface authority: communication posture / constraints
Final bearer admissibility + selection authority: StegTalk ST-031
Selected-edge execution coordinator: StegTalk ST-032
First non-loopback IP/local edge adapter: StegTalk ST-033
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

KnowledgeVault extension binding, recovery host, portable execution store, and connected `_System/Execution/{Attempts,Extensions,Receipts,Recovery}` structure are implemented. ST-032 now uses the canonical `KnowledgeVaultExecutionStore` for selection, lease, dispatch-pending state, execution receipts, execution transitions, external-verification recovery records, and restart idempotency reconstruction.

```text
ST-032 -> KnowledgeVault execution-store source binding: IMPLEMENTED
KV-backed ST-032 idempotency reconstruction after process restart: VALIDATED
Live bearer-generated attempt persisted/reconstructed through connected KV: NOT PROVEN
Physical edge restart/device replacement after real dispatch: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-031 — Cross-Edge Best-Admissible Capability Resolver

ST-031 remains final bearer/admissibility/selection authority. It enforces expiring/attested edge advertisements, KNOWN/UNKNOWN/UNREACHABLE recipient capability, hard constraints before scoring, remote-edge denial, deterministic multidimensional scoring, one primary edge by default, ordered fallback, execution lease issuance, and hash-bound selection receipts.

```text
SDK demo run 32602726148: SUCCESS
SDK pinned StegTalk+KV run 32602863793: SUCCESS
StegWhisper -> StegTalk -> KV run 32602979304: SUCCESS
Physical/live edge advertisements and distinct-device bearer execution: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

## ST-032 — Bounded Edge Runtime Orchestrator

ST-032 bridges an already-admitted ST-031 selection + lease to exactly one edge executor without moving selection authority or durable continuity authority into the edge runtime.

Canonical surfaces:

```text
src/stegtalk/edge_runtime.py
src/stegtalk/physical_edge_runtime.py
runtime/cross-edge-physical-runtime.v1.json
tests/test_edge_runtime.py
tests/test_physical_edge_runtime.py
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

`LOOPBACK_TEST` exists only for CI plumbing. It is not a physical/network delivery claim. ST-029 is exposed as one bounded ST-032 executor adapter; modem submission remains `INDETERMINATE` until independent delivery evidence such as `+CDS` exists.

Observed ST-032 validation:

```text
PR #30 Edge Runtime Validation run 32608123831: SUCCESS
PR #32 Cross-Edge Resolution run 32608477245: SUCCESS
PR #32 Edge Runtime Validation run 32608477241: SUCCESS
PR #32 Managed Completion run 32608477186: SUCCESS
PR #32 Test Readiness run 32608477257: SUCCESS
PR #32 device-continuity run 32608477342: SUCCESS
PR #32 merge e6e8bc94e75d5cbad0c41dfb1417a4f20cec3818
```

## ST-033 — Admitted Non-Loopback Local TCP Edge

PR #34 installed the first non-loopback IP/local bearer adapter under ST-032.

```text
src/stegtalk/local_tcp_edge.py
runtime/local-tcp-edge.v1.json
tests/test_local_tcp_edge.py
.github/workflows/edge-runtime.yml
```

The adapter uses real OS TCP socket I/O and framed protocol `stegtalk.edge-tcp.v0.1`. It hash-binds payload and request content and accepts only a correlated application ACK using `stegtalk.edge-tcp-ack.v0.1`. A connection failure before any frame is sent is a confirmed no-side-effect `FAILED` outcome. Any failure after frame transmission, invalid ACK, mismatched hash, mismatched idempotency key, or uncertain peer state is `INDETERMINATE` and therefore cannot authorize automatic fallback.

`ACKNOWLEDGED` means the receiving StegTalk edge accepted the exact frame. It does not prove human rendering, read receipt, application consequence, public-internet delivery, or production activation.

The merged validation uses an actual localhost OS TCP listener and socket rather than the in-process `LOOPBACK_TEST`; this proves socket plumbing and ACK correlation, but it is still one host and therefore is not distinct-device or public-network activation evidence.

```text
StegTalk PR #34
Head ae359adaf568d8cedb3b4875ad62b6165c7c294b
Edge Runtime Validation run 32609103130: SUCCESS
Test Readiness run 32609103116: SUCCESS
Managed Completion run 32609103120: SUCCESS
device-continuity run 32609103119: SUCCESS
Merge c3654655a075124fd1ab3e864aa67db5e2b2a8fd
Distinct runtime-edge dispatch proof: NOT PROVEN
Connected-KV live ST-033 execution receipt: NOT PROVEN
Edge restart/replacement proof after real dispatch: NOT PROVEN
Public-network TLS adapter: NOT INSTALLED
Production activation: NOT ACTIVE
Claim state: OPEN
```

Plaintext `stegtalk-tcp` is restricted to explicitly admitted local-network edges. Any public-network endpoint requires a TLS-bound adapter before use. Endpoint/admission metadata must come from the selected attested ST-031 advertisement; synthetic attestation is not authorized.

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
    +--> ST-033 admitted local TCP
    +--> ST-029 SMS modem
    +--> future TLS-bound public IP
    +--> Wi-Fi / Wi-Fi Direct
    +--> Bluetooth/local
    +--> admitted relay/store-forward
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
StegTalk ST-033 = non-loopback local TCP edge implementation
StegWhisper = posture/consent/presentation surface
Edge device = ephemeral execution capability
SDK = non-authorizing demonstration/conformance boundary
```

## Required continuation

The next integration goal is now live/runtime evidence rather than another local socket primitive:

1. admit at least two actual device-edge advertisements under ST-031;
2. let ST-031 select one actual edge;
3. run ST-033 between distinct runtime edges and persist selection + lease + execution evidence through the connected KnowledgeVault;
4. obtain independently meaningful acknowledgement/delivery evidence beyond mere local socket acceptance where applicable;
5. restart or replace the selected edge and reconstruct from connected KV without duplicate dispatch;
6. before any public-network endpoint use, install and validate a TLS-bound public IP executor adapter;
7. complete ST-029 modem/SIM outbound, `+CDS` delivery report, inbound correlation, and multipart partial-failure evidence on physical hardware;
8. only after those proofs mark the relevant runtime activation states complete.

## Archive posture

DO NOT archive as fully activated. ST-033 now supplies real OS TCP socket execution under ST-032, but actual admitted distinct-device edges, connected-KV live execution, public-network TLS, physical/network delivery, edge replacement proof, and production activation remain open.
