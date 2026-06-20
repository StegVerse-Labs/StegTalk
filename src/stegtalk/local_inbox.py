from __future__ import annotations

from typing import Iterable

from .entity_interactions import create_attention_receipt, create_feed_item_receipt, explain_visibility
from .entity_runtime import JsonObject, stable_hash, utc_now


def create_local_inbox(*, owner_entity: str) -> JsonObject:
    return {
        "schema_version": "1.0.0",
        "inbox_type": "stegtalk_local_inbox",
        "owner_entity": owner_entity,
        "created_at": utc_now(),
        "items": [],
    }


def receive_envelope(
    *,
    inbox: JsonObject,
    envelope: JsonObject,
    visible_to_basis: str = "relationship_scope",
    feed_type: str = "recipient",
) -> tuple[JsonObject, JsonObject, JsonObject, JsonObject]:
    updated = {**inbox, "items": list(inbox.get("items", []))}
    feed_receipt = create_feed_item_receipt(
        feed_type=feed_type,
        source_type="message_envelope",
        source_ref=envelope["envelope_hash"],
        visible_to_basis=visible_to_basis,
        author_entity=envelope["sender_entity"],
    )
    visibility = explain_visibility(feed_receipt)
    attention = create_attention_receipt(
        user_identity=inbox["owner_entity"],
        source_entity=envelope["sender_entity"],
        feed_item_ref=feed_receipt["id"],
        delivery_scope=envelope.get("scope", "private"),
        feed_control_rule_applied="allow_relationship_messages",
        attention_reason=visible_to_basis,
        user_action="delivered",
    )
    item = {
        "item_type": "local_inbox_item",
        "envelope_hash": envelope["envelope_hash"],
        "sender_entity": envelope["sender_entity"],
        "receiver_entity": envelope["receiver_entity"],
        "scope": envelope.get("scope", "private"),
        "feed_type": feed_type,
        "feed_item_receipt_ref": feed_receipt["id"],
        "attention_receipt_ref": attention["id"],
        "received_at": utc_now(),
    }
    item["item_hash"] = stable_hash(item)
    updated["items"].append(item)
    updated["inbox_hash"] = stable_hash(updated)
    return updated, item, feed_receipt, attention


def project_feed(inbox: JsonObject, *, feed_type: str | None = None) -> list[JsonObject]:
    items: Iterable[JsonObject] = inbox.get("items", [])
    if feed_type is not None:
        items = [item for item in items if item.get("feed_type") == feed_type]
    return sorted(items, key=lambda item: item.get("received_at", ""))
