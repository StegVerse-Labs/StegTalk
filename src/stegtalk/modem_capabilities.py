from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .entity_runtime import JsonObject, utc_now, with_receipt_identity
from .sms_transport import SmsTransportError
from .sovereign_sms_modem import ModemPort


@dataclass(frozen=True)
class ModemCapabilities:
    identity: tuple[str, ...]
    sim_ready: bool
    registration: str
    signal_rssi: int | None
    sms_text_mode: bool


def _clean(lines: Iterable[str]) -> tuple[str, ...]:
    return tuple(line.strip() for line in lines if line.strip() and line.strip() != "OK")


def _single_prefixed(lines: Iterable[str], prefix: str) -> str | None:
    for line in _clean(lines):
        if line.startswith(prefix):
            return line
    return None


def _parse_cpin(lines: Iterable[str]) -> bool:
    line = _single_prefixed(lines, "+CPIN:")
    return bool(line and line.split(":", 1)[1].strip().upper() == "READY")


def _parse_creg(lines: Iterable[str]) -> str:
    line = _single_prefixed(lines, "+CREG:")
    if not line:
        return "unknown"
    fields = [part.strip() for part in line.split(":", 1)[1].split(",")]
    status = fields[-1] if fields else ""
    return {
        "0": "not_registered",
        "1": "home",
        "2": "searching",
        "3": "denied",
        "4": "unknown",
        "5": "roaming",
    }.get(status, "unknown")


def _parse_csq(lines: Iterable[str]) -> int | None:
    line = _single_prefixed(lines, "+CSQ:")
    if not line:
        return None
    first = line.split(":", 1)[1].split(",", 1)[0].strip()
    try:
        value = int(first)
    except ValueError:
        return None
    return None if value == 99 else value


def interrogate_modem(port: ModemPort) -> tuple[ModemCapabilities, JsonObject]:
    """Interrogate directly attached cellular hardware without cloud services."""

    identity = _clean(port.command("ATI"))
    sim_ready = _parse_cpin(port.command("AT+CPIN?"))
    registration = _parse_creg(port.command("AT+CREG?"))
    signal_rssi = _parse_csq(port.command("AT+CSQ"))

    cmgf_lines = port.command("AT+CMGF?")
    cmgf = _single_prefixed(cmgf_lines, "+CMGF:")
    sms_text_mode = bool(cmgf and cmgf.split(":", 1)[1].strip() == "1")

    caps = ModemCapabilities(
        identity=identity,
        sim_ready=sim_ready,
        registration=registration,
        signal_rssi=signal_rssi,
        sms_text_mode=sms_text_mode,
    )
    receipt = with_receipt_identity(
        {
            "type": "sovereign_sms_modem_capability_receipt",
            "provider": "direct_cellular_modem",
            "sim_ready": sim_ready,
            "registration": registration,
            "signal_rssi": signal_rssi,
            "sms_text_mode": sms_text_mode,
            "cloud_messaging_dependency": False,
            "recorded_at": utc_now(),
        }
    )
    return caps, receipt


def require_registered_sms_capability(caps: ModemCapabilities) -> None:
    if not caps.sim_ready:
        raise SmsTransportError("SIM/eSIM is not ready")
    if caps.registration not in {"home", "roaming"}:
        raise SmsTransportError(f"modem is not registered for public mobile service: {caps.registration}")
    if not caps.sms_text_mode:
        raise SmsTransportError("modem SMS text mode is not active")
