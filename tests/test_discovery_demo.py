from scripts.run_discovery_demo import build_trace


def test_discovery_demo_builds_index_and_search_result():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_discovery_demo"
    assert len(trace["records"]) == 2
    assert trace["index"]["record_count"] == 2
    assert trace["search_result"]["result_count"] == 1
    assert trace["search_result"]["results"][0]["entity_id"] == "stegweather"
