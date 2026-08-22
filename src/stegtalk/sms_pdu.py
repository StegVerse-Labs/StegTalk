from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .sms_transport import SmsTransportError, normalize_e164


@dataclass(frozen=True)
class SubmitPdu:
    pdu_hex: str
    tpdu_octets: int
    destination: str
    part_number: int
    total_parts: int
    concat_reference: int | None
    text: str


@dataclass(frozen=True)
class StatusReportPdu:
    message_reference: int
    recipient: str
    service_center_timestamp_raw: str
    discharge_time_raw: str
    status_code: int
    delivery_state: str


def _semi_octet_encode(digits: str) -> str:
    if not digits.isdigit():
        raise SmsTransportError("address must contain digits only after normalization")
    padded = digits if len(digits) % 2 == 0 else digits + "F"
    return "".join(padded[i + 1] + padded[i] for i in range(0, len(padded), 2))


def _semi_octet_decode(encoded: str, digit_count: int) -> str:
    if len(encoded) % 2:
        raise SmsTransportError("semi-octet field must contain whole octets")
    digits = "".join(encoded[i + 1] + encoded[i] for i in range(0, len(encoded), 2))
    return digits[:digit_count].replace("F", "")


def _chunks_for_ucs2(text: str, *, multipart_octets: int = 134) -> tuple[str, ...]:
    """Split Unicode text without breaking code points for concatenated UCS-2 SMS.

    A concatenated UCS-2 TP-UD has 140 octets total. The 6-octet 8-bit
    concatenation UDH leaves 134 octets, or at most 67 BMP code points when
    every code point encodes to one UTF-16BE code unit. Astral code points use
    surrogate pairs and therefore consume four octets.
    """

    if not text:
        raise SmsTransportError("SMS text is required")
    parts: list[str] = []
    current = ""
    used = 0
    for char in text:
        encoded = char.encode("utf-16-be")
        if len(encoded) > multipart_octets:
            raise SmsTransportError("single character exceeds SMS multipart capacity")
        # Keep astral code points away from an exact segment edge. They occupy a
        # UTF-16 surrogate pair, and moving the whole code point to the next
        # segment avoids boundary handling that could otherwise split the pair
        # in downstream modem/SMSC implementations while preserving text order.
        if current and (
            used + len(encoded) > multipart_octets
            or (len(encoded) == 4 and used + len(encoded) == multipart_octets)
        ):
            parts.append(current)
            current = ""
            used = 0
        current += char
        used += len(encoded)
    if current:
        parts.append(current)
    return tuple(parts)


def build_ucs2_submit_pdus(
    *,
    to_number: str,
    text: str,
    concat_reference: int | None = None,
    request_status_report: bool = True,
) -> tuple[SubmitPdu, ...]:
    """Build SMS-SUBMIT PDUs for an ordinary recipient using UCS-2.

    SMSC information is omitted (00) so the modem/SIM uses its configured SMSC.
    Multipart messages use the standardized 8-bit concatenation UDH IEI 00.
    """

    destination = normalize_e164(to_number)
    digits = destination[1:]
    single_capacity = 140
    encoded_all = text.encode("utf-16-be")
    multipart = len(encoded_all) > single_capacity
    if multipart:
        parts = _chunks_for_ucs2(text)
        if len(parts) > 255:
            raise SmsTransportError("multipart SMS exceeds 255-part concatenation limit")
        if concat_reference is None:
            concat_reference = int(stable_hash({"to": destination, "text": text})[:2], 16)
        if not 0 <= concat_reference <= 255:
            raise SmsTransportError("concat_reference must be between 0 and 255")
    else:
        if not text:
            raise SmsTransportError("SMS text is required")
        parts = (text,)
        concat_reference = None

    address = _semi_octet_encode(digits)
    results: list[SubmitPdu] = []
    for index, part in enumerate(parts, start=1):
        udhi = len(parts) > 1
        first_octet = 0x01 | (0x20 if request_status_report else 0) | (0x40 if udhi else 0)
        user_text = part.encode("utf-16-be")
        if udhi:
            assert concat_reference is not None
            udh = bytes([0x05, 0x00, 0x03, concat_reference, len(parts), index])
            user_data = udh + user_text
        else:
            user_data = user_text
        if len(user_data) > 140:
            raise SmsTransportError("encoded TP-UD exceeds 140 octets")

        tpdu = bytes([first_octet, 0x00, len(digits), 0x91])
        tpdu += bytes.fromhex(address)
        tpdu += bytes([0x00, 0x08, len(user_data)])
        tpdu += user_data
        full = bytes([0x00]) + tpdu
        results.append(
            SubmitPdu(
                pdu_hex=full.hex().upper(),
                tpdu_octets=len(tpdu),
                destination=destination,
                part_number=index,
                total_parts=len(parts),
                concat_reference=concat_reference,
                text=part,
            )
        )
    return tuple(results)


