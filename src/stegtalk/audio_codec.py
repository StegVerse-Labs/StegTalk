from __future__ import annotations

import math
import struct
import wave
from pathlib import Path
from typing import Iterable

from .transport_codec import from_bits, to_bits

F0 = 1100.0
F1 = 1800.0
FS = 44100
SYMBOL_SECONDS = 0.040
START_WORD = bytes([0x55, 0xAA])
END_WORD = bytes([0x33, 0xCC])


def _tone(freq: float, duration: float, *, sample_rate: int = FS, amp: float = 0.3) -> list[float]:
    count = int(sample_rate * duration)
    return [amp * math.sin(2 * math.pi * freq * (index / sample_rate)) for index in range(count)]


def encode_bfsk_samples(payload: bytes, *, sample_rate: int = FS, symbol_seconds: float = SYMBOL_SECONDS) -> list[float]:
    if symbol_seconds <= 0:
        raise ValueError("symbol_seconds must be positive")
    framed = START_WORD + payload + END_WORD
    samples: list[float] = []
    for _ in range(8):
        samples.extend(_tone(1500.0, symbol_seconds, sample_rate=sample_rate))
    for bit in to_bits(framed):
        samples.extend(_tone(F1 if bit else F0, symbol_seconds, sample_rate=sample_rate))
    for _ in range(8):
        samples.extend(_tone(1500.0, symbol_seconds, sample_rate=sample_rate))
    return samples


def write_wav(path: str | Path, samples: Iterable[float], *, sample_rate: int = FS) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        for sample in samples:
            value = max(-32767, min(32767, int(sample * 32767)))
            handle.writeframesraw(struct.pack("<h", value))


def read_wav(path: str | Path) -> tuple[list[float], int]:
    with wave.open(str(path), "rb") as handle:
        frames = handle.getnframes()
        sample_rate = handle.getframerate()
        data = handle.readframes(frames)
    samples = struct.unpack("<" + "h" * frames, data)
    return [sample / 32767.0 for sample in samples], sample_rate


def _goertzel_power(samples: list[float], sample_rate: int, freq: float) -> float:
    n = len(samples)
    if n == 0:
        return 0.0
    k = int(0.5 + (n * freq) / sample_rate)
    omega = (2.0 * math.pi * k) / n
    coeff = 2.0 * math.cos(omega)
    s_prev = 0.0
    s_prev2 = 0.0
    for sample in samples:
        s_val = sample + coeff * s_prev - s_prev2
        s_prev2 = s_prev
        s_prev = s_val
    return s_prev2 * s_prev2 + s_prev * s_prev - coeff * s_prev * s_prev2


def decode_bfsk_samples(samples: list[float], *, sample_rate: int = FS, symbol_seconds: float = SYMBOL_SECONDS) -> bytes:
    width = int(symbol_seconds * sample_rate)
    if width <= 0:
        raise ValueError("symbol width must be positive")
    bits: list[int] = []
    for offset in range(0, len(samples) - width + 1, width):
        window = samples[offset : offset + width]
        p0 = _goertzel_power(window, sample_rate, F0)
        p1 = _goertzel_power(window, sample_rate, F1)
        bits.append(1 if p1 > p0 else 0)
    usable = len(bits) - (len(bits) % 8)
    by = from_bits(bits[:usable]) if usable else b""
    start = by.find(START_WORD)
    if start < 0:
        return b""
    payload_start = start + len(START_WORD)
    end = by.find(END_WORD, payload_start)
    if end < 0:
        return b""
    return by[payload_start:end]
