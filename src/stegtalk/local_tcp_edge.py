from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
from dataclasses import dataclass
from typing import Callable, Mapping

from .edge_runtime import EdgeExecutionRequest, EdgeExecutor, EdgeRuntimeError
from .entity_runtime import stable_hash, utc_now


class LocalTcpEdgeError(EdgeRuntimeError):
    pass


@dataclass(frozen=True)
class TcpEndpoint:
    host: str
    port: int
    timeout_seconds: float = 2.0

    def validate(self) -> None:
        if not self.host:
            raise LocalTcpEdgeError("TCP endpoint host is required")
        if not 1 <= self.port <= 65535:
            raise LocalTcpEdgeError("TCP endpoint port is invalid")
        if not 0.05 <= self.timeout_seconds <= 30.0:
            raise LocalTcpEdgeError("TCP timeout is outside admitted bounds")


PayloadLoader = Callable[[str], bytes]


def _send_frame(sock: socket.socket, value: Mapping[str, object]) -> None:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    if len(payload) > 4 * 1024 * 1024:
        raise LocalTcpEdgeError("TCP frame exceeds maximum size")
    sock.sendall(struct.pack("!I", len(payload)) + payload)


def _recv_exact(sock: socket.socket, length: int) -> bytes:
    chunks: list[bytes] = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise LocalTcpEdgeError("TCP peer closed before complete frame")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_frame(sock: socket.socket) -> dict[str, object]:
    header = _recv_exact(sock, 4)
    (length,) = struct.unpack("!I", header)
    if length < 2 or length > 4 * 1024 * 1024:
        raise LocalTcpEdgeError("TCP response frame length is invalid")
    value = json.loads(_recv_exact(sock, length).decode("utf-8"))
    if not isinstance(value, dict):
        raise LocalTcpEdgeError("TCP response must be a JSON object")
    return value


def tcp_edge_executor(*, endpoint: TcpEndpoint, payload_loader: PayloadLoader, expected_bearer: str = "stegtalk-tcp") -> EdgeExecutor:
    """Execute an already-selected ST-032 request over a framed TCP socket.

    ACKNOWLEDGED means the remote StegTalk edge accepted the exact frame. It does
    not establish human rendering/read receipt or production activation.
    """
    endpoint.validate()

    def _execute(request: EdgeExecutionRequest) -> Mapping[str, object]:
        if request.bearer != expected_bearer:
            raise LocalTcpEdgeError("TCP executor received an unexpected bearer")
        payload = payload_loader(request.payload_ref)
        if not isinstance(payload, bytes):
            raise LocalTcpEdgeError("payload loader must return bytes")
        payload_sha256 = "sha256:" + hashlib.sha256(payload).hexdigest()
        message: dict[str, object] = {
            "protocol": "stegtalk.edge-tcp.v0.1",
            "attempt_id": request.attempt_id,
            "selection_sha256": request.selection_sha256,
            "edge_id": request.edge_id,
            "bearer": request.bearer,
            "idempotency_key": request.idempotency_key,
            "lease_epoch": request.lease_epoch,
            "payload_ref": request.payload_ref,
            "payload_sha256": payload_sha256,
            "payload_b64": base64.b64encode(payload).decode("ascii"),
        }
        request_sha256 = stable_hash(message)
        message["request_sha256"] = request_sha256
        sent = False
        try:
            with socket.create_connection((endpoint.host, endpoint.port), timeout=endpoint.timeout_seconds) as sock:
                sock.settimeout(endpoint.timeout_seconds)
                _send_frame(sock, message)
                sent = True
                response = _recv_frame(sock)
        except (OSError, LocalTcpEdgeError, UnicodeError, json.JSONDecodeError):
            if sent:
                return {"dispatch_state": "DISPATCHED", "outcome": "INDETERMINATE", "side_effect_absence_confirmed": False, "observed_at": utc_now()}
            return {"dispatch_state": "NOT_DISPATCHED", "outcome": "FAILED", "side_effect_absence_confirmed": True, "observed_at": utc_now()}

        if response.get("protocol") != "stegtalk.edge-tcp-ack.v0.1":
            return {"dispatch_state": "DISPATCHED", "outcome": "INDETERMINATE", "side_effect_absence_confirmed": False, "observed_at": utc_now()}
        if response.get("request_sha256") != request_sha256 or response.get("idempotency_key") != request.idempotency_key:
            return {"dispatch_state": "DISPATCHED", "outcome": "INDETERMINATE", "side_effect_absence_confirmed": False, "observed_at": utc_now()}
        if response.get("accepted") is not True:
            return {"dispatch_state": "DISPATCHED", "outcome": "INDETERMINATE", "side_effect_absence_confirmed": False, "observed_at": utc_now()}
        return {"dispatch_state": "OBSERVED", "outcome": "ACKNOWLEDGED", "side_effect_absence_confirmed": False, "observed_at": utc_now()}

    return _execute


def receive_one_tcp_edge_message(listener: socket.socket) -> dict[str, object]:
    """Receive and acknowledge one framed message on an already-admitted edge."""
    conn, _address = listener.accept()
    with conn:
        message = _recv_frame(conn)
        request_sha256 = message.get("request_sha256")
        body = dict(message)
        body.pop("request_sha256", None)
        accepted = isinstance(request_sha256, str) and stable_hash(body) == request_sha256
        ack = {
            "protocol": "stegtalk.edge-tcp-ack.v0.1",
            "request_sha256": request_sha256,
            "idempotency_key": message.get("idempotency_key"),
            "accepted": accepted,
            "received_at": utc_now(),
        }
        _send_frame(conn, ack)
        if not accepted:
            raise LocalTcpEdgeError("received TCP request hash mismatch")
        return message
