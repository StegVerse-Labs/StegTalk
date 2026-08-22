from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .message_envelope import build_local_message
from .sms_pdu import SubmitPdu, build_ucs2_submit_pdus, parse_cds_notification
from .sms_transport import SmsTransportError, normalize_e164


CTRL_Z = "\x1a"


@dataclass(frozen=True)
class ModemSendResult:
    reference: str | None
    raw_lines: tuple[str, ...]


class ModemPort:
    """Minimal dependency-free modem port abstraction.

    A runtime host supplies read/write functions for a local serial, USB CDC ACM,
    UART, or other directly attached modem. No cloud API or provider SDK is required.
    """

    def __init__(self, write: Callable[[str], None], read_until: Callable[[tuple[str, ...]], list[str]]):
        self._write = write
        self._read_until = read_until

    def command(self, command: str, *, expect: tuple[str, ...] = ("OK", "ERROR")) -> list[str]:
        self._write(command + "\r")
        lines = self._read_until(expect)
        if any(line.strip() == "ERROR" for line in lines):
            raise SmsTransportError(f"modem rejected command: {command}")
        return lines

    def write_raw(self, data: str) -> None:
        self._write(data)

    def read_until(self, expect: tuple[str, ...]) -> list[str]:
        return self._read_until(expect)


def initialize_sms_modem(port: ModemPort) -> JsonObject:
    """Initialize a directly attached modem for SMS text-mode operation."""

    port.command("AT")
    port.command("ATE0")
    port.command("AT+CMGF=1")
    port.command('AT+CSCS="GSM"')
    port.command("AT+CNMI=2,2,0,0,0")
    return {
        "transport": "sms",
        "boundary": "direct_cellular_modem",
        "standard_profiles": ["3GPP_TS_27.005", "3GPP_TS_27.007"],
        "cloud_dependency": False,
        "initialized_at": utc_now(),
    }


def _extract_cmgs_reference(lines: Iterable[str]) -> str | None:
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("+CMGS:"):
            return stripped.split(":", 1)[1].strip()
    return None


def send_sms_via_modem(
    *,
    port: ModemPort,
    envelope: JsonObject,
    to_number: str,
    allow_plaintext_external: bool = False,
) -> tuple[ModemSendResult, JsonObject]:
    """Send an admitted StegTalk envelope directly through local cellular hardware."""

    if not allow_plaintext_external:
        raise SmsTransportError("external plaintext SMS transition was not admitted")
    destination = normalize_e164(to_number)
    body = str(envelope.get("body") or "")
    if not body:
        raise SmsTransportError("message envelope body is required")

    port.command("AT+CMGF=1")
    port.write_raw(f'AT+CMGS="{destination}"\r')
    prompt_lines = port.read_until((">", "ERROR"))
    if any(line.strip() == "ERROR" for line in prompt_lines):
        raise SmsTransportError("modem rejected SMS destination")
    port.write_raw(body + CTRL_Z)
    result_lines = port.read_until(("OK", "ERROR"))
    if any(line.strip() == "ERROR" for line in result_lines):
        raise SmsTransportError("modem failed to submit SMS")

    reference = _extract_cmgs_reference(result_lines)
    result = ModemSendResult(reference=reference, raw_lines=tuple(result_lines))
    receipt = with_receipt_identity(
        {
            "type": "external_sms_transport_receipt",
            "provider": "direct_cellular_modem",
            "direction": "outbound",
            "envelope_hash": envelope["envelope_hash"],
            "to": destination,
            "modem_reference": reference,
            "result": "submitted",
            "encoding": "text_mode_gsm",
            "boundary": "external_plaintext_sms",
            "network_dependency": "mobile_carrier_only",
            "cloud_messaging_dependency": False,
            "recorded_at": utc_now(),
        }
    )
    return result, receipt


def submit_pdu_via_modem(*, port: ModemPort, pdu: SubmitPdu, envelope_hash: str) -> tuple[ModemSendResult, JsonObject]:
    """Submit one pre-built SMS-SUBMIT PDU through a directly attached modem."""

    port.command("AT+CMGF=0")
    port.write_raw(f"AT+CMGS={pdu.tpdu_octets}\r")
    prompt_lines = port.read_until((">", "ERROR"))
    if any(line.strip() == "ERROR" for line in prompt_lines):
        raise SmsTransportError("modem rejected SMS PDU length")
    port.write_raw(pdu.pdu_hex + CTRL_Z)
    result_lines = port.read_until(("OK", "ERROR"))
    if any(line.strip() == "ERROR" for line in result_lines):
        raise SmsTransportError("modem failed to submit SMS PDU")
    reference = _extract_cmgs_reference(result_lines)
    result = ModemSendResult(reference=reference, raw_lines=tuple(result_lines))
    receipt = with_receipt_identity(
        {
            "type": "external_sms_transport_receipt",
            "provider": "direct_cellular_modem",
            "direction": "outbound",
            "envelope_hash": envelope_hash,
            "to": pdu.destination,
            "modem_reference": reference,
            "result": "submitted",
            "encoding": "ucs2_pdu",
            "part_number": pdu.part_number,
            "total_parts": pdu.total_parts,
            "concat_reference": pdu.concat_reference,
            "pdu_hash": stable_hash({"pdu_hex": pdu.pdu_hex}),
            "boundary": "external_plaintext_sms",
            "network_dependency": "mobile_carrier_only",
            "cloud_messaging_dependency": False,
            "recorded_at": utc_now(),
        }
    )
    return result, receipt


