from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_store import COLLECTIONS, initialize_store
from .mobile_shell_session_checkpoint import create_managed_checkpoint, restore_managed_checkpoint
from .mobile_shell_session_receipts import verify_session_receipt_chain

COLLECTION = "mobile_shell_session_checkpoint_history"
DEFAULT_RETENTION = 3


def rotate_managed_checkpoint(*, store_root: str | Path, shell: JsonObject, session_id: str, retention: int = DEFAULT_RETENTION) -> JsonObject:
    if retention < 1:
        raise ValueError("checkpoint retention must be at least 1")
    created = create_managed_checkpoint(store_root=store_root, shell=shell, session_id=session_id)
    restored = restore_managed_checkpoint(store_root=store_root, session_id=session_id)
    history = _load_history(store_root, session_id)
    generation = (history[-1]["generation"] + 1) if history else 1
    entry = {
        "schema_version": "1.0.0",
        "entry_type": "stegtalk_mobile_shell_session_checkpoint_history_entry",
        "session_id": session_id,
        "generation": generation,
        "checkpoint_hash": created["checkpoint_hash"],
        "mobile_shell_hash": restored["shell"]["mobile_shell_hash"],
        "shell": restored["shell"],
        "receipt_chain": restored["receipt_chain"],
        "receipt_chain_head": created["receipt_chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "created_at": utc_now(),
    }
    entry["entry_hash"] = stable_hash(entry)
    updated = [*history, entry][-retention:]
    record = _build_history_record(session_id=session_id, retention=retention, entries=updated)
    _atomic_write_json(_history_path(store_root, session_id), record)
    return {
        "session_id": session_id,
        "generation": generation,
        "retained_generations": [item["generation"] for item in updated],
        "current_checkpoint_hash": created["checkpoint_hash"],
        "history_hash": record["history_hash"],
        "manual_tasks_required": [],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def restore_latest_valid_checkpoint(*, store_root: str | Path, session_id: str) -> JsonObject:
    record = _read_history_record(store_root, session_id)
    failures: list[JsonObject] = []
    for entry in reversed(record["entries"]):
        try:
            _verify_entry(entry, expected_session_id=session_id)
        except ValueError as exc:
            failures.append({"generation": entry.get("generation"), "reason": str(exc)})
            continue
        return {
            "session_id": session_id,
            "generation": entry["generation"],
            "shell": entry["shell"],
            "receipt_chain": entry["receipt_chain"],
            "checkpoint_hash": entry["checkpoint_hash"],
            "fallback_used": entry["generation"] != record["entries"][-1]["generation"],
            "rejected_generations": failures,
            "verified": True,
            "production_ready": False,
            "local_only": True,
            "authorizing": False,
        }
    raise ValueError("no valid retained managed checkpoint")


def inspect_checkpoint_history(*, store_root: str | Path, session_id: str) -> JsonObject:
    record = _read_history_record(store_root, session_id)
    return {
        "session_id": session_id,
        "retention": record["retention"],
        "retained_generations": [entry["generation"] for entry in record["entries"]],
        "history_hash": record["history_hash"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def _build_history_record(*, session_id: str, retention: int, entries: list[JsonObject]) -> JsonObject:
    record = {
        "schema_version": "1.0.0",
        "record_type": "stegtalk_mobile_shell_session_checkpoint_history",
        "session_id": session_id,
        "retention": retention,
        "entries": entries,
        "entry_count": len(entries),
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "updated_at": utc_now(),
    }
    record["history_hash"] = stable_hash(record)
    return record


def _read_history_record(store_root: str | Path, session_id: str) -> JsonObject:
    path = _history_path(store_root, session_id)
    record = json.loads(path.read_text(encoding="utf-8"))
    expected = stable_hash({key: value for key, value in record.items() if key != "history_hash"})
    if record.get("history_hash") != expected:
        raise ValueError("checkpoint history integrity check failed")
    if record.get("session_id") != session_id:
        raise ValueError("checkpoint history session mismatch")
    if record.get("entry_count") != len(record.get("entries", [])):
        raise ValueError("checkpoint history count mismatch")
    if record.get("production_ready") is not False or record.get("local_only") is not True or record.get("authorizing") is not False:
        raise ValueError("checkpoint history authority boundary violated")
    return record


def _load_history(store_root: str | Path, session_id: str) -> list[JsonObject]:
    path = _history_path(store_root, session_id)
    if not path.exists():
        initialize_store(store_root)
        return []
    return list(_read_history_record(store_root, session_id)["entries"])


def _verify_entry(entry: JsonObject, *, expected_session_id: str) -> None:
    if entry.get("session_id") != expected_session_id:
        raise ValueError("checkpoint entry session mismatch")
    expected = stable_hash({key: value for key, value in entry.items() if key != "entry_hash"})
    if entry.get("entry_hash") != expected:
        raise ValueError("checkpoint entry integrity check failed")
    shell = entry.get("shell", {})
    shell_hash = stable_hash({key: value for key, value in shell.items() if key != "mobile_shell_hash"})
    if shell.get("mobile_shell_hash") != shell_hash or entry.get("mobile_shell_hash") != shell_hash:
        raise ValueError("checkpoint entry shell integrity check failed")
    verification = verify_session_receipt_chain(list(entry.get("receipt_chain", [])))
    if verification["chain_head"] != entry.get("receipt_chain_head"):
        raise ValueError("checkpoint entry receipt head mismatch")
    if entry.get("production_ready") is not False or entry.get("local_only") is not True or entry.get("authorizing") is not False:
        raise ValueError("checkpoint entry authority boundary violated")


def _history_path(store_root: str | Path, session_id: str) -> Path:
    if not session_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in session_id):
        raise ValueError("session_id contains unsupported characters")
    return Path(store_root) / COLLECTIONS[COLLECTION] / f"{session_id}.json"


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
