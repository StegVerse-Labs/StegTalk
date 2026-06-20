from scripts.run_message_envelope_demo import build_trace
from stegtalk.message_envelope import build_local_message, create_message_envelope


def test_create_message_envelope_has_hash_and_required_fields():
    envelope = create_message_envelope(
        sender_entity="Rigel",
        receiver_entity="Auri",
        body="Route this to StegWeather.",
        scope="private",
        metadata={"intent_hint": "weather"},
    )
    assert envelope["envelope_type"] == "stegtalk_local_message_envelope"
    assert envelope["sender_entity"] == "Rigel"
    assert envelope["receiver_entity"] == "Auri"
    assert envelope["envelope_hash"].startswith("sha256:")


def test_build_local_message_returns_envelope_and_receipt():
    envelope, receipt = build_local_message(
        sender_entity="Sarah",
        receiver_entity="stegweather",
        body="Send local notices only.",
    )
    assert envelope["receipt_ref"] == receipt["id"]
    assert receipt["type"] == "message_envelope_receipt"
    assert receipt["result"] == "created"


def test_message_envelope_demo_builds_trace():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_message_envelope_demo"
    assert trace["message_envelope"]["receipt_ref"] == trace["message_receipt"]["id"]
