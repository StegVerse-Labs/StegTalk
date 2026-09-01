from datetime import datetime, timezone

import pytest

from stegtalk.transport.adapters import AdapterEventType, AdapterKind, PermissionState
from stegtalk.transport.platform_events import NativeCallback, NativeCallbackType, normalize_callback, permission_transition_event
from stegtalk.transport.platform_integration import PlatformAdapterState, PlatformPermission, PlatformStatus

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def value(permission, state, binding="device-1"):
    return PlatformStatus(AdapterKind.BLE, permission, state, NOW, binding, "test")


def test_revocation_emits_invalidation_event():
    event = permission_transition_event(
        value(PlatformPermission.GRANTED, PlatformAdapterState.READY),
        value(PlatformPermission.REVOKED, PlatformAdapterState.UNAVAILABLE),
    )
    assert event is not None
    assert event.event_type is AdapterEventType.PERMISSION_REVOKED
    assert event.permission_state is PermissionState.REVOKED


def test_denial_emits_fail_closed_event():
    event = permission_transition_event(
        value(PlatformPermission.GRANTED, PlatformAdapterState.READY),
        value(PlatformPermission.DENIED, PlatformAdapterState.UNAVAILABLE),
    )
    assert event is not None
    assert event.event_type is AdapterEventType.PERMISSION_DENIED


def test_grant_transition_does_not_claim_peer_observation():
    event = permission_transition_event(
        value(PlatformPermission.NOT_DETERMINED, PlatformAdapterState.UNAVAILABLE),
        value(PlatformPermission.GRANTED, PlatformAdapterState.READY),
    )
    assert event is None


def test_binding_change_rejected():
    with pytest.raises(ValueError, match="continuity mismatch"):
        permission_transition_event(
            value(PlatformPermission.GRANTED, PlatformAdapterState.READY, "a"),
            value(PlatformPermission.REVOKED, PlatformAdapterState.UNAVAILABLE, "b"),
        )


def test_callback_normalization_requires_valid_ready_state():
    callback = NativeCallback(
        NativeCallbackType.STATE_CHANGED,
        AdapterKind.WIFI_PEER,
        NOW,
        PlatformPermission.DENIED,
        PlatformAdapterState.READY,
        "device-1",
        "invalid",
    )
    with pytest.raises(ValueError, match="granted permission"):
        normalize_callback(callback)
