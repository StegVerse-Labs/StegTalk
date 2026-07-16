from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import hmac


@dataclass(frozen=True)
class ChunkAcknowledgement:
    message_id: str
    chunk_index: int
    custody_hash: str
    acknowledgement_hash: str


def make_chunk_acknowledgement(*, message_id: str, chunk_index: int, custody_hash: str, key: bytes) -> ChunkAcknowledgement:
    if not message_id or not custody_hash or not key:
        raise ValueError("message_id, custody_hash, and key are required")
    if chunk_index < 0:
        raise ValueError("chunk_index must be non-negative")
    payload = f"{message_id}\x1f{chunk_index}\x1f{custody_hash}".encode("utf-8")
    digest = hmac.new(key, payload, sha256).hexdigest()
    return ChunkAcknowledgement(message_id, chunk_index, custody_hash, digest)


def verify_chunk_acknowledgement(ack: ChunkAcknowledgement, *, key: bytes) -> bool:
    try:
        expected = make_chunk_acknowledgement(
            message_id=ack.message_id,
            chunk_index=ack.chunk_index,
            custody_hash=ack.custody_hash,
            key=key,
        )
    except ValueError:
        return False
    return hmac.compare_digest(expected.acknowledgement_hash, ack.acknowledgement_hash)


def verified_acknowledged_chunks(acks: tuple[ChunkAcknowledgement, ...], *, key: bytes, message_id: str, custody_hash: str) -> tuple[int, ...]:
    verified: set[int] = set()
    for ack in acks:
        if ack.message_id != message_id or ack.custody_hash != custody_hash:
            continue
        if verify_chunk_acknowledgement(ack, key=key):
            verified.add(ack.chunk_index)
    return tuple(sorted(verified))
