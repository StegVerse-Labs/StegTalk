from datetime import datetime, timedelta, timezone

import pytest

from stegtalk.cross_edge_resolver import Lease
from stegtalk.edge_runtime import (
    EdgeExecutionRequest,
    EdgeRuntimeError,
    execute_selected_edge,
    loopback_test_executor,
    next_runtime_action,
    receipt_as_record,
)


SELECTION = {
    "attempt_id": "attempt:st032:1",
    "selection_sha256": "a" * 64,
    "selected_edge_id": "edge:loopback",
    "selected_bearer": "LOOPBACK_TEST",
    "fallback_order": [{"edge_id": "edge:fallback", "bearer": "sms", "score": 1.0}],
}


def lease(epoch=1):
    return Lease(
        attempt_id="attempt:st032:1",
        edge_id="edge:loopback",
        lease_epoch=epoch,
        expires_at=(datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
    )


def request(epoch=1, key="idem:st032:1"):
    return EdgeExecutionRequest(
        attempt_id="attempt:st032:1",
        selection_sha256="a" * 64,
        edge_id="edge:loopback",
        bearer="LOOPBACK_TEST",
        payload_ref="kv://payload/st032/1",
        idempotency_key=key,
        lease_epoch=epoch,
    )


def test_loopback_dispatch_produces_hash_bound_execution_receipt():
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(),
        request=request(),
        executors={"edge:loopback": loopback_test_executor(outcome="DELIVERED")},
    )
    assert receipt.outcome == "DELIVERED"
    assert receipt.dispatch_state == "OBSERVED"
    assert receipt.edge_id == "edge:loopback"
    assert receipt.bearer == "LOOPBACK_TEST"
    assert receipt.receipt_sha256.startswith("sha256:")
    assert next_runtime_action(selection_receipt=SELECTION, receipt=receipt)["action"] == "STOP"
    assert receipt_as_record(receipt)["receipt_sha256"] == receipt.receipt_sha256


def test_idempotency_cache_returns_same_receipt_without_second_dispatch():
    calls = {"count": 0}

    def executor(req):
        calls["count"] += 1
        return {"dispatch_state": "OBSERVED", "outcome": "DELIVERED", "side_effect_absence_confirmed": False}

    cache = {}
    first = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(),
        request=request(),
        executors={"edge:loopback": executor},
        execution_cache=cache,
    )
    second = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(),
        request=request(),
        executors={"edge:loopback": executor},
        execution_cache=cache,
    )
    assert first == second
    assert calls["count"] == 1


def test_idempotency_key_cannot_be_rebound_to_new_lease_epoch():
    cache = {}
    execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(1),
        request=request(1),
        executors={"edge:loopback": loopback_test_executor()},
        execution_cache=cache,
    )
    with pytest.raises(EdgeRuntimeError, match="idempotency key reused"):
        execute_selected_edge(
            selection_receipt=SELECTION,
            lease=lease(2),
            request=request(2),
            executors={"edge:loopback": loopback_test_executor()},
            execution_cache=cache,
        )


def test_ambiguous_dispatch_requires_external_verification():
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(),
        request=request(),
        executors={"edge:loopback": loopback_test_executor(outcome="TIMEOUT_AFTER_DISPATCH")},
    )
    action = next_runtime_action(selection_receipt=SELECTION, receipt=receipt)
    assert action == {"action": "VERIFY_EXTERNALLY", "reason": "AMBIGUOUS_AFTER_DISPATCH"}


def test_confirmed_no_side_effect_failure_allows_exact_fallback():
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=lease(),
        request=request(),
        executors={"edge:loopback": loopback_test_executor(outcome="FAILED", side_effect_absence_confirmed=True)},
    )
    action = next_runtime_action(selection_receipt=SELECTION, receipt=receipt)
    assert action["action"] == "TRY_FALLBACK"
    assert action["fallback"]["edge_id"] == "edge:fallback"
    assert action["fallback"]["bearer"] == "sms"


def test_wrong_edge_or_bearer_is_rejected_before_executor_runs():
    bad = EdgeExecutionRequest(
        attempt_id="attempt:st032:1",
        selection_sha256="a" * 64,
        edge_id="edge:other",
        bearer="sms",
        payload_ref="kv://payload/st032/1",
        idempotency_key="idem:bad",
        lease_epoch=1,
    )
    with pytest.raises(EdgeRuntimeError):
        execute_selected_edge(
            selection_receipt=SELECTION,
            lease=lease(),
            request=bad,
            executors={"edge:other": loopback_test_executor()},
        )


def test_ambiguous_result_cannot_claim_side_effect_absence():
    with pytest.raises(EdgeRuntimeError, match="ambiguous dispatch"):
        execute_selected_edge(
            selection_receipt=SELECTION,
            lease=lease(),
            request=request(),
            executors={
                "edge:loopback": loopback_test_executor(
                    outcome="INDETERMINATE",
                    side_effect_absence_confirmed=True,
                )
            },
        )
