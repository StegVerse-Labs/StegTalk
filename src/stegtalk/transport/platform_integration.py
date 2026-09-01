from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from .adapters import AdapterKind, DiscoveryEvent, PermissionState


class PlatformPermission(StrEnum):
    UNKNOWN = "unknown"
    NOT_DETERMINED = "not_determined"
    GRANTED = "granted"
    DENIED = "denied"
    RESTRICTED = "restricted"
    REVOKED = "revoked"


class PlatformAdapterState(StrEnum):
    UNAVAILABLE = "unavailable"
    POWERED_OFF = "powered_off"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass(frozen=True)
class PlatformStatus:
    adapter_kind: AdapterKind
    permission: PlatformPermission
    state: PlatformAdapterState
    observed_at: datetime
    device_binding_hash: str
    reason: str


class NativeTransportAdapter(Protocol):
    kind: AdapterKind

    def status(self, *, now: datetime) -> PlatformStatus: ...
    def scan(self, *, now: datetime) -> tuple[DiscoveryEvent, ...]: ...


class DeviceKeyStore(Protocol):
    def current_key_id(self) -> str: ...
    def sign(self, *, key_id: str, payload: bytes) -> bytes: ...
    def verify(self, *, key_id: str, payload: bytes, signature: bytes) -> bool: ...


def normalize_permission(permission: PlatformPermission) -> PermissionState:
    if permission is PlatformPermission.GRANTED:
        return PermissionState.GRANTED
    if permission is PlatformPermission.REVOKED:
        return PermissionState.REVOKED
    return PermissionState.DENIED


def validate_platform_status(status: PlatformStatus) -> None:
    if status.observed_at.tzinfo is None:
        raise ValueError("observed_at must be timezone-aware")
    if not status.device_binding_hash:
        raise ValueError("device binding is required")
    if status.state is PlatformAdapterState.READY and status.permission is not PlatformPermission.GRANTED:
        raise ValueError("ready adapter requires granted permission")


def adapter_admissible(status: PlatformStatus) -> bool:
    validate_platform_status(status)
    return status.permission is PlatformPermission.GRANTED and status.state in {
        PlatformAdapterState.READY,
        PlatformAdapterState.DEGRADED,
    }
