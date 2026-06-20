from __future__ import annotations

import json
from pathlib import Path

from stegtalk.contact_routing import build_contact_index
from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import create_entity_card, recognize_entity
from stegtalk.public_discovery import create_public_discovery_record
from stegtalk.shell_actions import create_shell_action, run_discovery_action, run_route_message_action
from stegtalk.shell_state import create_shell_state, summarize_shell_state

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "shell_demo_trace.json"


def build_trace() -> dict:
    auri = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="routing and guidance",
        capabilities=["routing"],
    )
    auri, _ = recognize_entity(auri, "Rigel")
    weather = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="weather forecasts",
        capabilities=["forecasts"],
    )
    index = build_discovery_index([create_public_discovery_record(weather)])
    state = create_shell_state(user_entity="Rigel")
    route_action = create_shell_action(
        action_type="route_message",
        payload={"sender_entity": "Rigel", "receiver_hint": "auri", "body": "Hello"},
    )
    state, route_result = run_route_message_action(
        state=state,
        action=route_action,
        contact_index=build_contact_index([auri]),
    )
    search_action = create_shell_action(action_type="discovery_search", payload={"query": "weather"})
    state, search_result = run_discovery_action(state=state, action=search_action, index=index)
    return {
        "trace_type": "stegtalk_shell_demo",
        "summary": summarize_shell_state(state),
        "route_result": route_result,
        "search_result": search_result,
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "summary": trace["summary"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
