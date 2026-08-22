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
Physical modem binding: NOT PROVEN
Live carrier registration proof: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Multipart/PDU support: NOT IMPLEMENTED
Delivery-report ingestion: NOT IMPLEMENTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

## Installed ST-029 artifacts

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
src/stegtalk/serial_modem.py
src/stegtalk/sovereign_sms_runtime.py
src/stegtalk/sovereign_sms_journal.py
tests/test_sovereign_sms_modem.py
tests/test_modem_capabilities.py
tests/test_serial_modem.py
tests/test_sovereign_sms_runtime.py
tests/test_sovereign_sms_journal.py
.github/workflows/sovereign-sms.yml
runtime/sovereign-sms-modem.v1.json
STEGTALK_TASK_QUEUE.json
```

Recent implementation commits:

```text
4bca21ebb089a7744d3dda3cf8e674785a70f0de  modem identity/SIM/registration/signal/SMS-mode interrogation
dac9975e746ce4428a6889a7380f50b3d009ef96  capability and registration-gate tests
fb44a8437bd54dd3eab335eab6dfe63cfb3118b6  dedicated sovereign-SMS CI lane
7c647efc8155bc4d18d0db43cd9cffc9aef27bff  concrete POSIX serial discovery/runtime binding
a49d7d80cb45eca5721e2770ad00169368232480  serial discovery/binding tests
bae0db8959dc6c973460853a7778653bbc69ffd8  composed discovery/readiness runtime
cf3b4354eab18cb5a6abe97ce7cd074952f8cf37  same-live-session readiness/send gate
bd9722264ee93dfe83d297dbca6c13af02fd442c  state-drift/submission tests
149859dd0f3c6926ed2216249fa6d2050f6c25e1  append-only hash-chained SMS evidence journal
2ae26b6d5cc759789fad930adb70d1240b74f73f  restart/replay/tamper/dedupe journal tests
857af4405b84aeab6d5643c24f087a76977313ee  live session bound to evidence journal
a6fd3986e9b370f5b636922241ab01a92ae22a0a  live-session journal integration tests
0141556ae109275f9cb278ce9a9ed40192ffa8af  CI expanded across journal/recovery lane
679c44839780449950a6c99d5496c933eec0534c  runtime contract advanced to v1.2.0
780d8e1f11f129ec6fd34e8e130525969d1d3ed9  task queue advanced through replay recovery/dedupe
```

## Runtime architecture now implemented in software

```text
StegTalk/Auri
    |
    v
StegVerse admissibility + receipt boundary
    |
    v
ST-029 sovereign SMS driver
    |
    v
local serial discovery
    |
    v
POSIX 115200 8N1 serial runtime
    |
    v
SMS initialization
    |
    v
ATI / CPIN / CREG / CSQ / CMGF readiness gate
    |
    +--> capability + readiness receipts --> local hash-chained journal
    |
    v
persistent live modem session
    |
    v
fresh CPIN / CREG / CSQ / CMGF check immediately before send
    |
    +--> fresh capability receipt --> local hash-chained journal
    |
    v
AT+CMGS submission
    |
    +--> transport + session receipts --> local hash-chained journal
    |
    v
mobile carrier radio/SMSC
    |
    v
ordinary telephone SMS
```

Inbound/recovery software path:

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
3GPP +CMT notification
    |
    v
ST-029 parse + correlation hash
    |
    v
journal duplicate check
    |---- duplicate --> suppress
    |
    +---- new -------> append + StegTalk external_sms envelope/inbox

restart
    |
    v
verify every journal sequence/link/receipt hash/record hash
    |
    v
reconstruct receipt order + inbound correlation set + runtime summary
```

The carrier is an external transport network, not an evidentiary authority. StegVerse owns application protocol, modem control, admission, local evidence, replay, reconstruction, duplicate suppression, message normalization, storage, correlation, and receipts.

## Standards and local binding boundary

ST-029 targets standardized terminal control rather than a vendor cloud API:

```text
3GPP TS 27.005 — DTE/DCE interface for SMS/CBS
3GPP TS 27.007 — AT command set for User Equipment
```

Text-mode initialization/send path:

```text
AT
ATE0
AT+CMGF=1
AT+CSCS="GSM"
AT+CNMI=2,2,0,0,0
AT+CMGS="+E164_NUMBER"
<body><CTRL-Z>
```

Capability interrogation:

```text
ATI
AT+CPIN?
AT+CREG?
AT+CSQ
AT+CMGF?
```

`src/stegtalk/serial_modem.py` provides dependency-free POSIX serial discovery/binding. `src/stegtalk/modem_capabilities.py` fails closed unless SIM readiness, HOME/ROAMING registration, and SMS mode are valid. `src/stegtalk/sovereign_sms_runtime.py` keeps readiness proof and submission in the same live session and refreshes registration before each send.

`src/stegtalk/sovereign_sms_journal.py` is local StegVerse state. It appends canonical JSONL records with sequence, previous-record hash, receipt hash, and record hash; fsyncs every append; verifies the entire chain on restart; exposes deterministic receipt replay and reconstructed summary; and persists inbound correlation hashes so duplicate suppression survives restart. Journal corruption fails closed.

## Validation boundary

`.github/workflows/sovereign-sms.yml` now runs:

```text
python -m pytest -q \
  tests/test_sovereign_sms_modem.py \
  tests/test_modem_capabilities.py \
  tests/test_serial_modem.py \
  tests/test_sovereign_sms_runtime.py \
  tests/test_sovereign_sms_journal.py
```

A combined-status query for commit `0141556ae109275f9cb278ce9a9ed40192ffa8af` returned no surfaced statuses. Direct workflow-run lookup is unavailable through the current connector route. Targeted validation therefore remains unobserved rather than passed.

## Authority and security boundary

```text
no cloud messaging provider != no carrier
carrier network != trusted StegVerse runtime
carrier network != evidence authority
source implementation != validation
software serial binding != physical modem binding
software registration parser != live registration proof
startup registration != registration at submission
journal replay != live delivery proof
registered != SMS proven
submitted != delivered
SMS != StegTalk secure channel
```

Ordinary SMS remains an external transport boundary. StegVerse must explicitly govern any downgrade or presentation transformation required for an ordinary unmodified SMS recipient.

## ST-028 ClickSend status

```text
ST-028 state: OPTIONAL_NONCANONICAL
ClickSend activation required: false
ClickSend credentials required for ST-029: false
```

## Required continuation

1. Observe the dedicated `StegTalk Sovereign SMS` workflow result on a surfaced run and repair any failure.
2. Execute `SovereignSmsSession` + `SovereignSmsJournal` against an actual StegVerse-owned modem through `PosixSerialRuntime`.
3. Bind SIM/eSIM and persist the emitted capability/readiness evidence.
4. Prove live carrier registration in the same open session used for submission.
5. Send StegVerse -> ordinary phone and retain the full chained evidence sequence.
6. Send ordinary phone -> StegVerse and prove direct `+CMT` ingestion plus journal-backed duplicate suppression.
7. Implement multipart/PDU handling and delivery-report ingestion while physical proof remains pending.
8. Only after live bidirectional proof mark ST-029 activated.

## Archive posture

DO NOT archive as complete. Restart/recovery, replay, reconstruction, and duplicate suppression are now implemented in software, but observed CI, physical hardware binding, live carrier registration, bidirectional delivery proof, multipart/PDU, delivery reports, and activation remain open.

## Percentages

```text
ST-029 current software slice: 100% implemented
ST-029 targeted validation: 0% observed until a workflow result is surfaced
ST-029 hardware/runtime integration: 50% (software path through governed live session + durable recovery exists; physical modem not bound)
ST-029 live bidirectional proof: 0%
ST-029 goal activation: 68%
Developed active ST-029 artifacts vs placeholders: 13 developed / 0 placeholder artifacts; physical modem/SIM/network proof remains external to repository software
```
