from __future__ import annotations

import json
from pathlib import Path

from stegtalk.local_inbox import create_local_inbox, project_feed, receive_envelope
from stegtalk.message_envelope import build_local_message

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "examples" / "local_inbox_projection_trace.json"


def build_trace() -> dict:
    inbox = create_local_inbox(owner_entity="Auri")
    envelope, message_receipt = build_local_message(
        sender_entity="Rigel",
        receiver_entity="Auri",
        body="Route this to StegWeather.",
        scope="private",
        metadata={"intent_hint": "weather"},
    )
    inbox, item, feed_receipt, attention = receive_envelope(
        inbox=inbox,
        envelope=envelope,
        visible_to_basis="relationship_scope",
        feed_type="recipient",
    )
    return {
        "trace_type": "stegtalk_local_inbox_demo",
        "inbox": inbox,
        "message_receipt": message_receipt,
        "inbox_item": item,
        "feed_item_receipt": feed_receipt,
        "attention_receipt": attention,
        "recipient_feed": project_feed(inbox, feed_type="recipient"),
    }


def main() -> None:
    trace = build_trace()
    OUTPUT_PATH.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUTPUT_PATH), "item_count": len(trace["recipient_feed"])}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
