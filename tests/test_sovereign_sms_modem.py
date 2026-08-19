from stegtalk.message_envelope import build_local_message
from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_modem import (
    ModemPort,
    ingest_modem_sms,
    initialize_sms_modem,
    parse_cmt_notification,
    send_sms_via_modem,
)


class FakeModem:
    def __init__(self):
        self.writes = []
        self.responses = [
            ["OK"],
            ["OK"],
            ["OK"],
            ["OK"],
            ["OK"],
            ["OK"],
            [">"],
            ["+CMGS: 42", "OK"],
        ]

    def write(self, data):
        self.writes.append(data)

    def read_until(self, expect):
        return self.responses.pop(0)


def test_initialize_and_send_without_cloud_provider():
    modem = FakeModem()
    port = ModemPort(modem.write, modem.read_until)
    summary = initialize_sms_modem(port)
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="hello",
    )
    result, receipt = send_sms_via_modem(
        port=port,
        envelope=envelope,
        to_number="+15551234567",
        allow_plaintext_external=True,
    )

    assert summary["cloud_dependency"] is False
    assert result.reference == "42"
    assert receipt["provider"] == "direct_cellular_modem"
    assert receipt["cloud_messaging_dependency"] is False
    assert receipt["network_dependency"] == "mobile_carrier_only"
    assert any('AT+CMGS="+15551234567"' in write for write in modem.writes)
    assert modem.writes[-1] == "hello\x1a"


def test_send_fails_closed_without_plaintext_admission():
    modem = FakeModem()
    port = ModemPort(modem.write, modem.read_until)
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="hello",
    )
    try:
        send_sms_via_modem(port=port, envelope=envelope, to_number="+15551234567")
    except SmsTransportError as exc:
        assert "plaintext" in str(exc)
    else:
        raise AssertionError("direct SMS must fail closed without boundary admission")


def test_parse_and_ingest_direct_modem_sms():
    lines = [
        '+CMT: "+15550001111","","26/08/19,11:20:00-20"',
        "reply from handset",
    ]
    parsed = parse_cmt_notification(lines)
    assert parsed["from"] == "+15550001111"
    assert parsed["body"] == "reply from handset"

    envelope, message_receipt, transport_receipt = ingest_modem_sms(
        lines=lines,
        receiver_entity="entity:stegverse",
    )
    assert envelope["scope"] == "external_sms"
    assert envelope["metadata"]["provider"] == "direct_cellular_modem"
    assert message_receipt["envelope_hash"] == envelope["envelope_hash"]
    assert transport_receipt["direction"] == "inbound"
    assert transport_receipt["cloud_messaging_dependency"] is False
