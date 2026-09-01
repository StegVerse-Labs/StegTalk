from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
import json

from .adapters import DiscoveryEvent


def _stable_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_adapter_receipt(events: tuple[DiscoveryEvent, ...], *, previous_receipt_hash: str | None = None) -> dict[str, object]:
    event_records = [asdict(event) for event in events]
    receipt: dict[str, object] = {
        "schema_version": "0.1.0",
        "receipt_type": "stegtalk_discovery_adapter",
        "events_hash": _stable_hash(event_records),
        "event_count": len(events),
        "adapter_kinds": sorted({event.adapter_kind.value for event in events}),
        "permission_failures": sum(event.event_type.value.startswith("permission_") for event in events),
        "previous_receipt_hash": previous_receipt_hash,
        "authority": {
            "identity_authority_granted": False,
            "execution_authority_granted": False,
            "delivery_authority_granted": False,
        },
    }
    receipt["receipt_hash"] = _stable_hash(receipt)
    return receipt


def verify_adapter_receipt(
    receipt: dict[str, object],
    *,
    events: tuple[DiscoveryEvent, ...],
    expected_previous_receipt_hash: str | None = None,
) -> bool:
    if receipt.get("receipt_type") != "stegtalk_discovery_adapter":
        return False
    if receipt.get("previous_receipt_hash") != expected_previous_receipt_hash:
        return False
    if receipt.get("events_hash") != _stable_hash([asdict(event) for event in events]):
        return False
    authority = receipt.get("authority", {})
    if not isinstance(authority, dict):
        return False
    if any(authority.get(key) is not False for key in (
        "identity_authority_granted", "execution_authority_granted", "delivery_authority_granted"
    )):
        return False
    stored_hash = receipt.get("receipt_hash")
    unhashed = {key: value for key, value in receipt.items() if key != "receipt_hash"}
    return stored_hash == _stable_hash(unhashed)
