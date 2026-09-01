from datetime import datetime, timedelta, timezone

from stegtalk.transport.adapter_receipts import build_adapter_receipt, verify_adapter_receipt
from stegtalk.transport.adapters import (
    AdapterEventType,
    BleDiscoveryAdapter,
    NoRadioDiscoveryAdapter,
    PermissionState,
    RawPeerSignal,
    WifiPeerDiscoveryAdapter,
    collect_discovery_events,
)

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def signal(name: str, *, age: int = 0, verified: bool = True) -> RawPeerSignal:
    return RawPeerSignal(name, NOW - timedelta(seconds=age), 4, 5, 1, verified)


def test_ble_and_wifi_events_are_deterministic_and_peer_private() -> None:
    events = collect_discovery_events((
        WifiPeerDiscoveryAdapter(signals=(signal("wifi-peer"),)),
        BleDiscoveryAdapter(signals=(signal("ble-peer"),)),
    ), now=NOW)
    assert [event.adapter_kind.value for event in events] == ["ble", "wifi_peer"]
    assert all(event.peer_reference_hash not in {"ble-peer", "wifi-peer"} for event in events)
    assert all(event.event_type is AdapterEventType.PEER_OBSERVED for event in events)


def test_permission_revocation_stops_peer_observation() -> None:
    adapter = BleDiscoveryAdapter(permission_state=PermissionState.REVOKED, signals=(signal("peer"),))
    events = adapter.scan(now=NOW)
    assert len(events) == 1
    assert events[0].event_type is AdapterEventType.PERMISSION_REVOKED
    assert events[0].peer_reference_hash is None


def test_stale_and_future_signals_are_not_emitted() -> None:
    adapter = BleDiscoveryAdapter(signals=(signal("old", age=31), RawPeerSignal("future", NOW + timedelta(seconds=1), 4, 4, 1, True)))
    events = adapter.scan(now=NOW)
    assert len(events) == 1
    assert events[0].event_type is AdapterEventType.SCAN_EMPTY


def test_no_radio_adapter_is_deterministic() -> None:
    events = NoRadioDiscoveryAdapter().scan(now=NOW)
    assert events[0].event_type is AdapterEventType.SCAN_EMPTY
    assert events[0].reason == "no_fresh_peers"


def test_adapter_failure_is_explicit() -> None:
    events = WifiPeerDiscoveryAdapter(failure_reason="platform_adapter_failed").scan(now=NOW)
    assert events[0].event_type is AdapterEventType.ADAPTER_FAILED
    assert events[0].reason == "platform_adapter_failed"


def test_receipt_binds_event_stream_and_chain() -> None:
    events = BleDiscoveryAdapter(signals=(signal("peer"),)).scan(now=NOW)
    first = build_adapter_receipt(events)
    assert verify_adapter_receipt(first, events=events)
    second = build_adapter_receipt(events, previous_receipt_hash=first["receipt_hash"])
    assert verify_adapter_receipt(second, events=events, expected_previous_receipt_hash=first["receipt_hash"])
    assert not verify_adapter_receipt(second, events=(), expected_previous_receipt_hash=first["receipt_hash"])


def test_receipt_rejects_authority_escalation() -> None:
    events = NoRadioDiscoveryAdapter().scan(now=NOW)
    receipt = build_adapter_receipt(events)
    receipt["authority"]["execution_authority_granted"] = True
    assert not verify_adapter_receipt(receipt, events=events)
