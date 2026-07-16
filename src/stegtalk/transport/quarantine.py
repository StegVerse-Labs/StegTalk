from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum


class QuarantineState(StrEnum):
    ACTIVE = "ACTIVE"
    REMEDIATION_REQUIRED = "REMEDIATION_REQUIRED"
    ELIGIBLE_FOR_REVIEW = "ELIGIBLE_FOR_REVIEW"
    RELEASED = "RELEASED"


@dataclass(frozen=True)
class PeerContinuityRecord:
    peer_reference_hash: str
    highest_protocol_version: str
    device_binding_hash: str
    quarantine_state: QuarantineState = QuarantineState.RELEASED
    quarantine_reason: str | None = None
    quarantine_until: datetime | None = None
    remediation_receipt_hash: str | None = None


def quarantine_peer(
    record: PeerContinuityRecord,
    *,
    reason: str,
    now: datetime,
    duration_seconds: int,
) -> PeerContinuityRecord:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be positive")
    return replace(
        record,
        quarantine_state=QuarantineState.ACTIVE,
        quarantine_reason=reason,
        quarantine_until=now + timedelta(seconds=duration_seconds),
        remediation_receipt_hash=None,
    )


def advance_quarantine(record: PeerContinuityRecord, *, now: datetime) -> PeerContinuityRecord:
    if record.quarantine_state != QuarantineState.ACTIVE:
        return record
    if record.quarantine_until is None or now < record.quarantine_until:
        return record
    return replace(record, quarantine_state=QuarantineState.REMEDIATION_REQUIRED)


def submit_remediation(
    record: PeerContinuityRecord,
    *,
    remediation_receipt_hash: str,
) -> PeerContinuityRecord:
    if record.quarantine_state != QuarantineState.REMEDIATION_REQUIRED:
        raise ValueError("remediation is not currently admissible")
    if len(remediation_receipt_hash) < 16:
        raise ValueError("remediation receipt hash is too short")
    return replace(
        record,
        quarantine_state=QuarantineState.ELIGIBLE_FOR_REVIEW,
        remediation_receipt_hash=remediation_receipt_hash,
    )


def release_quarantine(record: PeerContinuityRecord, *, approved: bool) -> PeerContinuityRecord:
    if record.quarantine_state != QuarantineState.ELIGIBLE_FOR_REVIEW:
        raise ValueError("peer is not eligible for quarantine review")
    if not approved:
        return replace(record, quarantine_state=QuarantineState.REMEDIATION_REQUIRED)
    return replace(
        record,
        quarantine_state=QuarantineState.RELEASED,
        quarantine_reason=None,
        quarantine_until=None,
    )


def verify_peer_continuity(
    record: PeerContinuityRecord,
    *,
    protocol_version: str,
    device_binding_hash: str,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if record.quarantine_state != QuarantineState.RELEASED:
        reasons.append("peer_quarantined")
    if protocol_version < record.highest_protocol_version:
        reasons.append("protocol_downgrade_detected")
    if device_binding_hash != record.device_binding_hash:
        reasons.append("device_binding_discontinuity")
    return (not reasons, tuple(reasons) or ("peer_continuity_valid",))
