from scripts.run_local_store_demo import build_trace
from stegtalk.entity_runtime import create_entity_card
from stegtalk.local_store import build_store_snapshot, initialize_store, list_records, read_record, write_record


def test_local_store_writes_and_reads_record(tmp_path):
    initialize_store(tmp_path)
    card = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="weather",
    )
    written = write_record(tmp_path, "entity_cards", "stegweather", card)
    loaded = read_record(tmp_path, "entity_cards", "stegweather")
    assert written["record_hash"] == loaded["record_hash"]
    assert loaded["record"]["identity"]["id"] == "stegweather"


def test_local_store_lists_records_and_builds_snapshot(tmp_path):
    initialize_store(tmp_path)
    card = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="routing",
    )
    write_record(tmp_path, "entity_cards", "auri", card)
    records = list_records(tmp_path, "entity_cards")
    snapshot = build_store_snapshot(tmp_path)
    assert len(records) == 1
    assert snapshot["collections"]["entity_cards"]["count"] == 1
    assert snapshot["snapshot_hash"].startswith("sha256:")


def test_local_store_demo_builds_trace():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_local_store_demo"
    assert len(trace["records"]) >= 4
    assert trace["snapshot"]["snapshot_hash"].startswith("sha256:")
