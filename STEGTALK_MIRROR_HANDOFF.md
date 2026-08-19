# StegTalk Mirror Handoff

## Status

This file is the current handoff and task source of truth for `StegVerse-Labs/StegTalk`.

```text
Repository: StegVerse-Labs/StegTalk
Branch: main
Production ready: false
Active task: ST-028
Manual tasks required: provider account/number binding only when live activation is attempted
External tasks required: ClickSend account + two-way-capable number + inbound URL rule for live proof
```

## Active workstream — governed SMS bridge

### ST-028 — Governed ClickSend SMS Transport

```text
Originating goal: allow bidirectional communication between ordinary phone SMS and StegVerse/StegTalk
Provider: ClickSend
Claim state: OPEN
Source implementation: COMPLETE
Targeted validation: PENDING
Provider binding: NOT STARTED
Live outbound proof: NOT STARTED
Live inbound proof: NOT STARTED
Production activation: NOT ACTIVE
Credential authority: TV/TVC_ONLY
```

Installed files:

```text
src/stegtalk/sms_transport.py
tests/test_sms_transport.py
runtime/clicksend-sms-transport.v1.json
STEGTALK_TASK_QUEUE.json
```

Implementation commits:

```text
28365ae1166b56a85c9942ce9458c4ce0972437e
4022940586131cd343856818e4a12e3b94cb2078
b32826c97e87afb9eae5de670e9834ed65532064
47a7e287ff4c0c8f7efe33713468a4bad5d4b919
```

Implemented behavior:

- ClickSend outbound adapter for `POST https://rest.clicksend.com/v3/sms/send`;
- runtime-only ClickSend username/API-key injection; no credentials persisted in repository state;
- explicit `TV/TVC_ONLY` credential authority contract;
- fail-closed requirement for explicit admission of the external plaintext SMS boundary;
- strict E.164 phone-number requirement rather than guessed country routing;
- envelope-hash correlation through ClickSend `custom_string`;
- bounded outbound provider receipt including provider message ID and queue result;
- inbound ClickSend payload ingestion into a StegTalk `external_sms` envelope;
- preservation of `message_id`, `original_message_id`, `custom_string`, carrier endpoints, and provider timestamp;
- fail-closed inbound webhook-token verification with optional `user_id` and `custom_string` matching;
- inbound transport receipt with a deterministic correlation hash;
- explicit declaration that ordinary SMS does not inherit StegTalk secure-channel guarantees.

## Required continuation

Execute in this order and do not collapse any step into a later state:

1. Observe hosted CI for the new tests or reproduce the exact files in a deterministic local test environment and run `PYTHONPATH=. pytest -q tests/test_sms_transport.py`.
2. Repair any test failures and record validation evidence.
3. Bind ClickSend credentials through TV/TVC only. Do not add GitHub, repository, workflow, or application secrets outside TV/TVC authority.
4. Bind a ClickSend number capable of receiving replies in the intended country/route.
5. Deploy the StegVerse inbound HTTPS endpoint that performs the webhook-token boundary check before calling `ingest_clicksend_sms`.
6. Create the ClickSend inbound SMS automation with Action `URL`, preferably JSON webhook mode, targeting that endpoint.
7. Send one StegVerse -> phone SMS and record provider message ID, StegTalk envelope hash, and transport receipt.
8. Reply from the phone -> StegVerse and prove `original_message_id` / `custom_string` correlation into the expected StegTalk thread.
9. Only after both live directions and receipts are proven may ST-028 be marked activated.

## Security and authority boundary

```text
source implemented != validated
validated != provider bound
provider bound != deployed
outbound queued != handset delivered
inbound webhook received != authenticated identity
SMS transport != StegTalk secure channel
carrier plaintext exposure != encrypted StegTalk transport
ClickSend API log != StegVerse continuity receipt
TV/TVC credential authority != repository secret storage
```

The ClickSend carrier leg is ordinary SMS. StegVerse can govern admission to that leg, correlate it, retain receipts, and bind it to internal entities, but it must not represent the carrier segment as end-to-end encrypted or metadata-private.

## Previous completed workstream — personal-data control

ST-026 and ST-027 remain complete. The previously validated local personal-data lifecycle is unchanged:

```text
Task: ST-026
State: COMPLETE
Task manifest: runtime/personal-data-control.v1.json

Task: ST-027
State: COMPLETE
Implementation: src/stegtalk/personal_data_control.py, src/stegtalk/local_store.py
Validation: 3 targeted tests passed in reconstructed deterministic local execution
Evidence: evidence/personal-data-control/ST-027-local-validation.json
```

## Machine-owned continuation

```text
Owner: .github/workflows/ci.yml
Trigger: push, pull_request
Input: current repository state
Output: complete pytest result
Failure behavior: exact pytest failure; repository-local repair
```

Hosted CI may validate source behavior, but it does not own ClickSend credentials, provider binding, deployment authority, or activation.

## Archive posture

DO NOT archive this workstream as complete. ST-028 source exists, but validation, provider binding, deployment, bidirectional runtime proof, and activation remain open.

## Percentages

```text
ST-028 source implementation: 100%
ST-028 targeted validation: 0% observed
ST-028 provider/deployment integration: 0%
ST-028 bidirectional runtime proof: 0%
ST-028 goal activation: 35%
Developed files vs scaffolding/stubs: 4 developed / 0 placeholder stubs for the source slice; live-provider surfaces remain unactivated rather than stubbed
```
