from scripts.run_local_inbox_demo import build_trace
from stegtalk.local_inbox import create_local_inbox, project_feed, receive_envelope
from stegtalk.message_envelope import build_local_message


def test_receive_envelope_adds_inbox_item_and_receipts():
    inbox = create_local_inbox(owner_entity="Auri")
    envelope, _ = build_local_message(
        sender_entity="Rigel",
        receiver_entity="Auri",
        body="Route this to StegWeather.",
    )
    updated, item, feed_receipt, attention = receive_envelope(inbox=inbox, envelope=envelope)
    assert len(updated["items"]) == 1
    assert item["envelope_hash"] == envelope["envelope_hash"]
    assert feed_receipt["type"] == "feed_item_receipt"
    assert attention["type"] == "attention_receipt"
    assert updated["inbox_hash"].startswith("sha256:")


def test_project_feed_filters_by_feed_type():
    inbox = create_local_inbox(owner_entity="Auri")
    envelope, _ = build_local_message(sender_entity="Rigel", receiver_entity="Auri", body="Hello")
    inbox, _, _, _ = receive_envelope(inbox=inbox, envelope=envelope, feed_type="recipient")
    assert len(project_feed(inbox, feed_type="recipient")) == 1
    assert project_feed(inbox, feed_type="public") == []


def test_local_inbox_demo_builds_trace():
    trace = build_trace()
    assert trace["trace_type"] == "stegtalk_local_inbox_demo"
    assert len(trace["recipient_feed"]) == 1
    assert trace["inbox_item"]["feed_type"] == "recipient"
