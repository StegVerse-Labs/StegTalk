from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .entity_runtime import JsonObject, stable_hash, utc_now

COLLECTIONS = {
    "entity_cards": "entity_cards",
    "relationship_contracts": "relationship_contracts",
    "message_envelopes": "message_envelopes",
    "receipts": "receipts",
    "inboxes": "inboxes",
    "mobile_shell_sessions": "mobile_shell_sessions",
}


def initialize_store(root: str | Path) -> JsonObject:
    root_path = Path(root)
    root_path.mkdir(parents=True, exist_ok=True)
    for directory in COLLECTIONS.values():
        (root_path / directory).mkdir(exist_ok=True)
    manifest = {
        "schema_version": "1.1.0",
        "store_type": "stegtalk_local_store",
        "created_at": utc_now(),
        "collections": COLLECTIONS,
    }
    manifest["store_hash"] = stable_hash(manifest)
    _write_json(root_path / "store_manifest.json", manifest)
    return manifest


def write_record(root: str | Path, collection: str, record_id: str, record: JsonObject) -> JsonObject:
    if collection not in COLLECTIONS:
        raise ValueError(f"unknown collection: {collection}")
    if not record_id:
        raise ValueError("record_id is required")
    root_path = Path(root)
    record_payload = {
        "record_id": record_id,
        "collection": collection,
        "record": record,
        "written_at": utc_now(),
    }
    record_payload["record_hash"] = stable_hash(record_payload)
    path = root_path / COLLECTIONS[collection] / f"{record_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(path, record_payload)
    return record_payload


def read_record(root: str | Path, collection: str, record_id: str) -> JsonObject:
    if collection not in COLLECTIONS:
        raise ValueError(f"unknown collection: {collection}")
    path = Path(root) / COLLECTIONS[collection] / f"{record_id}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def list_records(root: str | Path, collection: str) -> list[JsonObject]:
    if collection not in COLLECTIONS:
        raise ValueError(f"unknown collection: {collection}")
    directory = Path(root) / COLLECTIONS[collection]
    if not directory.exists():
        return []
    return [json.loads(path.read_text(encoding="utf-8")) for path in sorted(directory.glob("*.json"))]


def build_store_snapshot(root: str | Path) -> JsonObject:
    root_path = Path(root)
    snapshot: dict[str, Any] = {
        "schema_version": "1.1.0",
        "snapshot_type": "stegtalk_local_store_snapshot",
        "created_at": utc_now(),
        "collections": {},
    }
    for collection in COLLECTIONS:
        records = list_records(root_path, collection)
        snapshot["collections"][collection] = {
            "count": len(records),
            "record_hashes": [record["record_hash"] for record in records],
        }
    snapshot["snapshot_hash"] = stable_hash(snapshot)
    return snapshot


def _write_json(path: Path, value: JsonObject) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
