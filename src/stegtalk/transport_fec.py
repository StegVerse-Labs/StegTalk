from __future__ import annotations

import math
from .entity_runtime import JsonObject, stable_hash, utc_now
from .transport_codec import _b64u, _unb64u, sha256_hex


def _xor_bytes(parts: list[bytes], width: int) -> bytes:
    out = bytearray(width)
    for part in parts:
        padded = part + bytes(width - len(part))
        for index, value in enumerate(padded[:width]):
            out[index] ^= value
    return bytes(out)


def chunk_payload_with_xor_fec(
    payload: bytes,
    *,
    chunk_size: int = 223,
    group_size: int = 4,
    msg_id: str | None = None,
    ttl_seconds: int = 300,
) -> list[JsonObject]:
    """Chunk payload and add one XOR parity chunk per group.

    This is not a replacement for RS(255,223). It is a repo-native operational
    recovery primitive that proves the endpoint can recover one missing chunk
    per FEC group without external dependencies. RS can replace this interface
    later.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if group_size <= 1:
        raise ValueError("group_size must be greater than one")
    payload_sha = sha256_hex(payload)
    resolved_msg_id = msg_id or "msg_" + payload_sha[:24]
    total_data_chunks = max(1, math.ceil(len(payload) / chunk_size))
    chunks: list[JsonObject] = []
    for index in range(total_data_chunks):
        part = payload[index * chunk_size : (index + 1) * chunk_size]
        group_index = index // group_size
        chunk = {
            "schema_version": "1.0.0",
            "chunk_type": "stegtalk_transport_chunk",
            "fec_profile": "xor-one-loss-v1",
            "fec_role": "data",
            "fec_group": group_index,
            "msg_id": resolved_msg_id,
            "payload_sha256": payload_sha,
            "payload_length": len(payload),
            "chunk_index": index,
            "total_chunks": total_data_chunks,
            "chunk_size": chunk_size,
            "chunk_sha256": sha256_hex(part),
            "chunk_b64u": _b64u(part),
            "ttl_seconds": ttl_seconds,
            "created_at": utc_now(),
        }
        chunk["chunk_hash"] = stable_hash(chunk)
        chunks.append(chunk)
    data_only = list(chunks)
    for group_start in range(0, total_data_chunks, group_size):
        group = data_only[group_start : group_start + group_size]
        group_index = group_start // group_size
        parts = [_unb64u(str(chunk["chunk_b64u"])) for chunk in group]
        parity = _xor_bytes(parts, chunk_size)
        parity_chunk = {
            "schema_version": "1.0.0",
            "chunk_type": "stegtalk_transport_chunk",
            "fec_profile": "xor-one-loss-v1",
            "fec_role": "parity",
            "fec_group": group_index,
            "msg_id": resolved_msg_id,
            "payload_sha256": payload_sha,
            "payload_length": len(payload),
            "chunk_index": f"parity-{group_index}",
            "total_chunks": total_data_chunks,
            "chunk_size": chunk_size,
            "covers_indexes": [int(chunk["chunk_index"]) for chunk in group],
            "chunk_sha256": sha256_hex(parity),
            "chunk_b64u": _b64u(parity),
            "ttl_seconds": ttl_seconds,
            "created_at": utc_now(),
        }
        parity_chunk["chunk_hash"] = stable_hash(parity_chunk)
        chunks.append(parity_chunk)
    return chunks


def recover_reassemble_xor_fec(chunks: list[JsonObject]) -> bytes:
    if not chunks:
        raise ValueError("at least one chunk is required")
    data_chunks = [chunk for chunk in chunks if chunk.get("fec_role", "data") == "data"]
    parity_chunks = [chunk for chunk in chunks if chunk.get("fec_role") == "parity"]
    if not data_chunks and not parity_chunks:
        raise ValueError("no recoverable chunks")
    sample = (data_chunks or parity_chunks)[0]
    total_chunks = int(sample["total_chunks"])
    chunk_size = int(sample["chunk_size"])
    by_index: dict[int, JsonObject] = {int(chunk["chunk_index"]): chunk for chunk in data_chunks}
    parity_by_group = {int(chunk["fec_group"]): chunk for chunk in parity_chunks}
    recovered: dict[int, bytes] = {}
    for index, chunk in by_index.items():
        part = _unb64u(str(chunk["chunk_b64u"]))
        if sha256_hex(part) != chunk.get("chunk_sha256"):
            raise ValueError(f"chunk {index} hash mismatch")
        recovered[index] = part
    for group_index, parity in parity_by_group.items():
        covered = [int(i) for i in parity.get("covers_indexes", [])]
        missing = [index for index in covered if index not in recovered]
        if not missing:
            continue
        if len(missing) > 1:
            raise ValueError(f"FEC group {group_index} has too many missing chunks")
        parity_bytes = _unb64u(str(parity["chunk_b64u"]))
        known = [recovered[index] for index in covered if index in recovered]
        recovered[missing[0]] = _xor_bytes([parity_bytes] + known, chunk_size).rstrip(b"\x00")
    missing_indexes = [index for index in range(total_chunks) if index not in recovered]
    if missing_indexes:
        raise ValueError(f"missing chunks: {missing_indexes}")
    payload = b"".join(recovered[index] for index in range(total_chunks))
    payload = payload[: int(sample.get("payload_length", len(payload)))]
    if sha256_hex(payload) != sample.get("payload_sha256"):
        raise ValueError("payload hash mismatch")
    return payload
