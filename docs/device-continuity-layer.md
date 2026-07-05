# Device Continuity Layer Handoff

Source: `StegVerse-Labs/device-continuity-layer`
Destination: `StegVerse-Labs/StegTalk`
Candidate tag: `v0.1.0-offline-baseline`
Status: installed as non-authorizing integration payload

## Purpose

This document records how StegTalk consumes Device Continuity Layer handoff receipts for communication-device candidates.

A Device Continuity Layer recommendation is not StegTalk execution authority. It is a governed adapter candidate that StegTalk may accept, deny, or place under manual review.

## Accepted Initial Device Classes

- `microphone`
- `headset`
- `push_to_talk`
- `local_alert`
- `button`
- `unknown_ble_peripheral` only as observe/manual-review

## Required StegTalk Response

StegTalk should respond to a handoff with one of:

- `accepted_observe_only`
- `accepted_read_control`
- `manual_review_required`
- `denied`

## Activation Boundary

Device Continuity Layer output cannot activate audio capture, message sending, user notification, contact selection, transmission, or persistent device trust. StegTalk must issue its own acceptance receipt before any destination behavior is enabled.

## Installed Files

- `contracts/device-continuity-handoff.contract.md`
- `fixtures/device-continuity/stegtalk-device-continuity-handoff.json`
- `fixtures/device-continuity/fixture-ble-button-stegtalk-001.receipt.json`
