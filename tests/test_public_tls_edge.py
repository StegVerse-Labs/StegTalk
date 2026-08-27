from __future__ import annotations

import ssl

import pytest

from stegtalk.cross_edge_resolver import Lease
from stegtalk.edge_runtime import EdgeExecutionRequest, execute_selected_edge, next_runtime_action
from stegtalk.public_tls_edge import (
    PublicTlsEdgeError,
    TlsEndpoint,
    _verified_context,
    tls_edge_executor,
)


SELECTION = {
    "attempt_id": "attempt:st034:1",
    "selection_sha256": "b" * 64,
    "selected_edge_id": "edge:public-tls",
    "selected_bearer": "stegtalk-tls",
    "fallback_order": [{"edge_id": "edge:sms", "bearer": "sms", "score": 1.0}],
}
LEASE = Lease(
    attempt_id="attempt:st034:1",
    edge_id="edge:public-tls",
    lease_epoch=1,
    expires_at="2099-01-01T00:00:00Z",
)
REQUEST = EdgeExecutionRequest(
    attempt_id="attempt:st034:1",
    selection_sha256="b" * 64,
    edge_id="edge:public-tls",
    bearer="stegtalk-tls",
    payload_ref="kv://payload/st034/1",
    idempotency_key="idem:st034:1",
    lease_epoch=1,
)


def test_verified_context_requires_certificate_and_hostname_verification():
    endpoint = TlsEndpoint("edge.example.test", 443, "edge.example.test")
    context = _verified_context(endpoint)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.minimum_version >= ssl.TLSVersion.TLSv1_2


def test_tls_endpoint_requires_server_name():
    with pytest.raises(PublicTlsEdgeError, match="server_name"):
        TlsEndpoint("edge.example.test", 443, "").validate()


def test_wrong_bearer_fails_closed_before_network_use():
    executor = tls_edge_executor(
        endpoint=TlsEndpoint("edge.example.test", 443, "edge.example.test"),
        payload_loader=lambda ref: b"payload",
    )
    bad = EdgeExecutionRequest(
        attempt_id=REQUEST.attempt_id,
        selection_sha256=REQUEST.selection_sha256,
        edge_id=REQUEST.edge_id,
        bearer="stegtalk-tcp",
        payload_ref=REQUEST.payload_ref,
        idempotency_key="idem:st034:bad",
        lease_epoch=REQUEST.lease_epoch,
    )
    with pytest.raises(PublicTlsEdgeError, match="unexpected bearer"):
        execute_selected_edge(
            selection_receipt={**SELECTION, "selected_bearer": "stegtalk-tcp"},
            lease=LEASE,
            request=bad,
            executors={REQUEST.edge_id: executor},
        )


def test_tls_handshake_failure_is_confirmed_pre_dispatch_failure(monkeypatch):
    class RawSocket:
        def settimeout(self, value):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    class Context:
        verify_mode = ssl.CERT_REQUIRED
        check_hostname = True
        minimum_version = ssl.TLSVersion.TLSv1_2
        def wrap_socket(self, sock, *, server_hostname):
            assert server_hostname == "edge.example.test"
            raise ssl.SSLError("certificate verify failed")

    monkeypatch.setattr("stegtalk.public_tls_edge._verified_context", lambda endpoint: Context())
    monkeypatch.setattr("stegtalk.public_tls_edge.socket.create_connection", lambda *args, **kwargs: RawSocket())

    executor = tls_edge_executor(
        endpoint=TlsEndpoint("edge.example.test", 443, "edge.example.test"),
        payload_loader=lambda ref: b"payload",
    )
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=LEASE,
        request=REQUEST,
        executors={REQUEST.edge_id: executor},
    )
    assert receipt.dispatch_state == "NOT_DISPATCHED"
    assert receipt.outcome == "FAILED"
    assert receipt.side_effect_absence_confirmed is True
    assert next_runtime_action(selection_receipt=SELECTION, receipt=receipt)["action"] == "TRY_FALLBACK"


def test_failure_after_tls_frame_send_is_indeterminate(monkeypatch):
    class TlsSocket:
        def sendall(self, value):
            pass
        def recv(self, length):
            raise OSError("peer disappeared after send")
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    class RawSocket:
        def settimeout(self, value):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    class Context:
        verify_mode = ssl.CERT_REQUIRED
        check_hostname = True
        minimum_version = ssl.TLSVersion.TLSv1_2
        def wrap_socket(self, sock, *, server_hostname):
            return TlsSocket()

    monkeypatch.setattr("stegtalk.public_tls_edge._verified_context", lambda endpoint: Context())
    monkeypatch.setattr("stegtalk.public_tls_edge.socket.create_connection", lambda *args, **kwargs: RawSocket())

    executor = tls_edge_executor(
        endpoint=TlsEndpoint("edge.example.test", 443, "edge.example.test"),
        payload_loader=lambda ref: b"payload",
    )
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=LEASE,
        request=REQUEST,
        executors={REQUEST.edge_id: executor},
    )
    assert receipt.dispatch_state == "DISPATCHED"
    assert receipt.outcome == "INDETERMINATE"
    assert receipt.side_effect_absence_confirmed is False
    assert next_runtime_action(selection_receipt=SELECTION, receipt=receipt)["action"] == "VERIFY_EXTERNALLY"


def test_correlated_tls_ack_is_acknowledged_not_delivery(monkeypatch):
    import json
    import struct
    from stegtalk.entity_runtime import stable_hash

    class TlsSocket:
        def __init__(self):
            self.sent = b""
            self.response = b""
        def sendall(self, value):
            self.sent += value
            if len(self.sent) >= 4:
                length = struct.unpack("!I", self.sent[:4])[0]
                if len(self.sent) >= 4 + length:
                    message = json.loads(self.sent[4:4+length].decode("utf-8"))
                    ack = {
                        "protocol": "stegtalk.edge-tls-ack.v0.1",
                        "request_sha256": message["request_sha256"],
                        "idempotency_key": message["idempotency_key"],
                        "accepted": True,
                    }
                    body = json.dumps(ack, sort_keys=True, separators=(",", ":")).encode("utf-8")
                    self.response = struct.pack("!I", len(body)) + body
        def recv(self, length):
            chunk, self.response = self.response[:length], self.response[length:]
            return chunk
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    class RawSocket:
        def settimeout(self, value):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    class Context:
        verify_mode = ssl.CERT_REQUIRED
        check_hostname = True
        minimum_version = ssl.TLSVersion.TLSv1_2
        def wrap_socket(self, sock, *, server_hostname):
            return TlsSocket()

    monkeypatch.setattr("stegtalk.public_tls_edge._verified_context", lambda endpoint: Context())
    monkeypatch.setattr("stegtalk.public_tls_edge.socket.create_connection", lambda *args, **kwargs: RawSocket())

    executor = tls_edge_executor(
        endpoint=TlsEndpoint("edge.example.test", 443, "edge.example.test"),
        payload_loader=lambda ref: b"payload",
    )
    receipt = execute_selected_edge(
        selection_receipt=SELECTION,
        lease=LEASE,
        request=REQUEST,
        executors={REQUEST.edge_id: executor},
    )
    assert receipt.dispatch_state == "OBSERVED"
    assert receipt.outcome == "ACKNOWLEDGED"
    assert receipt.side_effect_absence_confirmed is False
    assert next_runtime_action(selection_receipt=SELECTION, receipt=receipt)["action"] == "STOP"
