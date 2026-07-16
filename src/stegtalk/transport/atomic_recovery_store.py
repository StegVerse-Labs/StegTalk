from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class StoreEnvelope:
    generation: int
    payload: str
    previous_envelope_hash: str | None
    envelope_hash: str


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _hash(value: object) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def make_envelope(*, generation: int, payload: str, previous_envelope_hash: str | None) -> StoreEnvelope:
    if generation < 0:
        raise ValueError("generation must be non-negative")
    if not payload:
        raise ValueError("payload is required")
    body = {
        "generation": generation,
        "payload": payload,
        "previous_envelope_hash": previous_envelope_hash,
    }
    return StoreEnvelope(generation, payload, previous_envelope_hash, _hash(body))


def verify_envelope(envelope: StoreEnvelope) -> bool:
    try:
        return make_envelope(
            generation=envelope.generation,
            payload=envelope.payload,
            previous_envelope_hash=envelope.previous_envelope_hash,
        ) == envelope
    except ValueError:
        return False


def choose_committed_slot(*, slot_a: StoreEnvelope | None, slot_b: StoreEnvelope | None, minimum_generation: int = 0) -> StoreEnvelope:
    candidates = [slot for slot in (slot_a, slot_b) if slot is not None and verify_envelope(slot)]
    candidates = [slot for slot in candidates if slot.generation >= minimum_generation]
    if not candidates:
        raise ValueError("no valid committed recovery slot")
    return sorted(candidates, key=lambda item: (item.generation, item.envelope_hash), reverse=True)[0]


def detect_torn_write(*, committed: StoreEnvelope, candidate: StoreEnvelope) -> bool:
    if not verify_envelope(committed) or not verify_envelope(candidate):
        return True
    if candidate.generation != committed.generation + 1:
        return True
    return candidate.previous_envelope_hash != committed.envelope_hash


@dataclass
class ReplayLedger:
    highest_generation_by_message: dict[str, int]

    def accept(self, *, message_id: str, envelope: StoreEnvelope) -> None:
        if not message_id:
            raise ValueError("message_id is required")
        if not verify_envelope(envelope):
            raise ValueError("invalid envelope")
        highest = self.highest_generation_by_message.get(message_id, -1)
        if envelope.generation <= highest:
            raise ValueError("restored snapshot replay detected")
        self.highest_generation_by_message[message_id] = envelope.generation
