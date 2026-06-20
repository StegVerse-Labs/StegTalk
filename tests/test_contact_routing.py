from scripts.run_contact_routing_demo import build_trace
from stegtalk.contact_routing import build_contact_index, route_contact
from stegtalk.entity_runtime import create_entity_card, recognize_entity


def make_card(entity_id, display_name, entity_type="service"):
    card = create_entity_card(
        entity_id=entity_id,
        display_name=display_name,
        entity_type=entity_type,
        purpose="test contact",
        capabilities=["test"],
        boundaries=["local_only"],
    )
    return recognize_entity(card, "Rigel")[0]


def test_contact_index_matches_id_display_name_and_alias():
    card = make_card("stegweather", "StegWeather")
    card["identity"]["alias"] = "Weather"
    index = build_contact_index([card])
    assert index["stegweather"]["identity"]["id"] == "stegweather"
    assert index["stegweather"]["identity"]["id"] == index["weather"]["identity"]["id"]


def test_route_contact_creates_envelope_for_single_match():
    index = build_contact_index([make_card("stegweather", "StegWeather")])
    decision, envelope, receipt = route_contact(
        sender_entity="Rigel",
        receiver_hint="weather",
        body="Will it rain tomorrow?",
        contact_index=index,
    )
    assert decision["result"] == "routed"
    assert decision["selected_entity"] == "stegweather"
    assert envelope["receiver_entity"] == "stegweather"
    assert envelope["receipt_ref"] == receipt["id"]


def test_route_contact_requires_clarification_for_multiple_matches():
    index = build_contact_index([
        make_card("stegweather", "StegWeather"),
        make_card("weatherlab", "WeatherLab"),
    ])
    decision, envelope, receipt = route_contact(
        sender_entity="Rigel",
        receiver_hint="weather",
        body="Will it rain tomorrow?",
        contact_index=index,
    )
    assert decision["result"] == "clarification_required"
    assert decision["candidate_count"] == 2
    assert envelope == {}
    assert receipt == {}


def test_route_contact_returns_unresolved_when_no_match_exists():
    index = build_contact_index([make_card("auri", "Auri", "assistant")])
    decision, envelope, receipt = route_contact(
        sender_entity="Rigel",
        receiver_hint="weather",
        body="Will it rain tomorrow?",
        contact_index=index,
    )
    assert decision["result"] == "unresolved"
    assert envelope == {}
    assert receipt == {}


def test_contact_routing_demo_builds_routed_trace():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_contact_routing_demo"
    assert trace["decision"]["result"] == "routed"
    assert trace["message_envelope"]["receiver_entity"] == "stegweather"
