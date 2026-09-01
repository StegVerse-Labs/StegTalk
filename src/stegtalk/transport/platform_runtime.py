from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from .adapters import AdapterKind
from .platform_integration import PlatformAdapterState, PlatformPermission, PlatformStatus, adapter_admissible


class PermissionRequestState(StrEnum):
    NOT_REQUESTED = "not_requested"
    REQUESTED = "requested"
    RESOLVED = "resolved"


class AppLifecycle(StrEnum):
    FOREGROUND = "foreground"
    SUSPENDED = "suspended"
    RESTORING = "restoring"


@dataclass(frozen=True)
class PlatformRuntimeState:
    status: PlatformStatus
    permission_request_state: PermissionRequestState = PermissionRequestState.NOT_REQUESTED
    lifecycle: AppLifecycle = AppLifecycle.FOREGROUND
    restoration_token_hash: str | None = None


@dataclass(frozen=True)
class CapabilityManifest:
    adapter_kind: AdapterKind
    permission_api_available: bool
    background_restoration_supported: bool
    secure_key_store_available: bool
    atomic_storage_available: bool


class NativePermissionBroker(Protocol):
    def request(self, *, adapter_kind: AdapterKind) -> None: ...


class NativeAtomicStore(Protocol):
    def write_atomic(self, *, slot: str, payload: bytes) -> None: ...
    def read(self, *, slot: str) -> bytes | None: ...
    def synchronize(self) -> None: ...


class NativeKeyCustody(Protocol):
    def device_binding_hash(self) -> str: ...
    def active_key_id(self) -> str: ...
    def sign(self, *, key_id: str, payload: bytes) -> bytes: ...
    def verify(self, *, key_id: str, payload: bytes, signature: bytes) -> bool: ...


def request_permission(state: PlatformRuntimeState, broker: NativePermissionBroker) -> PlatformRuntimeState:
    if state.status.permission not in {PlatformPermission.UNKNOWN, PlatformPermission.NOT_DETERMINED}:
        raise ValueError("permission request is only valid before resolution")
    broker.request(adapter_kind=state.status.adapter_kind)
    return replace(state, permission_request_state=PermissionRequestState.REQUESTED)


def resolve_permission(state: PlatformRuntimeState, *, permission: PlatformPermission, now: datetime) -> PlatformRuntimeState:
    if state.permission_request_state is not PermissionRequestState.REQUESTED:
        raise ValueError("permission was not requested")
    if permission in {PlatformPermission.UNKNOWN, PlatformPermission.NOT_DETERMINED}:
        raise ValueError("permission result must be resolved")
    status = replace(
        state.status,
        permission=permission,
        observed_at=now,
        state=state.status.state if permission is PlatformPermission.GRANTED else PlatformAdapterState.UNAVAILABLE,
        reason="permission_resolved",
    )
    return replace(state, status=status, permission_request_state=PermissionRequestState.RESOLVED)


def suspend(state: PlatformRuntimeState) -> PlatformRuntimeState:
    return replace(state, lifecycle=AppLifecycle.SUSPENDED)


def begin_restoration(state: PlatformRuntimeState, *, restoration_token_hash: str) -> PlatformRuntimeState:
    if state.lifecycle is not AppLifecycle.SUSPENDED:
        raise ValueError("restoration requires suspended state")
    if not restoration_token_hash:
        raise ValueError("restoration token hash is required")
    return replace(state, lifecycle=AppLifecycle.RESTORING, restoration_token_hash=restoration_token_hash)


def complete_restoration(state: PlatformRuntimeState, *, status: PlatformStatus) -> PlatformRuntimeState:
    if state.lifecycle is not AppLifecycle.RESTORING:
        raise ValueError("restoration was not started")
    if status.device_binding_hash != state.status.device_binding_hash:
        raise ValueError("device binding changed during restoration")
    return replace(state, lifecycle=AppLifecycle.FOREGROUND, status=status)


def runtime_admissible(state: PlatformRuntimeState, manifest: CapabilityManifest) -> bool:
    return (
        state.lifecycle is AppLifecycle.FOREGROUND
        and manifest.adapter_kind is state.status.adapter_kind
        and manifest.permission_api_available
        and manifest.secure_key_store_available
        and manifest.atomic_storage_available
        and adapter_admissible(state.status)
    )
