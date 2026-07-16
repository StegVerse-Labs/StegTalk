from copy import deepcopy

from stegtalk.transport.receipts import (
    build_transport_decision_receipt,
    verify_transport_decision_receipt,
)
from stegtalk.transport.selector import (
    BearerObservation,
    TransportRequest,
    select_transport,
)


def _observation() -> BearerObservation:
    return BearerObservation(
        bearer_id="wifi-peer-1",
        kind="wifi_peer",
        available=True,
        latency_ms=40,
        bandwidth_kbps=4096,
        reliability=4,
        privacy=4,
        metadata_exposure=1,
        energy_cost=2,
        congestion=1,
        supports_receipts=True,
        uses_relay=False,
        local_path=True,
    )


def test_receipt_binds_request_observations_and_decision():
    request = TransportRequest(message_id="m-100", require_receipt=True)
    observations = [_observation()]
    decision = select_transport(request, observations)
    receipt = build_transport_decision_receipt(
        request=request,
        observations=observations,
        decision=decision,
    )
    assert verify_transport_decision_receipt(
        receipt,
        request=request,
        observations=observations,
        decision=decision,
    )


def test_receipt_rejects_observation_tampering():
    request = TransportRequest(message_id="m-101")
    observations = [_observation()]
    decision = select_transport(request, observations)
    receipt = build_transport_decision_receipt(
        request=request,
        observations=observations,
        decision=decision,
    )
    changed = [
        BearerObservation(
            **{**observations[0].__dict__, "metadata_exposure": 5}
        )
    ]
    assert not verify_transport_decision_receipt(
        receipt,
        request=request,
        observations=changed,
        decision=decision,
    )


def test_receipt_rejects_authority_escalation():
    request = TransportRequest(message_id="m-102")
    observations = [_observation()]
    decision = select_transport(request, observations)
    receipt = build_transport_decision_receipt(
        request=request,
        observations=observations,
        decision=decision,
    )
    tampered = deepcopy(receipt)
    tampered["authority"]["network_priority_granted"] = True
    assert not verify_transport_decision_receipt(
        tampered,
        request=request,
        observations=observations,
        decision=decision,
    )


def test_receipt_chain_predecessor_is_enforced():
    request = TransportRequest(message_id="m-103")
    observations = [_observation()]
    decision = select_transport(request, observations)
    receipt = build_transport_decision_receipt(
        request=request,
        observations=observations,
        decision=decision,
        previous_receipt_hash="prior-hash",
    )
    assert verify_transport_decision_receipt(
        receipt,
        request=request,
        observations=observations,
        decision=decision,
        expected_previous_receipt_hash="prior-hash",
    )
    assert not verify_transport_decision_receipt(
        receipt,
        request=request,
        observations=observations,
        decision=decision,
        expected_previous_receipt_hash="wrong-hash",
    )
