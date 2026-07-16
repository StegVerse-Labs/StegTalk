from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Iterable

from .adapters import AdapterEventType, AdapterKind, DiscoveryEvent, PermissionState
from .selector import BearerObservation, TransportDecision, TransportRequest, select_transport


@dataclass(frozen=True)
class ProvenancedObservation:
    observation: BearerObservation
    peer_reference_hash: str
    adapter_kinds: tuple[AdapterKind, ...]
    source_event_hashes: tuple[str, ...]


@dataclass(frozen=True)
class DiscoverySelectionResult:
    observations: tuple[ProvenancedObservation, ...]
    decision: TransportDecision
    invalidated_bearer_ids: tuple[str, ...]
    reasons: tuple[str, ...]


def _event_hash(event: DiscoveryEvent) -> str:
    payload = "|".join(
        [
            event.adapter_kind.value,
            event.event_type.value,
            event.observed_at.isoformat(),
            event.peer_reference_hash or "",
            str(event.proximity),
            str(event.reliability),
            str(event.energy_cost),
            str(event.capability_verified),
            event.permission_state.value,
            event.reason,
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def _privacy_for(kind: AdapterKind) -> int:
    return 5 if kind is AdapterKind.BLE else 4


def _metadata_exposure_for(kind: AdapterKind) -> int:
    return 1 if kind is AdapterKind.BLE else 2


def _latency_for(kind: AdapterKind, proximity: int) -> int:
    base = 180 if kind is AdapterKind.BLE else 90
    return max(10, base - proximity * 20)


def _bandwidth_for(kind: AdapterKind) -> int:
    return 256 if kind is AdapterKind.BLE else 2048


def bridge_discovery_events(events: Iterable[DiscoveryEvent]) -> tuple[ProvenancedObservation, ...]:
    grouped: dict[str, list[DiscoveryEvent]] = {}
    revoked_adapters = {
        event.adapter_kind
        for event in events
        if event.event_type in {AdapterEventType.PERMISSION_REVOKED, AdapterEventType.PERMISSION_DENIED, AdapterEventType.ADAPTER_FAILED}
    }

    for event in events:
        if event.adapter_kind in revoked_adapters:
            continue
        if event.event_type is not AdapterEventType.PEER_OBSERVED:
            continue
        if event.permission_state is not PermissionState.GRANTED:
            continue
        if not event.capability_verified or not event.peer_reference_hash:
            continue
        grouped.setdefault(event.peer_reference_hash, []).append(event)

    bridged: list[ProvenancedObservation] = []
    for peer_hash, peer_events in grouped.items():
        selected = sorted(
            peer_events,
            key=lambda item: (
                -(item.reliability or 0),
                item.energy_cost or 5,
                item.adapter_kind.value,
            ),
        )[0]
        kinds = tuple(sorted({event.adapter_kind for event in peer_events}, key=lambda item: item.value))
        event_hashes = tuple(sorted(_event_hash(event) for event in peer_events))
        kind = "ble" if selected.adapter_kind is AdapterKind.BLE else "wifi_peer"
        bearer_id = f"{kind}:{peer_hash[:16]}"
        observation = BearerObservation(
            bearer_id=bearer_id,
            kind=kind,
            available=True,
            latency_ms=_latency_for(selected.adapter_kind, selected.proximity or 0),
            bandwidth_kbps=_bandwidth_for(selected.adapter_kind),
            reliability=selected.reliability or 0,
            privacy=_privacy_for(selected.adapter_kind),
            metadata_exposure=_metadata_exposure_for(selected.adapter_kind),
            energy_cost=selected.energy_cost or 0,
            congestion=0,
            supports_receipts=True,
            uses_relay=False,
            local_path=True,
            reasons=("discovery_event_bridge",),
        )
        bridged.append(ProvenancedObservation(observation, peer_hash, kinds, event_hashes))

    return tuple(sorted(bridged, key=lambda item: item.observation.bearer_id))


def select_from_discovery(
    request: TransportRequest,
    events: Iterable[DiscoveryEvent],
    *,
    previous_observations: Iterable[ProvenancedObservation] = (),
) -> DiscoverySelectionResult:
    events = tuple(events)
    invalidating_kinds = {
        event.adapter_kind
        for event in events
        if event.event_type in {AdapterEventType.PERMISSION_REVOKED, AdapterEventType.PERMISSION_DENIED, AdapterEventType.ADAPTER_FAILED}
    }
    invalidated = tuple(
        sorted(
            item.observation.bearer_id
            for item in previous_observations
            if any(kind in invalidating_kinds for kind in item.adapter_kinds)
        )
    )
    observations = bridge_discovery_events(events)
    decision = select_transport(request, [item.observation for item in observations])
    reasons = ["discovery_events_bridged"]
    if invalidated:
        reasons.append("prior_observations_invalidated")
    if decision.result == "SELECT" and invalidated:
        reasons.append("alternate_bearer_selected")
    if decision.result != "SELECT":
        reasons.append("no_admissible_discovery_bearer")
    return DiscoverySelectionResult(observations, decision, invalidated, tuple(reasons))
