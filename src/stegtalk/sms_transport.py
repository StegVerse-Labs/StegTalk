from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Any, Callable
from urllib import request

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .message_envelope import build_local_message


CLICKSEND_BASE_URL = "https://rest.clicksend.com/v3"
CLICKSEND_SEND_PATH = "/sms/send"
SMS_SCOPE = "external_sms"


class SmsTransportError(RuntimeError):
    """Raised when the external SMS boundary rejects or cannot complete a transition."""


@dataclass(frozen=True)
class ClickSendCredentials:
    """Runtime-injected credentials.

    StegTalk does not persist these values. In StegVerse deployments they must be supplied
    only by the TV/TVC credential authority.
    """

    username: str
    api_key: str

    def validate(self) -> None:
        if not self.username:
            raise SmsTransportError("ClickSend username is required")
        if not self.api_key:
            raise SmsTransportError("ClickSend API key is required")


def normalize_e164(value: str) -> str:
    """Validate a deliberately narrow E.164 representation.

    The adapter does not guess countries or rewrite local numbers because a guessed routing
    decision would cross an external carrier boundary.
    """

    number = value.strip()
    if not number.startswith("+"):
        raise SmsTransportError("SMS number must use explicit E.164 format")
    digits = number[1:]
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        raise SmsTransportError("invalid E.164 number")
    return number


def build_clicksend_payload(
    *,
    envelope: JsonObject,
    to_number: str,
    from_number: str | None = None,
    custom_string: str | None = None,
    allow_plaintext_external: bool = False,
) -> JsonObject:
    """Create a ClickSend payload only after an explicit plaintext-boundary admission.

    SMS is not claimed to be a StegTalk secure transport. The body is exposed to the carrier
    provider and downstream telecom network. The caller must therefore explicitly admit the
    external plaintext transition for every send path.
    """

    if not allow_plaintext_external:
        raise SmsTransportError("external plaintext SMS transition was not admitted")
    if not envelope.get("body"):
        raise SmsTransportError("message envelope body is required")

    message: JsonObject = {
        "source": "stegtalk",
        "body": str(envelope["body"]),
        "to": normalize_e164(to_number),
        "custom_string": custom_string or str(envelope["envelope_hash"]),
    }
    if from_number:
        message["from"] = normalize_e164(from_number)

    return {"messages": [message], "shorten_urls": False}


def _authorization_header(credentials: ClickSendCredentials) -> str:
    credentials.validate()
    token = base64.b64encode(
        f"{credentials.username}:{credentials.api_key}".encode("utf-8")
    ).decode("ascii")
    return f"Basic {token}"


