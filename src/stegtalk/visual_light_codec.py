from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .transport_codec import from_bits, manchester_decode, manchester_encode, to_bits

START_WORD = bytes([0x55, 0xAA])
END_WORD = bytes([0x33, 0xCC])


def encode_light_bits(payload: bytes, *, preamble_ones: int = 32, preamble_zeros: int = 32) -> list[int]:
    if preamble_ones < 0 or preamble_zeros < 0:
        raise ValueError("preamble lengths must be non-negative")
    preamble = [1] * preamble_ones + [0] * preamble_zeros
    framed_bits = preamble + to_bits(START_WORD + payload + END_WORD)
    return manchester_encode(framed_bits)


def decode_light_bits(bits: Iterable[int], *, strict: bool = False) -> bytes:
    decoded_bits = manchester_decode(bits, strict=strict)
    framed = from_bits(decoded_bits[-(len(decoded_bits) // 8 * 8) :])
    start = framed.find(START_WORD)
    if start < 0:
        return b""
    payload_start = start + len(START_WORD)
    end = framed.find(END_WORD, payload_start)
    if end < 0:
        return b""
    return framed[payload_start:end]


def write_light_timing_csv(path: str | Path, bits: Iterable[int], *, bit_ms: float = 40.0) -> None:
    if bit_ms <= 0:
        raise ValueError("bit_ms must be positive")
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["index", "time_ms", "level"])
        time_ms = 0.0
        for index, bit in enumerate(bits):
            writer.writerow([index, f"{time_ms:.3f}", 1 if bit else 0])
            time_ms += bit_ms


def read_light_timing_csv(path: str | Path) -> list[int]:
    values: list[float] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        for row in reader:
            if not row:
                continue
            values.append(float(row[-1]))
    if not values:
        return []
    threshold = (min(values) + max(values)) / 2.0
    return [1 if value >= threshold else 0 for value in values]
