from __future__ import annotations

import json
from pathlib import Path

from stegtalk.message_envelope import build_local_message

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "stegtalk_message_envelope_trace.json"


def build_trace() -> dict:
    envelope, receipt = build_local_message(
        sender_entity="Rigel",
        receiver_entity="Auri",
        body="Route this request to StegWeather when weather context is detected.",
        scope="private",
        metadata={"intent_hint": "weather_routing"},
    )
    return {
        "trace_type": "stegtalk_message_envelope_demo",
        "message_envelope": envelope,
        "message_receipt": receipt,
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "receipt": trace["message_receipt"]["id"]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
