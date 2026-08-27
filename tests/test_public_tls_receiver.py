from __future__ import annotations

import json
import socket
import ssl
import struct

import pytest

from stegtalk.entity_runtime import stable_hash
from stegtalk.public_tls_receiver import PublicTlsReceiverError, receive_one_tls_edge_message


def _frame(value):
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return struct.pack("!I", len(body)) + body


def _request(**overrides):
    body = {
        "protocol": "stegtalk.edge-tls.v0.1",
        "attempt_id": "attempt:st035:1",
        "selection_sha256": "c" * 64,
        "edge_id": "edge:public-tls",
        "bearer": "stegtalk-tls",
        "idempotency_key": "idem:st035:1",
        "lease_epoch": 1,
        "payload_ref": "kv://payload/st035/1",
        "payload_sha256": "sha256:" + "d" * 64,
        "payload_b64": "cGF5bG9hZA==",
        "tls_server_name": "edge.example.test",
    }
    body.update(overrides)
    body["request_sha256"] = stable_hash(body)
    return body


class FakeTlsConnection:
    def __init__(self, request):
        self.incoming = _frame(request)
        self.sent = b""

    def recv(self, length):
        chunk, self.incoming = self.incoming[:length], self.incoming[length:]
        return chunk

    def sendall(self, value):
        self.sent += value

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeRawConnection:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeListener:
    def accept(self):
        return FakeRawConnection(), ("127.0.0.1", 12345)


class FakeServerContext(ssl.SSLContext):
    def __new__(cls, tls_conn):
        obj = super().__new__(cls, ssl.PROTOCOL_TLS_SERVER)
        obj._tls_conn = tls_conn
        return obj

    def wrap_socket(self, sock, *, server_side=False, **kwargs):
        assert server_side is True
        return self._tls_conn


def _decode_ack(sent):
    length = struct.unpack("!I", sent[:4])[0]
    return json.loads(sent[4:4+length].decode("utf-8"))


def test_receiver_requires_ssl_context():
    with pytest.raises(PublicTlsReceiverError, match="SSLContext"):
        receive_one_tls_edge_message(
            FakeListener(),
            server_context=object(),
            admission_check=lambda message: True,
        )


def test_admitted_exact_request_is_acknowledged():
    req = _request()
    tls = FakeTlsConnection(req)
    observed = receive_one_tls_edge_message(
        FakeListener(),
        server_context=FakeServerContext(tls),
        admission_check=lambda message: message["edge_id"] == "edge:public-tls",
    )
    assert observed["attempt_id"] == req["attempt_id"]
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is True
    assert ack["request_sha256"] == req["request_sha256"]
    assert ack["idempotency_key"] == req["idempotency_key"]


def test_unadmitted_request_gets_negative_ack_and_fails_closed():
    req = _request()
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match="not admitted"):
        receive_one_tls_edge_message(
            FakeListener(),
            server_context=FakeServerContext(tls),
            admission_check=lambda message: False,
        )
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is False


def test_hash_mismatch_gets_negative_ack_and_fails_closed():
    req = _request()
    req["payload_ref"] = "kv://tampered"
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match="hash mismatch"):
        receive_one_tls_edge_message(
            FakeListener(),
            server_context=FakeServerContext(tls),
            admission_check=lambda message: True,
        )
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is False


def test_wrong_protocol_fails_closed():
    req = _request(protocol="stegtalk.edge-tcp.v0.1")
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match="protocol mismatch"):
        receive_one_tls_edge_message(
            FakeListener(),
            server_context=FakeServerContext(tls),
            admission_check=lambda message: True,
        )
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is False


def test_missing_binding_fails_closed_before_application_acceptance():
    req = _request(idempotency_key="")
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match="missing required execution binding"):
        receive_one_tls_edge_message(
            FakeListener(),
            server_context=FakeServerContext(tls),
            admission_check=lambda message: True,
        )
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is False
