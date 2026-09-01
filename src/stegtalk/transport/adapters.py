from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from hashlib import sha256
from typing import Iterable, Protocol


class AdapterKind(StrEnum):
    BLE = "ble"
    WIFI_PEER = "wifi_peer"
    NO_RADIO = "no_radio"


class PermissionState(StrEnum):
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class AdapterEventType(StrEnum):
    PEER_OBSERVED = "peer_observed"
    SCAN_EMPTY = "scan_empty"
    PERMISSION_DENIED = "permission_denied"
    PERMISSION_REVOKED = "permission_revoked"
    ADAPTER_FAILED = "adapter_failed"


@dataclass(frozen=True)
class RawPeerSignal:
    peer_reference: str
    observed_at: datetime
    proximity: int
    reliability: int
    energy_cost: int
    capability_verified: bool


@dataclass(frozen=True)
class DiscoveryEvent:
    adapter_kind: AdapterKind
    event_type: AdapterEventType
    observed_at: datetime
    peer_reference_hash: str | None
    proximity: int | None
    reliability: int | None
    energy_cost: int | None
    capability_verified: bool
    permission_state: PermissionState
    reason: str


class DiscoveryAdapter(Protocol):
    kind: AdapterKind

    def scan(self, *, now: datetime) -> tuple[DiscoveryEvent, ...]: ...


def _peer_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _validate_now(now: datetime) -> None:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")


@dataclass
class SimulatedDiscoveryAdapter:
    kind: AdapterKind
    permission_state: PermissionState = PermissionState.GRANTED
    signals: tuple[RawPeerSignal, ...] = ()
    failure_reason: str | None = None
    max_signal_age_seconds: int = 30

    def scan(self, *, now: datetime) -> tuple[DiscoveryEvent, ...]:
        _validate_now(now)
        if self.permission_state is PermissionState.DENIED:
            return (self._permission_event(now, AdapterEventType.PERMISSION_DENIED, "permission_denied"),)
        if self.permission_state is PermissionState.REVOKED:
            return (self._permission_event(now, AdapterEventType.PERMISSION_REVOKED, "permission_revoked"),)
        if self.failure_reason:
            return (DiscoveryEvent(self.kind, AdapterEventType.ADAPTER_FAILED, now, None, None, None, None, False, self.permission_state, self.failure_reason),)

        events: list[DiscoveryEvent] = []
        for signal in self.signals:
            age = (now - signal.observed_at).total_seconds()
            if age < 0 or age > self.max_signal_age_seconds:
                continue
            if not all(0 <= value <= 5 for value in (signal.proximity, signal.reliability, signal.energy_cost)):
                continue
            events.append(DiscoveryEvent(
                adapter_kind=self.kind,
                event_type=AdapterEventType.PEER_OBSERVED,
                observed_at=signal.observed_at,
                peer_reference_hash=_peer_hash(signal.peer_reference),
                proximity=signal.proximity,
                reliability=signal.reliability,
                energy_cost=signal.energy_cost,
                capability_verified=signal.capability_verified,
                permission_state=self.permission_state,
                reason="peer_observed",
            ))
        if not events:
            events.append(DiscoveryEvent(self.kind, AdapterEventType.SCAN_EMPTY, now, None, None, None, None, False, self.permission_state, "no_fresh_peers"))
        return tuple(events)

    def _permission_event(self, now: datetime, event_type: AdapterEventType, reason: str) -> DiscoveryEvent:
        return DiscoveryEvent(self.kind, event_type, now, None, None, None, None, False, self.permission_state, reason)


class BleDiscoveryAdapter(SimulatedDiscoveryAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(kind=AdapterKind.BLE, **kwargs)


class WifiPeerDiscoveryAdapter(SimulatedDiscoveryAdapter):
    def __init__(self, **kwargs: object) -> None:
        super().__init__(kind=AdapterKind.WIFI_PEER, **kwargs)


class NoRadioDiscoveryAdapter(SimulatedDiscoveryAdapter):
    def __init__(self) -> None:
        super().__init__(kind=AdapterKind.NO_RADIO, signals=())


def collect_discovery_events(adapters: Iterable[DiscoveryAdapter], *, now: datetime) -> tuple[DiscoveryEvent, ...]:
    _validate_now(now)
    events: list[DiscoveryEvent] = []
    for adapter in adapters:
        events.extend(adapter.scan(now=now))
    return tuple(sorted(events, key=lambda item: (item.observed_at, item.adapter_kind, item.event_type, item.peer_reference_hash or "")))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
