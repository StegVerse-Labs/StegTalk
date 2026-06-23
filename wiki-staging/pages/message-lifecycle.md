# Message Lifecycle

## Purpose

The StegTalk message lifecycle describes how a local message moves from sender intent into an envelope, route decision, inbox item, and receipt-bearing local state.

## Lifecycle

1. Sender creates a local message intent.
2. Contact routing resolves a receiver from available contact records.
3. Message envelope is created with sender, receiver, body, scope, and hash material.
4. Local inbox receives the envelope as an inbox item.
5. Local store or shell state records the resulting item.
6. Receipts preserve the transition state for later inspection.

## StegTalk Ownership

StegTalk owns the product/runtime behavior of local message creation, routing, envelope handling, inbox projection, and local receipt state.

## Overlap

Admissibility may evaluate whether a message action has standing. StegGuardian may evaluate whether account, device, guardian, or recovery boundaries affect message authority.

## Boundary

The staged message lifecycle is a local prototype path. It is not production transport, production cryptography, or public network delivery.
