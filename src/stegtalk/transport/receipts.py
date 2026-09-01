from __future__ import annotations

from dataclasses import asdict

from ..entity_runtime import JsonObject, stable_hash, utc_now
from .selector import BearerObservation, SelectionPolicy, TransportDecision, TransportRequest


def build_transport_decision_receipt(
    *,
    request: TransportRequest,
    observations: list[BearerObservation],
    decision: TransportDecision,
    previous_receipt_hash: str | None = None,
) -> JsonObject:
    """Build a payload-free, hash-bound receipt for one selector decision.

    The receipt preserves the request constraints, normalized bearer observations,
    policy version, selected result, and chain predecessor. It intentionally carries
    no message body, contact content, secret, or raw interface capture.
    """
    request_record = asdict(request)
    observation_records = [asdict(item) for item in observations]
    decision_record = asdict(decision)

    receipt: JsonObject = {
        "schema_version": "0.1.0",
        "receipt_type": "stegtalk_transport_decision",
        "message_id": request.message_id,
        "request_hash": stable_hash(request_record),
        "observations_hash": stable_hash(observation_records),
        "decision_hash": stable_hash(decision_record),
        "policy_version": decision.policy_version,
        "result": decision.result,
        "selected_bearer_id": decision.selected_bearer_id,
        "selected_kind": decision.selected_kind,
        "rejected_count": len(decision.rejected),
        "previous_receipt_hash": previous_receipt_hash,
        "authority": {
            "network_priority_granted": False,
            "responder_authority_granted": False,
            "execution_authority_granted": False,
        },
        "created_at": utc_now(),
    }
    receipt["receipt_hash"] = stable_hash(receipt)
    return receipt


def verify_transport_decision_receipt(
    receipt: JsonObject,
    *,
    request: TransportRequest,
    observations: list[BearerObservation],
    decision: TransportDecision,
    expected_previous_receipt_hash: str | None = None,
) -> bool:
    """Verify receipt integrity and binding to the supplied selector inputs."""
    if receipt.get("receipt_type") != "stegtalk_transport_decision":
        return False
    if receipt.get("previous_receipt_hash") != expected_previous_receipt_hash:
        return False
    if receipt.get("request_hash") != stable_hash(asdict(request)):
        return False
    if receipt.get("observations_hash") != stable_hash([asdict(item) for item in observations]):
        return False
    if receipt.get("decision_hash") != stable_hash(asdict(decision)):
        return False
    if receipt.get("policy_version") != decision.policy_version:
        return False
    if receipt.get("result") != decision.result:
        return False
    if receipt.get("selected_bearer_id") != decision.selected_bearer_id:
        return False
    authority = receipt.get("authority", {})
    if any(authority.get(key) is not False for key in (
        "network_priority_granted",
        "responder_authority_granted",
        "execution_authority_granted",
    )):
        return False
    stored_hash = receipt.get("receipt_hash")
    unhashed = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return stored_hash == stable_hash(unhashed)
