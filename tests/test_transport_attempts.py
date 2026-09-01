from stegtalk.transport.attempts import (
    build_attempt_receipt,
    cancel_custody,
    create_custody,
    record_attempt_failure,
    record_attempt_success,
    start_next_attempt,
    transition_custody,
    verify_attempt_receipt,
)
from stegtalk.transport.failover import build_failover_plan
from stegtalk.transport.selector import BearerObservation, TransportRequest


def bearer(bearer_id: str, kind: str, reliability: int) -> BearerObservation:
    return BearerObservation(
        bearer_id=bearer_id,
        kind=kind,
        available=True,
        latency_ms=100,
        bandwidth_kbps=1024,
        reliability=reliability,
        privacy=4,
        metadata_exposure=1,
        energy_cost=2,
        local_path=True,
    )


def plan():
    return build_failover_plan(
        TransportRequest(message_id="m-1"),
        [bearer("wifi", "wifi_peer", 5), bearer("ble", "ble", 3)],
    )


def test_failure_advances_to_next_bearer():
    custody = create_custody("m-1")
    custody = start_next_attempt(custody, plan())
    assert custody.active_bearer_id == "wifi"
    custody = record_attempt_failure(custody, failure_code="link_timeout")
    custody = start_next_attempt(custody, plan())
    assert custody.active_bearer_id == "ble"
    assert custody.failed_bearer_ids == ("wifi",)


def test_success_preserves_attempt_and_delivery_claim():
    custody = start_next_attempt(create_custody("m-1"), plan())
    custody = record_attempt_success(custody, resulting_state="DELIVERED")
    assert custody.state == "DELIVERED"
    assert custody.attempts[-1].result == "SUCCEEDED"
    custody = transition_custody(custody, "ACKNOWLEDGED")
    assert custody.state == "ACKNOWLEDGED"


def test_exhausted_plan_fails_closed():
    custody = start_next_attempt(create_custody("m-1"), plan())
    custody = record_attempt_failure(custody, failure_code="timeout")
    custody = start_next_attempt(custody, plan())
    custody = record_attempt_failure(custody, failure_code="permission_revoked")
    custody = start_next_attempt(custody, plan())
    assert custody.state == "FAILED"


def test_cancel_marks_active_attempt_and_becomes_terminal():
    custody = start_next_attempt(create_custody("m-1"), plan())
    custody = cancel_custody(custody)
    assert custody.state == "CANCELED"
    assert custody.attempts[-1].result == "CANCELED"


def test_inadmissible_transition_rejected():
    custody = create_custody("m-1")
    try:
        transition_custody(custody, "DELIVERED")
    except ValueError as error:
        assert "inadmissible" in str(error)
    else:
        raise AssertionError("inadmissible transition accepted")


def test_attempt_receipt_is_hash_bound_and_non_authorizing():
    custody = start_next_attempt(create_custody("m-1"), plan())
    receipt = build_attempt_receipt(custody)
    assert verify_attempt_receipt(receipt, custody)
    receipt["authority"]["execution_authority_granted"] = True
    assert not verify_attempt_receipt(receipt, custody)
