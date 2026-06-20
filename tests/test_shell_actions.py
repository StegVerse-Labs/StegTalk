from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import create_entity_card, recognize_entity
from stegtalk.public_discovery import create_public_discovery_record
from stegtalk.shell_actions import create_shell_action, run_discovery_action, run_route_message_action
from stegtalk.shell_state import create_shell_state
from stegtalk.contact_routing import build_contact_index


def test_shell_action_routes_message_into_inbox_view():
    card = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="routing",
    )
    card, _ = recognize_entity(card, "Rigel")
    state = create_shell_state(user_entity="Rigel")
    action = create_shell_action(
        action_type="route_message",
        payload={"sender_entity": "Rigel", "receiver_hint": "auri", "body": "Hello"},
    )
    updated, result = run_route_message_action(
        state=state,
        action=action,
        contact_index=build_contact_index([card]),
    )
    assert updated["active_view"] == "inbox"
    assert len(updated["inbox_items"]) == 1
    assert result["decision"]["result"] == "routed"


def test_shell_action_runs_discovery_search():
    card = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="weather forecasts",
        capabilities=["forecasts"],
    )
    index = build_discovery_index([create_public_discovery_record(card)])
    state = create_shell_state(user_entity="Rigel")
    action = create_shell_action(action_type="discovery_search", payload={"query": "weather"})
    updated, result = run_discovery_action(state=state, action=action, index=index)
    assert updated["active_view"] == "discovery"
    assert len(updated["discovery_results"]) == 1
    assert result["result_count"] == 1
