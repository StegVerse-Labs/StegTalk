# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active tasks: ST-029, ST-030
Primary SMS architecture: sovereign direct cellular modem
Durable continuity host: KnowledgeVault / StegVerse-Labs/continuity-vault-kit
Cloud messaging dependency: none
SMS aggregator dependency: none
Public mobile-network dependency: yes for ordinary public SMS
```

## Active workstream — ST-029 Sovereign Direct-Modem SMS

Goal: bidirectional SMS between ordinary telephone messaging and StegVerse without ClickSend, Twilio, another aggregator, webhook SaaS, or provider SDK.

```text
Source implementation: COMPLETE FOR CURRENT SOFTWARE SLICE
Dedicated CI lane: INSTALLED AND EXPANDED
Targeted validation: AWAITING OBSERVED WORKFLOW RESULT
Serial-device discovery: IMPLEMENTED
Concrete POSIX serial runtime binding: IMPLEMENTED
SIM/eSIM readiness interrogation: IMPLEMENTED IN SOFTWARE
Network registration interrogation/gate: IMPLEMENTED IN SOFTWARE
Readiness orchestration: IMPLEMENTED
Same-live-session readiness/send binding: IMPLEMENTED
Fresh registration immediately before submission: IMPLEMENTED
Append-only hash-chained evidence journal: IMPLEMENTED
Restart verification/reconstruction: IMPLEMENTED
Deterministic receipt replay: IMPLEMENTED
Inbound duplicate suppression: IMPLEMENTED
Duplicate suppression across restart: IMPLEMENTED
UCS-2 PDU submission: IMPLEMENTED
Multipart concatenation UDH: IMPLEMENTED
Status-report request on PDU submission: IMPLEMENTED
+CDS delivery-report ingestion: IMPLEMENTED
Delivery-report journal evidence: IMPLEMENTED
Physical modem binding: NOT PROVEN
Live carrier registration proof: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Live delivery-report proof: NOT STARTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

## Active workstream — ST-030 KnowledgeVault-Hosted Communication Extension

Goal: make StegTalk a communication execution extension of an individual's durable KnowledgeVault while keeping the handset/modem/device as an ephemeral edge rather than continuity authority.

```text
KV extension request builder: IMPLEMENTED
Closed host binding validation: IMPLEMENTED
KV extension tests: IMPLEMENTED
StegTalk CI integration: IMPLEMENTED
KnowledgeVault host schemas/runtime: IMPLEMENTED IN continuity-vault-kit SOURCE SLICE
Live KnowledgeVault backing proof: NOT STARTED
Edge restart/device replacement reconstruction proof: NOT STARTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

ST-030 does not replace ST-029. ST-029 remains the transport implementation for direct public SMS. ST-030 changes where durable authority/state lives and how transport is invoked.

## Installed ST-029/ST-030 artifacts

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
src/stegtalk/serial_modem.py
src/stegtalk/sovereign_sms_runtime.py
src/stegtalk/sovereign_sms_journal.py
src/stegtalk/sms_pdu.py
src/stegtalk/sovereign_sms_pdu_runtime.py
src/stegtalk/knowledge_vault_extension.py
tests/test_sovereign_sms_modem.py
tests/test_modem_capabilities.py
tests/test_serial_modem.py
tests/test_sovereign_sms_runtime.py
tests/test_sovereign_sms_journal.py
tests/test_sms_pdu.py
tests/test_sovereign_sms_pdu_runtime.py
tests/test_knowledge_vault_extension.py
.github/workflows/sovereign-sms.yml
runtime/sovereign-sms-modem.v1.json
STEGTALK_TASK_QUEUE.json
```

## Current software path

The durable-hosted path is now:

```text
individual KnowledgeVault / cloud account
    |
    +--> durable subject + authority refs
    +--> payload ref + hash
    +--> idempotency + recoverable execution state
    +--> replay / reconstruction / recovery truth
    |
    v
ST-030 StegTalk communication extension
    |
    +--> exact host binding validation
    +--> secure envelope / routing / bearer / delivery truth
    |
    v
EPHEMERAL_TRANSPORT_EDGE
(handset / cellular modem / radio / gateway)
    |
    v
ST-029 direct cellular transport or another admitted StegTalk bearer
    |
    v
recipient / external network
```

The edge device explicitly has:

```text
device_role = EPHEMERAL_TRANSPORT_EDGE
device_authority = false
device_continuity_authority = false
vault_continuity_authority = true
credential_material = null
```

The device may execute the consequence of a KV-hosted communication decision. It cannot become the durable source of identity, authorization, conversation continuity, replay state, or recovery authority merely because it transported the message.

## ST-029 modem path

```text
StegTalk extension execution
    |
    v
local serial discovery / POSIX modem runtime
    |
    v
ATI / CPIN / CREG / CSQ / CMGF readiness gate
    |
    +--> readiness + capability evidence --> evidence journal / KV host bridge target
    |
    v
same open modem session
    |
    v
fresh registration check immediately before submission
    |
    +----------------------+-------------------------+
    |                                                |
    v                                                v
text SMS path                                  UCS-2 PDU path
AT+CMGF=1                                     AT+CMGF=0
AT+CMGS="destination"                        AT+CMGS=<TPDU octets>
    |                                                |
    |                                         one or N parts
    |                                         8-bit concat UDH
    |                                         status-report request
    |                                                |
    +----------------------+-------------------------+
                           |
                           v
                  transport receipts
                           |
                           v
                   carrier radio/SMSC
                           |
                           v
                 ordinary SMS endpoint
```

Delivery evidence path:

```text
carrier delivery status
    |
    v
+CDS unsolicited report + SMS-STATUS-REPORT PDU
    |
    v
parse message reference / recipient / status / timestamps
    |
    v
StegVerse delivery-report receipt + raw-PDU hash
    |
    v
local journal now; KV-hosted durable recovery target under ST-030
```

Carrier delivery status is evidence only. It does not grant or alter StegVerse authority.

## PDU and multipart boundary

`src/stegtalk/sms_pdu.py` implements a bounded SMS-SUBMIT/SMS-STATUS-REPORT lane:

- UCS-2 / UTF-16BE user data for ordinary recipient rendering;
- SMSC omitted in the PDU so modem/SIM configured SMSC is used;
- 8-bit concatenation UDH (`IEI 00`) for multipart messages;
- deterministic 8-bit concat reference when not supplied;
- no split inside a UTF-16 code point/surrogate pair;
- maximum 255 concatenated parts;
- status-report request bit on generated submit PDUs;
- mandatory-core SMS-STATUS-REPORT parser;
- message-reference, recipient, SCTS, discharge-time, and TP-ST capture;
- fail-closed malformed/wrong-MTI parsing;
- raw PDU retained by cryptographic hash in the resulting receipt.

`src/stegtalk/sovereign_sms_modem.py` submits these PDUs with `AT+CMGF=0` / `AT+CMGS=<tpdu_octets>` and restores text mode after the PDU sequence so the existing `+CMT` inbound path remains available.

`src/stegtalk/sovereign_sms_pdu_runtime.py` re-runs the live modem registration gate before governed Unicode/PDU submission, correlates all segment receipts in one aggregate multipart receipt, and appends delivery reports to the same journal when provided.

## Evidence/recovery boundary

`src/stegtalk/sovereign_sms_journal.py` remains the current local evidence implementation and provides append-only canonical JSONL, sequence/hash chaining, fsync, restart verification, deterministic replay, reconstruction, and duplicate suppression.

ST-030 now establishes KnowledgeVault as the durable host target for the same class of continuity state. The local journal is therefore not the final ownership boundary; it remains useful as an edge-local cache/evidence source and fallback proof surface, while durable cross-device recovery belongs to KnowledgeVault.