def _default_http_post(url: str, headers: dict[str, str], payload: JsonObject) -> JsonObject:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    req = request.Request(url=url, data=encoded, headers=headers, method="POST")
    with request.urlopen(req, timeout=15) as response:  # nosec B310 - fixed HTTPS endpoint
        raw = response.read().decode("utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise SmsTransportError("ClickSend returned a non-object response")
    return parsed


def send_clicksend_sms(
    *,
    envelope: JsonObject,
    to_number: str,
    credentials: ClickSendCredentials,
    from_number: str | None = None,
    custom_string: str | None = None,
    allow_plaintext_external: bool = False,
    http_post: Callable[[str, dict[str, str], JsonObject], JsonObject] = _default_http_post,
) -> tuple[JsonObject, JsonObject]:
    """Submit one admitted StegTalk envelope to ClickSend and return a bounded receipt."""

    payload = build_clicksend_payload(
        envelope=envelope,
        to_number=to_number,
        from_number=from_number,
        custom_string=custom_string,
        allow_plaintext_external=allow_plaintext_external,
    )
    response = http_post(
        f"{CLICKSEND_BASE_URL}{CLICKSEND_SEND_PATH}",
        {
            "Authorization": _authorization_header(credentials),
            "Content-Type": "application/json",
            "User-Agent": "StegTalk-ClickSend/1.0",
        },
        payload,
    )

    http_code = response.get("http_code")
    response_code = response.get("response_code")
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    messages = data.get("messages") if isinstance(data, dict) else []
    first = messages[0] if isinstance(messages, list) and messages else {}
    provider_status = first.get("status") if isinstance(first, dict) else None
    accepted = http_code in {200, 201} and response_code == "SUCCESS" and provider_status != "FAILURE"

    receipt = with_receipt_identity(
        {
            "type": "external_sms_transport_receipt",
            "provider": "clicksend",
            "direction": "outbound",
            "envelope_hash": envelope["envelope_hash"],
            "to": normalize_e164(to_number),
            "provider_message_id": first.get("message_id") if isinstance(first, dict) else None,
            "provider_status": provider_status,
            "provider_response_code": response_code,
            "result": "queued" if accepted else "rejected",
            "boundary": "external_plaintext_sms",
            "recorded_at": utc_now(),
        }
    )
    if not accepted:
        raise SmsTransportError(
            f"ClickSend rejected SMS: {response_code or http_code or 'unknown response'}"
        )
    return response, receipt


def verify_inbound_clicksend(
    payload: JsonObject,
    *,
    expected_user_id: str | int | None = None,
    expected_custom_string: str | None = None,
    webhook_token_verified: bool = False,
) -> None:
    """Apply available ClickSend webhook correlation checks.

    HTTPS termination and any query-token comparison occur at the service boundary; this
    function receives the boolean result so secrets never need to enter the message object.
    """

    if not webhook_token_verified:
        raise SmsTransportError("inbound webhook token was not verified")
    if expected_user_id is not None and str(payload.get("user_id")) != str(expected_user_id):
        raise SmsTransportError("ClickSend user_id mismatch")
    if expected_custom_string is not None and payload.get("custom_string") != expected_custom_string:
        raise SmsTransportError("ClickSend custom_string mismatch")


def ingest_clicksend_sms(
    *,
    payload: JsonObject,
    receiver_entity: str,
    sender_entity: str,
    expected_user_id: str | int | None = None,
    expected_custom_string: str | None = None,
    webhook_token_verified: bool = False,
) -> tuple[JsonObject, JsonObject, JsonObject]:
    """Convert a verified inbound carrier SMS into a StegTalk external-message envelope."""

    verify_inbound_clicksend(
        payload,
        expected_user_id=expected_user_id,
        expected_custom_string=expected_custom_string,
        webhook_token_verified=webhook_token_verified,
    )
    body = str(payload.get("body") or "")
    if not body:
        raise SmsTransportError("inbound SMS body is required")

    from_number = normalize_e164(str(payload.get("from") or ""))
    to_number = normalize_e164(str(payload.get("to") or ""))
    provider_message_id = payload.get("message_id")
    original_message_id = payload.get("original_message_id")

    envelope, message_receipt = build_local_message(
        sender_entity=sender_entity,
        receiver_entity=receiver_entity,
        body=body,
        scope=SMS_SCOPE,
        metadata={
            "transport": "sms",
            "provider": "clicksend",
            "external_plaintext": True,
            "from": from_number,
            "to": to_number,
            "provider_message_id": provider_message_id,
            "original_message_id": original_message_id,
            "custom_string": payload.get("custom_string"),
            "provider_timestamp": payload.get("timestamp", payload.get("timestamp_send")),
        },
    )
    transport_receipt = with_receipt_identity(
        {
            "type": "external_sms_transport_receipt",
            "provider": "clicksend",
            "direction": "inbound",
            "envelope_hash": envelope["envelope_hash"],
            "provider_message_id": provider_message_id,
            "original_message_id": original_message_id,
            "from": from_number,
            "to": to_number,
            "result": "accepted",
            "boundary": "external_plaintext_sms",
            "recorded_at": utc_now(),
        }
    )
    transport_receipt["correlation_hash"] = stable_hash(
        {
            "envelope_hash": envelope["envelope_hash"],
            "provider_message_id": provider_message_id,
            "original_message_id": original_message_id,
            "custom_string": payload.get("custom_string"),
        }
    )
    return envelope, message_receipt, transport_receipt


def sms_transport_summary() -> JsonObject:
    return {
        "transport": "sms",
        "provider": "clicksend",
        "outbound_api": f"{CLICKSEND_BASE_URL}{CLICKSEND_SEND_PATH}",
        "inbound_mode": "https_webhook",
        "credential_authority": "TV/TVC_ONLY",
        "production_network": False,
        "security_boundary": "external_plaintext_sms",
        "requires_explicit_plaintext_admission": True,
        "supports_message_correlation": True,
    }
