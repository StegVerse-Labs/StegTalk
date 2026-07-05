# Device Continuity Layer Handoff Contract

## Purpose

This contract defines how StegTalk receives Device Continuity Layer handoff records.

A Device Continuity Layer recommendation is not StegTalk execution authority. It is only a governed adapter candidate that StegTalk may accept, deny, or place under review.

## Accepted Classes

Initial classes:

- `headset`
- `push_to_talk`
- `local_alert`
- `button`
- `unknown_ble_peripheral` only as observe/manual-review

## Required Handoff Fields

A handoff candidate should provide:

- `adapter_id`
- `version`
- `status`
- `capability_classes`
- `transports`
- `destination_surfaces` containing `stegtalk`
- `required_evidence`
- `control_policy`
- receipt reference

## Boundary Rules

- Destination-side behavior remains inactive until StegTalk creates its own acceptance receipt.
- Push-to-talk controls may be read-only candidates before destination activation.
- Local alert devices may not trigger user-impacting behavior without StegTalk-side authorization.
- Unknown devices remain observe-only or manual-review.

## Destination Response

StegTalk should respond with one of:

- `accepted_observe_only`
- `accepted_read_control`
- `manual_review_required`
- `denied`

The response should become a new governance receipt in this repo or its designated receipt store.
