from __future__ import annotations

from dataclasses import asdict

from ..entity_runtime import JsonObject, stable_hash, utc_now
from .attestation import AttestationDecision, PeerAttestation


def build_attestation_receipt(
    *,
    attestation: PeerAttestation,
    decision: AttestationDecision,
    previous_receipt_hash: str | None = None,
) -> JsonObject:
    """Create a payload-free receipt binding one attestation to its decision."""
    receipt: JsonObject = {
        "schema_version": "0.1.0",
        "receipt_type": "stegtalk_peer_attestation",
        "peer_reference_hash": stable_hash({"peer_id": attestation.peer_id}),
        "attestation_hash": stable_hash(asdict(attestation)),
        "decision_hash": stable_hash(asdict(decision)),
        "posture": decision.posture,
        "reasons": list(decision.reasons),
        "previous_receipt_hash": previous_receipt_hash,
        "authority": {
            "identity_authority_granted": False,
            "execution_authority_granted": False,
            "delivery_authority_granted": False,
        },
        "created_at": utc_now(),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def verify_attestation_receipt(
    receipt: JsonObject,
    *,
    attestation: PeerAttestation,
    decision: AttestationDecision,
    expected_previous_receipt_hash: str | None = None,
) -> bool:
    if receipt.get("receipt_type") != "stegtalk_peer_attestation":
        return False
    if receipt.get("previous_receipt_hash") != expected_previous_receipt_hash:
        return False
    if receipt.get("attestation_hash") != stable_hash(asdict(attestation)):
        return False
    if receipt.get("decision_hash") != stable_hash(asdict(decision)):
        return False
    if receipt.get("posture") != decision.posture:
        return False
    authority = receipt.get("authority", {})
    if any(authority.get(key) is not False for key in (
        "identity_authority_granted",
        "execution_authority_granted",
        "delivery_authority_granted",
    )):
        return False
    stored_hash = receipt.get("receipt_hash")
    unhashed = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return stored_hash == stable_hash(unhashed)
