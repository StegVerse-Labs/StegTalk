import pytest

from stegtalk.sms_pdu import (
    build_status_report_receipt,
    build_ucs2_submit_pdus,
    parse_cds_notification,
    parse_status_report_pdu,
)
from stegtalk.sms_transport import SmsTransportError


def test_single_part_ucs2_submit_pdu_requests_status_report():
    pdus = build_ucs2_submit_pdus(to_number="+15551234567", text="hello")
    assert len(pdus) == 1
    pdu = pdus[0]
    assert pdu.total_parts == 1
    assert pdu.concat_reference is None
    assert pdu.pdu_hex.startswith("00")
    # TP first octet 0x21 = SMS-SUBMIT + status-report request, no UDHI.
    assert pdu.pdu_hex[2:4] == "21"
    assert "00680065006C006C006F" in pdu.pdu_hex


def test_long_unicode_message_builds_concatenated_ucs2_pdus():
    text = "A" * 80
    pdus = build_ucs2_submit_pdus(to_number="+15551234567", text=text, concat_reference=0x7A)
    assert len(pdus) == 2
    assert [p.part_number for p in pdus] == [1, 2]
    assert all(p.total_parts == 2 for p in pdus)
    assert all(p.concat_reference == 0x7A for p in pdus)
    # 0x61 = SMS-SUBMIT + SRR + UDHI.
    assert all(p.pdu_hex[2:4] == "61" for p in pdus)
    # UDH: 05 00 03 ref total sequence
    assert "0500037A0201" in pdus[0].pdu_hex
    assert "0500037A0202" in pdus[1].pdu_hex
    assert "".join(p.text for p in pdus) == text


def test_unicode_split_does_not_break_surrogate_pair():
    text = "A" * 65 + "😀" + "B" * 10
    pdus = build_ucs2_submit_pdus(to_number="+15551234567", text=text, concat_reference=1)
    assert len(pdus) == 2
    assert "".join(p.text for p in pdus) == text
    assert "😀" in pdus[1].text


def test_rejects_empty_text_and_invalid_concat_reference():
    with pytest.raises(SmsTransportError, match="SMS text is required"):
        build_ucs2_submit_pdus(to_number="+15551234567", text="")
    with pytest.raises(SmsTransportError, match="concat_reference"):
        build_ucs2_submit_pdus(to_number="+15551234567", text="A" * 80, concat_reference=256)


def sample_status_report_pdu(status="00"):
    # SMSC length 00; first octet 02 (SMS-STATUS-REPORT); MR 2A;
    # RA +15551234567; synthetic SCTS and discharge time; TP-ST supplied by caller.
    return (
        "00"
        "02"
        "2A"
        "0B"
        "91"
        "5155214365F7"
        "62108021436500"
        "62108021446500"
        + status
    )


def test_parse_delivered_status_report_and_receipt():
    raw = sample_status_report_pdu("00")
    report = parse_status_report_pdu(raw)
    assert report.message_reference == 0x2A
    assert report.recipient == "+15551234567"
    assert report.status_code == 0
    assert report.delivery_state == "delivered"
    receipt = build_status_report_receipt(pdu_hex=raw, report=report)
    assert receipt["type"] == "sovereign_sms_delivery_report_receipt"
    assert receipt["message_reference"] == 0x2A
    assert receipt["delivery_state"] == "delivered"
    assert receipt["cloud_messaging_dependency"] is False


def test_parse_cds_notification_and_permanent_failure():
    raw = sample_status_report_pdu("40")
    report, receipt = parse_cds_notification(["+CDS: 25", raw])
    assert report.delivery_state == "permanent_error"
    assert receipt["status_code"] == 0x40


def test_status_report_parser_fails_closed_on_wrong_mti_or_truncation():
    with pytest.raises(SmsTransportError, match="not SMS-STATUS-REPORT"):
        parse_status_report_pdu("0001")
    with pytest.raises(SmsTransportError):
        parse_status_report_pdu("0002")