The carrier is an external transport network, not the evidentiary authority. The device is an execution edge, not continuity authority.

## Validation boundary

`.github/workflows/sovereign-sms.yml` now validates:

```text
ST-029 modem + capability + serial runtime
ST-029 journal/restart/replay/dedupe
ST-029 PDU/multipart/delivery reports
ST-030 KnowledgeVault extension request/binding
```

The available combined-status endpoint for current main commits continues to return no surfaced statuses. Targeted validation therefore remains `AWAITING OBSERVED WORKFLOW RESULT`; it is not claimed passed.

## Authority and security boundary

```text
KnowledgeVault host != bearer selector
StegTalk transport authority != durable personal continuity authority
device execution != device authority
device restart != loss of durable communication state
no cloud messaging provider != no carrier
carrier network != trusted StegVerse runtime
carrier network != evidence authority
source implementation != validation
software serial binding != physical modem binding
software registration parser != live registration proof
startup registration != registration at submission
PDU submission != recipient delivery
+CMGS submitted != delivered
+CDS carrier status = evidence, not StegVerse authority
journal replay != live delivery proof
SMS != StegTalk secure channel
```

Ordinary SMS remains an external transport boundary. User-visible SMS content is a governed presentation downgrade when an unmodified recipient must render ordinary text.

## ST-028 ClickSend status

```text
ST-028 state: OPTIONAL_NONCANONICAL
ClickSend activation required: false
ClickSend credentials required for ST-029/ST-030: false
```

## Recent ST-030 commits

```text
adbba9e4180c74031f1a9bf57b1b5827ed0b4d88  initial KnowledgeVault StegTalk extension adapter
b903fb27834c10749a0f0d8e818837516ef504c8  adapter aligned to closed KV host contract
c5f36b78e5d993544f8acc84cea38d7f5f214c40  StegTalk KV binding tests
b7afb502504fc3aa40c6e6c6b573ee51c35a79bc  sovereign SMS CI expanded to KV extension
5c71c2611401fa51bbaf796591740274d9e4eb6f  task queue adds ST-030
```

## Required continuation

1. Observe StegTalk sovereign-SMS/KV-extension CI and repair failures.
2. Observe KnowledgeVault execution-recovery CI and repair failures.
3. Bind ST-030 to an actual durable KnowledgeVault instance rather than only the schema/source contract.
4. Move/correlate ST-029 readiness, dispatch, delivery-report, inbound, and duplicate-suppression evidence into KV-hosted attempt state while preserving edge-local evidence where useful.
5. Restart or replace the edge device and prove the exact communication attempt is reconstructed from KV without new authority or duplicate dispatch.
6. Exercise the existing serial/runtime/PDU code against an actual StegVerse-owned cellular modem.
7. Prove HOME/ROAMING registration in the same open session used for send.
8. Send single-part and multipart ordinary SMS and retain KV-hosted + edge-local evidence.
9. Receive a real `+CDS` and inbound `+CMT`, correlate them to the KV-hosted attempt, and prove restart-safe dedupe.
10. Only after those proofs mark ST-029/ST-030 activated as applicable.

## Archive posture

DO NOT archive as complete. ST-030 now has a real source/test/CI binding and the durable authority topology is recorded, but observed CI, a real KV backing instance, edge restart/device replacement reconstruction, physical modem/SIM binding, live registration, recipient reconstruction, delivery reports, inbound proof, and production activation remain open.

## Percentages

```text
ST-029 current software slice: 100% implemented
ST-029 goal activation: 74%
ST-030 current software slice: 100% implemented for KV request/binding adapter
ST-030 goal activation: 35% (source/tests/CI and host contract exist; no live KV-backed edge execution/recovery proof yet)
Developed active ST-029/ST-030 artifacts vs placeholders: 19 developed / 0 placeholder artifacts
```
