from __future__ import annotations

from datetime import datetime, timezone
from .entity_runtime import JsonObject, utc_now


def _parse_utc(value: str) -> datetime:
    if not value:
        raise ValueError("timestamp is required")
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class InMemoryReplayCache:
    """Small destination-side replay cache for local/runtime tests.

    The cache stores nonce/msg_id pairs that have already crossed the local
    boundary. It is intentionally simple so callers can replace it with a
    durable device store later without changing package validation semantics.
    """

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def key_for_chunk(self, chunk: JsonObject) -> str:
        return f"{chunk.get('msg_id')}:{chunk.get('nonce')}"

    def has_seen(self, chunk: JsonObject) -> bool:
        return self.key_for_chunk(chunk) in self._seen

    def mark_seen(self, chunk: JsonObject) -> None:
        self._seen.add(self.key_for_chunk(chunk))


def validate_chunk_ttl(chunk: JsonObject, *, now: str | None = None) -> None:
    ttl_seconds = int(chunk.get("ttl_seconds", 0))
    if ttl_seconds <= 0:
        raise ValueError("chunk ttl_seconds must be positive")
    created = _parse_utc(str(chunk.get("created_at", "")))
    current = _parse_utc(now or utc_now())
    age = (current - created).total_seconds()
    if age < -5:
        raise ValueError("chunk created_at is in the future")
    if age > ttl_seconds:
        raise ValueError("chunk TTL expired")


def validate_package_freshness(chunks: list[JsonObject], *, now: str | None = None) -> None:
    for chunk in chunks:
        validate_chunk_ttl(chunk, now=now)


def enforce_replay_cache(chunks: list[JsonObject], cache: InMemoryReplayCache | None) -> None:
    if cache is None or not chunks:
        return
    first = chunks[0]
    if cache.has_seen(first):
        raise ValueError("replayed transport package")
    cache.mark_seen(first)
