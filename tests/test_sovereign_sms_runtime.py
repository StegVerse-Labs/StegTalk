import json

import pytest

from stegtalk.message_envelope import build_local_message
from stegtalk.serial_modem import SerialCandidate
from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_modem import ModemPort
from stegtalk.sovereign_sms_runtime import (
    SovereignSmsSession,
    persist_runtime_readiness_receipt,
    select_ready_sovereign_modem,
)


class FakeRuntime:
    def __init__(self, path, responses):
        self.path = path
        self.responses = list(responses)
        self.writes = []
        self.is_open = False

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return None

    def write(self, data):
        if not self.is_open:
            raise SmsTransportError("fake serial runtime is closed")
        self.writes.append(data)

    def read_until(self, expect):
        if not self.responses:
            raise AssertionError(f"unexpected modem read waiting for {expect}")
        return self.responses.pop(0)

    def modem_port(self):
        return ModemPort(self.write, self.read_until)


def interrogation_responses(*, registration="1"):
    return [
        ["Quectel EC25", "OK"],
        ["+CPIN: READY", "OK"],
        [f"+CREG: 0,{registration}", "OK"],
        ["+CSQ: 20,99", "OK"],
        ["+CMGF: 1", "OK"],
    ]


def ready_responses():
    return [
        ["OK"],
        ["OK"],
        ["OK"],
        ["OK"],
        ["OK"],
        *interrogation_responses(),
    ]


def test_select_ready_modem_composes_discovery_initialization_and_registration_gate():
    candidate = SerialCandidate(path="/dev/ttyUSB2", family="ttyUSB")
    runtimes = []

    def factory(path):
        runtime = FakeRuntime(path, ready_responses())
        runtimes.append(runtime)
        return runtime

    ready = select_ready_sovereign_modem(candidates=[candidate], runtime_factory=factory)

    assert ready.candidate == candidate
    assert ready.capabilities.sim_ready is True
    assert ready.capabilities.registration == "home"
    assert ready.capabilities.sms_text_mode is True
    assert ready.readiness_receipt["delivery_proven"] is False
    assert ready.readiness_receipt["production_active"] is False
    assert ready.readiness_receipt["cloud_messaging_dependency"] is False
    assert "AT\r" in runtimes[0].writes
    assert "ATI\r" in runtimes[0].writes
    assert "AT+CREG?\r" in runtimes[0].writes
    assert runtimes[0].is_open is False


def test_select_ready_modem_rejects_unregistered_candidate_and_uses_next_ready_candidate():
    bad = SerialCandidate(path="/dev/ttyUSB0", family="ttyUSB")
    good = SerialCandidate(path="/dev/ttyUSB1", family="ttyUSB")
    responses_by_path = {
        bad.path: [["OK"], ["OK"], ["OK"], ["OK"], ["OK"], *interrogation_responses(registration="2")],
        good.path: ready_responses(),
    }

    def factory(path):
        return FakeRuntime(path, responses_by_path[path])

    ready = select_ready_sovereign_modem(candidates=[bad, good], runtime_factory=factory)

    assert ready.candidate.path == good.path
    assert ready.readiness_receipt["prior_candidate_failures"][0]["candidate"] == bad.path
    assert "not registered" in ready.readiness_receipt["prior_candidate_failures"][0]["reason"]


def test_select_ready_modem_fails_closed_when_no_candidate_is_available():
    with pytest.raises(SmsTransportError, match="no local serial modem candidates"):
        select_ready_sovereign_modem(candidates=[])


def test_live_session_refreshes_registration_immediately_before_submission():
    candidate = SerialCandidate(path="/dev/ttyUSB4", family="ttyUSB")
    responses = [
        *ready_responses(),
        *interrogation_responses(),
        ["OK"],
        [">"],
        ["+CMGS: 77", "OK"],
    ]
    runtime = FakeRuntime(candidate.path, responses)
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="governed hello",
    )

    with SovereignSmsSession(candidate, runtime_factory=lambda path: runtime) as session:
        result, transport_receipt, session_receipt = session.send(
            envelope=envelope,
            to_number="+15551234567",
            allow_plaintext_external=True,
        )
        assert runtime.is_open is True
        assert result.reference == "77"
        assert transport_receipt["result"] == "submitted"
        assert session_receipt["registration_at_submission"] == "home"
        assert session_receipt["delivery_proven"] is False
        assert runtime.writes.count("AT+CREG?\r") == 2
        assert any('AT+CMGS="+15551234567"' in write for write in runtime.writes)

    assert runtime.is_open is False


def test_live_session_blocks_send_if_registration_changes_after_initial_readiness():
    candidate = SerialCandidate(path="/dev/ttyUSB5", family="ttyUSB")
    responses = [*ready_responses(), *interrogation_responses(registration="2")]
    runtime = FakeRuntime(candidate.path, responses)
    envelope, _ = build_local_message(
        sender_entity="entity:stegverse",
        receiver_entity="external:sms:+15551234567",
        body="must not submit",
    )

    with SovereignSmsSession(candidate, runtime_factory=lambda path: runtime) as session:
        with pytest.raises(SmsTransportError, match="not registered"):
            session.send(
                envelope=envelope,
                to_number="+15551234567",
                allow_plaintext_external=True,
            )
        assert not any("AT+CMGS=" in write for write in runtime.writes)


def test_persist_runtime_readiness_receipt_appends_canonical_jsonl(tmp_path):
    receipt = {"z": 2, "a": 1, "type": "sovereign_sms_runtime_readiness_receipt"}
    destination = persist_runtime_readiness_receipt(tmp_path / "receipts" / "runtime.jsonl", receipt)
    persist_runtime_readiness_receipt(destination, {"type": "second", "value": 3})

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == receipt
    assert json.loads(lines[1]) == {"type": "second", "value": 3}
    assert lines[0].startswith('{"a":1,')
