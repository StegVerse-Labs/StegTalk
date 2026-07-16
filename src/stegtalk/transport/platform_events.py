from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .adapters import AdapterEventType, AdapterKind, DiscoveryEvent, PermissionState
from .platform_integration import PlatformAdapterState, PlatformPermission, PlatformStatus, normalize_permission, validate_platform_status


class NativeCallbackType(StrEnum):
    STATE_CHANGED = "state_changed"
    PERMISSION_CHANGED = "permission_changed"
    PEER_FOUND = "peer_found"
    SCAN_COMPLETED = "scan_completed"
    ERROR = "error"


@dataclass(frozen=True)
class NativeCallback:
    callback_type: NativeCallbackType
    adapter_kind: AdapterKind
    observed_at: datetime
    permission: PlatformPermission
    adapter_state: PlatformAdapterState
    device_binding_hash: str
    reason: str


def normalize_callback(callback: NativeCallback) -> PlatformStatus:
    status = PlatformStatus(
        adapter_kind=callback.adapter_kind,
        permission=callback.permission,
        state=callback.adapter_state,
        observed_at=callback.observed_at,
        device_binding_hash=callback.device_binding_hash,
        reason=callback.reason,
    )
    validate_platform_status(status)
    return status


def permission_transition_event(previous: PlatformStatus, current: PlatformStatus) -> DiscoveryEvent | None:
    if previous.adapter_kind != current.adapter_kind or previous.device_binding_hash != current.device_binding_hash:
        raise ValueError("platform status continuity mismatch")
    previous_permission = normalize_permission(previous.permission)
    current_permission = normalize_permission(current.permission)
    if previous_permission is current_permission:
        return None
    if current_permission is PermissionState.REVOKED:
        event_type = AdapterEventType.PERMISSION_REVOKED
        reason = "native_permission_revoked"
    elif current_permission is PermissionState.DENIED:
        event_type = AdapterEventType.PERMISSION_DENIED
        reason = "native_permission_denied"
    else:
        return None
    return DiscoveryEvent(
        adapter_kind=current.adapter_kind,
        event_type=event_type,
        observed_at=current.observed_at,
        peer_reference_hash=None,
        proximity=None,
        reliability=None,
        energy_cost=None,
        capability_verified=False,
        permission_state=current_permission,
        reason=reason,
    )
