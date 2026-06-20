from __future__ import annotations

from copy import deepcopy
from typing import Any

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity


def create_message_envelope(
    *,
    sender_entity: str,
    receiver_entity: str,
    body: str,
    scope: str = "private",
    message_type: str = "text",
    metadata: dict[str, Any] | None = None,
) -> JsonObject:
    if not sender_entity:
        raise ValueError("sender_entity is required")
    if not receiver_entity:
        raise ValueError("receiver_entity is required")
    if not body:
        raise ValueError("body is required")
    envelope = {
        "schema_version": "1.0.0",
        "envelope_type": "stegtalk_local_message_envelope",
        "sender_entity": sender_entity,
        "receiver_entity": receiver_entity,
        "message_type": message_type,
        "scope": scope,
        "body": body,
        "metadata": metadata or {},
        "created_at": utc_now(),
    }
    envelope["envelope_hash"] = stable_hash(envelope)
    return envelope


def create_message_receipt(envelope: JsonObject, *, result: str = "created") -> JsonObject:
    return with_receipt_identity(
        {
            "type": "message_envelope_receipt",
            "envelope_hash": envelope["envelope_hash"],
            "sender_entity": envelope["sender_entity"],
            "receiver_entity": envelope["receiver_entity"],
            "scope": envelope["scope"],
            "message_type": envelope["message_type"],
            "result": result,
        }
    )


def attach_message_receipt(envelope: JsonObject, receipt: JsonObject) -> JsonObject:
    updated = deepcopy(envelope)
    updated["receipt_ref"] = receipt["id"]
    updated["receipt_chain_head"] = receipt["receipt_chain_head"]
    updated["envelope_with_receipt_hash"] = stable_hash(updated)
    return updated


def build_local_message(
    *,
    sender_entity: str,
    receiver_entity: str,
    body: str,
    scope: str = "private",
    message_type: str = "text",
    metadata: dict[str, Any] | None = None,
) -> tuple[JsonObject, JsonObject]:
    envelope = create_message_envelope(
        sender_entity=sender_entity,
        receiver_entity=receiver_entity,
        body=body,
        scope=scope,
        message_type=message_type,
        metadata=metadata,
    )
    receipt = create_message_receipt(envelope)
    return attach_message_receipt(envelope, receipt), receipt
