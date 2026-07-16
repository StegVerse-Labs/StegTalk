from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum


class RecoveryState(StrEnum):
    QUEUED = "QUEUED"
    READY_TO_RESUME = "READY_TO_RESUME"
    RESUMED = "RESUMED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class RecoveryQueueEntry:
    message_id: str
    state: RecoveryState
    queued_at: datetime
    expires_at: datetime
    invalidated_adapters: tuple[str, ...]
    last_confirmed_chunk_index: int
    last_confirmed_custody_hash: str
    custody_spend_count: int = 1
    restored_adapter: str | None = None
    resumed_bearer_id: str | None = None

    def __post_init__(self) -> None:
        if self.queued_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("queue timestamps must be timezone-aware")
        if self.expires_at <= self.queued_at:
            raise ValueError("expires_at must follow queued_at")
        if self.last_confirmed_chunk_index < -1:
            raise ValueError("last_confirmed_chunk_index cannot be below -1")
        if self.custody_spend_count < 0:
            raise ValueError("custody_spend_count cannot be negative")
        if not self.invalidated_adapters:
            raise ValueError("at least one invalidated adapter is required")


def queue_after_path_exhaustion(
    *,
    message_id: str,
    now: datetime,
    expires_at: datetime,
    invalidated_adapters: tuple[str, ...],
    last_confirmed_chunk_index: int,
    last_confirmed_custody_hash: str,
    custody_spend_count: int = 1,
) -> RecoveryQueueEntry:
    return RecoveryQueueEntry(
        message_id=message_id,
        state=RecoveryState.QUEUED,
        queued_at=now,
        expires_at=expires_at,
        invalidated_adapters=tuple(sorted(set(invalidated_adapters))),
        last_confirmed_chunk_index=last_confirmed_chunk_index,
        last_confirmed_custody_hash=last_confirmed_custody_hash,
        custody_spend_count=custody_spend_count,
    )


def refresh_recovery_state(entry: RecoveryQueueEntry, *, now: datetime) -> RecoveryQueueEntry:
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    if entry.state in {RecoveryState.RESUMED, RecoveryState.EXPIRED}:
        return entry
    if now >= entry.expires_at:
        return replace(entry, state=RecoveryState.EXPIRED)
    return entry


def mark_permission_restored(entry: RecoveryQueueEntry, *, adapter_kind: str, now: datetime) -> RecoveryQueueEntry:
    entry = refresh_recovery_state(entry, now=now)
    if entry.state is RecoveryState.EXPIRED:
        return entry
    if entry.state is not RecoveryState.QUEUED:
        raise ValueError("only queued recovery can become ready")
    if adapter_kind not in entry.invalidated_adapters:
        raise ValueError("restored adapter was not part of the exhausted path set")
    return replace(entry, state=RecoveryState.READY_TO_RESUME, restored_adapter=adapter_kind)


def resume_from_confirmed_chunk(
    entry: RecoveryQueueEntry,
    *,
    bearer_id: str,
    now: datetime,
) -> RecoveryQueueEntry:
    entry = refresh_recovery_state(entry, now=now)
    if entry.state is RecoveryState.EXPIRED:
        return entry
    if entry.state is not RecoveryState.READY_TO_RESUME:
        raise ValueError("permission restoration is required before resume")
    if not bearer_id:
        raise ValueError("bearer_id is required")
    return replace(entry, state=RecoveryState.RESUMED, resumed_bearer_id=bearer_id)


def next_chunk_index(entry: RecoveryQueueEntry) -> int:
    if entry.state is not RecoveryState.RESUMED:
        raise ValueError("recovery has not resumed")
    return entry.last_confirmed_chunk_index + 1


def verify_recovery_continuity(before: RecoveryQueueEntry, after: RecoveryQueueEntry) -> bool:
    return (
        before.message_id == after.message_id
        and before.last_confirmed_chunk_index == after.last_confirmed_chunk_index
        and before.last_confirmed_custody_hash == after.last_confirmed_custody_hash
        and before.custody_spend_count == after.custody_spend_count
    )
