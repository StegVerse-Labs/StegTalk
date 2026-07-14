"""Minimal HTTP adapter for the deployment-neutral AURI-L1 service.

The adapter uses only the Python standard library. It starts fail-closed unless an
explicit provider mode is configured. The bundled reference provider is suitable
for packaging and smoke verification only; it is not live Auri activation.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Mapping

from .containment import ContainmentState, quarantine_provider
from .runtime import AuriRuntime
from .service import AuriService


def _reference_provider(prompt: str, context: Mapping[str, Any]) -> str:
    return f"reference advisory for {context['action']}: {prompt}"


def build_service_from_environment() -> AuriService:
    provider_mode = os.getenv("AURI_PROVIDER_MODE", "disabled").strip().lower()
    provider_id = os.getenv("AURI_PROVIDER_ID", "provider:disabled").strip()

    if provider_mode == "reference_echo":
        runtime = AuriRuntime(_reference_provider, provider_id or "provider:reference-echo")
        containment = ContainmentState()
    else:
        # A disabled provider still gets a deterministic runtime object so health
        # can be emitted, but the service remains fail-closed.
        runtime = AuriRuntime(_reference_provider, provider_id or "provider:disabled")
        containment = quarantine_provider(
            ContainmentState(), "deployment.provider_not_configured"
        )
    return AuriService(runtime, containment=containment)


class AuriRequestHandler(BaseHTTPRequestHandler):
    service: AuriService

    def _write_json(self, status: int, value: Mapping[str, Any]) -> None:
        payload = json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True
        ).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            health = self.service.health_document()
            status = 200 if health["ready_for_advisory_requests"] else 503
            self._write_json(status, health)
            return
        self._write_json(404, {"error": "not_found", "execution_performed": False})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/advisory":
            self._write_json(404, {"error": "not_found", "execution_performed": False})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(request, dict):
                raise ValueError("request body must be an object")
            result = self.service.submit(request)
        except PermissionError as exc:
            self._write_json(
                503,
                {
                    "error": "service_fail_closed",
                    "detail": str(exc),
                    "execution_performed": False,
                },
            )
            return
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self._write_json(
                400,
                {
                    "error": "invalid_request",
                    "detail": str(exc),
                    "execution_performed": False,
                },
            )
            return
        self._write_json(
            200,
            {
                "candidate": result.candidate,
                "advisory_receipt": result.advisory_receipt,
                "execution_performed": False,
            },
        )

    def log_message(self, format: str, *args: object) -> None:
        # Hosting systems can wrap stdout/stderr; avoid leaking request bodies.
        return


def serve(host: str | None = None, port: int | None = None) -> None:
    resolved_host = host or os.getenv("AURI_HOST", "0.0.0.0")
    resolved_port = port or int(os.getenv("PORT", "8080"))
    service = build_service_from_environment()
    handler = type("BoundAuriRequestHandler", (AuriRequestHandler,), {"service": service})
    ThreadingHTTPServer((resolved_host, resolved_port), handler).serve_forever()
