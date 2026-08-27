from __future__ import annotations

import ssl
from pathlib import Path
from typing import Callable, Mapping

from .edge_runtime import EdgeRuntimeError
from .entity_runtime import stable_hash, utc_now
from .local_tcp_edge import _recv_frame, _send_frame


class PublicTlsReceiverError(EdgeRuntimeError):
    pass


AdmissionCheck = Callable[[Mapping[str, object]], bool]
AcceptanceSink = Callable[[Mapping[str, object], Mapping[str, object]], None]


def _ack(*, request_sha256: object, idempotency_key: object, accepted: bool, received_at: str) -> dict[str, object]:
    return {
        "protocol": "stegtalk.edge-tls-ack.v0.1",
        "request_sha256": request_sha256,
        "idempotency_key": idempotency_key,
        "accepted": accepted,
        "received_at": received_at,
    }


def receive_one_tls_edge_message(listener, *, server_context: ssl.SSLContext, admission_check: AdmissionCheck, acceptance_sink: AcceptanceSink) -> dict[str, object]:
    """Accept one governed TLS request only after durable receiver acceptance."""
    if not isinstance(server_context, ssl.SSLContext):
        raise PublicTlsReceiverError("server_context must be an SSLContext")
    if not callable(admission_check):
        raise PublicTlsReceiverError("admission_check is required")
    if not callable(acceptance_sink):
        raise PublicTlsReceiverError("acceptance_sink is required")

    raw_conn, _address = listener.accept()
    with raw_conn:
        with server_context.wrap_socket(raw_conn, server_side=True) as tls_conn:
            message = _recv_frame(tls_conn)
            received_at = utc_now()
            protocol_ok = message.get("protocol") == "stegtalk.edge-tls.v0.1"
            request_sha256 = message.get("request_sha256")
            body = dict(message)
            body.pop("request_sha256", None)
            hash_ok = isinstance(request_sha256, str) and stable_hash(body) == request_sha256
            required = (
                isinstance(message.get("attempt_id"), str) and bool(message.get("attempt_id"))
                and isinstance(message.get("selection_sha256"), str) and bool(message.get("selection_sha256"))
                and isinstance(message.get("edge_id"), str) and bool(message.get("edge_id"))
                and message.get("bearer") == "stegtalk-tls"
                and isinstance(message.get("idempotency_key"), str) and bool(message.get("idempotency_key"))
            )

            def negative(reason: str) -> None:
                _send_frame(tls_conn, _ack(request_sha256=request_sha256, idempotency_key=message.get("idempotency_key"), accepted=False, received_at=received_at))
                raise PublicTlsReceiverError(reason)

            if not protocol_ok: negative("received TLS request protocol mismatch")
            if not hash_ok: negative("received TLS request hash mismatch")
            if not required: negative("received TLS request is missing required execution binding")
            if not admission_check(message):
                negative("received TLS request is not admitted")

            evidence = {
                "attempt_id": message["attempt_id"],
                "selection_sha256": message["selection_sha256"],
                "edge_id": message["edge_id"],
                "bearer": message["bearer"],
                "idempotency_key": message["idempotency_key"],
                "request_sha256": request_sha256,
                "ack_protocol": "stegtalk.edge-tls-ack.v0.1",
                "accepted": True,
                "received_at": received_at,
                "authority_created": False,
            }
            try:
                acceptance_sink(message, evidence)
            except Exception as exc:
                _send_frame(tls_conn, _ack(request_sha256=request_sha256, idempotency_key=message.get("idempotency_key"), accepted=False, received_at=received_at))
                raise PublicTlsReceiverError("receiver acceptance durability failed") from exc

            _send_frame(tls_conn, _ack(request_sha256=request_sha256, idempotency_key=message.get("idempotency_key"), accepted=True, received_at=received_at))
            return message


def knowledge_vault_acceptance_sink(vault_root: str | Path) -> AcceptanceSink:
    """Use the canonical continuity-vault-kit journal for durable receiver acceptance."""
    try:
        from execution.communication_runtime import CommunicationRuntimeJournal
        from execution.vault_store import KnowledgeVaultExecutionStore
    except ImportError as exc:
        raise PublicTlsReceiverError("KnowledgeVault communication runtime is unavailable; install or expose StegVerse-Labs/continuity-vault-kit") from exc
    store = KnowledgeVaultExecutionStore(vault_root)
    store.initialize()
    journal = CommunicationRuntimeJournal(store)
    def _persist(message: Mapping[str, object], evidence: Mapping[str, object]) -> None:
        attempt_id = str(message.get("attempt_id") or "")
        if not attempt_id:
            raise PublicTlsReceiverError("receiver request has no attempt_id")
        recovered = journal.recover(attempt_id)
        journal.record_receive(selection=recovered.selection, lease=recovered.lease, evidence=dict(evidence))
    return _persist
