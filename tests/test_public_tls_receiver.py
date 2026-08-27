from __future__ import annotations

import json
import ssl
import struct
import sys
import types

import pytest

from stegtalk.entity_runtime import stable_hash
from stegtalk.public_tls_receiver import PublicTlsReceiverError, knowledge_vault_acceptance_sink, receive_one_tls_edge_message


def _frame(value):
    body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return struct.pack("!I", len(body)) + body

def _request(**overrides):
    body = {
        "protocol": "stegtalk.edge-tls.v0.1", "attempt_id": "attempt:st036:1",
        "selection_sha256": "c" * 64, "edge_id": "edge:public-tls", "bearer": "stegtalk-tls",
        "idempotency_key": "idem:st036:1", "lease_epoch": 1, "payload_ref": "kv://payload/st036/1",
        "payload_sha256": "sha256:" + "d" * 64, "payload_b64": "cGF5bG9hZA==", "tls_server_name": "edge.example.test",
    }
    body.update(overrides)
    body["request_sha256"] = stable_hash(body)
    return body

class FakeTlsConnection:
    def __init__(self, request): self.incoming, self.sent = _frame(request), b''
    def recv(self, length):
        chunk, self.incoming = self.incoming[:length], self.incoming[length:]; return chunk
    def sendall(self, value): self.sent += value
    def __enter__(self): return self
    def __exit__(self, *args): return False

class FakeRawConnection:
    def __enter__(self): return self
    def __exit__(self, *args): return False

class FakeListener:
    def accept(self): return FakeRawConnection(), ("127.0.0.1", 12345)

class FakeServerContext(ssl.SSLContext):
    def __new__(cls, tls_conn):
        obj = super().__new__(cls, ssl.PROTOCOL_TLS_SERVER); obj._tls_conn = tls_conn; return obj
    def wrap_socket(self, sock, *, server_side=False, **kwargs): assert server_side is True; return self._tls_conn

def _decode_ack(sent):
    length = struct.unpack("!I", sent[:4])[0]; return json.loads(sent[4:4+length].decode("utf-8"))

def test_admitted_request_is_persisted_before_positive_ack():
    req, calls = _request(), []
    tls = FakeTlsConnection(req)
    def persist(message, evidence):
        assert tls.sent == b''
        calls.append((dict(message), dict(evidence)))
    observed = receive_one_tls_edge_message(FakeListener(), server_context=FakeServerContext(tls), admission_check=lambda m: True, acceptance_sink=persist)
    assert observed["attempt_id"] == req["attempt_id"]
    assert len(calls) == 1
    evidence = calls[0][1]
    assert evidence["accepted"] is True and evidence["authority_created"] is False
    ack = _decode_ack(tls.sent)
    assert ack["accepted"] is True and ack["received_at"] == evidence["received_at"]

def test_unadmitted_request_never_reaches_acceptance_sink():
    req, calls = _request(), []
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match='not admitted'):
        receive_one_tls_edge_message(FakeListener(), server_context=FakeServerContext(tls), admission_check=lambda m: False, acceptance_sink=lambda m,e: calls.append(e))
    assert calls == []
    assert _decode_ack(tls.sent)["accepted"] is False

def test_hash_mismatch_never_reaches_acceptance_sink():
    req, calls = _request(), []
    req["payload_ref"] = "kv://tampered"
    tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match='hash mismatch'):
        receive_one_tls_edge_message(FakeListener(), server_context=FakeServerContext(tls), admission_check=lambda m: True, acceptance_sink=lambda m,e: calls.append(e))
    assert calls == []
    assert _decode_ack(tls.sent)["accepted"] is False

def test_durability_failure_cannot_emit_positive_ack():
    req = _request(); tls = FakeTlsConnection(req)
    def fail(message, evidence):
        assert tls.sent == b''
        raise RuntimeError('KV unavailable')
    with pytest.raises(PublicTlsReceiverError, match='durability failed'):
        receive_one_tls_edge_message(FakeListener(), server_context=FakeServerContext(tls), admission_check=lambda m: True, acceptance_sink=fail)
    assert _decode_ack(tls.sent)["accepted"] is False

def test_receiver_requires_acceptance_sink():
    req = _request(); tls = FakeTlsConnection(req)
    with pytest.raises(PublicTlsReceiverError, match='acceptance_sink'):
        receive_one_tls_edge_message(FakeListener(), server_context=FakeServerContext(tls), admission_check=lambda m: True, acceptance_sink=None)

def test_knowledge_vault_sink_uses_canonical_journal(monkeypatch, tmp_path):
    calls = []
    class Recovered:
        selection = {"attempt_id": "attempt:st036:1"}; lease = {"attempt_id": "attempt:st036:1"}
    class FakeStore:
        def __init__(self, root): calls.append(('store', str(root)))
        def initialize(self): calls.append(('initialize',))
    class FakeJournal:
        def __init__(self, store): calls.append(('journal',))
        def recover(self, attempt_id): calls.append(('recover', attempt_id)); return Recovered()
        def record_receive(self, *, selection, lease, evidence): calls.append(('record_receive', dict(evidence)))
    execution = types.ModuleType('execution')
    communication_runtime = types.ModuleType('execution.communication_runtime')
    vault_store = types.ModuleType('execution.vault_store')
    communication_runtime.CommunicationRuntimeJournal = FakeJournal
    vault_store.KnowledgeVaultExecutionStore = FakeStore
    monkeypatch.setitem(sys.modules, 'execution', execution)
    monkeypatch.setitem(sys.modules, 'execution.communication_runtime', communication_runtime)
    monkeypatch.setitem(sys.modules, 'execution.vault_store', vault_store)
    sink = knowledge_vault_acceptance_sink(tmp_path)
    req = _request()
    evidence = {
        "attempt_id": req["attempt_id"], "selection_sha256": req["selection_sha256"], "edge_id": req["edge_id"],
        "bearer": req["bearer"], "idempotency_key": req["idempotency_key"], "request_sha256": req["request_sha256"],
        "ack_protocol": "stegtalk.edge-tls-ack.v0.1", "accepted": True, "received_at": "2026-08-27T00:00:00Z", "authority_created": False
    }
    sink(req, evidence)
    assert ('recover', req['attempt_id']) in calls
    assert [c for c in calls if c[0] == 'record_receive'][0][1] == evidence
