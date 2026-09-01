from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import hmac
import json


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _hash(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


@dataclass(frozen=True)
class DeviceContinuity:
    device_id_hash: str
    continuity_epoch: int
    highest_store_generation: int


@dataclass(frozen=True)
class StoreSlot:
    slot_name: str
    generation: int
    snapshot_hash: str
    previous_slot_hash: str | None
    slot_hash: str


@dataclass(frozen=True)
class AckKey:
    key_id: str
    secret: bytes
    active_from_generation: int
    retired_after_generation: int | None = None


@dataclass(frozen=True)
class AckSetReceipt:
    message_id: str
    custody_hash: str
    store_generation: int
    acknowledged_chunks: tuple[int, ...]
    key_id: str
    signature: str


@dataclass(frozen=True)
class CrashRestartResult:
    selected_slot: str
    selected_generation: int
    missing_chunks: tuple[int, ...]
    replay_blocked: bool
    reconstruction_failed: bool


def make_slot(*, slot_name: str, generation: int, snapshot_hash: str, previous_slot_hash: str | None) -> StoreSlot:
    if slot_name not in {"A", "B"}:
        raise ValueError("slot_name must be A or B")
    if generation < 0 or not snapshot_hash:
        raise ValueError("invalid slot content")
    payload = {
        "slot_name": slot_name,
        "generation": generation,
        "snapshot_hash": snapshot_hash,
        "previous_slot_hash": previous_slot_hash,
    }
    return StoreSlot(slot_name, generation, snapshot_hash, previous_slot_hash, _hash(payload))


def verify_slot(slot: StoreSlot) -> bool:
    try:
        return make_slot(
            slot_name=slot.slot_name,
            generation=slot.generation,
            snapshot_hash=slot.snapshot_hash,
            previous_slot_hash=slot.previous_slot_hash,
        ) == slot
    except ValueError:
        return False


def select_recovery_slot(slots: tuple[StoreSlot, ...], continuity: DeviceContinuity) -> StoreSlot:
    valid = [slot for slot in slots if verify_slot(slot)]
    if not valid:
        raise ValueError("reconstruction failed: no valid atomic slot")
    selected = max(valid, key=lambda slot: (slot.generation, slot.slot_name))
    if selected.generation < continuity.highest_store_generation:
        raise ValueError("snapshot replay blocked")
    return selected


def bind_continuity(continuity: DeviceContinuity, slot: StoreSlot) -> DeviceContinuity:
    if not verify_slot(slot):
        raise ValueError("invalid slot")
    if slot.generation < continuity.highest_store_generation:
        raise ValueError("snapshot replay blocked")
    return DeviceContinuity(
        device_id_hash=continuity.device_id_hash,
        continuity_epoch=continuity.continuity_epoch,
        highest_store_generation=slot.generation,
    )


def _key_is_valid(key: AckKey, generation: int) -> bool:
    if generation < key.active_from_generation:
        return False
    return key.retired_after_generation is None or generation <= key.retired_after_generation


def sign_ack_set(
    *,
    message_id: str,
    custody_hash: str,
    store_generation: int,
    acknowledged_chunks: tuple[int, ...],
    key: AckKey,
) -> AckSetReceipt:
    chunks = tuple(sorted(set(acknowledged_chunks)))
    if chunks != acknowledged_chunks or any(index < 0 for index in chunks):
        raise ValueError("acknowledged chunks must be unique, sorted, and nonnegative")
    if not _key_is_valid(key, store_generation):
        raise ValueError("acknowledgement key is not valid for generation")
    payload = {
        "message_id": message_id,
        "custody_hash": custody_hash,
        "store_generation": store_generation,
        "acknowledged_chunks": chunks,
        "key_id": key.key_id,
    }
    signature = hmac.new(key.secret, _canonical(payload), sha256).hexdigest()
    return AckSetReceipt(message_id, custody_hash, store_generation, chunks, key.key_id, signature)


def verify_ack_set(receipt: AckSetReceipt, keys: tuple[AckKey, ...]) -> bool:
    key = next((candidate for candidate in keys if candidate.key_id == receipt.key_id), None)
    if key is None or not _key_is_valid(key, receipt.store_generation):
        return False
    expected = sign_ack_set(
        message_id=receipt.message_id,
        custody_hash=receipt.custody_hash,
        store_generation=receipt.store_generation,
        acknowledged_chunks=receipt.acknowledged_chunks,
        key=key,
    )
    return hmac.compare_digest(expected.signature, receipt.signature)


def missing_chunks(*, total_chunks: int, receipt: AckSetReceipt, keys: tuple[AckKey, ...]) -> tuple[int, ...]:
    if total_chunks <= 0 or not verify_ack_set(receipt, keys):
        raise ValueError("invalid acknowledgement set")
    if any(index >= total_chunks for index in receipt.acknowledged_chunks):
        raise ValueError("acknowledged chunk out of range")
    acknowledged = set(receipt.acknowledged_chunks)
    return tuple(index for index in range(total_chunks) if index not in acknowledged)


def demonstrate_crash_restart(
    *,
    slots: tuple[StoreSlot, ...],
    continuity: DeviceContinuity,
    total_chunks: int,
    acknowledgement_receipt: AckSetReceipt,
    keys: tuple[AckKey, ...],
) -> CrashRestartResult:
    try:
        selected = select_recovery_slot(slots, continuity)
    except ValueError as exc:
        return CrashRestartResult("", -1, (), "replay blocked" in str(exc), True)
    if selected.generation != acknowledgement_receipt.store_generation:
        raise ValueError("acknowledgement generation does not match recovered slot")
    return CrashRestartResult(
        selected_slot=selected.slot_name,
        selected_generation=selected.generation,
        missing_chunks=missing_chunks(total_chunks=total_chunks, receipt=acknowledgement_receipt, keys=keys),
        replay_blocked=False,
        reconstruction_failed=False,
    )
