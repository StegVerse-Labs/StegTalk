from datetime import datetime, timezone

import pytest

from stegtalk.transport.adapters import AdapterKind
from stegtalk.transport.platform_integration import PlatformAdapterState, PlatformPermission, PlatformStatus
from stegtalk.transport.platform_runtime import (
    AppLifecycle,
    CapabilityManifest,
    PermissionRequestState,
    PlatformRuntimeState,
    begin_restoration,
    complete_restoration,
    request_permission,
    resolve_permission,
    runtime_admissible,
    suspend,
)

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def status(permission=PlatformPermission.NOT_DETERMINED, state=PlatformAdapterState.UNAVAILABLE):
    return PlatformStatus(AdapterKind.BLE, permission, state, NOW, "device-hash", "test")


class Broker:
    requested = None
    def request(self, *, adapter_kind):
        self.requested = adapter_kind


def manifest(**overrides):
    values = dict(
        adapter_kind=AdapterKind.BLE,
        permission_api_available=True,
        background_restoration_supported=True,
        secure_key_store_available=True,
        atomic_storage_available=True,
    )
    values.update(overrides)
    return CapabilityManifest(**values)


def test_permission_request_is_not_a_grant():
    broker = Broker()
    initial = PlatformRuntimeState(status())
    requested = request_permission(initial, broker)
    assert requested.permission_request_state is PermissionRequestState.REQUESTED
    assert requested.status.permission is PlatformPermission.NOT_DETERMINED
    assert broker.requested is AdapterKind.BLE
    assert not runtime_admissible(requested, manifest())


def test_denied_permission_stays_inadmissible():
    requested = request_permission(PlatformRuntimeState(status()), Broker())
    denied = resolve_permission(requested, permission=PlatformPermission.DENIED, now=NOW)
    assert denied.status.state is PlatformAdapterState.UNAVAILABLE
    assert not runtime_admissible(denied, manifest())


def test_suspend_and_restore_preserve_device_binding():
    ready = PlatformRuntimeState(status(PlatformPermission.GRANTED, PlatformAdapterState.READY))
    restoring = begin_restoration(suspend(ready), restoration_token_hash="restore-hash")
    restored = complete_restoration(restoring, status=status(PlatformPermission.GRANTED, PlatformAdapterState.READY))
    assert restored.lifecycle is AppLifecycle.FOREGROUND
    assert runtime_admissible(restored, manifest())


def test_restoration_rejects_binding_change():
    ready = PlatformRuntimeState(status(PlatformPermission.GRANTED, PlatformAdapterState.READY))
    restoring = begin_restoration(suspend(ready), restoration_token_hash="restore-hash")
    changed = PlatformStatus(AdapterKind.BLE, PlatformPermission.GRANTED, PlatformAdapterState.READY, NOW, "other-device", "restored")
    with pytest.raises(ValueError, match="device binding"):
        complete_restoration(restoring, status=changed)


def test_missing_secure_or_atomic_capability_fails_closed():
    ready = PlatformRuntimeState(status(PlatformPermission.GRANTED, PlatformAdapterState.READY))
    assert not runtime_admissible(ready, manifest(secure_key_store_available=False))
    assert not runtime_admissible(ready, manifest(atomic_storage_available=False))
