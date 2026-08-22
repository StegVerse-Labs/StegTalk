from stegtalk.message_envelope import build_local_message
from stegtalk.sovereign_sms_journal import SovereignSmsJournal
from stegtalk.sovereign_sms_modem import ModemPort
from stegtalk.sovereign_sms_pdu_runtime import (
    record_governed_delivery_report,
    send_governed_unicode,
)


class FakeModem:
    def __init__(self):
        self.writes = []
        self.responses = [
            ["Fake Modem", "OK"],
            ["+CPIN: READY", "OK"],
            ["+CREG: 0,1", "OK"],
            ["+CSQ: 20,99", "OK"],
            ["+CMGF: 1", "OK"],
            ["OK"], [">"], ["+CMGS: 11", "OK"],
            ["OK"], [">"], ["+CMGS: 12", "OK"],
            ["OK"],
        ]

    def write(self, data):
        self.writes.append(data)

    def read_until(self, expect):
        return self.responses.pop(0)


def sample_status_report_pdu(status="00"):
    return (
        "00" "02" "0B" "0B" "91" "5155214365F7"
        "62108021436500" "62108021446500" + status
    )


def test_governed_unicode_send_chains_freshness_parts_and_aggregate(tmp_path):
    modem = FakeModem()
    port = ModemPort(modem.write, modem.read_until)
    journal = SovereignSmsJournal(tmp_path / "sms.jsonl")
    readiness = {"type": "sovereign_sms_runtime_readiness_receipt", "receipt_id": "ready-1"}
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="A" * 80,
    )

    result = send_governed_unicode(
        port=port,
        envelope=envelope,
        to_number="+15551234567",
        readiness_receipt=readiness,
        journal=journal,
        allow_plaintext_external=True,
        concat_reference=0x22,
    )

    assert len(result.results) == 2
    assert [item.reference for item in result.results] == ["11", "12"]
    assert result.aggregate_receipt["part_count"] == 2
    assert result.aggregate_receipt["multipart"] is True
    assert result.aggregate_receipt["concat_reference"] == 0x22
    replayed = journal.replay_receipts()
    assert replayed[0]["type"] == "sovereign_sms_modem_capability_receipt"
    assert replayed[-1]["type"] == "sovereign_sms_multipart_submission_receipt"
    assert sum(r["type"] == "external_sms_transport_receipt" for r in replayed) == 2


def test_delivery_report_is_journaled_as_evidence(tmp_path):
    journal = SovereignSmsJournal(tmp_path / "sms.jsonl")
    receipt = record_governed_delivery_report(
        lines=["+CDS: 25", sample_status_report_pdu("00")],
        journal=journal,
    )
    assert receipt["delivery_state"] == "delivered"
    replayed = journal.replay_receipts()
    assert replayed[-1]["type"] == "sovereign_sms_delivery_report_receipt"
    assert replayed[-1]["message_reference"] == 0x0B
