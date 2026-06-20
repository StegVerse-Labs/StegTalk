from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now

PRIVATE_KEYS = {
    "private",
    "personal",
    "location",
    "device",
    "message",
    "receipt_chain_head",
    "latest",
}


def create_public_discovery_record(entity_card: JsonObject) -> JsonObject:
    identity = entity_card["identity"]
    declarations = entity_card["declarations"]
    state = entity_card.get("state", {})
    relationship = entity_card.get("relationship", {})
    record = {
        "schema_version": "1.0.0",
        "record_type": "stegtalk_public_discovery_record",
        "entity_id": identity["id"],
        "display_name": identity["display_name"],
        "entity_type": identity["type"],
        "purpose": declarations.get("purpose"),
        "capabilities": list(declarations.get("capabilities", [])),
        "boundaries": list(declarations.get("boundaries", [])),
        "lineage": identity.get("lineage"),
        "published_status": state.get("published_status", "unpublished"),
        "recognition_count": int(state.get("active_users", 0)),
        "reliance_count": int(state.get("active_reliance_count", 0)),
        "compensation_model": relationship.get("compensation", {}).get("model", "none"),
        "created_at": utc_now(),
    }
    record["record_hash"] = stable_hash(record)
    assert_public_record_safe(record)
    return record


def assert_public_record_safe(record: JsonObject) -> None:
    for key in record:
        lowered = key.lower()
        if any(private_key in lowered for private_key in PRIVATE_KEYS):
            raise AssertionError(f"private field is not allowed in public discovery record: {key}")


def summarize_public_record(record: JsonObject) -> str:
    return f"{record['display_name']} ({record['entity_type']}): {record['purpose']}"
