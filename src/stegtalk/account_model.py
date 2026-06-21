from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now


def create_account_profile(*, account_id: str, display_name: str, owner_entity: str) -> JsonObject:
    if not account_id:
        raise ValueError("account_id is required")
    if not owner_entity:
        raise ValueError("owner_entity is required")
    profile = {
        "schema_version": "1.0.0",
        "profile_type": "stegtalk_account_profile",
        "account_id": account_id,
        "display_name": display_name,
        "owner_entity": owner_entity,
        "linked_entities": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    profile["profile_hash"] = stable_hash(profile)
    return profile


def link_account_entity(profile: JsonObject, *, entity_id: str, role: str) -> JsonObject:
    updated = {**profile, "linked_entities": list(profile.get("linked_entities", []))}
    updated["linked_entities"].append({"entity_id": entity_id, "role": role, "linked_at": utc_now()})
    updated["updated_at"] = utc_now()
    updated["profile_hash"] = stable_hash({key: value for key, value in updated.items() if key != "profile_hash"})
    return updated


def summarize_account_profile(profile: JsonObject) -> JsonObject:
    return {
        "account_id": profile["account_id"],
        "display_name": profile["display_name"],
        "owner_entity": profile["owner_entity"],
        "linked_entity_count": len(profile.get("linked_entities", [])),
        "profile_hash": profile["profile_hash"],
    }
