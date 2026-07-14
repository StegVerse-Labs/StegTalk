from __future__ import annotations

from copy import deepcopy

from .contact_routing import build_contact_index
from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_inbox import project_feed
from .shell_actions import create_shell_action, run_discovery_action, run_route_message_action
from .shell_state import add_shell_contact, create_shell_state, summarize_shell_state


SUPPORTED_CAPABILITIES = (
    "load_local_identity",
    "show_local_contacts",
    "create_local_message",
    "show_local_inbox",
    "run_public_discovery_search",
)

DEFERRED_CAPABILITIES = (
    "native_ios_ui",
    "native_android_ui",
    "push_notifications",
    "external_account_sync",
)


def create_mobile_shell(
    *,
    identity_card: JsonObject,
    contacts: list[JsonObject] | None = None,
    inbox: JsonObject | None = None,
    discovery_index: JsonObject | None = None,
) -> JsonObject:
    """Build a deterministic, local-only StegTalk mobile shell state.

    This boundary provides application-facing state and actions without creating
    network, platform, notification, account-sync, or execution authority.
    """
    identity = deepcopy(identity_card)
    user_entity = identity["identity"]["id"]
    contact_cards = [deepcopy(card) for card in contacts or []]
    state = create_shell_state(user_entity=user_entity)
    for card in contact_cards:
        state = add_shell_contact(state, card)

    shell = {
        "schema_version": "1.0.0",
        "state_type": "stegtalk_mobile_shell",
        "mode": "local_prototype",
        "production_ready": False,
        "user_entity": user_entity,
        "identity_card": identity,
        "shell_state": state,
        "contact_index": build_contact_index(contact_cards),
        "inbox": deepcopy(inbox) if inbox is not None else {"owner_entity": user_entity, "items": []},
        "discovery_index": deepcopy(discovery_index) if discovery_index is not None else {"records": []},
        "supported_capabilities": list(SUPPORTED_CAPABILITIES),
        "deferred_capabilities": list(DEFERRED_CAPABILITIES),
        "authority": {
            "network_authority": False,
            "execution_authority": False,
            "external_account_authority": False,
            "native_platform_authority": False,
        },
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    return _rehash(shell)


def load_local_identity(shell: JsonObject) -> JsonObject:
    return deepcopy(shell["identity_card"])


def show_local_contacts(shell: JsonObject) -> list[JsonObject]:
    return deepcopy(shell["shell_state"].get("contacts", []))


def create_local_message(
    shell: JsonObject,
    *,
    receiver_hint: str,
    body: str,
    scope: str = "private",
) -> tuple[JsonObject, JsonObject]:
    action = create_shell_action(
        action_type="route_local_message",
        payload={
            "sender_entity": shell["user_entity"],
            "receiver_hint": receiver_hint,
            "body": body,
            "scope": scope,
        },
    )
    updated_state, result = run_route_message_action(
        state=shell["shell_state"],
        action=action,
        contact_index=shell["contact_index"],
    )
    updated = _copy_shell(shell)
    updated["shell_state"] = updated_state
    if result.get("envelope"):
        updated["inbox"] = {
            "owner_entity": result["envelope"]["receiver_entity"],
            "items": list(updated_state.get("inbox_items", [])),
        }
    updated["last_action"] = {
        "action_hash": action["action_hash"],
        "action_type": action["action_type"],
        "result": result["decision"]["result"],
    }
    return _rehash(updated), result


def show_local_inbox(shell: JsonObject, *, feed_type: str | None = None) -> list[JsonObject]:
    inbox = deepcopy(shell["inbox"])
    if feed_type is None:
        return list(inbox.get("items", []))
    return project_feed(inbox, feed_type=feed_type)


def run_public_discovery_search(shell: JsonObject, *, query: str) -> tuple[JsonObject, JsonObject]:
    action = create_shell_action(action_type="public_discovery_search", payload={"query": query})
    updated_state, result = run_discovery_action(
        state=shell["shell_state"],
        action=action,
        index=shell["discovery_index"],
    )
    updated = _copy_shell(shell)
    updated["shell_state"] = updated_state
    updated["last_action"] = {
        "action_hash": action["action_hash"],
        "action_type": action["action_type"],
        "result_count": len(result.get("results", [])),
    }
    return _rehash(updated), result


def summarize_mobile_shell(shell: JsonObject) -> JsonObject:
    summary = summarize_shell_state(shell["shell_state"])
    return {
        "state_type": shell["state_type"],
        "mode": shell["mode"],
        "production_ready": shell["production_ready"],
        "supported_capabilities": list(shell["supported_capabilities"]),
        "deferred_capabilities": list(shell["deferred_capabilities"]),
        "authority": deepcopy(shell["authority"]),
        "shell": summary,
        "mobile_shell_hash": shell["mobile_shell_hash"],
    }


def _copy_shell(shell: JsonObject) -> JsonObject:
    return deepcopy(shell)


def _rehash(shell: JsonObject) -> JsonObject:
    shell["updated_at"] = utc_now()
    shell["mobile_shell_hash"] = stable_hash(
        {key: value for key, value in shell.items() if key != "mobile_shell_hash"}
    )
    return shell
