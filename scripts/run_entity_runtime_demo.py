from __future__ import annotations

import json
from pathlib import Path

from stegtalk.entity_interactions import (
    create_attention_receipt,
    create_feed_item_receipt,
    create_scoped_message_receipt,
    explain_visibility,
    settle_compensation,
    settle_contributor_splits,
)
from stegtalk.entity_runtime import (
    build_discovery_record,
    commit_change,
    create_change_request,
    create_entity_card,
    create_relationship_contract,
    evaluate_readiness,
    fork_entity,
    recognize_entity,
    rely_on_entity,
    revoke_reliance,
    transition_entity,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "stegweather_runtime_trace.json"


def build_trace() -> dict:
    trace: dict[str, object] = {"trace_type": "stegtalk_entity_runtime_demo", "steps": []}

    card = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts", "local_alerts", "user_messaging"],
        boundaries=["not_dispatch_authority", "not_official_alert_authority", "no_personal_data_resale"],
        version_policy="newest_stable",
        lineage="Rigel/StegWeather",
    )
    trace["steps"].append({"name": "create_entity", "entity_card": card})

    request = create_change_request(
        requester="Rigel",
        target_entity="stegweather",
        change_type="publish_entity",
        scope="public",
        reason="make StegWeather available for recognition and reliance",
        required_conditions=["publication_scope", "compensation_terms", "update_policy"],
    )
    ready = evaluate_readiness(
        request,
        {"publication_scope": True, "compensation_terms": True, "update_policy": True},
    )
    commitment = commit_change(
        change_request=request,
        readiness_evaluation=ready,
        committed_by="Rigel",
        binding_effect="StegWeather may become publicly discoverable",
    )
    card, transition = transition_entity(
        entity_card=card,
        commitment_receipt=commitment,
        transition_type="publish_entity",
        new_state_patch={
            "state": {"published_status": "published"},
            "relationship": {
                "reliance": {"status": "inactive", "scope": None, "terms": "stegweather_public_reliance_v1"},
                "compensation": {"model": "per_active_reliance", "rate": "contract_defined", "recipient": "Rigel"},
            },
        },
        executed_by="publication_steward",
    )
    trace["steps"].append(
        {
            "name": "publish_entity",
            "change_request": request,
            "readiness_evaluation": ready,
            "commitment_receipt": commitment,
            "transition_receipt": transition,
            "discovery_record": build_discovery_record(card),
        }
    )

    card, recognition = recognize_entity(card, "Sarah", local_alias="My Weather")
    contract = create_relationship_contract(
        user_identity="Sarah",
        entity_identity="stegweather",
        relationship_type=["recognition", "reliance"],
        scope="local",
        permissions={
            "may_message": True,
            "may_notify": "weather_alerts_only",
            "may_read_local_state": ["location_region", "weather_preferences"],
            "may_write_local_state": False,
            "may_request_payment": True,
            "may_publish_updates": True,
            "may_represent_user": False,
        },
        compensation={
            "model": "per_active_reliance",
            "rate": "contract_defined",
            "recipient": "Rigel",
            "settlement_token": "StegCoin",
        },
    )
    card, reliance = rely_on_entity(card, contract)
    trace["steps"].append({"name": "recognize_and_rely", "recognition_receipt": recognition, "relationship_contract": contract, "reliance_receipt": reliance})

    scoped = create_scoped_message_receipt(
        sender_entity="stegweather",
        message_ref="regional_notice_v1",
        scope_used="local_reliance_users",
        recipient_basis="region_scope",
        recipient_count=418,
    )
    feed = create_feed_item_receipt(
        feed_type="local",
        source_type="scoped_message",
        source_ref=scoped["id"],
        visible_to_basis="region_scope",
        author_entity="stegweather",
    )
    attention = create_attention_receipt(
        user_identity="Sarah",
        source_entity="stegweather",
        feed_item_ref=feed["id"],
        delivery_scope="local_reliance_users",
        feed_control_rule_applied="allow_weather_notices",
        attention_reason="active_reliance_contract",
        user_action="viewed",
    )
    trace["steps"].append({"name": "message_feed_attention", "scoped_message_receipt": scoped, "feed_item_receipt": feed, "visibility_explanation": explain_visibility(feed), "attention_receipt": attention})

    compensation = settle_compensation(
        reliance_contract=contract,
        entity_identity="stegweather",
        amount=0.1,
        period="2026-06",
    )
    split = settle_contributor_splits(
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
    trace["steps"].append({"name": "settlement", "compensation_settlement_receipt": compensation, "split_settlement_receipt": split})

    card, revocation = revoke_reliance(card)
    forked, fork = fork_entity(card, new_entity_id="sarahweather", new_display_name="SarahWeather")
    trace["steps"].append({"name": "revoke_and_fork", "revocation_receipt": revocation, "fork_receipt": fork, "forked_entity_card": forked})
    return trace


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "step_count": len(trace["steps"])}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
