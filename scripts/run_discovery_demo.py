from __future__ import annotations

import json
from pathlib import Path

from stegtalk.discovery_index import build_discovery_index, search_discovery
from stegtalk.entity_runtime import create_entity_card
from stegtalk.public_discovery import create_public_discovery_record

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "discovery_demo_trace.json"


def build_trace() -> dict:
    weather = create_entity_card(
        entity_id="stegweather",
        display_name="StegWeather",
        entity_type="service",
        purpose="personalized weather intelligence",
        capabilities=["forecasts", "local_alerts"],
        boundaries=["public_record_only"],
        lineage="Rigel/StegWeather",
    )
    auri = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="routing and guidance",
        capabilities=["routing"],
        boundaries=["public_record_only"],
        lineage="StegVerse/Auri",
    )
    records = [create_public_discovery_record(weather), create_public_discovery_record(auri)]
    index = build_discovery_index(records)
    result = search_discovery(index, "weather forecasts")
    return {
        "trace_type": "stegtalk_discovery_demo",
        "records": records,
        "index": index,
        "search_result": result,
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "result_count": trace["search_result"]["result_count"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
