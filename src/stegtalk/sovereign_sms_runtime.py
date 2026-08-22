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
from .sovereign_sms_modem import ModemPort, initialize_sms_modem


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


def select_ready_sovereign_modem(
    *,
    candidates: Iterable[SerialCandidate] | None = None,
    runtime_factory: RuntimeFactory = _runtime_factory,
) -> ReadySovereignModem:
    """Find and prove a locally attached SMS modem ready for governed use.

    Discovery, serial binding, SMS initialization, SIM readiness, and public-network
    registration are composed into one fail-closed software path. A successful return
    is still only an observation of the attached hardware at that moment; it is not
    delivery proof and it does not activate ST-029 by itself.
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

        readiness = with_receipt_identity(
            {
                "type": "sovereign_sms_runtime_readiness_receipt",
                "transport": "sms",
                "boundary": "direct_cellular_modem",
                "candidate": candidate.path,
                "candidate_family": candidate.family,
                "capabilities": asdict(capabilities),
                "initialization_hash": stable_hash(initialization),
                "capability_receipt_hash": stable_hash(capability_receipt),
                "prior_candidate_failures": failures,
                "cloud_messaging_dependency": False,
                "sms_aggregator_dependency": False,
                "delivery_proven": False,
                "production_active": False,
                "recorded_at": utc_now(),
            }
        )
        return ReadySovereignModem(
            candidate=candidate,
            capabilities=capabilities,
            initialization_receipt=initialization,
            capability_receipt=capability_receipt,
            readiness_receipt=readiness,
        )

    raise SmsTransportError(
        "no discovered modem satisfied the sovereign SMS readiness gate: "
        + "; ".join(f"{item['candidate']}: {item['reason']}" for item in failures)
    )


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
