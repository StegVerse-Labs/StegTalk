from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .modem_capabilities import ModemCapabilities, interrogate_modem, require_registered_sms_capability
from .sms_transport import SmsTransportError
from .sovereign_sms_journal import SovereignSmsJournal
from .sovereign_sms_modem import ModemPort, ModemSendResult, ingest_delivery_report, send_ucs2_sms_via_modem


@dataclass(frozen=True)
class GovernedMultipartResult:
    results: tuple[ModemSendResult, ...]
    transport_receipts: tuple[JsonObject, ...]
    aggregate_receipt: JsonObject


def send_governed_unicode(
    *,
    port: ModemPort,
    envelope: JsonObject,
    to_number: str,
    readiness_receipt: JsonObject,
    journal: SovereignSmsJournal | None = None,
    allow_plaintext_external: bool = False,
    concat_reference: int | None = None,
) -> GovernedMultipartResult:
    """Refresh live modem state, submit Unicode PDU part(s), and chain evidence."""

    capabilities, freshness_receipt = interrogate_modem(port)
    require_registered_sms_capability(capabilities)
    if journal is not None:
        journal.append(freshness_receipt)

    results, transport_receipts = send_ucs2_sms_via_modem(
        port=port,
        envelope=envelope,
        to_number=to_number,
        allow_plaintext_external=allow_plaintext_external,
        concat_reference=concat_reference,
    )
    aggregate = with_receipt_identity(
        {
            "type": "sovereign_sms_multipart_submission_receipt",
            "readiness_receipt_hash": stable_hash(readiness_receipt),
            "fresh_capability_receipt_hash": stable_hash(freshness_receipt),
            "envelope_hash": envelope["envelope_hash"],
            "transport_receipt_hashes": [stable_hash(receipt) for receipt in transport_receipts],
            "modem_references": [result.reference for result in results],
            "registration_at_submission": capabilities.registration,
            "sim_ready_at_submission": capabilities.sim_ready,
            "part_count": len(results),
            "concat_reference": transport_receipts[0].get("concat_reference") if transport_receipts else None,
            "multipart": len(results) > 1,
            "delivery_proven": False,
            "production_active": False,
            "recorded_at": utc_now(),
        }
    )
    if journal is not None:
        for receipt in transport_receipts:
            journal.append(receipt)
        journal.append(aggregate)
    return GovernedMultipartResult(results, transport_receipts, aggregate)


def record_governed_delivery_report(
    *,
    lines: Iterable[str],
    journal: SovereignSmsJournal | None = None,
) -> JsonObject:
    """Record +CDS evidence locally; carrier status never grants StegVerse authority."""

    receipt = ingest_delivery_report(lines)
    if journal is not None:
        journal.append(receipt)
    return receipt
