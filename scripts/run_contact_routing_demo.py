from __future__ import annotations

import json
from pathlib import Path

from stegtalk.contact_routing import build_contact_index, route_contact
from stegtalk.entity_runtime import create_entity_card, recognize_entity

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "contact_routing_trace.json"


def build_trace() -> dict:
    auri = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="StegTalk routing and StegVerse guidance",
        capabilities=["route_requests", "explain_context"],
        boundaries=["no_silent_consequence"],
        version_policy="newest_stable",
        lineage="StegVerse/Auri",
    )
    weather = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts", "local_alerts"],
        boundaries=["not_official_alert_authority"],
        version_policy="newest_stable",
        lineage="Rigel/StegWeather",
    )
    auri, _ = recognize_entity(auri, "Rigel")
    weather, _ = recognize_entity(weather, "Rigel")
    contacts = build_contact_index([auri, weather])
    decision, envelope, receipt = route_contact(
        sender_entity="Rigel",
        receiver_hint="weather",
        body="Will it rain tomorrow?",
        contact_index=contacts,
        scope="private",
    )
    return {
        "trace_type": "stegtalk_contact_routing_demo",
        "decision": decision,
        "message_envelope": envelope,
        "message_receipt": receipt,
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "result": trace["decision"]["result"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
