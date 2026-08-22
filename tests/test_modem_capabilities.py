from stegtalk.modem_capabilities import interrogate_modem, require_registered_sms_capability
from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_modem import ModemPort


class CapabilityModem:
    def __init__(self, responses):
        self.responses = list(responses)
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def read_until(self, expect):
        return self.responses.pop(0)


def test_interrogate_registered_modem_without_cloud_dependency():
    modem = CapabilityModem(
        [
            ["StegVerse LTE Modem", "OK"],
            ["+CPIN: READY", "OK"],
            ["+CREG: 0,1", "OK"],
            ["+CSQ: 19,99", "OK"],
            ["+CMGF: 1", "OK"],
        ]
    )
    caps, receipt = interrogate_modem(ModemPort(modem.write, modem.read_until))

    assert caps.identity == ("StegVerse LTE Modem",)
    assert caps.sim_ready is True
    assert caps.registration == "home"
    assert caps.signal_rssi == 19
    assert caps.sms_text_mode is True
    assert receipt["cloud_messaging_dependency"] is False
    require_registered_sms_capability(caps)
    assert modem.writes == ["ATI\r", "AT+CPIN?\r", "AT+CREG?\r", "AT+CSQ\r", "AT+CMGF?\r"]


def test_registration_denial_fails_closed():
    modem = CapabilityModem(
        [
            ["modem", "OK"],
            ["+CPIN: READY", "OK"],
            ["+CREG: 0,3", "OK"],
            ["+CSQ: 10,99", "OK"],
            ["+CMGF: 1", "OK"],
        ]
    )
    caps, _ = interrogate_modem(ModemPort(modem.write, modem.read_until))
    assert caps.registration == "denied"
    try:
        require_registered_sms_capability(caps)
    except SmsTransportError as exc:
        assert "not registered" in str(exc)
    else:
        raise AssertionError("network-registration denial must fail closed")


def test_unknown_signal_is_not_invented():
    modem = CapabilityModem(
        [
            ["modem", "OK"],
            ["+CPIN: READY", "OK"],
            ["+CREG: 0,5", "OK"],
            ["+CSQ: 99,99", "OK"],
            ["+CMGF: 1", "OK"],
        ]
    )
    caps, _ = interrogate_modem(ModemPort(modem.write, modem.read_until))
    assert caps.registration == "roaming"
    assert caps.signal_rssi is None
    require_registered_sms_capability(caps)
