from __future__ import annotations

from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_store import initialize_store, read_record, write_record
from .mobile_shell_session import inspect_mobile_shell_session, restore_mobile_shell_session
from .mobile_shell_session_receipt_store import inspect_persisted_receipt_chain, restore_receipt_chain
from .mobile_shell_session_receipts import persist_session_with_receipt
from .mobile_shell_session_receipt_store import persist_receipt_chain

CHECKPOINT_COLLECTION = "mobile_shell_session_checkpoints"


def create_managed_checkpoint(*, store_root: str | Path, shell: JsonObject, session_id: str) -> JsonObject:
    """Persist shell/session/receipt state and bind them in one local checkpoint."""
    persisted, chain = persist_session_with_receipt(store_root=store_root, shell=shell, session_id=session_id)
    if persisted is None:
        raise ValueError("managed checkpoint session persistence rejected")
    receipt_record = persist_receipt_chain(store_root=store_root, session_id=session_id, chain=chain)
    session_info = inspect_mobile_shell_session(store_root=store_root, session_id=session_id)
    receipt_info = inspect_persisted_receipt_chain(store_root=store_root, session_id=session_id)
    checkpoint = {
        "schema_version": "1.0.0",
        "checkpoint_type": "stegtalk_mobile_shell_session_managed_checkpoint",
        "session_id": session_id,
        "user_entity": shell["user_entity"],
        "mobile_shell_hash": shell["mobile_shell_hash"],
        "session_record_hash": session_info["record_hash"],
        "session_snapshot_hash": session_info["snapshot_hash"],
        "receipt_record_hash": receipt_record["record_hash"],
        "receipt_count": receipt_info["receipt_count"],
        "receipt_chain_head": receipt_info["chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "created_at": utc_now(),
    }
    checkpoint["checkpoint_hash"] = stable_hash(checkpoint)
    initialize_store(store_root)
    written = write_record(store_root, CHECKPOINT_COLLECTION, session_id, checkpoint)
    return {
        "session_id": session_id,
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "checkpoint_record_hash": written["record_hash"],
        "receipt_chain_head": checkpoint["receipt_chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


def restore_managed_checkpoint(*, store_root: str | Path, session_id: str) -> JsonObject:
    stored = read_record(store_root, CHECKPOINT_COLLECTION, session_id)
    _verify_wrapper(stored)
    checkpoint = stored["record"]
    if checkpoint.get("session_id") != session_id:
        raise ValueError("managed checkpoint session mismatch")
    expected_hash = stable_hash({k: v for k, v in checkpoint.items() if k != "checkpoint_hash"})
    if checkpoint.get("checkpoint_hash") != expected_hash:
        raise ValueError("managed checkpoint integrity check failed")
    if checkpoint.get("production_ready") is not False or checkpoint.get("local_only") is not True or checkpoint.get("authorizing") is not False:
        raise ValueError("managed checkpoint authority boundary violated")

    shell = restore_mobile_shell_session(store_root=store_root, session_id=session_id)
    session_info = inspect_mobile_shell_session(store_root=store_root, session_id=session_id)
    chain = restore_receipt_chain(store_root=store_root, session_id=session_id)
    receipt_info = inspect_persisted_receipt_chain(store_root=store_root, session_id=session_id)

    if shell.get("user_entity") != checkpoint.get("user_entity"):
        raise ValueError("managed checkpoint user mismatch")
    if shell.get("mobile_shell_hash") != checkpoint.get("mobile_shell_hash"):
        raise ValueError("managed checkpoint shell hash mismatch")
    if session_info["record_hash"] != checkpoint.get("session_record_hash"):
        raise ValueError("managed checkpoint session record drift")
    if session_info["snapshot_hash"] != checkpoint.get("session_snapshot_hash"):
        raise ValueError("managed checkpoint snapshot drift")
    if receipt_info["receipt_count"] != checkpoint.get("receipt_count"):
        raise ValueError("managed checkpoint receipt count drift")
    if receipt_info["chain_head"] != checkpoint.get("receipt_chain_head"):
        raise ValueError("managed checkpoint receipt head drift")
    return {
        "session_id": session_id,
        "shell": shell,
        "receipt_chain": chain,
        "checkpoint_hash": checkpoint["checkpoint_hash"],
        "verified": True,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def inspect_managed_checkpoint(*, store_root: str | Path, session_id: str) -> JsonObject:
    restored = restore_managed_checkpoint(store_root=store_root, session_id=session_id)
    return {
        "session_id": session_id,
        "checkpoint_hash": restored["checkpoint_hash"],
        "receipt_count": len(restored["receipt_chain"]),
        "user_entity": restored["shell"]["user_entity"],
        "verified": True,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def _verify_wrapper(stored: JsonObject) -> None:
    expected = stable_hash({k: v for k, v in stored.items() if k != "record_hash"})
    if stored.get("record_hash") != expected:
        raise ValueError("managed checkpoint wrapper integrity check failed")
    if stored.get("collection") != CHECKPOINT_COLLECTION:
        raise ValueError("managed checkpoint collection mismatch")
