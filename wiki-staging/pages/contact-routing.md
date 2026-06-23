# Contact Routing

## Purpose

Contact routing resolves a receiver hint into a local contact or entity target before a message envelope is created.

## Runtime Behavior

A contact routing action should identify:

- sender entity
- receiver hint
- message body
- contact index
- scope
- route decision
- envelope result when routed
- receipt result

## StegTalk Ownership

StegTalk owns the local routing behavior, contact index interpretation, route decision output, and message-envelope handoff.

## Overlap

StegGuardian may govern whether a sender, receiver, account, device, or guardian boundary affects routing authority. Admissibility may govern whether the requested route has current standing.

## Boundary

Contact routing readiness does not imply external messaging federation, production delivery, or guardian-approved communication.