def send_ucs2_sms_via_modem(
    *,
    port: ModemPort,
    envelope: JsonObject,
    to_number: str,
    allow_plaintext_external: bool = False,
    concat_reference: int | None = None,
) -> tuple[tuple[ModemSendResult, ...], tuple[JsonObject, ...]]:
    """Submit a Unicode message as one or more status-report-requesting PDUs."""

    if not allow_plaintext_external:
        raise SmsTransportError("external plaintext SMS transition was not admitted")
    body = str(envelope.get("body") or "")
    if not body:
        raise SmsTransportError("message envelope body is required")
    pdus = build_ucs2_submit_pdus(
        to_number=to_number,
        text=body,
        concat_reference=concat_reference,
        request_status_report=True,
    )
    results: list[ModemSendResult] = []
    receipts: list[JsonObject] = []
    for pdu in pdus:
        result, receipt = submit_pdu_via_modem(port=port, pdu=pdu, envelope_hash=envelope["envelope_hash"])
        results.append(result)
        receipts.append(receipt)
    # Restore text mode for +CMT text-mode inbound processing after PDU submission.
    port.command("AT+CMGF=1")
    return tuple(results), tuple(receipts)


def ingest_delivery_report(lines: Iterable[str]) -> JsonObject:
    """Parse a +CDS report into a StegVerse receipt without treating carrier state as authority."""

    _report, receipt = parse_cds_notification(lines)
    return receipt


def parse_cmt_notification(lines: Iterable[str]) -> JsonObject:
    """Parse a 3GPP +CMT unsolicited inbound SMS notification in text mode."""

    sequence = [line.rstrip("\r\n") for line in lines if line.strip()]
    header_index = next((i for i, line in enumerate(sequence) if line.startswith("+CMT:")), None)
    if header_index is None or header_index + 1 >= len(sequence):
        raise SmsTransportError("inbound modem data did not contain a complete +CMT message")

    header = sequence[header_index]
    body = sequence[header_index + 1]
    quoted = []
    current = ""
    inside = False
    for char in header:
        if char == '"':
            if inside:
                quoted.append(current)
                current = ""
            inside = not inside
        elif inside:
            current += char

    if not quoted:
        raise SmsTransportError("inbound +CMT sender could not be parsed")
    sender = normalize_e164(quoted[0])
    timestamp = quoted[-1] if len(quoted) > 1 else None
    return {"from": sender, "body": body, "modem_timestamp": timestamp, "raw_header": header}


def ingest_modem_sms(
    *,
    lines: Iterable[str],
    receiver_entity: str,
    sender_entity: str | None = None,
) -> tuple[JsonObject, JsonObject, JsonObject]:
    parsed = parse_cmt_notification(lines)
    external_sender = sender_entity or f"external:sms:{parsed['from']}"
    envelope, message_receipt = build_local_message(
        sender_entity=external_sender,
        receiver_entity=receiver_entity,
        body=parsed["body"],
        scope="external_sms",
        metadata={
            "transport": "sms",
            "provider": "direct_cellular_modem",
            "external_plaintext": True,
            "from": parsed["from"],
            "modem_timestamp": parsed.get("modem_timestamp"),
        },
    )
    transport_receipt = with_receipt_identity(
        {
            "type": "external_sms_transport_receipt",
            "provider": "direct_cellular_modem",
            "direction": "inbound",
            "envelope_hash": envelope["envelope_hash"],
            "from": parsed["from"],
            "result": "accepted",
            "boundary": "external_plaintext_sms",
            "network_dependency": "mobile_carrier_only",
            "cloud_messaging_dependency": False,
            "recorded_at": utc_now(),
        }
    )
    transport_receipt["correlation_hash"] = stable_hash(
        {"envelope_hash": envelope["envelope_hash"], "from": parsed["from"], "body": parsed["body"]}
    )
    return envelope, message_receipt, transport_receipt


def sovereign_sms_summary() -> JsonObject:
    return {
        "transport": "sms",
        "implementation": "direct_cellular_modem",
        "cloud_provider": None,
        "provider_sdk": None,
        "application_third_party_dependency": False,
        "mobile_carrier_dependency": True,
        "standard_profiles": ["3GPP_TS_27.005", "3GPP_TS_27.007"],
        "security_boundary": "external_plaintext_sms",
        "production_network": False,
    }
