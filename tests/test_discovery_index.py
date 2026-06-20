from stegtalk.discovery_index import build_discovery_index, lookup_record, search_index
from stegtalk.entity_runtime import create_entity_card
from stegtalk.public_discovery import create_public_discovery_record


def make_record(entity_id, display_name, purpose, capabilities=None):
    card = create_entity_card(
        entity_id=entity_id,
        display_name=display_name,
        entity_type="service",
        purpose=purpose,
        capabilities=capabilities or [],
        boundaries=["public_record_only"],
    )
    return create_public_discovery_record(card)


def test_discovery_index_builds_terms_and_hash():
    records = [
        make_record("stegweather", "StegWeather", "personalized weather intelligence", ["forecasts"]),
        make_record("auriroute", "AuriRoute", "assistant routing", ["routing"]),
    ]
    index = build_discovery_index(records)
    assert index["record_count"] == 2
    assert index["index_hash"].startswith("sha256:")
    assert "weather" in index["terms"]
    assert "routing" in index["terms"]


def test_discovery_lookup_and_search_return_public_records():
    weather = make_record("stegweather", "StegWeather", "personalized weather intelligence", ["forecasts"])
    route = make_record("auriroute", "AuriRoute", "assistant routing", ["routing"])
    index = build_discovery_index([weather, route])
    assert lookup_record(index, "stegweather")["display_name"] == "StegWeather"
    results = search_index(index, "forecast weather")
    assert [record["entity_id"] for record in results] == ["stegweather"]
    assert search_index(index, "missingterm") == []
