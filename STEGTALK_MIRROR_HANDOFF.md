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
Source implementation: COMPLETE FOR CURRENT SOFTWARE SLICE
Dedicated CI lane: INSTALLED
Targeted validation: AWAITING OBSERVED WORKFLOW RESULT
Direct serial-device binding: NOT STARTED
SIM/eSIM readiness interrogation: IMPLEMENTED IN SOFTWARE
Network registration interrogation/gate: IMPLEMENTED IN SOFTWARE
Live carrier registration proof: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

Installed source:

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
tests/test_sovereign_sms_modem.py
tests/test_modem_capabilities.py
.github/workflows/sovereign-sms.yml
runtime/sovereign-sms-modem.v1.json
STEGTALK_TASK_QUEUE.json
```

Implementation commits:

```text
18d7cfbaeca24a82fa20a14923113b7d328b9324
9308c4df3fc955bdbe4de00005c1699a0213221b
fe1e6954c604387fb1e6a964a5a3ff3f16a4dc54
258fb130e6b9cfc56c8ea71546313c65398b769b
4bca21ebb089a7744d3dda3cf8e674785a70f0de
dac9975e746ce4428a6889a7380f50b3d009ef96
fb44a8437bd54dd3eab335eab6dfe63cfb3118b6
29fa9193b0e86b2d69e0a74bd65f7c8f2561d90d
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
capability + SIM + registration gate
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

Current capability interrogation adds:

```text
ATI
AT+CPIN?
AT+CREG?
AT+CSQ
AT+CMGF?
```

`src/stegtalk/modem_capabilities.py` records modem identity, SIM readiness, registration state, signal observation, and SMS text-mode state. `require_registered_sms_capability()` fails closed unless the SIM is ready, registration is HOME or ROAMING, and SMS text mode is active. These are software observations only; they are not live hardware proof until exercised against an attached modem.

Inbound source parses direct `+CMT` notifications into StegTalk `external_sms` envelopes and emits StegVerse transport receipts.

## Validation boundary

`.github/workflows/sovereign-sms.yml` now runs only the sovereign-SMS software slice:

```text
python -m pytest -q tests/test_sovereign_sms_modem.py tests/test_modem_capabilities.py
```

The workflow exists and is triggered on relevant pushes/PRs. A green run must be observed before targeted validation is marked complete.

## Authority and security boundary

```text
no cloud messaging provider != no carrier
carrier network != trusted StegVerse runtime
source implementation != validation
software registration parser != live registration proof
modem detected != modem registered
registered != SMS proven
submitted != delivered
SMS != StegTalk secure channel
```

Ordinary SMS remains an external transport boundary. StegVerse must explicitly govern any downgrade or presentation transformation required for an ordinary unmodified SMS recipient.

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

1. Observe the dedicated `StegTalk Sovereign SMS` workflow result for the current head and repair any failures.
2. Add concrete local serial-device discovery and runtime binding without cloud dependencies.
3. Bind StegVerse-owned cellular hardware and SIM/eSIM.
4. Execute the implemented capability interrogation against hardware and persist the resulting receipt.
5. Prove live carrier registration.
6. Send StegVerse -> ordinary phone and persist modem + StegTalk receipts.
7. Send ordinary phone -> StegVerse and prove direct `+CMT` ingestion.
8. Add restart/recovery, duplicate suppression, multipart/PDU handling, and delivery-report ingestion.
9. Only after live bidirectional proof mark ST-029 activated.

## Archive posture

DO NOT archive as complete. The current software slice and dedicated validation lane exist, but observed CI, serial-device binding, physical hardware binding, radio registration, live bidirectional proof, and activation remain open.

## Percentages

```text
ST-029 source implementation for current software slice: 100%
ST-029 targeted validation: 0% observed until CI result is inspected
ST-029 hardware/runtime integration: 10% (capability/registration software gate exists; no serial or physical binding)
ST-029 live bidirectional proof: 0%
ST-029 goal activation: 45%
Developed source/test/workflow artifacts vs placeholders: 7 developed / 0 placeholder artifacts in the active ST-029 slice; physical runtime remains unbound
```
