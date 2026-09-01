from datetime import datetime, timezone

from stegtalk.transport.adapters import AdapterEventType, AdapterKind, DiscoveryEvent, PermissionState
from stegtalk.transport.discovery_bridge import bridge_discovery_events, select_from_discovery
from stegtalk.transport.selector import TransportRequest

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def event(kind, peer, reliability, energy, *, capability=True, event_type=AdapterEventType.PEER_OBSERVED, permission=PermissionState.GRANTED):
    return DiscoveryEvent(
        adapter_kind=kind,
        event_type=event_type,
        observed_at=NOW,
        peer_reference_hash=peer,
        proximity=4 if peer else None,
        reliability=reliability if peer else None,
        energy_cost=energy if peer else None,
        capability_verified=capability,
        permission_state=permission,
        reason=event_type.value,
    )


def test_bridge_rejects_unverified_capability():
    assert bridge_discovery_events([event(AdapterKind.BLE, "peer-a", 5, 1, capability=False)]) == ()


def test_duplicate_peer_collapses_with_provenance():
    observations = bridge_discovery_events([
        event(AdapterKind.BLE, "peer-a", 4, 1),
        event(AdapterKind.WIFI_PEER, "peer-a", 5, 2),
    ])
    assert len(observations) == 1
    assert observations[0].observation.kind == "wifi_peer"
    assert observations[0].adapter_kinds == (AdapterKind.BLE, AdapterKind.WIFI_PEER)
    assert len(observations[0].source_event_hashes) == 2


def test_permission_revocation_invalidates_prior_observation_and_reselects():
    request = TransportRequest(message_id="msg-demo-001", preference="fastest_admissible")
    prior = bridge_discovery_events([
        event(AdapterKind.WIFI_PEER, "peer-a", 5, 1),
    ])
    result = select_from_discovery(
        request,
        [
            event(AdapterKind.WIFI_PEER, None, 0, 0, event_type=AdapterEventType.PERMISSION_REVOKED, permission=PermissionState.REVOKED),
            event(AdapterKind.BLE, "peer-b", 4, 1),
        ],
        previous_observations=prior,
    )
    assert result.invalidated_bearer_ids == (prior[0].observation.bearer_id,)
    assert result.decision.result == "SELECT"
    assert result.decision.selected_kind == "ble"
    assert "alternate_bearer_selected" in result.reasons


def test_adapter_failure_removes_all_observations_from_that_adapter():
    request = TransportRequest(message_id="msg-demo-001")
    result = select_from_discovery(
        request,
        [
            event(AdapterKind.BLE, "peer-a", 5, 1),
            event(AdapterKind.BLE, None, 0, 0, event_type=AdapterEventType.ADAPTER_FAILED),
        ],
    )
    assert result.observations == ()
    assert result.decision.result == "DENY"


def test_selection_is_deterministic_across_event_order():
    request = TransportRequest(message_id="msg-demo-001", preference="most_private")
    events = [
        event(AdapterKind.WIFI_PEER, "peer-b", 5, 1),
        event(AdapterKind.BLE, "peer-a", 5, 1),
    ]
    first = select_from_discovery(request, events)
    second = select_from_discovery(request, reversed(events))
    assert first.decision == second.decision
