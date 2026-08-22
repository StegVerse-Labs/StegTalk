import json

import pytest

from stegtalk.serial_modem import SerialCandidate
from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_modem import ModemPort
from stegtalk.sovereign_sms_runtime import (
    persist_runtime_readiness_receipt,
    select_ready_sovereign_modem,
)


class FakeRuntime:
    def __init__(self, path, responses):
        self.path = path
        self.responses = list(responses)
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def write(self, data):
        self.writes.append(data)

    def read_until(self, expect):
        if not self.responses:
            raise AssertionError(f"unexpected modem read waiting for {expect}")
        return self.responses.pop(0)

    def modem_port(self):
        return ModemPort(self.write, self.read_until)


def ready_responses():
    return [
        ["OK"],
        ["OK"],
        ["OK"],
        ["OK"],
        ["OK"],
        ["Quectel EC25", "OK"],
        ["+CPIN: READY", "OK"],
        ["+CREG: 0,1", "OK"],
        ["+CSQ: 20,99", "OK"],
        ["+CMGF: 1", "OK"],
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


def test_select_ready_modem_rejects_unregistered_candidate_and_uses_next_ready_candidate():
    bad = SerialCandidate(path="/dev/ttyUSB0", family="ttyUSB")
    good = SerialCandidate(path="/dev/ttyUSB1", family="ttyUSB")
    responses_by_path = {
        bad.path: ready_responses()[:-3] + [["+CREG: 0,2", "OK"], ["+CSQ: 10,99", "OK"], ["+CMGF: 1", "OK"]],
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


def test_persist_runtime_readiness_receipt_appends_canonical_jsonl(tmp_path):
    receipt = {"z": 2, "a": 1, "type": "sovereign_sms_runtime_readiness_receipt"}
    destination = persist_runtime_readiness_receipt(tmp_path / "receipts" / "runtime.jsonl", receipt)
    persist_runtime_readiness_receipt(destination, {"type": "second", "value": 3})

    lines = destination.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == receipt
    assert json.loads(lines[1]) == {"type": "second", "value": 3}
    assert lines[0].startswith('{"a":1,')
