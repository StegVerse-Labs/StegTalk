from stegtalk.message_envelope import build_local_message
from stegtalk.sms_transport import (
    ClickSendCredentials,
    SmsTransportError,
    build_clicksend_payload,
    ingest_clicksend_sms,
    send_clicksend_sms,
)


def _envelope():
    envelope, _ = build_local_message(
        sender_entity="entity:sender",
        receiver_entity="entity:receiver",
        body="hello over sms",
    )
    return envelope


def test_outbound_requires_explicit_plaintext_admission():
    envelope = _envelope()
    try:
        build_clicksend_payload(envelope=envelope, to_number="+15551234567")
    except SmsTransportError as exc:
        assert "plaintext" in str(exc)
    else:
        raise AssertionError("SMS send must fail closed without explicit plaintext admission")


def test_outbound_builds_clicksend_payload_and_receipt():
    envelope = _envelope()
    seen = {}

    def fake_post(url, headers, payload):
        seen["url"] = url
        seen["headers"] = headers
        seen["payload"] = payload
        return {
            "http_code": 200,
            "response_code": "SUCCESS",
            "response_msg": "Messages queued for delivery.",
            "data": {
                "queued_count": 1,
                "messages": [
                    {
                        "to": "+15551234567",
                        "message_id": "outbound-1",
                        "status": "SUCCESS",
                    }
                ],
            },
        }

    response, receipt = send_clicksend_sms(
        envelope=envelope,
        to_number="+15551234567",
        credentials=ClickSendCredentials(username="runtime-user", api_key="runtime-key"),
        allow_plaintext_external=True,
        http_post=fake_post,
    )

    assert seen["url"].endswith("/v3/sms/send")
    assert seen["payload"]["messages"][0]["body"] == "hello over sms"
    assert seen["payload"]["messages"][0]["custom_string"] == envelope["envelope_hash"]
    assert seen["headers"]["Authorization"].startswith("Basic ")
    assert response["response_code"] == "SUCCESS"
    assert receipt["result"] == "queued"
    assert receipt["provider_message_id"] == "outbound-1"
    assert receipt["boundary"] == "external_plaintext_sms"


def test_inbound_requires_verified_webhook_token():
    payload = {
        "from": "+15550001111",
        "to": "+15550002222",
        "body": "reply",
        "message_id": "inbound-1",
        "original_message_id": "outbound-1",
        "custom_string": "corr-1",
    }
    try:
        ingest_clicksend_sms(
            payload=payload,
            receiver_entity="entity:stegverse",
            sender_entity="external:sms:+15550001111",
        )
    except SmsTransportError as exc:
        assert "token" in str(exc)
    else:
        raise AssertionError("Inbound webhook must fail closed without token verification")


def test_inbound_becomes_external_sms_envelope_with_correlation():
    payload = {
        "timestamp": 1723012981,
        "from": "+15550001111",
        "to": "+15550002222",
        "body": "reply from phone",
        "original_body": "hello over sms",
        "original_message_id": "outbound-1",
        "custom_string": "corr-1",
        "message_id": "inbound-1",
        "user_id": 12345,
        "_keyword": "reply",
    }
    envelope, message_receipt, transport_receipt = ingest_clicksend_sms(
        payload=payload,
        receiver_entity="entity:stegverse",
        sender_entity="external:sms:+15550001111",
        expected_user_id=12345,
        expected_custom_string="corr-1",
        webhook_token_verified=True,
    )

    assert envelope["body"] == "reply from phone"
    assert envelope["scope"] == "external_sms"
    assert envelope["metadata"]["external_plaintext"] is True
    assert envelope["metadata"]["provider_message_id"] == "inbound-1"
    assert envelope["metadata"]["original_message_id"] == "outbound-1"
    assert message_receipt["envelope_hash"] == envelope["envelope_hash"]
    assert transport_receipt["direction"] == "inbound"
    assert transport_receipt["result"] == "accepted"
    assert transport_receipt["correlation_hash"]


def test_number_format_is_not_guessed():
    envelope = _envelope()
    try:
        build_clicksend_payload(
            envelope=envelope,
            to_number="5551234567",
            allow_plaintext_external=True,
        )
    except SmsTransportError as exc:
        assert "E.164" in str(exc)
    else:
        raise AssertionError("local phone numbers must not be guessed into a country")
