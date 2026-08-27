from __future__ import annotations

import ssl
from typing import Callable, Mapping

from .edge_runtime import EdgeRuntimeError
from .entity_runtime import stable_hash, utc_now
from .local_tcp_edge import _recv_frame, _send_frame


class PublicTlsReceiverError(EdgeRuntimeError):
    pass


AdmissionCheck = Callable[[Mapping[str, object]], bool]


def receive_one_tls_edge_message(
    listener,
    *,
    server_context: ssl.SSLContext,
    admission_check: AdmissionCheck,
) -> dict[str, object]:
    """Accept and acknowledge one already-governed StegTalk TLS edge request.

    The server TLS context is supplied by the runtime. This module does not load
    or own certificates/private keys. Application acceptance additionally
    requires the caller-supplied admission_check to approve the exact request.
    """

    if not isinstance(server_context, ssl.SSLContext):
        raise PublicTlsReceiverError("server_context must be an SSLContext")
    if not callable(admission_check):
        raise PublicTlsReceiverError("admission_check is required")

    raw_conn, _address = listener.accept()
    with raw_conn:
        with server_context.wrap_socket(raw_conn, server_side=True) as tls_conn:
            message = _recv_frame(tls_conn)

            protocol_ok = message.get("protocol") == "stegtalk.edge-tls.v0.1"
            request_sha256 = message.get("request_sha256")
            body = dict(message)
            body.pop("request_sha256", None)
            hash_ok = isinstance(request_sha256, str) and stable_hash(body) == request_sha256

            required = (
                isinstance(message.get("attempt_id"), str)
                and bool(message.get("attempt_id"))
                and isinstance(message.get("selection_sha256"), str)
                and bool(message.get("selection_sha256"))
                and isinstance(message.get("edge_id"), str)
                and bool(message.get("edge_id"))
                and message.get("bearer") == "stegtalk-tls"
                and isinstance(message.get("idempotency_key"), str)
                and bool(message.get("idempotency_key"))
            )

            admitted = bool(protocol_ok and hash_ok and required and admission_check(message))
            ack = {
                "protocol": "stegtalk.edge-tls-ack.v0.1",
                "request_sha256": request_sha256,
                "idempotency_key": message.get("idempotency_key"),
                "accepted": admitted,
                "received_at": utc_now(),
            }
            _send_frame(tls_conn, ack)

            if not protocol_ok:
                raise PublicTlsReceiverError("received TLS request protocol mismatch")
            if not hash_ok:
                raise PublicTlsReceiverError("received TLS request hash mismatch")
            if not required:
                raise PublicTlsReceiverError("received TLS request is missing required execution binding")
            if not admitted:
                raise PublicTlsReceiverError("received TLS request is not admitted")

            return message
