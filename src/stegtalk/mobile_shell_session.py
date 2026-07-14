from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .contact_routing import build_contact_index
from .entity_runtime import JsonObject, stable_hash, utc_now
from .local_store import initialize_store, read_record, write_record

SESSION_COLLECTION = "mobile_shell_sessions"


def persist_mobile_shell_session(
    *,
    store_root: str | Path,
    shell: JsonObject,
    session_id: str,
) -> JsonObject:
    """Persist a local mobile-shell snapshot through the StegTalk local store."""
    if not session_id:
        raise ValueError("session_id is required")
    _assert_local_authority_boundary(shell)
    initialize_store(store_root)
    snapshot = _build_snapshot(shell=shell, session_id=session_id)
    written = write_record(store_root, SESSION_COLLECTION, session_id, snapshot)
    return {
        "schema_version": "1.0.0",
        "receipt_type": "stegtalk_mobile_shell_session_persist_receipt",
        "session_id": session_id,
        "record_hash": written["record_hash"],
        "snapshot_hash": snapshot["snapshot_hash"],
        "production_ready": False,
        "local_only": True,
        "persisted_at": written["written_at"],
    }


def restore_mobile_shell_session(
    *,
    store_root: str | Path,
    session_id: str,
) -> JsonObject:
    """Restore and verify a local mobile-shell snapshot, failing closed on drift."""
    stored = read_record(store_root, SESSION_COLLECTION, session_id)
    snapshot = stored["record"]
    expected_snapshot_hash = snapshot.get("snapshot_hash")
    actual_snapshot_hash = stable_hash(
        {key: value for key, value in snapshot.items() if key != "snapshot_hash"}
    )
    if expected_snapshot_hash != actual_snapshot_hash:
        raise ValueError("mobile shell session snapshot integrity check failed")

    shell = deepcopy(snapshot["shell"])
    expected_shell_hash = shell.get("mobile_shell_hash")
    actual_shell_hash = stable_hash(
        {key: value for key, value in shell.items() if key != "mobile_shell_hash"}
    )
    if expected_shell_hash != actual_shell_hash:
        raise ValueError("mobile shell state integrity check failed")

    _assert_local_authority_boundary(shell)
    contacts = list(shell.get("shell_state", {}).get("contacts", []))
    rebuilt_index = build_contact_index(contacts)
    if shell.get("contact_index") != rebuilt_index:
        raise ValueError("mobile shell contact index reconstruction mismatch")
    return shell


def inspect_mobile_shell_session(
    *,
    store_root: str | Path,
    session_id: str,
) -> JsonObject:
    stored = read_record(store_root, SESSION_COLLECTION, session_id)
    snapshot = stored["record"]
    return {
        "session_id": session_id,
        "record_hash": stored["record_hash"],
        "snapshot_hash": snapshot["snapshot_hash"],
        "user_entity": snapshot["user_entity"],
        "contact_count": len(snapshot["shell"].get("shell_state", {}).get("contacts", [])),
        "inbox_count": len(snapshot["shell"].get("inbox", {}).get("items", [])),
        "discovery_result_count": len(
            snapshot["shell"].get("shell_state", {}).get("discovery_results", [])
        ),
        "production_ready": False,
        "local_only": True,
    }


def _build_snapshot(*, shell: JsonObject, session_id: str) -> JsonObject:
    snapshot = {
        "schema_version": "1.0.0",
        "snapshot_type": "stegtalk_mobile_shell_session_snapshot",
        "session_id": session_id,
        "user_entity": shell["user_entity"],
        "shell": deepcopy(shell),
        "production_ready": False,
        "local_only": True,
        "created_at": utc_now(),
    }
    snapshot["snapshot_hash"] = stable_hash(snapshot)
    return snapshot


def _assert_local_authority_boundary(shell: JsonObject) -> None:
    if shell.get("production_ready") is not False:
        raise ValueError("mobile shell session must remain non-production")
    if shell.get("mode") != "local_prototype":
        raise ValueError("mobile shell session must remain local_prototype")
    authority = shell.get("authority", {})
    if any(
        authority.get(key) is not False
        for key in (
            "network_authority",
            "execution_authority",
            "external_account_authority",
            "native_platform_authority",
        )
    ):
        raise ValueError("mobile shell session authority boundary violated")
