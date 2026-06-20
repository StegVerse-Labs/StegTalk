from scripts.run_entity_runtime_demo import build_trace


def test_runtime_demo_builds_complete_trace():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_entity_runtime_demo"
    assert [step["name"] for step in trace["steps"]] == [
        "create_entity",
        "publish_entity",
        "recognize_and_rely",
        "message_feed_attention",
        "settlement",
        "revoke_and_fork",
    ]
    publish = trace["steps"][1]
    assert publish["readiness_evaluation"]["result"] == "ready"
    assert publish["transition_receipt"]["type"] == "transition_receipt"
    interaction = trace["steps"][3]
    assert interaction["visibility_explanation"]["receipt_ref"] == interaction["feed_item_receipt"]["id"]
    settlement = trace["steps"][4]
    assert settlement["split_settlement_receipt"]["distributions"][0]["amount"] == 750.0
    fork = trace["steps"][5]
    assert fork["forked_entity_card"]["identity"]["id"] == "sarahweather"
