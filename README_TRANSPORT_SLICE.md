# StegTalk Transport Integration Slice

This branch implements the first governed best-available-transport layer for StegTalk.

## Implemented

- deterministic bearer selection;
- hard locality, relay, receipt, metadata, energy, and reliability constraints;
- normalized observation freshness and permission checks;
- payload-free decision receipts;
- bounded failover planning;
- custody and attempt state transitions;
- payload-free attempt receipts;
- density classification;
- duplicate-message suppression;
- relay-copy and hop budgets;
- expiry enforcement;
- congestion-sensitive scan intervals;
- battery-floor deferral;
- deterministic relay-peer selection.

## Authority boundary

This layer does not grant network priority, responder authority, execution authority, identity authority, consent, or permission to relay. It only evaluates already-declared constraints and observed device/network state.

## Deferred

- physical BLE, Wi-Fi Direct, LAN, cellular, satellite, optical, acoustic, and mesh adapters;
- platform permission adapters;
- live custody transfer between devices;
- cryptographic peer attestation;
- field and density testing on real hardware.
