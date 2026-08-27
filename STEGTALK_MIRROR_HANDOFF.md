# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active tasks: ST-029, ST-030, ST-031, ST-032, ST-033, ST-034, ST-035, ST-036
Durable continuity host: KnowledgeVault / StegVerse-Labs/continuity-vault-kit
Messenger surface authority: communication posture / constraints
Final bearer admissibility + selection authority: StegTalk ST-031
Selected-edge execution coordinator: StegTalk ST-032
First non-loopback IP/local edge adapter: StegTalk ST-033
TLS-bound public IP edge adapter: StegTalk ST-034
TLS receiving-edge admission surface: StegTalk ST-035
Durable-before-positive-ACK gate: StegTalk ST-036 + KnowledgeVault
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
Public-network TLS adapter: ST-034 SOURCE VALIDATED AND MERGED / LIVE PUBLIC EDGE PENDING
Production activation: NOT ACTIVE
Claim state: OPEN
```

Plaintext `stegtalk-tcp` is restricted to explicitly admitted local-network edges. Any public-network endpoint requires a TLS-bound adapter before use. Endpoint/admission metadata must come from the selected attested ST-031 advertisement; synthetic attestation is not authorized.


## ST-034 — TLS-Bound Public IP Edge

Issue #36 owns the first public-network-capable ST-032 executor. It is intentionally separate from plaintext ST-033 local TCP.

```text
src/stegtalk/public_tls_edge.py
runtime/public-tls-edge.v1.json
tests/test_public_tls_edge.py
.github/workflows/edge-runtime.yml
```

ST-034 requires certificate-chain verification and hostname verification with no insecure/verification-disabled mode. The client TLS context is built from the platform trust store or an explicitly supplied non-secret CA file, requires `CERT_REQUIRED`, enables `check_hostname`, and enforces a minimum TLS version of TLSv1.2. Endpoint, server-name, and trust-policy inputs do not grant admission; the selected bearer and edge must already have been admitted and selected by ST-031.

Execution semantics preserve the ST-032 uncertainty boundary:

```text
connection/TLS handshake failure before frame send -> FAILED + confirmed side-effect absence
failure after request frame send -> INDETERMINATE
invalid/mismatched ACK -> INDETERMINATE
correlated application ACK -> ACKNOWLEDGED
ACKNOWLEDGED != human rendering/read receipt/final delivery truth
```

```text
Source adapter: IMPLEMENTED
Deterministic TLS policy/failure/ACK tests: IMPLEMENTED
Runtime manifest: IMPLEMENTED
Hosted validation: SUCCESS
PR #37 exact head b9cdea0505adabc4a5ecab316caf6f454c907f81
Edge Runtime Validation run 33032871912: SUCCESS
Managed Completion run 33032871878: SUCCESS
Test Readiness run 33032871859: SUCCESS
device-continuity run 33032871855: SUCCESS
Merge 772428118cfb033a8d5a55eea8a3b1eb8320f8f2
Real admitted public TLS endpoint dispatch: NOT PROVEN
Connected-KV live ST-034 execution receipt: NOT PROVEN
Distinct-device delivery evidence: NOT PROVEN
Edge restart/replacement proof after real dispatch: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```


## ST-035 — TLS Receiving-Edge Admission Surface

Issue #39 owns the receiver-side public TLS surface required to turn ST-034 from an outbound client primitive into a distinct-edge runtime path.

```text
src/stegtalk/public_tls_receiver.py
runtime/public-tls-receiver.v1.json
tests/test_public_tls_receiver.py
.github/workflows/edge-runtime.yml
```

StegTalk does not load, mint, store, or expose the TLS server private key. A preconfigured `ssl.SSLContext` is supplied by the runtime under TV/TVC-owned credential authority. The receiver then verifies the exact framed request hash, requires machine-visible attempt/selection/edge/bearer/idempotency bindings, and invokes a caller-supplied admission check against that exact request before returning application acceptance.

```text
invalid protocol -> negative ACK + fail closed
request hash mismatch -> negative ACK + fail closed
missing execution binding -> negative ACK + fail closed
admission callback false -> negative ACK + fail closed
admitted exact request -> correlated application ACK
application ACK != human rendering/read receipt/final delivery truth
```

```text
Source receiver: IMPLEMENTED
Runtime manifest: IMPLEMENTED
Deterministic receiver/admission tests: IMPLEMENTED
Hosted validation: SUCCESS
PR #40 exact head a1f086b0d1dbc5545f872c9fb1144171348e3c01
Edge Runtime Validation run 33033096653: SUCCESS
Managed Completion run 33033096602: SUCCESS
Test Readiness run 33033096983: SUCCESS
device-continuity run 33033096643: SUCCESS
Merge dcda8a8405f510d9abce239ecd246c87220d2c6b
Real server certificate/runtime context proof: NOT PROVEN
Real public-network receive proof: NOT PROVEN
Connected-KV receive evidence: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```


## ST-036 — KnowledgeVault Durability Before Positive TLS ACK

Issue #41 closes the receiver-side durability race between ST-035 admission and application acknowledgement. A positive TLS application ACK is no longer permitted merely because the frame is syntactically valid and admitted.

The exact admitted request is converted into receiver-acceptance evidence and handed to an `AcceptanceSink` before any `accepted=true` ACK is emitted. The canonical live sink dynamically consumes continuity-vault-kit rather than duplicating its persistence contract:

```text
execution.vault_store.KnowledgeVaultExecutionStore
execution.communication_runtime.CommunicationRuntimeJournal
continuity-vault-kit receiver-evidence merge:
08011eea59ad2b7613102c032f6fe25035b8f765
```

The sink recovers the already-bound selection + lease for the attempt and calls `CommunicationRuntimeJournal.record_receive(...)`. Therefore KnowledgeVault validates the exact attempt, selection hash, selected edge, bearer, idempotency key, request hash, positive acceptance, and no-new-authority boundary.

```text
invalid/unadmitted request -> negative ACK; no acceptance persistence
admitted + durable KV acceptance -> positive ACK
admitted + KV/sink failure -> negative ACK / receiver error
sender interpretation after any post-dispatch negative/missing ACK -> INDETERMINATE / VERIFY_EXTERNALLY
positive ACK != human rendering/read receipt/final delivery truth
```

```text
StegTalk source: IMPLEMENTED
continuity-vault-kit receiver persistence: MERGED
ST-036 runtime manifest: IMPLEMENTED
Hosted validation: PENDING
Connected personal KnowledgeVault live receive proof: NOT PROVEN
Real distinct-device TLS dispatch+receive proof: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

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
    +--> ST-034 TLS-bound public IP client
    +--> ST-035 TLS receiving edge
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
StegTalk ST-034 = TLS-bound public IP edge implementation
StegTalk ST-035 = TLS receiving-edge admission implementation
StegTalk ST-036 = durable-before-positive-ACK gate into KnowledgeVault
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
6. hosted-validate and merge ST-036;
7. configure ST-035 server TLS context only through TV/TVC-owned runtime authority;
8. use merged ST-034 only with an actually admitted ST-035 public TLS endpoint;
9. prove a real TLS handshake/public-network dispatch+receive with sender execution and receiver acceptance durably persisted to connected KV before positive ACK;
10. complete ST-029 modem/SIM outbound, `+CDS` delivery report, inbound correlation, and multipart partial-failure evidence on physical hardware;
11. only after those proofs mark the relevant runtime activation states complete.

## Archive posture

DO NOT archive as fully activated. ST-033 now supplies real OS TCP socket execution under ST-032, but actual admitted distinct-device edges, connected-KV live execution, real public-network TLS dispatch, physical/network delivery, edge replacement proof, and production activation remain open.
