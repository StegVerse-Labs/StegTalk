from stegtalk.transport import BearerObservation, TransportRequest, select_transport


def bearer(bearer_id: str, kind: str, **overrides):
    values = {
        "bearer_id": bearer_id,
        "kind": kind,
        "available": True,
        "latency_ms": 100,
        "bandwidth_kbps": 1024,
        "reliability": 4,
        "privacy": 4,
        "metadata_exposure": 1,
        "energy_cost": 2,
        "congestion": 1,
        "supports_receipts": True,
        "uses_relay": False,
        "local_path": True,
    }
    values.update(overrides)
    return BearerObservation(**values)


def test_auto_selects_highest_scoring_admissible_bearer():
    decision = select_transport(
        TransportRequest(message_id="m-1"),
        [
            bearer("ble-1", "ble", bandwidth_kbps=128, latency_ms=300),
            bearer("wifi-1", "wifi_peer", bandwidth_kbps=4096, latency_ms=40),
        ],
    )
    assert decision.result == "SELECT"
    assert decision.selected_bearer_id == "wifi-1"


def test_local_only_rejects_internet_even_when_faster():
    decision = select_transport(
        TransportRequest(message_id="m-2", local_only=True),
        [
            bearer("internet-1", "internet", local_path=False, latency_ms=10),
            bearer("ble-1", "ble", latency_ms=250),
        ],
    )
    assert decision.selected_bearer_id == "ble-1"
    assert ("internet-1", "local_only_constraint") in decision.rejected


def test_no_relays_cannot_be_broadened_by_selector():
    decision = select_transport(
        TransportRequest(message_id="m-3", allow_relays=False),
        [bearer("relay-1", "nearby_relay", uses_relay=True)],
    )
    assert decision.result == "DENY"
    assert decision.selected_bearer_id is None
    assert decision.rejected == (("relay-1", "relay_not_permitted"),)


def test_receipt_requirement_fails_closed():
    decision = select_transport(
        TransportRequest(message_id="m-4", require_receipt=True),
        [bearer("acoustic-1", "acoustic", supports_receipts=False)],
    )
    assert decision.result == "DENY"
    assert decision.reasons == ("no_admissible_bearer",)


def test_emergency_resilient_does_not_override_metadata_limit():
    decision = select_transport(
        TransportRequest(
            message_id="m-5",
            preference="emergency_resilient",
            urgency=5,
            max_metadata_exposure=1,
        ),
        [
            bearer(
                "satellite-1",
                "satellite_gateway",
                local_path=False,
                metadata_exposure=4,
                reliability=5,
            ),
            bearer("store-1", "store_and_forward", uses_relay=True, reliability=4),
        ],
    )
    assert decision.selected_bearer_id == "store-1"
    assert ("satellite-1", "metadata_exposure_limit") in decision.rejected


def test_ties_are_deterministic():
    request = TransportRequest(message_id="m-6")
    first = bearer("b", "ble")
    second = bearer("a", "ble")
    assert select_transport(request, [first, second]).selected_bearer_id == "a"
    assert select_transport(request, [second, first]).selected_bearer_id == "a"
