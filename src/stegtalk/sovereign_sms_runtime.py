from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .modem_capabilities import ModemCapabilities, interrogate_modem, require_registered_sms_capability
from .serial_modem import PosixSerialRuntime, SerialCandidate, discover_serial_modems
from .sms_transport import SmsTransportError
from .sovereign_sms_modem import ModemPort, ModemSendResult, initialize_sms_modem, send_sms_via_modem


@dataclass(frozen=True)
class ReadySovereignModem:
    candidate: SerialCandidate
    capabilities: ModemCapabilities
    initialization_receipt: JsonObject
    capability_receipt: JsonObject
    readiness_receipt: JsonObject


RuntimeFactory = Callable[[str], PosixSerialRuntime]


def _runtime_factory(path: str) -> PosixSerialRuntime:
    return PosixSerialRuntime(path)


def _readiness_receipt(
    *,
    candidate: SerialCandidate,
    capabilities: ModemCapabilities,
    initialization: JsonObject,
    capability_receipt: JsonObject,
    failures: list[JsonObject] | None = None,
) -> JsonObject:
    return with_receipt_identity(
        {
            "type": "sovereign_sms_runtime_readiness_receipt",
            "transport": "sms",
            "boundary": "direct_cellular_modem",
            "candidate": candidate.path,
            "candidate_family": candidate.family,
            "capabilities": asdict(capabilities),
            "initialization_hash": stable_hash(initialization),
            "capability_receipt_hash": stable_hash(capability_receipt),
            "prior_candidate_failures": failures or [],
            "cloud_messaging_dependency": False,
            "sms_aggregator_dependency": False,
            "delivery_proven": False,
            "production_active": False,
            "recorded_at": utc_now(),
        }
    )


def select_ready_sovereign_modem(
    *,
    candidates: Iterable[SerialCandidate] | None = None,
    runtime_factory: RuntimeFactory = _runtime_factory,
) -> ReadySovereignModem:
    """Find and prove a locally attached SMS modem ready for governed use.

    This discovery helper closes each probe session before returning. Use
    SovereignSmsSession for a send path where the readiness proof and submission
    must share one live modem session.
    """

    discovered = tuple(candidates) if candidates is not None else discover_serial_modems()
    if not discovered:
        raise SmsTransportError("no local serial modem candidates were discovered")

    failures: list[JsonObject] = []
    for candidate in discovered:
        try:
            with runtime_factory(candidate.path) as runtime:
                port: ModemPort = runtime.modem_port()
                initialization = initialize_sms_modem(port)
                capabilities, capability_receipt = interrogate_modem(port)
                require_registered_sms_capability(capabilities)
        except (OSError, SmsTransportError) as exc:
            failures.append(
                {
                    "candidate": candidate.path,
                    "family": candidate.family,
                    "result": "rejected",
                    "reason": str(exc),
                }
            )
            continue

        return ReadySovereignModem(
            candidate=candidate,
            capabilities=capabilities,
            initialization_receipt=initialization,
            capability_receipt=capability_receipt,
            readiness_receipt=_readiness_receipt(
                candidate=candidate,
                capabilities=capabilities,
                initialization=initialization,
                capability_receipt=capability_receipt,
                failures=failures,
            ),
        )

    raise SmsTransportError(
        "no discovered modem satisfied the sovereign SMS readiness gate: "
        + "; ".join(f"{item['candidate']}: {item['reason']}" for item in failures)
    )


class SovereignSmsSession:
    """One live serial session binding readiness proof to SMS submission.

    The session opens one directly attached modem, initializes SMS, requires SIM
    readiness and HOME/ROAMING registration, and re-checks those capabilities
    immediately before each send. This prevents a stale discovery result from
    authorizing a later submission after modem or network state has changed.
    """

    def __init__(self, candidate: SerialCandidate, *, runtime_factory: RuntimeFactory = _runtime_factory):
        self.candidate = candidate
        self.runtime_factory = runtime_factory
        self.runtime: PosixSerialRuntime | None = None
        self.port: ModemPort | None = None
        self.initialization_receipt: JsonObject | None = None
        self.capabilities: ModemCapabilities | None = None
        self.capability_receipt: JsonObject | None = None
        self.readiness_receipt: JsonObject | None = None

    def __enter__(self) -> "SovereignSmsSession":
        runtime = self.runtime_factory(self.candidate.path)
        runtime.open()
        try:
            port = runtime.modem_port()
            initialization = initialize_sms_modem(port)
            capabilities, capability_receipt = interrogate_modem(port)
            require_registered_sms_capability(capabilities)
        except Exception:
            runtime.close()
            raise

        self.runtime = runtime
        self.port = port
        self.initialization_receipt = initialization
        self.capabilities = capabilities
        self.capability_receipt = capability_receipt
        self.readiness_receipt = _readiness_receipt(
            candidate=self.candidate,
            capabilities=capabilities,
            initialization=initialization,
            capability_receipt=capability_receipt,
        )
        return self

    def refresh_registration(self) -> tuple[ModemCapabilities, JsonObject]:
        if self.port is None:
            raise SmsTransportError("sovereign SMS session is not open")
        capabilities, capability_receipt = interrogate_modem(self.port)
        require_registered_sms_capability(capabilities)
        self.capabilities = capabilities
        self.capability_receipt = capability_receipt
        return capabilities, capability_receipt

    def send(
        self,
        *,
        envelope: JsonObject,
        to_number: str,
        allow_plaintext_external: bool = False,
    ) -> tuple[ModemSendResult, JsonObject, JsonObject]:
        if self.port is None or self.readiness_receipt is None:
            raise SmsTransportError("sovereign SMS session is not open")

        capabilities, freshness_receipt = self.refresh_registration()
        result, transport_receipt = send_sms_via_modem(
            port=self.port,
            envelope=envelope,
            to_number=to_number,
            allow_plaintext_external=allow_plaintext_external,
        )
        session_receipt = with_receipt_identity(
            {
                "type": "sovereign_sms_session_submission_receipt",
                "readiness_receipt_hash": stable_hash(self.readiness_receipt),
                "fresh_capability_receipt_hash": stable_hash(freshness_receipt),
                "transport_receipt_hash": stable_hash(transport_receipt),
                "registration_at_submission": capabilities.registration,
                "sim_ready_at_submission": capabilities.sim_ready,
                "sms_text_mode_at_submission": capabilities.sms_text_mode,
                "modem_reference": result.reference,
                "delivery_proven": False,
                "production_active": False,
                "recorded_at": utc_now(),
            }
        )
        return result, transport_receipt, session_receipt

    def close(self) -> None:
        if self.runtime is not None:
            self.runtime.close()
        self.runtime = None
        self.port = None

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def persist_runtime_readiness_receipt(path: str | os.PathLike[str], receipt: JsonObject) -> Path:
    """Append a canonical JSONL readiness receipt and force it to durable storage."""

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    return destination
