from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from hashlib import sha256
import json


class ActiveTransferState(StrEnum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    RESELECTING = "RESELECTING"
    RESUMED = "RESUMED"
    NO_ALTERNATE_PATH = "NO_ALTERNATE_PATH"


@dataclass(frozen=True)
class ActiveTransfer:
    message_id: str
    state: ActiveTransferState
    active_bearer_id: str
    adapter_receipt_hash: str
    observation_provenance_hash: str
    last_confirmed_custody_hash: str
    custody_spend_count: int = 1
    invalidated_adapter: str | None = None
    alternate_bearer_id: str | None = None


def _hash(payload: dict) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def provenance_hash(*, adapter_receipt_hash: str, source_event_hashes: tuple[str, ...]) -> str:
    return _hash({"adapter_receipt_hash": adapter_receipt_hash, "source_event_hashes": sorted(source_event_hashes)})


def pause_for_adapter_loss(transfer: ActiveTransfer, *, adapter_kind: str) -> ActiveTransfer:
    if transfer.state not in {ActiveTransferState.ACTIVE, ActiveTransferState.RESUMED}:
        raise ValueError("only active transfers can be paused")
    return replace(transfer, state=ActiveTransferState.PAUSED, invalidated_adapter=adapter_kind)


def begin_reselection(transfer: ActiveTransfer) -> ActiveTransfer:
    if transfer.state is not ActiveTransferState.PAUSED:
        raise ValueError("transfer must be paused before reselection")
    return replace(transfer, state=ActiveTransferState.RESELECTING)


def resume_on_alternate(transfer: ActiveTransfer, *, alternate_bearer_id: str, provenance: str) -> ActiveTransfer:
    if transfer.state is not ActiveTransferState.RESELECTING:
        raise ValueError("transfer must be reselecting")
    if not alternate_bearer_id or alternate_bearer_id == transfer.active_bearer_id:
        raise ValueError("a distinct alternate bearer is required")
    return replace(
        transfer,
        state=ActiveTransferState.RESUMED,
        active_bearer_id=alternate_bearer_id,
        alternate_bearer_id=alternate_bearer_id,
        observation_provenance_hash=provenance,
        custody_spend_count=transfer.custody_spend_count,
    )


def fail_no_alternate(transfer: ActiveTransfer) -> ActiveTransfer:
    if transfer.state is not ActiveTransferState.RESELECTING:
        raise ValueError("transfer must be reselecting")
    return replace(transfer, state=ActiveTransferState.NO_ALTERNATE_PATH, alternate_bearer_id=None)


def verify_no_duplicate_custody_spend(before: ActiveTransfer, after: ActiveTransfer) -> bool:
    return after.custody_spend_count == before.custody_spend_count and after.last_confirmed_custody_hash == before.last_confirmed_custody_hash
