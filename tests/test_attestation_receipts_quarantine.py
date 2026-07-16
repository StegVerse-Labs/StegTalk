from datetime import datetime, timedelta, timezone

import pytest

from stegtalk.transport.attestation import (
    AttestationDecision,
    PeerAttestation,
    PeerPosture,
)
from stegtalk.transport.attestation_receipts import (
    build_attestation_receipt,
    verify_attestation_receipt,
)
from stegtalk.transport.quarantine import (
    PeerContinuityRecord,
    QuarantineState,
    advance_quarantine,
    quarantine_peer,
    release_quarantine,
    submit_remediation,
    verify_peer_continuity,
)

NOW = datetime(2026, 7, 16, tzinfo=timezone.utc)


def attestation() -> PeerAttestation:
    return PeerAttestation(
        peer_id="peer-a",
        device_binding="device-a",
        protocol_version="0.1.0",
        issued_at=NOW - timedelta(seconds=5),
        expires_at=NOW + timedelta(minutes=5),
        nonce="nonce-a",
        capability_claims=("custody_transfer",),
        signature_verified=True,
    )


def test_attestation_receipt_binds_inputs_and_chain() -> None:
    item = attestation()
    decision = AttestationDecision("peer-a", PeerPosture.ELIGIBLE, ("attestation_valid",))
    receipt = build_attestation_receipt(
        attestation=item,
        decision=decision,
        previous_receipt_hash="a" * 64,
    )
    assert verify_attestation_receipt(
        receipt,
        attestation=item,
        decision=decision,
        expected_previous_receipt_hash="a" * 64,
    )
    tampered = dict(receipt)
    tampered["posture"] = "REJECTED"
    assert not verify_attestation_receipt(
        tampered,
        attestation=item,
        decision=decision,
        expected_previous_receipt_hash="a" * 64,
    )


def test_quarantine_requires_expiry_remediation_and_review() -> None:
    record = PeerContinuityRecord("peerhash", "0.2.0", "bindinghash")
    active = quarantine_peer(record, reason="false_confirmation", now=NOW, duration_seconds=60)
    assert active.quarantine_state == QuarantineState.ACTIVE
    assert advance_quarantine(active, now=NOW + timedelta(seconds=59)).quarantine_state == QuarantineState.ACTIVE
    remediation_required = advance_quarantine(active, now=NOW + timedelta(seconds=60))
    assert remediation_required.quarantine_state == QuarantineState.REMEDIATION_REQUIRED
    review = submit_remediation(remediation_required, remediation_receipt_hash="b" * 64)
    assert review.quarantine_state == QuarantineState.ELIGIBLE_FOR_REVIEW
    released = release_quarantine(review, approved=True)
    assert released.quarantine_state == QuarantineState.RELEASED


def test_quarantine_cannot_be_bypassed() -> None:
    record = PeerContinuityRecord("peerhash", "0.2.0", "bindinghash")
    with pytest.raises(ValueError):
        submit_remediation(record, remediation_receipt_hash="b" * 64)


def test_downgrade_and_binding_discontinuity_fail_closed() -> None:
    record = PeerContinuityRecord("peerhash", "0.2.0", "bindinghash")
    valid, reasons = verify_peer_continuity(
        record,
        protocol_version="0.1.0",
        device_binding_hash="other-binding",
    )
    assert valid is False
    assert "protocol_downgrade_detected" in reasons
    assert "device_binding_discontinuity" in reasons


def test_active_quarantine_blocks_peer() -> None:
    record = quarantine_peer(
        PeerContinuityRecord("peerhash", "0.1.0", "bindinghash"),
        reason="attestation_replay_detected",
        now=NOW,
        duration_seconds=60,
    )
    valid, reasons = verify_peer_continuity(
        record,
        protocol_version="0.1.0",
        device_binding_hash="bindinghash",
    )
    assert valid is False
    assert reasons == ("peer_quarantined",)
