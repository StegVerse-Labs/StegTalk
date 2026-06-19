from stegtalk.entity_interactions import (
    create_attention_receipt,
    create_feed_item_receipt,
    create_scoped_message_receipt,
    explain_visibility,
    settle_compensation,
    settle_contributor_splits,
)
from stegtalk.entity_runtime import create_relationship_contract


def test_scoped_message_feed_and_attention_receipts_are_explainable():
    scoped = create_scoped_message_receipt(
        sender_entity="stegweather",
        message_ref="regional_notice_v1",
        scope_used="local_reliance_users",
        recipient_basis="region_scope",
        recipient_count=418,
    )
    assert scoped["type"] == "scoped_message_receipt"
    assert scoped["recipient_count"] == 418
    assert scoped["private_recipient_list_ref"] == "local_or_encrypted_only"

    feed = create_feed_item_receipt(
        feed_type="local",
        source_type="scoped_message",
        source_ref=scoped["id"],
        visible_to_basis="region_scope",
        author_entity="stegweather",
    )
    explanation = explain_visibility(feed)
    assert explanation["receipt_ref"] == feed["id"]
    assert "local scope" in explanation["user_facing_text"]

    attention = create_attention_receipt(
        user_identity="Sarah",
        source_entity="stegweather",
        feed_item_ref=feed["id"],
        delivery_scope="local_reliance_users",
        feed_control_rule_applied="allow_weather_notices",
        attention_reason="active_reliance_contract",
        user_action="viewed",
    )
    assert attention["type"] == "attention_receipt"
    assert attention["user_action"] == "viewed"


def test_compensation_settlement_receipt_uses_contract_terms():
    contract = create_relationship_contract(
        user_identity="Sarah",
        entity_identity="stegweather",
        relationship_type=["recognition", "reliance"],
        scope="local",
        compensation={
            "model": "per_active_reliance",
            "rate": "contract_defined",
            "recipient": "Rigel",
            "settlement_token": "StegCoin",
        },
    )
    receipt = settle_compensation(
        reliance_contract=contract,
        entity_identity="stegweather",
        amount=0.1,
        period="2026-06",
    )
    assert receipt["type"] == "compensation_settlement_receipt"
    assert receipt["recipient_identity"] == "Rigel"
    assert receipt["token"] == "StegCoin"


def test_split_settlement_calculates_distribution_amounts():
    receipt = settle_contributor_splits(
        entity="stegweather",
        revenue_source="active_reliance",
        settlement_period="2026-06",
        gross_amount=1000.0,
        token="StegCoin",
        split_policy_ref="stegweather_split_v1",
        distributions=[
            {"recipient": "Rigel", "role": "primary_developer", "share": 0.75},
            {"recipient": "ForecastUIContributor", "role": "dashboard_contributor", "share": 0.10},
        ],
        upstream_distributions=[{"upstream_entity": "WeatherCapabilityBundle", "share": 0.05}],
        infrastructure_distribution={"recipient": "StegVerse Infrastructure", "share": 0.10},
    )
    assert receipt["type"] == "split_settlement_receipt"
    assert receipt["distributions"][0]["amount"] == 750.0
    assert receipt["distributions"][1]["amount"] == 100.0
    assert receipt["upstream_distributions"][0]["amount"] == 50.0
    assert receipt["infrastructure_distribution"]["amount"] == 100.0
