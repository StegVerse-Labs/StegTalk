from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity


def create_transport_receipt(*, bearer: str, chunk_count: int, payload_sha256: str, result: str = "encoded") -> JsonObject:
    if not bearer:
        raise ValueError("bearer is required")
    if chunk_count <= 0:
        raise ValueError("chunk_count must be positive")
    if result not in {"encoded", "transmitted", "received", "rejected"}:
        raise ValueError("unsupported transport result")
    return with_receipt_identity(
        {
            "type": "stegtalk_transport_receipt",
            "bearer": bearer,
            "chunk_count": chunk_count,
            "payload_sha256": payload_sha256,
            "result": result,
            "recorded_at": utc_now(),
            "boundary": "transport_prototype_only",
        }
    )


def create_reconstruction_receipt(*, chunks: list[JsonObject], payload: bytes, result: str = "complete") -> JsonObject:
    if result not in {"complete", "incomplete", "failed"}:
        raise ValueError("unsupported reconstruction result")
    chunk_hashes = [str(chunk["chunk_hash"]) for chunk in chunks]
    payload_ref = "sha256:" + __import__("hashlib").sha256(payload).hexdigest()
    return with_receipt_identity(
        {
            "type": "stegtalk_reconstruction_receipt",
            "chunk_count": len(chunks),
            "chunk_chain_hash": stable_hash(chunk_hashes),
            "payload_ref": payload_ref,
            "result": result,
            "recorded_at": utc_now(),
        }
    )


def create_presentation_receipt(*, reconstruction_receipt: JsonObject, decision: str, reason: str) -> JsonObject:
    if decision not in {"render", "quarantine", "reject"}:
        raise ValueError("unsupported presentation decision")
    return with_receipt_identity(
        {
            "type": "stegtalk_presentation_receipt",
            "reconstruction_receipt_ref": reconstruction_receipt["id"],
            "decision": decision,
            "reason": reason,
            "recorded_at": utc_now(),
        },
        previous_chain_head=reconstruction_receipt.get("receipt_chain_head"),
    )
