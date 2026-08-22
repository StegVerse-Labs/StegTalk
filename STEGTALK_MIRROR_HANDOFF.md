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

## ST-029 — Sovereign Direct-Modem SMS

Goal: bidirectional SMS between ordinary telephone messaging and StegVerse without ClickSend, Twilio, another aggregator, webhook SaaS, or provider SDK.

```text
Software slice: IMPLEMENTED
Dedicated CI lane: INSTALLED AND EXPANDED
Targeted validation: AWAITING OBSERVED WORKFLOW RESULT
Serial discovery/POSIX binding: IMPLEMENTED
SIM + registration capability gate: IMPLEMENTED
Same-live-session freshness gate: IMPLEMENTED
Append-only local evidence journal: IMPLEMENTED
Restart/replay/reconstruction/dedupe: IMPLEMENTED
UCS-2 PDU + multipart UDH: IMPLEMENTED
+CDS delivery-report ingestion: IMPLEMENTED
Physical modem binding: NOT PROVEN
Live carrier registration: NOT PROVEN
Live outbound/inbound/report proof: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

Current ST-029 implementation files:

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
src/stegtalk/serial_modem.py
src/stegtalk/sovereign_sms_runtime.py
src/stegtalk/sovereign_sms_journal.py
src/stegtalk/sms_pdu.py
src/stegtalk/sovereign_sms_pdu_runtime.py
```

ST-029 keeps registration proof and submission in the same live serial session, refreshes registration immediately before `AT+CMGS`, supports text and UCS-2 PDU multipart submission, parses delivery reports, and keeps edge-local replayable evidence. Submission or carrier status is evidence only; neither grants StegVerse authority.

## ST-030 — KnowledgeVault-Hosted Communication Extension

Goal: make StegTalk a communication execution extension of an individual's durable KnowledgeVault while keeping the handset/modem/device as an ephemeral execution edge rather than continuity authority.

```text
KV extension request builder: IMPLEMENTED
Closed host binding validation: IMPLEMENTED
KV extension tests: IMPLEMENTED
StegTalk CI integration: IMPLEMENTED
KnowledgeVault recovery/extension host: IMPLEMENTED IN SOURCE
KnowledgeVault portable execution backing store: IMPLEMENTED IN SOURCE
Connected KnowledgeVault _System/Execution backing layout: CREATED AND VERIFIED
Live communication attempt persisted into KV: NOT PROVEN
Edge restart/device replacement reconstruction: NOT PROVEN
Production activation: NOT ACTIVE
Claim state: OPEN
```

ST-030 implementation files:

```text
src/stegtalk/knowledge_vault_extension.py
tests/test_knowledge_vault_extension.py
.github/workflows/sovereign-sms.yml
```

KnowledgeVault host-side implementation now includes:

```text
schemas/execution-attempt-journal.schema.json
schemas/execution-recovery-decision.schema.json
schemas/communication-extension.schema.json
execution/recovery.py
execution/extensions.py
execution/vault_store.py
```

The connected KnowledgeVault contains:

```text
_System/Execution/
    Attempts/
    Extensions/
    Receipts/
    Recovery/
```

This proves the durable personal-cloud backing location exists. It does not yet prove that an actual StegTalk communication attempt has been persisted there and reconstructed across an edge interruption.

## Authority topology

```text
individual KnowledgeVault / cloud account
    |
    +--> durable subject + authority refs
    +--> payload ref + hash
    +--> idempotency + execution attempt state
    +--> replay / reconstruction / recovery truth
    |
    v
ST-030 StegTalk communication extension
    |
    +--> exact KV host binding
    +--> secure envelope / routing / bearer selection / delivery truth
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

Edge invariant:

```text
device_role = EPHEMERAL_TRANSPORT_EDGE
device_authority = false
device_continuity_authority = false
vault_continuity_authority = true
credential_material = null
```

The device may execute the consequence of a KV-hosted communication decision. It cannot become the durable source of identity, authorization, conversation continuity, replay state, or recovery authority merely because it transported the message.

ST-030 does not replace ST-029. ST-029 is a transport implementation. ST-030 changes the durable hosting/authority boundary from device-local continuity to KnowledgeVault-hosted continuity.

## Evidence boundary

`src/stegtalk/sovereign_sms_journal.py` remains useful as an edge-local evidence cache/fallback proof surface. It is no longer considered the intended final ownership boundary for cross-device continuity. Durable cross-device attempt state belongs in KnowledgeVault under ST-030.

```text
KnowledgeVault host != bearer selector
StegTalk transport authority != durable personal continuity authority
device execution != device authority
device restart != loss of durable communication state
carrier network != evidence authority
source implementation != validation
software registration != live registration proof
+CMGS submitted != delivered
+CDS status = evidence, not authority
SMS != StegTalk secure channel
```

Ordinary SMS remains an external transport boundary. User-visible SMS content is a governed presentation downgrade when an unmodified recipient must render ordinary text.

## Validation boundary

`.github/workflows/sovereign-sms.yml` validates the ST-029 modem/runtime/journal/PDU/report lanes plus ST-030 KnowledgeVault request/binding tests.

The available combined-status endpoint continues to surface no statuses for the current heads. Validation is therefore recorded as unobserved, not passed.

## ST-028 ClickSend status

```text
ST-028 state: OPTIONAL_NONCANONICAL
ClickSend activation required: false
ClickSend credentials required for ST-029/ST-030: false
```

## Recent ST-030 commits

```text
adbba9e4180c74031f1a9bf57b1b5827ed0b4d88  initial KnowledgeVault extension adapter
b903fb27834c10749a0f0d8e818837516ef504c8  closed-contract alignment
c5f36b78e5d993544f8acc84cea38d7f5f214c40  KV extension tests
b7afb502504fc3aa40c6e6c6b573ee51c35a79bc  CI expansion
5c71c2611401fa51bbaf796591740274d9e4eb6f  task queue adds ST-030
```

## Required continuation

1. Observe StegTalk and KnowledgeVault recovery/extension CI and repair any failures.
2. Persist a real ST-030 hosted request + execution attempt into the actual KnowledgeVault `_System/Execution` backing surface.
3. Bind the hosted attempt to ST-029 edge execution without copying continuity authority onto the device.
4. Persist readiness, dispatch, delivery-report, inbound, and dedupe evidence back into the KV-hosted attempt.
5. Interrupt/restart or replace the edge and prove KV reconstructs the exact attempt without new authority or duplicate dispatch.
6. Exercise ST-029 against actual StegVerse-owned modem/SIM hardware and prove live registration, outbound, delivery report, and inbound SMS.
7. Only after those proofs mark ST-029/ST-030 activated as applicable.

## Archive posture

DO NOT archive as complete. The durable host software and real KnowledgeVault backing layout now exist, but a live communication attempt has not yet been persisted/recovered through KV, and physical SMS proof remains open.

## Percentages

```text
ST-029 software slice: 100% implemented
ST-029 goal activation: 74%
ST-030 software/host slice: 100% implemented for request/binding/recovery/store structure
ST-030 goal activation: 52% (source/tests/CI + live KV backing layout exist; no live hosted attempt/recovery proof yet)
Developed active ST-029/ST-030 artifacts vs placeholders: 21 developed / 0 placeholder artifacts
```
