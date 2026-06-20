from scripts.run_shell_demo import build_trace


def test_shell_demo_runs_route_and_discovery_actions():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_shell_demo"
    assert trace["summary"]["active_view"] == "discovery"
    assert trace["summary"]["inbox_count"] == 1
    assert trace["summary"]["discovery_result_count"] == 1
    assert trace["route_result"]["decision"]["result"] == "routed"
    assert trace["search_result"]["result_count"] == 1
