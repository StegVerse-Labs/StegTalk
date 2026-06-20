from stegtalk.adapter_boundary import adapter_boundary_summary, create_adapter_handoff, create_adapter_receipt
from stegtalk.message_envelope import build_local_message


def test_boundary_handoff_records_receipt():
    envelope, _ = build_local_message(
        sender_entity="Rigel",
        receiver_entity="Auri",
        body="Record a local handoff.",
    )
    handoff = create_adapter_handoff(adapter_name="local_mock", envelope=envelope)
    receipt = create_adapter_receipt(adapter_handoff=handoff)
    assert handoff["handoff_hash"].startswith("sha256:")
    assert receipt["type"] == "adapter_handoff_receipt"
    assert receipt["adapter_handoff_hash"] == handoff["handoff_hash"]
    assert receipt["result"] == "accepted"


def test_boundary_summary_keeps_prototype_scope():
    summary = adapter_boundary_summary()
    assert summary["production_network"] is False
    assert summary["envelope_separation"] is True
