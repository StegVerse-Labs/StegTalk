from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now


def create_shell_state(*, user_entity: str, active_view: str = "home") -> JsonObject:
    state = {
        "schema_version": "1.0.0",
        "state_type": "stegtalk_shell_state",
        "user_entity": user_entity,
        "active_view": active_view,
        "contacts": [],
        "inbox_items": [],
        "discovery_results": [],
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    state["state_hash"] = stable_hash(state)
    return state


def add_shell_contact(state: JsonObject, contact: JsonObject) -> JsonObject:
    updated = _copy_state(state)
    updated["contacts"].append(contact)
    return _rehash(updated)


def add_shell_inbox_item(state: JsonObject, item: JsonObject) -> JsonObject:
    updated = _copy_state(state)
    updated["inbox_items"].append(item)
    return _rehash(updated)


def set_shell_discovery_results(state: JsonObject, search_result: JsonObject) -> JsonObject:
    updated = _copy_state(state)
    updated["discovery_results"] = list(search_result.get("results", []))
    return _rehash(updated)


def set_active_view(state: JsonObject, active_view: str) -> JsonObject:
    updated = _copy_state(state)
    updated["active_view"] = active_view
    return _rehash(updated)


def summarize_shell_state(state: JsonObject) -> JsonObject:
    return {
        "user_entity": state["user_entity"],
        "active_view": state["active_view"],
        "contact_count": len(state.get("contacts", [])),
        "inbox_count": len(state.get("inbox_items", [])),
        "discovery_result_count": len(state.get("discovery_results", [])),
        "state_hash": state["state_hash"],
    }


def _copy_state(state: JsonObject) -> JsonObject:
    return {
        **state,
        "contacts": list(state.get("contacts", [])),
        "inbox_items": list(state.get("inbox_items", [])),
        "discovery_results": list(state.get("discovery_results", [])),
    }


def _rehash(state: JsonObject) -> JsonObject:
    state["updated_at"] = utc_now()
    state["state_hash"] = stable_hash({key: value for key, value in state.items() if key != "state_hash"})
    return state
