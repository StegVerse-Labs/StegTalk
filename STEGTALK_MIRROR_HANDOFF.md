# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active task: ST-029
Primary SMS architecture: sovereign direct cellular modem
Cloud messaging dependency: none
SMS aggregator dependency: none
Public mobile-network dependency: yes
```

## Active workstream — ST-029 Sovereign Direct-Modem SMS

Goal: bidirectional SMS between ordinary telephone messaging and StegVerse without ClickSend, Twilio, another aggregator, webhook SaaS, or provider SDK.

```text
Source implementation: COMPLETE
Targeted validation: PENDING
Direct modem binding: NOT STARTED
SIM/eSIM binding: NOT STARTED
Carrier registration proof: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

Installed source:

```text
src/stegtalk/sovereign_sms_modem.py
tests/test_sovereign_sms_modem.py
runtime/sovereign-sms-modem.v1.json
STEGTALK_TASK_QUEUE.json
```

Implementation commits:

```text
18d7cfbaeca24a82fa20a14923113b7d328b9324
9308c4df3fc955bdbe4de00005c1699a0213221b
fe1e6954c604387fb1e6a964a5a3ff3f16a4dc54
258fb130e6b9cfc56c8ea71546313c65398b769b
```

## Architecture

```text
StegTalk/Auri
    |
    v
StegVerse admissibility + receipt boundary
    |
    v
local ST-029 modem driver
    |
    v
USB/UART cellular modem + SIM/eSIM
    |
    v
mobile carrier radio/SMSC
    |
    v
ordinary telephone SMS
```

Reverse direction:

```text
ordinary telephone SMS
    |
    v
mobile carrier radio/SMSC
    |
    v
StegVerse-owned modem + SIM/eSIM
    |
    v
3GPP +CMT inbound notification
    |
    v
ST-029 parser/receipt boundary
    |
    v
StegTalk external_sms envelope/inbox
```

The carrier is an external transport network, not an application provider. StegVerse owns the application protocol, modem control, message normalization, admission, storage, correlation, and receipts.

## Standards boundary

ST-029 targets the standardized cellular terminal interface rather than a vendor cloud API:

```text
3GPP TS 27.005 — DTE/DCE interface for SMS/CBS
3GPP TS 27.007 — AT command set for User Equipment
```

Current source implements the text-mode minimum path:

```text
AT
ATE0
AT+CMGF=1
AT+CSCS="GSM"
AT+CNMI=2,2,0,0,0
AT+CMGS="+E164_NUMBER"
<body><CTRL-Z>
```

Inbound source parses direct `+CMT` notifications into StegTalk `external_sms` envelopes and emits StegVerse transport receipts.

## Authority and security boundary

```text
no cloud messaging provider != no carrier
carrier network != trusted StegVerse runtime
source implementation != validation
modem detected != modem registered
registered != SMS proven
submitted != delivered
SMS != StegTalk secure channel
```

Ordinary SMS remains a plaintext external transport. StegVerse must explicitly admit any downgrade from protected internal content to carrier SMS.

## iPhone constraint

The iPhone is not the preferred autonomous gateway. Apple's public MessageUI interface lets an app present a user-controlled SMS composer, after which Messages performs the send; it is not a general autonomous background SMS gateway. Therefore the sovereign gateway should be separate StegVerse-owned cellular hardware, while an iPhone can remain an ordinary SMS endpoint.

## ST-028 ClickSend status

ST-028 remains only as an optional interoperability adapter and is no longer the canonical activation path.

```text
ST-028 state: OPTIONAL_NONCANONICAL
ClickSend activation required: false
ClickSend credentials required for ST-029: false
```

## Required continuation

1. Run `PYTHONPATH=. pytest -q tests/test_sovereign_sms_modem.py` and record deterministic evidence.
2. Add local modem discovery and capability interrogation (`ATI`, registration, SIM readiness, signal, SMS capability).
3. Add a concrete local serial runtime binding without cloud dependencies.
4. Bind StegVerse-owned cellular hardware and SIM/eSIM.
5. Prove carrier registration.
6. Send StegVerse -> ordinary phone and persist the modem + StegTalk receipts.
7. Send ordinary phone -> StegVerse and prove direct `+CMT` ingestion.
8. Add restart/recovery, duplicate suppression, multipart/PDU handling, and delivery-report ingestion.
9. Only after live bidirectional proof mark ST-029 activated.

## Archive posture

DO NOT archive as complete. ST-029 source exists, but validation, hardware binding, radio registration, live bidirectional proof, and activation remain open.

## Percentages

```text
ST-029 source implementation: 100%
ST-029 targeted validation: 0% observed
ST-029 hardware/runtime integration: 0%
ST-029 live bidirectional proof: 0%
ST-029 goal activation: 35%
Developed source files vs scaffolding/stubs: 4 developed / 0 placeholder source stubs; physical modem/runtime activation remains unbuilt
```
