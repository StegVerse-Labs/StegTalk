from __future__ import annotations

from .contact_routing import route_contact
from .discovery_index import search_discovery
from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_inbox import receive_envelope
from .shell_state import add_shell_inbox_item, set_active_view, set_shell_discovery_results


def create_shell_action(*, action_type: str, payload: JsonObject) -> JsonObject:
    action = {
        "schema_version": "1.0.0",
        "action_type": action_type,
        "payload": payload,
        "created_at": utc_now(),
    }
    action["action_hash"] = stable_hash(action)
    return action


def run_route_message_action(*, state: JsonObject, action: JsonObject, contact_index: dict[str, JsonObject]) -> tuple[JsonObject, JsonObject]:
    payload = action["payload"]
    decision, envelope, receipt = route_contact(
        sender_entity=payload["sender_entity"],
        receiver_hint=payload["receiver_hint"],
        body=payload["body"],
        contact_index=contact_index,
        scope=payload.get("scope", "private"),
    )
    updated = set_active_view(state, "inbox")
    if envelope:
        inbox = {"owner_entity": envelope["receiver_entity"], "items": []}
        _, item, _, _ = receive_envelope(inbox=inbox, envelope=envelope)
        updated = add_shell_inbox_item(updated, item)
    return updated, {"decision": decision, "envelope": envelope, "receipt": receipt}


def run_discovery_action(*, state: JsonObject, action: JsonObject, index: JsonObject) -> tuple[JsonObject, JsonObject]:
    result = search_discovery(index, action["payload"]["query"])
    updated = set_shell_discovery_results(set_active_view(state, "discovery"), result)
    return updated, result
