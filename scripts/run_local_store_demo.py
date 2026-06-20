from __future__ import annotations

import json
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card, create_relationship_contract
from stegtalk.local_store import build_store_snapshot, initialize_store, read_record, write_record
from stegtalk.message_envelope import build_local_message

ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = ROOT / "examples" / "local_store_demo_runtime"
OUTPUT_PATH = ROOT / "examples" / "local_store_demo_trace.json"


def build_trace() -> dict:
    manifest = initialize_store(STORE_PATH)
    card = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts"],
        boundaries=["local_only"],
    )
    contract = create_relationship_contract(
        user_identity="Rigel",
        entity_identity="stegweather",
        relationship_type=["recognition"],
        scope="local",
    )
    envelope, receipt = build_local_message(
        sender_entity="Rigel",
        receiver_entity="stegweather",
        body="Store this local envelope.",
    )
    card_record = write_record(STORE_PATH, "entity_cards", "stegweather", card)
    contract_record = write_record(STORE_PATH, "relationship_contracts", "rigel_stegweather", contract)
    envelope_record = write_record(STORE_PATH, "message_envelopes", envelope["envelope_hash"].replace("sha256:", ""), envelope)
    receipt_record = write_record(STORE_PATH, "receipts", receipt["id"], receipt)
    snapshot = build_store_snapshot(STORE_PATH)
    return {
        "trace_type": "stegtalk_local_store_demo",
        "manifest": manifest,
        "records": [card_record, contract_record, envelope_record, receipt_record],
        "reloaded_entity_card": read_record(STORE_PATH, "entity_cards", "stegweather"),
        "snapshot": snapshot,
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "snapshot": trace["snapshot"]["snapshot_hash"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
