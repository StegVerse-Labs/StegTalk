import pytest

from stegtalk.knowledge_vault_extension import (
    assert_kv_host_execution_binding,
    build_kv_send_extension_request,
)
from stegtalk.message_envelope import build_local_message
from stegtalk.sms_transport import SmsTransportError


def test_stegtalk_builds_kv_hosted_send_without_device_authority():
    envelope, _ = build_local_message(
        sender_entity="entity:sender",
        receiver_entity="external:sms:+15551234567",
        body="hello",
    )
    request = build_kv_send_extension_request(
        envelope=envelope,
        vault_subject_ref="vault:self",
        authority_ref="vault:authority:send:1",
        destination="sms:+15551234567",
        payload_ref="vault:payload:message:1",
        idempotency_key="message:1",
    )
    assert request["extension_type"] == "StegTalk"
    assert request["operation"] == "SEND_MESSAGE"
    assert request["destination"] == "sms:+15551234567"
    assert request["device_role"] == "EPHEMERAL_TRANSPORT_EDGE"
    assert request["device_authority"] is False
    assert request["device_continuity_authority"] is False
    assert request["vault_continuity_authority"] is True
    assert request["credential_material"] is None


def test_stegtalk_accepts_exact_kv_host_binding_and_rejects_widening():
    envelope, _ = build_local_message(
        sender_entity="entity:sender",
        receiver_entity="external:sms:+15551234567",
        body="hello",
    )
    request = build_kv_send_extension_request(
        envelope=envelope,
        vault_subject_ref="vault:self",
        authority_ref="vault:authority:send:1",
        destination="sms:+15551234567",
        payload_ref="vault:payload:message:1",
        idempotency_key="message:1",
    )
    hosted = {
        "host": "KnowledgeVault",
        "continuity_authority": "KnowledgeVault",
        **{key: request[key] for key in (
            "extension_type", "extension_id", "operation", "vault_subject_ref",
            "destination", "payload_ref", "payload_sha256", "authority_ref",
            "idempotency_key", "device_role", "device_authority",
            "device_continuity_authority",
        )},
    }
    assert_kv_host_execution_binding(request, hosted)
    hosted["destination"] = "sms:+15557654321"
    with pytest.raises(SmsTransportError, match="changed StegTalk-bound field"):
        assert_kv_host_execution_binding(request, hosted)
