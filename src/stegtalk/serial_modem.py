from __future__ import annotations

import glob
import os
import select
import termios
import time
from dataclasses import dataclass

from .sms_transport import SmsTransportError
from .sovereign_sms_modem import ModemPort


DEFAULT_MODEM_GLOBS = (
    "/dev/ttyUSB*",
    "/dev/ttyACM*",
    "/dev/cu.usbmodem*",
    "/dev/cu.usbserial*",
)


@dataclass(frozen=True)
class SerialCandidate:
    path: str
    family: str


def discover_serial_modems(patterns: tuple[str, ...] = DEFAULT_MODEM_GLOBS) -> tuple[SerialCandidate, ...]:
    """Discover locally attached serial modem candidates without a cloud service."""

    discovered: dict[str, SerialCandidate] = {}
    for pattern in patterns:
        family = pattern.rsplit("/", 1)[-1].rstrip("*")
        for path in glob.glob(pattern):
            if os.path.exists(path):
                discovered[path] = SerialCandidate(path=path, family=family)
    return tuple(discovered[path] for path in sorted(discovered))


class PosixSerialRuntime:
    """Minimal POSIX serial binding used to produce a ModemPort.

    This intentionally avoids vendor SDKs and messaging-provider dependencies.
    The runtime configures a directly attached TTY at 115200 8N1 and exposes
    bounded line-oriented reads suitable for the existing AT-command layer.
    """

    def __init__(self, path: str, *, baud: int = 115200, timeout_seconds: float = 5.0):
        if baud != 115200:
            raise SmsTransportError("current sovereign serial binding supports 115200 baud only")
        self.path = path
        self.timeout_seconds = timeout_seconds
        self._fd: int | None = None

    def open(self) -> None:
        if self._fd is not None:
            return
        try:
            fd = os.open(self.path, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
        except OSError as exc:
            raise SmsTransportError(f"unable to open modem serial device {self.path}: {exc}") from exc

        attrs = termios.tcgetattr(fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = termios.B115200
        attrs[5] = termios.B115200
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 1
        termios.tcsetattr(fd, termios.TCSANOW, attrs)
        termios.tcflush(fd, termios.TCIOFLUSH)
        self._fd = fd

    def close(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def write(self, data: str) -> None:
        if self._fd is None:
            raise SmsTransportError("serial modem is not open")
        os.write(self._fd, data.encode("utf-8"))

    def read_until(self, expect: tuple[str, ...]) -> list[str]:
        if self._fd is None:
            raise SmsTransportError("serial modem is not open")
        deadline = time.monotonic() + self.timeout_seconds
        buffer = ""
        lines: list[str] = []
        while time.monotonic() < deadline:
            readable, _, _ = select.select([self._fd], [], [], min(0.2, max(0.0, deadline - time.monotonic())))
            if not readable:
                continue
            chunk = os.read(self._fd, 4096)
            if not chunk:
                continue
            buffer += chunk.decode("utf-8", errors="replace")
            normalized = buffer.replace("\r\n", "\n").replace("\r", "\n")
            parts = normalized.split("\n")
            buffer = parts.pop()
            for part in parts:
                line = part.strip()
                if not line:
                    continue
                lines.append(line)
                if any(line == marker or marker in line for marker in expect):
                    return lines
        raise SmsTransportError(f"serial modem timed out waiting for {expect}")

    def modem_port(self) -> ModemPort:
        return ModemPort(self.write, self.read_until)

    def __enter__(self) -> "PosixSerialRuntime":
        self.open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
