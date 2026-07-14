from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .local_store import COLLECTIONS, initialize_store
from .mobile_shell_session_checkpoint_rotation import inspect_checkpoint_history, restore_latest_valid_checkpoint

COLLECTION = "mobile_shell_session_recovery_receipts"


def recover_session_with_receipt(*, store_root: str | Path, session_id: str) -> tuple[JsonObject | None, JsonObject]:
    """Recover the newest valid retained checkpoint and persist a payload-free receipt."""
    _validate_session_id(session_id)
    previous = _load_receipt_history(store_root, session_id)
    previous_head = previous[-1]["receipt_chain_head"] if previous else None
    try:
        history = inspect_checkpoint_history(store_root=store_root, session_id=session_id)
        recovered = restore_latest_valid_checkpoint(store_root=store_root, session_id=session_id)
        receipt = _build_receipt(
            session_id=session_id,
            result="recovered",
            selected_generation=recovered["generation"],
            fallback_used=recovered["fallback_used"],
            rejected_generations=recovered["rejected_generations"],
            retained_generations=history["retained_generations"],
            history_hash=history["history_hash"],
            checkpoint_hash=recovered["checkpoint_hash"],
            receipt_chain_head=_receipt_chain_head(recovered["receipt_chain"]),
            previous_chain_head=previous_head,
        )
    except (ValueError, FileNotFoundError) as exc:
        recovered = None
        receipt = _build_receipt(
            session_id=session_id,
            result="failed",
            selected_generation=None,
            fallback_used=False,
            rejected_generations=[],
            retained_generations=[],
            history_hash=None,
            checkpoint_hash=None,
            receipt_chain_head=None,
            previous_chain_head=previous_head,
            reason=str(exc),
        )
    _persist_receipt_history(store_root, session_id, [*previous, receipt])
    return recovered, receipt


def restore_recovery_receipts(*, store_root: str | Path, session_id: str) -> list[JsonObject]:
    history = _load_receipt_history(store_root, session_id)
    _verify_recovery_receipt_chain(history)
    return history


def inspect_recovery_receipts(*, store_root: str | Path, session_id: str) -> JsonObject:
    receipts = restore_recovery_receipts(store_root=store_root, session_id=session_id)
    return {
        "session_id": session_id,
        "receipt_count": len(receipts),
        "results": [receipt["result"] for receipt in receipts],
        "selected_generations": [receipt["selected_generation"] for receipt in receipts],
        "fallback_count": sum(1 for receipt in receipts if receipt["fallback_used"]),
        "chain_head": receipts[-1]["receipt_chain_head"] if receipts else None,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def _build_receipt(*, session_id: str, result: str, selected_generation: int | None, fallback_used: bool, rejected_generations: list[JsonObject], retained_generations: list[int], history_hash: str | None, checkpoint_hash: str | None, receipt_chain_head: str | None, previous_chain_head: str | None, reason: str | None = None) -> JsonObject:
    return with_receipt_identity({
        "type": "stegtalk_mobile_shell_session_recovery_receipt",
        "session_id": session_id,
        "result": result,
        "selected_generation": selected_generation,
        "fallback_used": fallback_used,
        "rejected_generations": rejected_generations,
        "retained_generations": retained_generations,
        "checkpoint_history_hash": history_hash,
        "selected_checkpoint_hash": checkpoint_hash,
        "selected_receipt_chain_head": receipt_chain_head,
        "reason": reason,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "recovered_at": utc_now(),
        "previous_chain_head": previous_chain_head,
    }, previous_chain_head=previous_chain_head)


def _verify_recovery_receipt_chain(receipts: list[JsonObject]) -> None:
    previous = None
    for index, receipt in enumerate(receipts):
        if receipt.get("type") != "stegtalk_mobile_shell_session_recovery_receipt":
            raise ValueError("unsupported recovery receipt type")
        if receipt.get("previous_chain_head") != previous:
            raise ValueError(f"recovery receipt chain discontinuity at index {index}")
        if receipt.get("production_ready") is not False or receipt.get("local_only") is not True or receipt.get("authorizing") is not False:
            raise ValueError("recovery receipt authority boundary violated")
        rebuilt = {key: value for key, value in receipt.items() if key not in {"id", "receipt_chain_head"}}
        expected = with_receipt_identity(rebuilt, previous_chain_head=previous)
        if receipt.get("id") != expected["id"] or receipt.get("receipt_chain_head") != expected["receipt_chain_head"]:
            raise ValueError(f"recovery receipt integrity check failed at index {index}")
        previous = receipt["receipt_chain_head"]


def _load_receipt_history(store_root: str | Path, session_id: str) -> list[JsonObject]:
    path = _receipt_path(store_root, session_id)
    if not path.exists():
        initialize_store(store_root)
        return []
    record = json.loads(path.read_text(encoding="utf-8"))
    expected_hash = stable_hash({key: value for key, value in record.items() if key != "record_hash"})
    if record.get("record_hash") != expected_hash:
        raise ValueError("recovery receipt history integrity check failed")
    if record.get("session_id") != session_id:
        raise ValueError("recovery receipt history session mismatch")
    receipts = list(record.get("receipts", []))
    _verify_recovery_receipt_chain(receipts)
    return receipts


def _persist_receipt_history(store_root: str | Path, session_id: str, receipts: list[JsonObject]) -> None:
    _verify_recovery_receipt_chain(receipts)
    record = {
        "schema_version": "1.0.0",
        "record_type": "stegtalk_mobile_shell_session_recovery_receipt_history",
        "session_id": session_id,
        "receipts": receipts,
        "receipt_count": len(receipts),
        "chain_head": receipts[-1]["receipt_chain_head"] if receipts else None,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "updated_at": utc_now(),
    }
    record["record_hash"] = stable_hash(record)
    _atomic_write_json(_receipt_path(store_root, session_id), record)


def _receipt_chain_head(chain: list[JsonObject]) -> str | None:
    return chain[-1]["receipt_chain_head"] if chain else None


def _receipt_path(store_root: str | Path, session_id: str) -> Path:
    _validate_session_id(session_id)
    return Path(store_root) / COLLECTIONS[COLLECTION] / f"{session_id}.json"


def _validate_session_id(session_id: str) -> None:
    if not session_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in session_id):
        raise ValueError("session_id contains unsupported characters")


def _atomic_write_json(path: Path, value: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
