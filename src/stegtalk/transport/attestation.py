from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum


class PeerPosture(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class PeerAttestation:
    peer_id: str
    device_binding: str
    protocol_version: str
    issued_at: datetime
    expires_at: datetime
    nonce: str
    capability_claims: tuple[str, ...]
    signature_verified: bool


@dataclass(frozen=True)
class AttestationPolicy:
    supported_protocol_versions: tuple[str, ...] = ("0.1.0",)
    required_capabilities: tuple[str, ...] = ("custody_transfer",)
    max_clock_skew_seconds: int = 30


@dataclass(frozen=True)
class AttestationDecision:
    peer_id: str
    posture: PeerPosture
    reasons: tuple[str, ...]


def evaluate_peer_attestation(
    attestation: PeerAttestation,
    *,
    now: datetime,
    seen_nonces: set[str],
    policy: AttestationPolicy | None = None,
) -> AttestationDecision:
    policy = policy or AttestationPolicy()
    reasons: list[str] = []

    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if not attestation.signature_verified:
        reasons.append("signature_unverified")
    if not attestation.device_binding:
        reasons.append("device_binding_missing")
    if attestation.protocol_version not in policy.supported_protocol_versions:
        reasons.append("protocol_version_unsupported")
    if attestation.nonce in seen_nonces:
        reasons.append("attestation_replay_detected")
    if attestation.issued_at > now:
        skew = (attestation.issued_at - now).total_seconds()
        if skew > policy.max_clock_skew_seconds:
            reasons.append("attestation_from_future")
    if now >= attestation.expires_at:
        reasons.append("attestation_expired")
    missing = sorted(set(policy.required_capabilities) - set(attestation.capability_claims))
    reasons.extend(f"capability_missing:{item}" for item in missing)

    if not reasons:
        return AttestationDecision(attestation.peer_id, PeerPosture.ELIGIBLE, ("attestation_valid",))
    hard_reject = {"signature_unverified", "device_binding_missing", "attestation_replay_detected"}
    posture = PeerPosture.REJECTED if any(reason in hard_reject for reason in reasons) else PeerPosture.QUARANTINED
    return AttestationDecision(attestation.peer_id, posture, tuple(reasons))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
