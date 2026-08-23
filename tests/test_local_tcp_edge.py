from __future__ import annotations

import base64
import hashlib
import socket
import threading

from stegtalk.cross_edge_resolver import Lease
from stegtalk.edge_runtime import EdgeExecutionRequest, execute_selected_edge, next_runtime_action
from stegtalk.local_tcp_edge import TcpEndpoint, receive_one_tcp_edge_message, tcp_edge_executor


SELECTION = {
    "attempt_id": "attempt:st033:1",
    "selection_sha256": "a" * 64,
    "selected_edge_id": "edge:tcp",
    "selected_bearer": "stegtalk-tcp",
    "fallback_order": [{"edge_id": "edge:sms", "bearer": "sms", "score": 1.0}],
}
LEASE = Lease(
    attempt_id="attempt:st033:1",
    edge_id="edge:tcp",
    lease_epoch=1,
    expires_at="2099-01-01T00:00:00Z",
)
REQUEST = EdgeExecutionRequest(
    attempt_id="attempt:st033:1",
    selection_sha256="a" * 64,
    edge_id="edge:tcp",
    bearer="stegtalk-tcp",
    payload_ref="kv://payload/st033/1",
    idempotency_key="idem:st033:1",
    lease_epoch=1,
)


def _listener():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    return server


def test_real_tcp_round_trip_through_st032():
    payload = b"StegTalk TCP edge\x00binary\xff"
    listener = _listener()
    port = listener.getsockname()[1]
    observed = {}

    def receive():
        observed.update(receive_one_tcp_edge_message(listener))
        listener.close()

    thread = threading.Thread(target=receive, daemon=True)
    thread.start()
    executor = tcp_edge_executor(
        endpoint=TcpEndpoint("127.0.0.1", port),
        payload_loader=lambda ref: payload,
    )
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=LEASE,
        request=REQUEST,
        executors={"edge:tcp": executor},
    )
    thread.join(timeout=3)

    assert not thread.is_alive()
    assert receipt.dispatch_state == "OBSERVED"
    assert receipt.outcome == "ACKNOWLEDGED"
    assert base64.b64decode(observed["payload_b64"]) == payload
    assert observed["payload_sha256"] == "sha256:" + hashlib.sha256(payload).hexdigest()
    assert observed["attempt_id"] == REQUEST.attempt_id
    assert observed["selection_sha256"] == REQUEST.selection_sha256
    assert observed["idempotency_key"] == REQUEST.idempotency_key
    assert next_runtime_action(selection_receipt=SELECTION, receipt=receipt)["action"] == "STOP"


def test_connection_failure_is_confirmed_pre_dispatch_failure_and_can_fallback():
    listener = _listener()
    port = listener.getsockname()[1]
    listener.close()
    executor = tcp_edge_executor(
        endpoint=TcpEndpoint("127.0.0.1", port, timeout_seconds=0.2),
        payload_loader=lambda ref: b"payload",
    )
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=LEASE,
        request=REQUEST,
        executors={"edge:tcp": executor},
    )
    assert receipt.dispatch_state == "NOT_DISPATCHED"
    assert receipt.outcome == "FAILED"
    assert receipt.side_effect_absence_confirmed is True
    action = next_runtime_action(selection_receipt=SELECTION, receipt=receipt)
    assert action["action"] == "TRY_FALLBACK"
    assert action["fallback"]["edge_id"] == "edge:sms"


def test_wrong_bearer_fails_closed_before_socket_use():
    executor = tcp_edge_executor(
        endpoint=TcpEndpoint("127.0.0.1", 9, timeout_seconds=0.2),
        payload_loader=lambda ref: b"payload",
    )
    bad = EdgeExecutionRequest(
        attempt_id=REQUEST.attempt_id,
        selection_sha256=REQUEST.selection_sha256,
        edge_id=REQUEST.edge_id,
        bearer="sms",
        payload_ref=REQUEST.payload_ref,
        idempotency_key="idem:bad",
        lease_epoch=REQUEST.lease_epoch,
    )
    try:
        execute_selected_edge(
            selection_receipt={**SELECTION, "selected_bearer": "sms"},
            lease=LEASE,
            request=bad,
            executors={"edge:tcp": executor},
        )
    except Exception as exc:
        assert "unexpected bearer" in str(exc)
    else:
        raise AssertionError("wrong bearer must fail closed")
