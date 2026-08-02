from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .local_store import COLLECTIONS, read_record, write_record

REQUEST_STATES = {
    "RECEIVED",
    "IDENTITY_VERIFICATION_REQUIRED",
    "VERIFIED",
    "PROCESSING_RESTRICTED",
    "INVENTORY_COMPLETE",
    "DELETION_IN_PROGRESS",
    "PROCESSOR_PROPAGATION_PENDING",
    "COMPLETED",
    "PARTIALLY_DENIED",
    "DENIED",
    "APPEAL_OPEN",
    "CHANNEL_FAILED",
}

DEFAULT_RETAINED_COLLECTIONS = {
    "receipts",
    "personal_data_control_requests",
    "personal_data_control_receipts",
}


def create_personal_data_request(
    *,
    request_id: str,
    account_id: str,
    requested_actions: Iterable[str] = ("access", "restrict", "delete"),
    identity_verified: bool = False,
) -> JsonObject:
    if not request_id or not account_id:
        raise ValueError("request_id and account_id are required")
    actions = sorted({str(action).strip().lower() for action in requested_actions if str(action).strip()})
    if not actions:
        raise ValueError("at least one requested action is required")
    request: JsonObject = {
        "schema_version": "1.0.0",
        "request_type": "stegtalk_personal_data_control",
        "request_id": request_id,
        "account_id": account_id,
        "requested_actions": actions,
        "state": "VERIFIED" if identity_verified else "IDENTITY_VERIFICATION_REQUIRED",
        "identity_verified": identity_verified,
        "processing_restricted": False,
        "inventory": [],
        "retained_data": [],
        "processor_propagation": {"state": "NOT_REQUIRED", "processors": []},
        "appeal": {"available": True, "state": "NOT_OPEN"},
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    request["request_hash"] = stable_hash(request)
    return request


def verify_request_identity(request: JsonObject, *, verification_ref: str) -> JsonObject:
    if not verification_ref:
        raise ValueError("verification_ref is required")
    updated = _copy_request(request)
    updated["identity_verified"] = True
    updated["identity_verification_ref"] = verification_ref
    updated["state"] = "VERIFIED"
    return _rehash(updated)


def restrict_processing(request: JsonObject) -> JsonObject:
    _require_verified(request)
    updated = _copy_request(request)
    updated["processing_restricted"] = True
    updated["state"] = "PROCESSING_RESTRICTED"
    return _rehash(updated)


def inventory_local_account_data(root: str | Path, request: JsonObject) -> JsonObject:
    _require_verified(request)
    account_id = request["account_id"]
    inventory: list[JsonObject] = []
    root_path = Path(root)
    for collection, directory in COLLECTIONS.items():
        collection_path = root_path / directory
        if not collection_path.exists():
            continue
        for path in sorted(collection_path.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            if _contains_account_id(payload, account_id):
                inventory.append(
                    {
                        "collection": collection,
                        "record_id": payload.get("record_id", path.stem),
                        "record_hash": payload.get("record_hash"),
                        "path": str(path.relative_to(root_path)),
                    }
                )
    updated = _copy_request(request)
    updated["inventory"] = inventory
    updated["state"] = "INVENTORY_COMPLETE"
    return _rehash(updated)


def execute_local_deletion(
    root: str | Path,
    request: JsonObject,
    *,
    retained_collections: Iterable[str] = DEFAULT_RETAINED_COLLECTIONS,
    processor_refs: Iterable[str] = (),
) -> tuple[JsonObject, JsonObject]:
    _require_verified(request)
    if request.get("state") != "INVENTORY_COMPLETE":
        raise ValueError("local deletion requires an INVENTORY_COMPLETE request")

    root_path = Path(root)
    retained = set(retained_collections)
    deleted: list[JsonObject] = []
    retained_data: list[JsonObject] = []

    for item in request.get("inventory", []):
        collection = item["collection"]
        record_id = item["record_id"]
        if collection in retained:
            retained_data.append(
                {
                    **item,
                    "basis": "continuity_or_request_audit_required",
                }
            )
            continue
        path = root_path / COLLECTIONS[collection] / f"{record_id}.json"
        if path.exists():
            path.unlink()
            deleted.append(item)

    processors = sorted({ref for ref in processor_refs if ref})
    propagation_state = "PROCESSOR_PROPAGATION_PENDING" if processors else "NOT_REQUIRED"
    completion_state = "PROCESSOR_PROPAGATION_PENDING" if processors else "COMPLETED"

    updated = _copy_request(request)
    updated["state"] = completion_state
    updated["retained_data"] = retained_data
    updated["deleted_records"] = deleted
    updated["processor_propagation"] = {
        "state": propagation_state,
        "processors": [{"processor_ref": ref, "state": "PENDING"} for ref in processors],
    }
    updated = _rehash(updated)

    receipt = with_receipt_identity(
        {
            "type": "personal_data_control_completion_receipt",
            "request_id": updated["request_id"],
            "account_id_hash": stable_hash(updated["account_id"]),
            "request_hash": updated["request_hash"],
            "result_state": completion_state,
            "deleted_record_refs": [stable_hash(item) for item in deleted],
            "retained_record_refs": [stable_hash(item) for item in retained_data],
            "processor_propagation_state": propagation_state,
            "authority": {
                "external_deletion": False,
                "legal_adjudication": False,
                "processor_completion": False,
            },
        }
    )
    write_record(root_path, "personal_data_control_requests", updated["request_id"], updated)
    write_record(root_path, "personal_data_control_receipts", receipt["id"], receipt)
    return updated, receipt


def mark_processor_propagation(
    request: JsonObject,
    *,
    processor_ref: str,
    state: str,
    evidence_ref: str,
) -> JsonObject:
    if state not in {"COMPLETE", "FAILED", "RETRY", "REVIEW_REQUIRED"}:
        raise ValueError("unsupported processor propagation state")
    updated = _copy_request(request)
    processors = list(updated.get("processor_propagation", {}).get("processors", []))
    found = False
    for processor in processors:
        if processor.get("processor_ref") == processor_ref:
            processor.update({"state": state, "evidence_ref": evidence_ref})
            found = True
    if not found:
        raise ValueError("processor_ref is not part of this request")
    pending = [p for p in processors if p.get("state") not in {"COMPLETE", "FAILED"}]
    failed = [p for p in processors if p.get("state") == "FAILED"]
    updated["processor_propagation"] = {
        "state": "COMPLETE" if not pending and not failed else "PROCESSOR_PROPAGATION_PENDING",
        "processors": processors,
    }
    if not pending and not failed:
        updated["state"] = "COMPLETED"
    return _rehash(updated)


def _require_verified(request: JsonObject) -> None:
    if not request.get("identity_verified"):
        raise ValueError("identity verification is required")
    if request.get("state") not in REQUEST_STATES:
        raise ValueError("request state is invalid")


def _contains_account_id(value: Any, account_id: str) -> bool:
    if isinstance(value, dict):
        return any(
            (key == "account_id" and item == account_id) or _contains_account_id(item, account_id)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_account_id(item, account_id) for item in value)
    return False


def _copy_request(request: JsonObject) -> JsonObject:
    return json.loads(json.dumps(request))


def _rehash(request: JsonObject) -> JsonObject:
    request["updated_at"] = utc_now()
    request.pop("request_hash", None)
    request["request_hash"] = stable_hash(request)
    return request
