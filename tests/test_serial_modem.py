from pathlib import Path

from stegtalk.serial_modem import PosixSerialRuntime, discover_serial_modems
from stegtalk.sms_transport import SmsTransportError


def test_discover_serial_modems_with_injected_glob(tmp_path: Path):
    first = tmp_path / "ttyUSB0"
    second = tmp_path / "ttyUSB1"
    first.touch()
    second.touch()

    candidates = discover_serial_modems((str(tmp_path / "ttyUSB*"),))
    assert [candidate.path for candidate in candidates] == [str(first), str(second)]
    assert all(candidate.family == "ttyUSB" for candidate in candidates)


def test_serial_runtime_fails_closed_when_device_missing(tmp_path: Path):
    runtime = PosixSerialRuntime(str(tmp_path / "missing-device"))
    try:
        runtime.open()
    except SmsTransportError as exc:
        assert "unable to open modem serial device" in str(exc)
    else:
        raise AssertionError("missing modem device must fail closed")


def test_serial_runtime_rejects_unimplemented_baud():
    try:
        PosixSerialRuntime("/dev/null", baud=9600)
    except SmsTransportError as exc:
        assert "115200" in str(exc)
    else:
        raise AssertionError("unsupported baud configuration must fail closed")
