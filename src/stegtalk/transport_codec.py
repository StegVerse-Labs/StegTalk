from __future__ import annotations

import base64
import hashlib
import math
from typing import Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now


def _b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _unb64u(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("utf-8"))


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def to_bits(data: bytes) -> list[int]:
    bits: list[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def from_bits(bits: Iterable[int]) -> bytes:
    bit_list = [1 if bit else 0 for bit in bits]
    if len(bit_list) % 8:
        raise ValueError("bit length must be a multiple of 8")
    out = bytearray()
    for offset in range(0, len(bit_list), 8):
        value = 0
        for bit in bit_list[offset : offset + 8]:
            value = (value << 1) | bit
        out.append(value)
    return bytes(out)


def manchester_encode(bits: Iterable[int]) -> list[int]:
    encoded: list[int] = []
    for bit in bits:
        encoded.extend([0, 1] if bit == 0 else [1, 0])
    return encoded


def manchester_decode(bits: Iterable[int], *, strict: bool = True) -> list[int]:
    bit_list = [1 if bit else 0 for bit in bits]
    if len(bit_list) % 2:
        if strict:
            raise ValueError("Manchester bitstream must contain pairs")
        bit_list = bit_list[:-1]
    decoded: list[int] = []
    invalid_pairs = 0
    for offset in range(0, len(bit_list), 2):
        pair = bit_list[offset : offset + 2]
        if pair == [0, 1]:
            decoded.append(0)
        elif pair == [1, 0]:
            decoded.append(1)
        else:
            invalid_pairs += 1
            if strict:
                raise ValueError(f"invalid Manchester pair at {offset}: {pair}")
    if invalid_pairs and not decoded:
        raise ValueError("Manchester stream contained no decodable pairs")
    return decoded


def chunk_payload(
    payload: bytes,
    *,
    chunk_size: int = 223,
    msg_id: str | None = None,
    ttl_seconds: int = 300,
    nonce: str | None = None,
) -> list[JsonObject]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    message_hash = sha256_hex(payload)
    resolved_msg_id = msg_id or "msg_" + message_hash[:24]
    resolved_nonce = nonce or sha256_hex(payload + resolved_msg_id.encode("utf-8"))[:24]
    total_chunks = max(1, math.ceil(len(payload) / chunk_size))
    chunks: list[JsonObject] = []
    for index in range(total_chunks):
        part = payload[index * chunk_size : (index + 1) * chunk_size]
        chunk = {
            "schema_version": "1.0.0",
            "chunk_type": "stegtalk_transport_chunk",
            "msg_id": resolved_msg_id,
            "payload_sha256": message_hash,
            "chunk_index": index,
            "total_chunks": total_chunks,
            "chunk_size": chunk_size,
            "chunk_sha256": sha256_hex(part),
            "chunk_b64u": _b64u(part),
            "nonce": resolved_nonce,
            "ttl_seconds": ttl_seconds,
            "created_at": utc_now(),
        }
        chunk["chunk_hash"] = stable_hash(chunk)
        chunks.append(chunk)
    return chunks


def reassemble_chunks(chunks: list[JsonObject]) -> bytes:
    if not chunks:
        raise ValueError("at least one chunk is required")
    msg_ids = {chunk.get("msg_id") for chunk in chunks}
    if len(msg_ids) != 1:
        raise ValueError("chunks must share one msg_id")
    total_values = {chunk.get("total_chunks") for chunk in chunks}
    if len(total_values) != 1:
        raise ValueError("chunks must share one total_chunks value")
    total_chunks = int(next(iter(total_values)))
    by_index = {int(chunk["chunk_index"]): chunk for chunk in chunks}
    missing = [index for index in range(total_chunks) if index not in by_index]
    if missing:
        raise ValueError(f"missing chunks: {missing}")
    parts: list[bytes] = []
    for index in range(total_chunks):
        chunk = by_index[index]
        part = _unb64u(str(chunk["chunk_b64u"]))
        if sha256_hex(part) != chunk.get("chunk_sha256"):
            raise ValueError(f"chunk {index} hash mismatch")
        parts.append(part)
    payload = b"".join(parts)
    expected = chunks[0].get("payload_sha256")
    if expected and sha256_hex(payload) != expected:
        raise ValueError("payload hash mismatch")
    return payload
