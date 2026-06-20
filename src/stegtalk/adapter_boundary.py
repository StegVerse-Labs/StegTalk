from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity


def create_adapter_handoff(*, adapter_name: str, envelope: JsonObject) -> JsonObject:
    if not adapter_name:
        raise ValueError("adapter_name is required")
    handoff = {
        "schema_version": "1.0.0",
        "handoff_type": "stegtalk_adapter_handoff",
        "adapter_name": adapter_name,
        "envelope_hash": envelope["envelope_hash"],
        "sender_entity": envelope["sender_entity"],
        "receiver_entity": envelope["receiver_entity"],
        "scope": envelope.get("scope", "private"),
        "created_at": utc_now(),
    }
    handoff["handoff_hash"] = stable_hash(handoff)
    return handoff


def create_adapter_receipt(*, adapter_handoff: JsonObject, result: str = "accepted") -> JsonObject:
    if result not in {"accepted", "queued", "rejected"}:
        raise ValueError("unsupported adapter result")
    return with_receipt_identity(
        {
            "type": "adapter_handoff_receipt",
            "adapter_name": adapter_handoff["adapter_name"],
            "adapter_handoff_hash": adapter_handoff["handoff_hash"],
            "envelope_hash": adapter_handoff["envelope_hash"],
            "sender_entity": adapter_handoff["sender_entity"],
            "receiver_entity": adapter_handoff["receiver_entity"],
            "scope": adapter_handoff["scope"],
            "result": result,
            "recorded_at": utc_now(),
            "boundary": "mock_handoff_only",
        }
    )


def adapter_boundary_summary() -> JsonObject:
    return {
        "boundary_type": "adapter_boundary",
        "production_network": False,
        "adapter_claim": "mock_handoff_receipt_only",
        "envelope_separation": True,
    }
