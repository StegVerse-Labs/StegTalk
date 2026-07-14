from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .mobile_shell_session import persist_mobile_shell_session, restore_mobile_shell_session

ALLOWED_EVENTS = {"persist", "restore", "rejection", "integrity_failure"}


def create_session_event_receipt(*, session_id: str, event: str, result: str, previous_chain_head: str | None = None, record_hash: str | None = None, snapshot_hash: str | None = None, reason: str | None = None) -> JsonObject:
    if not session_id:
        raise ValueError("session_id is required")
    if event not in ALLOWED_EVENTS:
        raise ValueError(f"unsupported session receipt event: {event}")
    return with_receipt_identity({
        "type": "stegtalk_mobile_shell_session_event_receipt",
        "session_id": session_id,
        "event": event,
        "result": result,
        "record_hash": record_hash,
        "snapshot_hash": snapshot_hash,
        "reason": reason,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "event_at": utc_now(),
        "previous_chain_head": previous_chain_head,
    }, previous_chain_head=previous_chain_head)


def append_session_receipt(chain: list[JsonObject], receipt: JsonObject) -> list[JsonObject]:
    updated = deepcopy(chain)
    expected_previous = updated[-1]["receipt_chain_head"] if updated else None
    if receipt.get("previous_chain_head") != expected_previous:
        raise ValueError("receipt previous chain head mismatch")
    _assert_receipt_boundary(receipt)
    updated.append(deepcopy(receipt))
    verify_session_receipt_chain(updated)
    return updated


def verify_session_receipt_chain(chain: list[JsonObject]) -> JsonObject:
    previous: str | None = None
    for index, receipt in enumerate(chain):
        _assert_receipt_boundary(receipt)
        if receipt.get("previous_chain_head") != previous:
            raise ValueError(f"receipt chain discontinuity at index {index}")
        rebuilt = {key: value for key, value in receipt.items() if key not in {"id", "receipt_chain_head"}}
        rebuilt_receipt = with_receipt_identity(rebuilt, previous_chain_head=previous)
        if receipt.get("id") != rebuilt_receipt["id"]:
            raise ValueError(f"receipt identity mismatch at index {index}")
        if receipt.get("receipt_chain_head") != rebuilt_receipt["receipt_chain_head"]:
            raise ValueError(f"receipt chain head mismatch at index {index}")
        previous = receipt["receipt_chain_head"]
    return {"verified": True, "receipt_count": len(chain), "chain_head": previous, "production_ready": False, "local_only": True, "authorizing": False}


def persist_session_with_receipt(*, store_root: str | Path, shell: JsonObject, session_id: str, chain: list[JsonObject] | None = None) -> tuple[JsonObject | None, list[JsonObject]]:
    current = list(chain or [])
    previous = current[-1]["receipt_chain_head"] if current else None
    try:
        persisted = persist_mobile_shell_session(store_root=store_root, shell=shell, session_id=session_id)
    except ValueError as exc:
        receipt = create_session_event_receipt(session_id=session_id, event="rejection", result="rejected", previous_chain_head=previous, reason=str(exc))
        return None, append_session_receipt(current, receipt)
    receipt = create_session_event_receipt(session_id=session_id, event="persist", result="success", previous_chain_head=previous, record_hash=persisted["record_hash"], snapshot_hash=persisted["snapshot_hash"])
    return persisted, append_session_receipt(current, receipt)


def restore_session_with_receipt(*, store_root: str | Path, session_id: str, chain: list[JsonObject] | None = None) -> tuple[JsonObject | None, list[JsonObject]]:
    current = list(chain or [])
    previous = current[-1]["receipt_chain_head"] if current else None
    try:
        shell = restore_mobile_shell_session(store_root=store_root, session_id=session_id)
    except (ValueError, FileNotFoundError) as exc:
        event = "integrity_failure" if "integrity" in str(exc) else "rejection"
        receipt = create_session_event_receipt(session_id=session_id, event=event, result="rejected", previous_chain_head=previous, reason=str(exc))
        return None, append_session_receipt(current, receipt)
    receipt = create_session_event_receipt(session_id=session_id, event="restore", result="success", previous_chain_head=previous, snapshot_hash=stable_hash({key: value for key, value in shell.items() if key != "mobile_shell_hash"}))
    return shell, append_session_receipt(current, receipt)


def summarize_session_receipts(chain: list[JsonObject]) -> JsonObject:
    return {**verify_session_receipt_chain(chain), "events": [receipt["event"] for receipt in chain], "results": [receipt["result"] for receipt in chain], "session_ids": sorted({receipt["session_id"] for receipt in chain})}


def _assert_receipt_boundary(receipt: JsonObject) -> None:
    if receipt.get("type") != "stegtalk_mobile_shell_session_event_receipt":
        raise ValueError("unsupported receipt type")
    if receipt.get("event") not in ALLOWED_EVENTS:
        raise ValueError("unsupported receipt event")
    if receipt.get("production_ready") is not False or receipt.get("local_only") is not True or receipt.get("authorizing") is not False:
        raise ValueError("session receipt authority boundary violated")
