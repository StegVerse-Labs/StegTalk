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


def make_stegweather():
    return create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts", "local_alerts", "user_messaging"],
        boundaries=["not_dispatch_authority", "not_official_alert_authority"],
        version_policy="newest_stable",
        lineage="Rigel/StegWeather",
    )


def test_create_recognize_rely_revoke_flow():
    card = make_stegweather()
    recognized, recognition_receipt = recognize_entity(card, "Sarah", local_alias="My Weather")
    assert recognized["identity"]["alias"] == "My Weather"
    assert recognition_receipt["type"] == "recognition_receipt"
    assert recognized["relationship"]["reliance"]["status"] == "inactive"

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
    relied, reliance_receipt = rely_on_entity(recognized, contract)
    assert relied["relationship"]["reliance"]["status"] == "active"
    assert relied["state"]["active_reliance_count"] == 1
    assert reliance_receipt["compensation_status"] == "active"

    revoked, revocation_receipt = revoke_reliance(relied)
    assert revoked["relationship"]["reliance"]["status"] == "inactive"
    assert revoked["relationship"]["recognition"]["status"] == "recognized"
    assert revocation_receipt["local_data_status"] == "user_owned"


def test_publish_change_request_requires_readiness_before_transition():
    card = make_stegweather()
    request = create_change_request(
        requester="Rigel",
        target_entity="stegweather",
        change_type="publish_entity",
        scope="public",
        reason="make StegWeather available for recognition and reliance",
        required_conditions=["publication_scope", "compensation_terms", "update_policy"],
    )
    not_ready = evaluate_readiness(request, {"publication_scope": True, "compensation_terms": False, "update_policy": True})
    assert not_ready["result"] == "not_ready"

    ready = evaluate_readiness(request, {"publication_scope": True, "compensation_terms": True, "update_policy": True})
    commitment = commit_change(
        change_request=request,
        readiness_evaluation=ready,
        committed_by="Rigel",
        binding_effect="StegWeather may become publicly discoverable",
    )
    published, transition_receipt = transition_entity(
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
    assert published["state"]["published_status"] == "published"
    assert transition_receipt["transition_type"] == "publish_entity"
    discovery = build_discovery_record(published)
    assert discovery["relationship_contract_template_ref"] == "stegweather_public_reliance_v1"


def test_fork_preserves_lineage_without_dependence():
    card = make_stegweather()
    forked, receipt = fork_entity(card, new_entity_id="sarahweather", new_display_name="SarahWeather")
    assert forked["identity"]["lineage"] == "stegweather"
    assert forked["relationship"]["reliance"]["status"] == "independent"
    assert receipt["type"] == "fork_receipt"
