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
Durable readiness receipt writer: IMPLEMENTED
Same-live-session readiness/send binding: IMPLEMENTED
Fresh registration immediately before submission: IMPLEMENTED
Physical modem binding: NOT PROVEN
Live carrier registration proof: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Production activation: NOT ACTIVE
Claim state: OPEN
```

## Installed ST-029 artifacts

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
src/stegtalk/serial_modem.py
src/stegtalk/sovereign_sms_runtime.py
tests/test_sovereign_sms_modem.py
tests/test_modem_capabilities.py
tests/test_serial_modem.py
tests/test_sovereign_sms_runtime.py
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
0edab12b18317c7b185d77221b29ecd68e011336  CI expanded across serial binding
bae0db8959dc6c973460853a7778653bbc69ffd8  composed discovery/readiness runtime + durable readiness receipt
36892bbb2e286d9dafdabecaf7dd7f804fa58586  readiness orchestration tests
171e59ae322b09504d29bbd12b3a1255a16922e0  CI expanded across readiness runtime
cf3b4354eab18cb5a6abe97ce7cd074952f8cf37  same-live-session readiness/send gate with pre-send registration refresh
bd9722264ee93dfe83d297dbca6c13af02fd442c  live-session state-drift and submission tests
fbfd51cd87ad710b81abfb3f603f97d3f78f9800  runtime contract advanced to v1.1.0
cf8d10107da896421bb7c404367861289614fbae  task queue advanced to live-session gate state
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
    v
persistent live modem session
    |
    v
fresh CPIN / CREG / CSQ / CMGF check immediately before send
    |
    v
AT+CMGS submission
    |
    v
mobile carrier radio/SMSC
    |
    v
ordinary telephone SMS
```

Reverse direction remains:

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

`src/stegtalk/serial_modem.py` discovers common Linux/macOS serial modem device families and provides a dependency-free POSIX serial binding at 115200 8N1. It creates the existing `ModemPort` boundary directly, with bounded reads and fail-closed open/timeout behavior. No cloud messaging provider or vendor provider SDK is introduced.

`src/stegtalk/modem_capabilities.py` records modem identity, SIM readiness, registration state, signal observation, and SMS text-mode state. `require_registered_sms_capability()` fails closed unless the SIM is ready, registration is HOME or ROAMING, and SMS text mode is active.

`src/stegtalk/sovereign_sms_runtime.py` now composes discovery, initialization, capability interrogation, durable readiness evidence, and a live session. `SovereignSmsSession.send()` re-runs the registration/capability gate immediately before `AT+CMGS`; if registration changes after startup, submission is blocked before the destination command is emitted. Readiness, fresh capability state, and transport submission are cryptographically correlated by receipt hashes.

These are implemented software capabilities, not live physical proof until executed against attached StegVerse-owned hardware.

## Validation boundary

`.github/workflows/sovereign-sms.yml` now runs:

```text
python -m pytest -q \
  tests/test_sovereign_sms_modem.py \
  tests/test_modem_capabilities.py \
  tests/test_serial_modem.py \
  tests/test_sovereign_sms_runtime.py
```

The available combined-status endpoint has not surfaced a status for the new main commits, and direct workflow-run lookup is not available through the current connector route. Therefore targeted validation remains recorded as unobserved rather than passed.

## Authority and security boundary

```text
no cloud messaging provider != no carrier
carrier network != trusted StegVerse runtime
source implementation != validation
software serial binding != physical modem binding
software registration parser != live registration proof
startup registration != registration at submission
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
2. Execute `SovereignSmsSession` against an actual StegVerse-owned modem through `PosixSerialRuntime`.
3. Bind SIM/eSIM and persist the emitted readiness/capability receipts.
4. Prove live carrier registration in the same open session used for submission.
5. Send StegVerse -> ordinary phone and persist readiness + fresh capability + modem + StegTalk receipts.
6. Send ordinary phone -> StegVerse and prove direct `+CMT` ingestion.
7. Add restart/recovery, duplicate suppression, multipart/PDU handling, and delivery-report ingestion.
8. Only after live bidirectional proof mark ST-029 activated.

## Archive posture

DO NOT archive as complete. The software path now reaches a readiness-bound live submission session, but observed CI, physical hardware binding, live carrier registration, bidirectional delivery proof, and activation remain open.

## Percentages

```text
ST-029 current software slice: 100% implemented
ST-029 targeted validation: 0% observed until a workflow result is surfaced
ST-029 hardware/runtime integration: 45% (discovery + serial runtime + capability gate + live-session orchestration implemented; physical device not bound)
ST-029 live bidirectional proof: 0%
ST-029 goal activation: 62%
Developed active ST-029 artifacts vs placeholders: 11 developed / 0 placeholder artifacts; physical modem/SIM/network proof remains external to repository software
```