def _decode_scts(raw: bytes) -> str:
    if len(raw) != 7:
        raise SmsTransportError("SCTS must contain seven octets")
    return raw.hex().upper()


def _status_name(code: int) -> str:
    if code == 0x00:
        return "delivered"
    if 0x01 <= code <= 0x1F:
        return "forwarded_or_temporary_success"
    if 0x20 <= code <= 0x3F:
        return "temporary_error"
    if 0x40 <= code <= 0x5F:
        return "permanent_error"
    return "unknown"


def parse_status_report_pdu(pdu_hex: str) -> StatusReportPdu:
    """Parse the mandatory core of an SMS-STATUS-REPORT PDU.

    Optional TP-PI fields are intentionally ignored after the mandatory status
    octet; raw receipt evidence should be retained by the caller.
    """

    compact = "".join(pdu_hex.split()).upper()
    try:
        data = bytes.fromhex(compact)
    except ValueError as exc:
        raise SmsTransportError("status-report PDU is not valid hex") from exc
    if len(data) < 2:
        raise SmsTransportError("status-report PDU is truncated")

    smsc_len = data[0]
    cursor = 1 + smsc_len
    if cursor >= len(data):
        raise SmsTransportError("status-report PDU missing TPDU")
    first_octet = data[cursor]
    cursor += 1
    if first_octet & 0x03 != 0x02:
        raise SmsTransportError("PDU is not SMS-STATUS-REPORT")
    if cursor >= len(data):
        raise SmsTransportError("status-report PDU is truncated")

    message_reference = data[cursor]
    cursor += 1
    if cursor >= len(data):
        raise SmsTransportError("status-report PDU is truncated")
    digit_count = data[cursor]
    cursor += 1
    if cursor >= len(data):
        raise SmsTransportError("status-report recipient address is truncated")
    toa = data[cursor]
    cursor += 1
    address_octets = (digit_count + 1) // 2
    if cursor + address_octets + 15 > len(data):
        raise SmsTransportError("status-report PDU is truncated")
    encoded_address = data[cursor : cursor + address_octets].hex().upper()
    cursor += address_octets
    recipient_digits = _semi_octet_decode(encoded_address, digit_count)
    recipient = ("+" if toa & 0x70 == 0x10 else "") + recipient_digits

    scts = data[cursor : cursor + 7]
    cursor += 7
    discharge = data[cursor : cursor + 7]
    cursor += 7
    status = data[cursor]

    return StatusReportPdu(
        message_reference=message_reference,
        recipient=recipient,
        service_center_timestamp_raw=_decode_scts(scts),
        discharge_time_raw=_decode_scts(discharge),
        status_code=status,
        delivery_state=_status_name(status),
    )


def build_status_report_receipt(*, pdu_hex: str, report: StatusReportPdu) -> JsonObject:
    return with_receipt_identity(
        {
            "type": "sovereign_sms_delivery_report_receipt",
            "transport": "sms",
            "provider": "direct_cellular_modem",
            "message_reference": report.message_reference,
            "recipient": report.recipient,
            "delivery_state": report.delivery_state,
            "status_code": report.status_code,
            "service_center_timestamp_raw": report.service_center_timestamp_raw,
            "discharge_time_raw": report.discharge_time_raw,
            "pdu_hash": stable_hash({"pdu_hex": "".join(pdu_hex.split()).upper()}),
            "cloud_messaging_dependency": False,
            "recorded_at": utc_now(),
        }
    )


def parse_cds_notification(lines: Iterable[str]) -> tuple[StatusReportPdu, JsonObject]:
    """Parse a modem +CDS unsolicited result whose next line is a status PDU."""

    sequence = [line.strip() for line in lines if line.strip()]
    index = next((i for i, line in enumerate(sequence) if line.startswith("+CDS:")), None)
    if index is None or index + 1 >= len(sequence):
        raise SmsTransportError("delivery report did not contain +CDS header and PDU")
    pdu_hex = sequence[index + 1]
    report = parse_status_report_pdu(pdu_hex)
    return report, build_status_report_receipt(pdu_hex=pdu_hex, report=report)
