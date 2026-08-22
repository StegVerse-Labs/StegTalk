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

## Installed ST-029 artifacts

```text
src/stegtalk/sovereign_sms_modem.py
src/stegtalk/modem_capabilities.py
src/stegtalk/serial_modem.py
src/stegtalk/sovereign_sms_runtime.py
src/stegtalk/sovereign_sms_journal.py
src/stegtalk/sms_pdu.py
src/stegtalk/sovereign_sms_pdu_runtime.py
tests/test_sovereign_sms_modem.py
tests/test_modem_capabilities.py
tests/test_serial_modem.py
tests/test_sovereign_sms_runtime.py
tests/test_sovereign_sms_journal.py
tests/test_sms_pdu.py
tests/test_sovereign_sms_pdu_runtime.py
.github/workflows/sovereign-sms.yml
runtime/sovereign-sms-modem.v1.json
STEGTALK_TASK_QUEUE.json
```

## Current software path

```text
StegTalk/Auri
    |
    v
StegVerse admissibility + receipt boundary
    |
    v
local serial discovery / POSIX modem runtime
    |
    v
ATI / CPIN / CREG / CSQ / CMGF readiness gate
    |
    +--> readiness + capability evidence --> hash-chained journal
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
                 hash-chained journal
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
hash-chained journal
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

`src/stegtalk/sovereign_sms_journal.py` remains local StegVerse state. It provides:

```text
append-only canonical JSONL
sequence + prior-record hash
receipt hash + record hash
fsync on append
full chain verification on restart
deterministic receipt replay
runtime-state reconstruction
restart-safe inbound correlation set
duplicate suppression across restart
fail-closed corruption handling
```

The carrier is an external transport network, not the evidentiary authority.

## Validation boundary

`.github/workflows/sovereign-sms.yml` now runs:

```text
python -m pytest -q \
  tests/test_sovereign_sms_modem.py \
  tests/test_modem_capabilities.py \
  tests/test_serial_modem.py \
  tests/test_sovereign_sms_runtime.py \
  tests/test_sovereign_sms_journal.py \
  tests/test_sms_pdu.py \
  tests/test_sovereign_sms_pdu_runtime.py
```

The available combined-status endpoint for current main commits continues to return no surfaced statuses. Targeted validation therefore remains `AWAITING OBSERVED WORKFLOW RESULT`; it is not claimed passed.

## Authority and security boundary

```text
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
ClickSend credentials required for ST-029: false
```

## Recent implementation commits

```text
149859dd0f3c6926ed2216249fa6d2050f6c25e1  append-only hash-chained SMS evidence journal
2ae26b6d5cc759789fad930adb70d1240b74f73f  restart/replay/tamper/dedupe journal tests
857af4405b84aeab6d5643c24f087a76977313ee  live session bound to evidence journal
a6fd3986e9b370f5b636922241ab01a92ae22a0a  live-session journal integration tests
0141556ae109275f9cb278ce9a9ed40192ffa8af  CI expanded across journal/recovery lane
3b3b0a711d84fd39e8e1561b23d44a3fa4e17dbb  UCS-2 multipart PDU and status-report codec
efbd601c17a0a9e078bdbb028642c40d8cefb8a8  PDU/status-report codec tests
47ac5294b7acbc7d40866e020ba0b5df82bc1977  modem PDU submission + delivery-report ingestion
ab071ad68555a0f834ec9d50ae5fb75afbac5004  modem PDU/report tests
817e1c0134537f3feb2ce5522388aa31ec918a57  governed multipart/report runtime wrapper
e92afbd9dbe8597adcc25164530cc33c24679cb5  governed multipart/report journal tests
5ab1ca2a565542708918982188b39967603a8c74  CI expanded across PDU/report lane
0fad898e84d7b7c4f030bd3e9b2bb0feaa4ed6e1  runtime contract v1.3.0
8131fa6dbc77c18f3f0035476148f667c305e518  queue advanced through multipart/report implementation
```

## Required continuation

1. Observe the dedicated `StegTalk Sovereign SMS` workflow result and repair any failures.
2. Exercise the existing serial/runtime/PDU code against an actual StegVerse-owned cellular modem.
3. Bind SIM/eSIM and persist actual capability/readiness evidence.
4. Prove HOME/ROAMING registration in the same open session used for send.
5. Send a single-part ordinary SMS and retain the complete evidence chain.
6. Send a multipart Unicode SMS and prove ordinary recipient reconstruction.
7. Receive and journal a real `+CDS` delivery report and correlate its message reference to the submitted segment.
8. Send ordinary phone -> StegVerse and prove direct `+CMT` ingestion plus restart-safe duplicate suppression.
9. Add modem-reference-to-envelope/segment reconciliation if live reports expose device/vendor variance not covered by current parser.
10. Only after live bidirectional proof mark ST-029 activated.

## Archive posture

DO NOT archive as complete. The unblocked repository software slice now includes multipart/PDU and delivery-report evidence, but observed CI, physical modem/SIM binding, live registration, recipient reconstruction, real delivery reports, inbound proof, and production activation remain open.

## Percentages

```text
ST-029 current software slice: 100% implemented
ST-029 targeted validation: 0% observed until a workflow result is surfaced
ST-029 hardware/runtime integration: 55% (governed text + PDU paths, evidence/recovery, and report ingestion implemented; physical device not bound)
ST-029 live bidirectional proof: 0%
ST-029 goal activation: 74%
Developed active ST-029 artifacts vs placeholders: 17 developed / 0 placeholder artifacts; remaining activation work is primarily observed validation + physical modem/SIM/network proof
```
