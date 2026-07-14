from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_store import COLLECTIONS, initialize_store
from .mobile_shell_session_receipts import verify_session_receipt_chain

COLLECTION = "mobile_shell_session_receipt_chains"


def persist_receipt_chain(
    *,
    store_root: str | Path,
    session_id: str,
    chain: list[JsonObject],
) -> JsonObject:
    """Persist a complete verified receipt chain using an atomic replace."""
    _validate_session_id(session_id)
    verification = verify_session_receipt_chain(chain)
    initialize_store(store_root)
    record = _build_record(session_id=session_id, chain=chain, verification=verification)
    _atomic_write_json(_chain_path(store_root, session_id), record)
    return record


def restore_receipt_chain(*, store_root: str | Path, session_id: str) -> list[JsonObject]:
    """Restore and replay a persisted chain, rejecting wrapper or chain drift."""
    _validate_session_id(session_id)
    path = _chain_path(store_root, session_id)
    record = json.loads(path.read_text(encoding="utf-8"))
    _verify_record(record, expected_session_id=session_id)
    return list(record["chain"])


def inspect_persisted_receipt_chain(*, store_root: str | Path, session_id: str) -> JsonObject:
    chain = restore_receipt_chain(store_root=store_root, session_id=session_id)
    verification = verify_session_receipt_chain(chain)
    return {
        "session_id": session_id,
        "receipt_count": verification["receipt_count"],
        "chain_head": verification["chain_head"],
        "events": [receipt["event"] for receipt in chain],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def append_receipt_atomic(
    *,
    store_root: str | Path,
    session_id: str,
    receipt: JsonObject,
    expected_chain_head: str | None = None,
) -> JsonObject:
    """Atomically append and replay a receipt with optimistic head matching.

    The caller may supply the head it observed. A mismatch fails closed instead
    of silently overwriting a concurrently advanced chain.
    """
    path = _chain_path(store_root, session_id)
    if path.exists():
        chain = restore_receipt_chain(store_root=store_root, session_id=session_id)
    else:
        initialize_store(store_root)
        chain = []
    current_head = chain[-1]["receipt_chain_head"] if chain else None
    if expected_chain_head != current_head:
        raise ValueError("persisted receipt-chain head changed")
    if receipt.get("previous_chain_head") != current_head:
        raise ValueError("receipt previous chain head does not match persisted chain")
    updated_chain = [*chain, receipt]
    return persist_receipt_chain(store_root=store_root, session_id=session_id, chain=updated_chain)


def append_and_restore_receipt(
    *,
    store_root: str | Path,
    session_id: str,
    receipt: JsonObject,
) -> tuple[JsonObject, list[JsonObject]]:
    """One-call append, persistence, restoration, and replay verification."""
    path = _chain_path(store_root, session_id)
    current_head = None
    if path.exists():
        current = restore_receipt_chain(store_root=store_root, session_id=session_id)
        current_head = current[-1]["receipt_chain_head"] if current else None
    record = append_receipt_atomic(
        store_root=store_root,
        session_id=session_id,
        receipt=receipt,
        expected_chain_head=current_head,
    )
    restored = restore_receipt_chain(store_root=store_root, session_id=session_id)
    return record, restored


def _build_record(*, session_id: str, chain: list[JsonObject], verification: JsonObject) -> JsonObject:
    payload = {
        "schema_version": "1.0.0",
        "record_type": "stegtalk_mobile_shell_session_receipt_chain",
        "session_id": session_id,
        "chain": chain,
        "receipt_count": verification["receipt_count"],
        "chain_head": verification["chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "written_at": utc_now(),
    }
    payload["record_hash"] = stable_hash(payload)
    return payload


def _verify_record(record: JsonObject, *, expected_session_id: str) -> None:
    if record.get("record_type") != "stegtalk_mobile_shell_session_receipt_chain":
        raise ValueError("unsupported persisted receipt-chain record")
    if record.get("session_id") != expected_session_id:
        raise ValueError("persisted receipt-chain session mismatch")
    if record.get("production_ready") is not False or record.get("local_only") is not True or record.get("authorizing") is not False:
        raise ValueError("persisted receipt-chain authority boundary violated")
    expected_hash = stable_hash({key: value for key, value in record.items() if key != "record_hash"})
    if record.get("record_hash") != expected_hash:
        raise ValueError("persisted receipt-chain integrity check failed")
    verification = verify_session_receipt_chain(list(record.get("chain", [])))
    if record.get("receipt_count") != verification["receipt_count"]:
        raise ValueError("persisted receipt-chain count mismatch")
    if record.get("chain_head") != verification["chain_head"]:
        raise ValueError("persisted receipt-chain head mismatch")


def _chain_path(store_root: str | Path, session_id: str) -> Path:
    _validate_session_id(session_id)
    return Path(store_root) / COLLECTIONS[COLLECTION] / f"{session_id}.json"


def _validate_session_id(session_id: str) -> None:
    if not session_id:
        raise ValueError("session_id is required")
    if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in session_id):
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
