from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now
from .sms_transport import SmsTransportError


class SovereignSmsJournal:
    """Append-only hash-chained journal for ST-029 runtime evidence.

    The journal is local StegVerse state. It records receipts required to replay and
    reconstruct SMS runtime transitions without delegating evidentiary authority to
    the carrier. Existing records are verified on open; corruption fails closed.
    """

    def __init__(self, path: str | os.PathLike[str]):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records = self._load_verified()

    def _load_verified(self) -> list[JsonObject]:
        if not self.path.exists():
            return []
        records: list[JsonObject] = []
        previous_hash: str | None = None
        with self.path.open("r", encoding="utf-8") as handle:
            for expected_sequence, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SmsTransportError(f"invalid sovereign SMS journal JSON at sequence {expected_sequence}") from exc
                if record.get("sequence") != expected_sequence:
                    raise SmsTransportError("sovereign SMS journal sequence is not contiguous")
                if record.get("previous_record_hash") != previous_hash:
                    raise SmsTransportError("sovereign SMS journal chain linkage is invalid")
                receipt = record.get("receipt")
                if not isinstance(receipt, dict):
                    raise SmsTransportError("sovereign SMS journal record has no receipt object")
                if record.get("receipt_hash") != stable_hash(receipt):
                    raise SmsTransportError("sovereign SMS journal receipt hash mismatch")
                claimed_hash = record.get("record_hash")
                canonical = dict(record)
                canonical.pop("record_hash", None)
                if claimed_hash != stable_hash(canonical):
                    raise SmsTransportError("sovereign SMS journal record hash mismatch")
                previous_hash = claimed_hash
                records.append(record)
        return records

    @property
    def records(self) -> tuple[JsonObject, ...]:
        return tuple(self._records)

    @property
    def head_hash(self) -> str | None:
        return self._records[-1]["record_hash"] if self._records else None

    def append(self, receipt: JsonObject) -> JsonObject:
        sequence = len(self._records) + 1
        record: JsonObject = {
            "type": "sovereign_sms_journal_record",
            "sequence": sequence,
            "previous_record_hash": self.head_hash,
            "receipt_hash": stable_hash(receipt),
            "receipt": receipt,
            "journaled_at": utc_now(),
        }
        record["record_hash"] = stable_hash(record)
        encoded = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        self._records.append(record)
        return record

    def replay_receipts(self) -> tuple[JsonObject, ...]:
        """Return verified receipts in transition order for deterministic replay."""
        return tuple(record["receipt"] for record in self._records)

    def reconstruct_summary(self) -> JsonObject:
        inbound = 0
        outbound = 0
        readiness = 0
        submissions = 0
        for receipt in self.replay_receipts():
            if receipt.get("type") == "sovereign_sms_runtime_readiness_receipt":
                readiness += 1
            if receipt.get("type") == "sovereign_sms_session_submission_receipt":
                submissions += 1
            if receipt.get("type") == "external_sms_transport_receipt":
                if receipt.get("direction") == "inbound":
                    inbound += 1
                elif receipt.get("direction") == "outbound":
                    outbound += 1
        return {
            "journal_records": len(self._records),
            "head_hash": self.head_hash,
            "readiness_receipts": readiness,
            "session_submission_receipts": submissions,
            "inbound_transport_receipts": inbound,
            "outbound_transport_receipts": outbound,
        }

    def seen_inbound_correlation_hashes(self) -> frozenset[str]:
        seen: set[str] = set()
        for receipt in self.replay_receipts():
            if receipt.get("type") != "external_sms_transport_receipt":
                continue
            if receipt.get("direction") != "inbound":
                continue
            correlation_hash = receipt.get("correlation_hash")
            if isinstance(correlation_hash, str) and correlation_hash:
                seen.add(correlation_hash)
        return frozenset(seen)

    def append_inbound_once(self, receipt: JsonObject) -> bool:
        """Persist one inbound transport receipt, suppressing replayed duplicates."""
        if receipt.get("type") != "external_sms_transport_receipt" or receipt.get("direction") != "inbound":
            raise SmsTransportError("append_inbound_once requires an inbound external SMS transport receipt")
        correlation_hash = receipt.get("correlation_hash")
        if not isinstance(correlation_hash, str) or not correlation_hash:
            raise SmsTransportError("inbound SMS receipt is missing correlation_hash")
        if correlation_hash in self.seen_inbound_correlation_hashes():
            return False
        self.append(receipt)
        return True


def journal_receipts(journal: SovereignSmsJournal, receipts: Iterable[JsonObject]) -> tuple[JsonObject, ...]:
    return tuple(journal.append(receipt) for receipt in receipts)
