from datetime import datetime, timezone

import pytest

from stegtalk.transport.adapters import AdapterKind, PermissionState
from stegtalk.transport.platform_integration import (
    PlatformAdapterState,
    PlatformPermission,
    PlatformStatus,
    adapter_admissible,
    normalize_permission,
    validate_platform_status,
)

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def status(permission=PlatformPermission.GRANTED, state=PlatformAdapterState.READY):
    return PlatformStatus(AdapterKind.BLE, permission, state, NOW, "device-binding", "test")


def test_ready_granted_adapter_is_admissible():
    assert adapter_admissible(status())


def test_degraded_granted_adapter_remains_admissible():
    assert adapter_admissible(status(state=PlatformAdapterState.DEGRADED))


def test_permission_states_fail_closed():
    for permission in (
        PlatformPermission.UNKNOWN,
        PlatformPermission.NOT_DETERMINED,
        PlatformPermission.DENIED,
        PlatformPermission.RESTRICTED,
        PlatformPermission.REVOKED,
    ):
        assert normalize_permission(permission) is not PermissionState.GRANTED


def test_ready_requires_granted_permission():
    with pytest.raises(ValueError, match="granted permission"):
        validate_platform_status(status(PlatformPermission.DENIED))


def test_device_binding_is_required():
    value = PlatformStatus(AdapterKind.WIFI_PEER, PlatformPermission.GRANTED, PlatformAdapterState.READY, NOW, "", "test")
    with pytest.raises(ValueError, match="device binding"):
        validate_platform_status(value)


def test_powered_off_adapter_is_not_admissible():
    assert not adapter_admissible(status(state=PlatformAdapterState.POWERED_OFF))
