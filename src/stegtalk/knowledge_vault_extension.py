from __future__ import annotations

from typing import Any

from .entity_runtime import JsonObject, stable_hash
from .sms_transport import SmsTransportError, normalize_e164


def build_kv_send_extension_request(
    *,
    envelope: JsonObject,
    vault_subject_ref: str,
    authority_ref: str,
    destination: str,
    payload_ref: str,
    idempotency_key: str,
    extension_id: str = "stegtalk:communication",
) -> JsonObject:
    """Bind a StegTalk send to the KnowledgeVault communication-extension contract.

    KnowledgeVault remains durable continuity/authority host. StegTalk performs the
    communication operation. Any handset/modem used later is only an ephemeral
    transport edge and receives no continuity authority from this request.
    """
    if not envelope.get("envelope_hash"):
        raise SmsTransportError("StegTalk envelope_hash is required for KV binding")
    if not vault_subject_ref or not authority_ref or not payload_ref or not idempotency_key:
        raise SmsTransportError("KV subject, authority, payload, and idempotency references are required")

    normalized_destination = destination
    if destination.startswith("sms:"):
        normalized_destination = f"sms:{normalize_e164(destination.split(':', 1)[1])}"

    body = str(envelope.get("body") or "")
    payload_sha256 = stable_hash({"envelope_hash": envelope["envelope_hash"], "body": body})
    return {
        "schema_version": "0.1",
        "extension_id": extension_id,
        "extension_type": "StegTalk",
        "vault_subject_ref": vault_subject_ref,
        "operation": "SEND_MESSAGE",
        "destination": normalized_destination,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
        "authority_ref": authority_ref,
        "idempotency_key": idempotency_key,
        "device_role": "EPHEMERAL_TRANSPORT_EDGE",
        "device_authority": False,
        "device_continuity_authority": False,
        "vault_continuity_authority": True,
        "receipt_required": True,
        "credential_material": None,
    }


def assert_kv_host_execution_binding(request: JsonObject, hosted: dict[str, Any]) -> None:
    """Reject a KV-hosted execution record that widens the StegTalk request."""
    if hosted.get("host") != "KnowledgeVault" or hosted.get("continuity_authority") != "KnowledgeVault":
        raise SmsTransportError("KnowledgeVault host authority is missing")
    immutable = (
        "extension_type", "extension_id", "operation", "vault_subject_ref",
        "destination", "payload_ref", "payload_sha256", "authority_ref",
        "idempotency_key", "device_role", "device_authority",
        "device_continuity_authority",
    )
    for field in immutable:
        if hosted.get(field) != request.get(field):
            raise SmsTransportError(f"KV-hosted execution changed StegTalk-bound field: {field}")
