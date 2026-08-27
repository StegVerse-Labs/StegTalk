from __future__ import annotations

import base64
import hashlib
import json
import socket
import ssl
from dataclasses import dataclass
from typing import Mapping

from .edge_runtime import EdgeExecutionRequest, EdgeExecutor, EdgeRuntimeError
from .entity_runtime import stable_hash, utc_now
from .local_tcp_edge import PayloadLoader, _recv_frame, _send_frame


class PublicTlsEdgeError(EdgeRuntimeError):
    pass


@dataclass(frozen=True)
class TlsEndpoint:
    host: str
    port: int
    server_name: str
    timeout_seconds: float = 4.0
    cafile: str | None = None

    def validate(self) -> None:
        if not self.host:
            raise PublicTlsEdgeError("TLS endpoint host is required")
        if not 1 <= self.port <= 65535:
            raise PublicTlsEdgeError("TLS endpoint port is invalid")
        if not self.server_name:
            raise PublicTlsEdgeError("TLS server_name is required for hostname verification")
        if not 0.05 <= self.timeout_seconds <= 30.0:
            raise PublicTlsEdgeError("TLS timeout is outside admitted bounds")


def _verified_context(endpoint: TlsEndpoint) -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=endpoint.cafile)
    if context.verify_mode != ssl.CERT_REQUIRED:
        raise PublicTlsEdgeError("TLS certificate verification must remain required")
    if context.check_hostname is not True:
        raise PublicTlsEdgeError("TLS hostname verification must remain enabled")
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return context


def tls_edge_executor(
    *,
    endpoint: TlsEndpoint,
    payload_loader: PayloadLoader,
    expected_bearer: str = "stegtalk-tls",
) -> EdgeExecutor:
    """Execute an already-selected ST-032 request over verified TLS.

    ACKNOWLEDGED means the remote StegTalk edge accepted the exact framed request.
    It does not establish human rendering, read receipt, downstream consequence,
    public production activation, or final delivery truth.
    """

    endpoint.validate()

    def _execute(request: EdgeExecutionRequest) -> Mapping[str, object]:
        if request.bearer != expected_bearer:
            raise PublicTlsEdgeError("TLS executor received an unexpected bearer")

        payload = payload_loader(request.payload_ref)
        if not isinstance(payload, bytes):
            raise PublicTlsEdgeError("payload loader must return bytes")

        message: dict[str, object] = {
            "protocol": "stegtalk.edge-tls.v0.1",
            "attempt_id": request.attempt_id,
            "selection_sha256": request.selection_sha256,
            "edge_id": request.edge_id,
            "bearer": request.bearer,
            "idempotency_key": request.idempotency_key,
            "lease_epoch": request.lease_epoch,
            "payload_ref": request.payload_ref,
            "payload_sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            "payload_b64": base64.b64encode(payload).decode("ascii"),
            "tls_server_name": endpoint.server_name,
        }
        request_sha256 = stable_hash(message)
        message["request_sha256"] = request_sha256

        sent = False
        try:
            context = _verified_context(endpoint)
            with socket.create_connection(
                (endpoint.host, endpoint.port),
                timeout=endpoint.timeout_seconds,
            ) as raw_sock:
                raw_sock.settimeout(endpoint.timeout_seconds)
                with context.wrap_socket(
                    raw_sock,
                    server_hostname=endpoint.server_name,
                ) as tls_sock:
                    _send_frame(tls_sock, message)
                    sent = True
                    response = _recv_frame(tls_sock)
        except (
            OSError,
            ssl.SSLError,
            PublicTlsEdgeError,
            UnicodeError,
            json.JSONDecodeError,
        ):
            if sent:
                return {
                    "dispatch_state": "DISPATCHED",
                    "outcome": "INDETERMINATE",
                    "side_effect_absence_confirmed": False,
                    "observed_at": utc_now(),
                }
            return {
                "dispatch_state": "NOT_DISPATCHED",
                "outcome": "FAILED",
                "side_effect_absence_confirmed": True,
                "observed_at": utc_now(),
            }

        if response.get("protocol") != "stegtalk.edge-tls-ack.v0.1":
            return {
                "dispatch_state": "DISPATCHED",
                "outcome": "INDETERMINATE",
                "side_effect_absence_confirmed": False,
                "observed_at": utc_now(),
            }
        if response.get("request_sha256") != request_sha256:
            return {
                "dispatch_state": "DISPATCHED",
                "outcome": "INDETERMINATE",
                "side_effect_absence_confirmed": False,
                "observed_at": utc_now(),
            }
        if response.get("idempotency_key") != request.idempotency_key:
            return {
                "dispatch_state": "DISPATCHED",
                "outcome": "INDETERMINATE",
                "side_effect_absence_confirmed": False,
                "observed_at": utc_now(),
            }
        if response.get("accepted") is not True:
            return {
                "dispatch_state": "DISPATCHED",
                "outcome": "INDETERMINATE",
                "side_effect_absence_confirmed": False,
                "observed_at": utc_now(),
            }

        return {
            "dispatch_state": "OBSERVED",
            "outcome": "ACKNOWLEDGED",
            "side_effect_absence_confirmed": False,
            "observed_at": utc_now(),
        }

    return _execute
