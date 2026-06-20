from stegtalk.entity_runtime import create_entity_card, rely_on_entity, create_relationship_contract
from stegtalk.public_discovery import create_public_discovery_record, summarize_public_record


def test_public_discovery_record_uses_public_entity_fields_only():
    card = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts", "local_alerts"],
        boundaries=["not_official_alert_authority"],
        lineage="Rigel/StegWeather",
    )
    card["state"]["published_status"] = "published"
    contract = create_relationship_contract(
        user_identity="Rigel",
        entity_identity="stegweather",
        relationship_type=["recognition", "reliance"],
        scope="local",
        compensation={"model": "per_active_reliance", "rate": "contract_defined", "recipient": "Rigel"},
    )
    card, _ = rely_on_entity(card, contract)
    record = create_public_discovery_record(card)
    assert record["entity_id"] == "stegweather"
    assert record["display_name"] == "StegWeather"
    assert record["published_status"] == "published"
    assert record["reliance_count"] == 1
    assert record["record_hash"].startswith("sha256:")
    assert "receipt" not in record
    assert "message" not in record


def test_public_discovery_summary_is_readable():
    card = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="routing and guidance",
    )
    summary = summarize_public_record(create_public_discovery_record(card))
    assert summary == "Auri (assistant): routing and guidance"
