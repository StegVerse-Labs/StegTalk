from stegtalk.message_envelope import build_local_message
from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_modem import (
    ModemPort,
    ingest_delivery_report,
    ingest_modem_sms,
    initialize_sms_modem,
    parse_cmt_notification,
    send_sms_via_modem,
    send_ucs2_sms_via_modem,
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


def test_submit_long_unicode_message_as_two_pdus_and_restore_text_mode():
    class PduModem:
        def __init__(self):
            self.writes = []
            self.responses = [
                ["OK"], [">"], ["+CMGS: 7", "OK"],
                ["OK"], [">"], ["+CMGS: 8", "OK"],
                ["OK"],
            ]

        def write(self, data):
            self.writes.append(data)

        def read_until(self, expect):
            return self.responses.pop(0)

    modem = PduModem()
    port = ModemPort(modem.write, modem.read_until)
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="A" * 80,
    )
    results, receipts = send_ucs2_sms_via_modem(
        port=port,
        envelope=envelope,
        to_number="+15551234567",
        allow_plaintext_external=True,
        concat_reference=0x44,
    )

    assert [result.reference for result in results] == ["7", "8"]
    assert len(receipts) == 2
    assert [receipt["part_number"] for receipt in receipts] == [1, 2]
    assert all(receipt["total_parts"] == 2 for receipt in receipts)
    assert all(receipt["encoding"] == "ucs2_pdu" for receipt in receipts)
    assert all(receipt["concat_reference"] == 0x44 for receipt in receipts)
    assert modem.writes[0] == "AT+CMGF=0\r"
    assert any(write.startswith("AT+CMGS=") for write in modem.writes)
    assert modem.writes[-1] == "AT+CMGF=1\r"


def test_ingest_delivery_report_creates_non_authoritative_evidence_receipt():
    pdu = (
        "00" "02" "2A" "0B" "91" "5155214365F7"
        "62108021436500" "62108021446500" "00"
    )
    receipt = ingest_delivery_report(["+CDS: 25", pdu])
    assert receipt["type"] == "sovereign_sms_delivery_report_receipt"
    assert receipt["message_reference"] == 0x2A
    assert receipt["recipient"] == "+15551234567"
    assert receipt["delivery_state"] == "delivered"
    assert receipt["cloud_messaging_dependency"] is False
