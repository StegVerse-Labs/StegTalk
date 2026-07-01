from __future__ import annotations

from .entity_runtime import JsonObject
from .transport_admissibility import decide_presentation
from .transport_codec import chunk_payload, reassemble_chunks, sha256_hex
from .transport_fec import chunk_payload_with_xor_fec, recover_reassemble_xor_fec
from .transport_manifest import assert_manifest_compatible
from .transport_receipts import create_presentation_receipt, create_reconstruction_receipt, create_transport_receipt
from .transport_replay import InMemoryReplayCache, enforce_replay_cache, validate_package_freshness

SUPPORTED_BEARERS = {"light", "audio", "image", "video", "ip", "local_mock"}


def build_transport_package(
    payload: bytes,
    *,
    bearer: str = "light",
    chunk_size: int = 223,
    ttl_seconds: int = 300,
    fec_profile: str = "none",
) -> JsonObject:
    if bearer not in SUPPORTED_BEARERS:
        raise ValueError("unsupported bearer")
    if fec_profile == "xor-one-loss-v1":
        chunks = chunk_payload_with_xor_fec(payload, chunk_size=chunk_size, ttl_seconds=ttl_seconds)
    elif fec_profile == "none":
        chunks = chunk_payload(payload, chunk_size=chunk_size, ttl_seconds=ttl_seconds)
    else:
        raise ValueError("unsupported fec_profile")
    receipt = create_transport_receipt(
        bearer=bearer,
        chunk_count=len(chunks),
        payload_sha256=sha256_hex(payload),
        result="encoded",
    )
    return {
        "schema_version": "1.0.0",
        "package_type": "stegtalk_transport_package",
        "bearer": bearer,
        "fec_profile": fec_profile,
        "chunks": chunks,
        "transport_receipt": receipt,
    }


def receive_transport_package(
    package: JsonObject,
    *,
    allow_render: bool = False,
    destination_manifest: JsonObject | None = None,
    destination_policy: JsonObject | None = None,
    replay_cache: InMemoryReplayCache | None = None,
    now: str | None = None,
) -> JsonObject:
    if destination_manifest is not None:
        assert_manifest_compatible(package, destination_manifest)
    chunks = list(package.get("chunks", []))
    validate_package_freshness(chunks, now=now)
    enforce_replay_cache(chunks, replay_cache)
    if package.get("fec_profile") == "xor-one-loss-v1":
        payload = recover_reassemble_xor_fec(chunks)
    else:
        payload = reassemble_chunks(chunks)
    reconstruction = create_reconstruction_receipt(chunks=chunks, payload=payload, result="complete")
    decision, reason = decide_presentation(
        allow_render=allow_render,
        destination_policy=destination_policy,
        package=package,
    )
    presentation = create_presentation_receipt(
        reconstruction_receipt=reconstruction,
        decision=decision,
        reason=reason,
    )
    return {
        "schema_version": "1.0.0",
        "result_type": "stegtalk_transport_receive_result",
        "payload": payload,
        "reconstruction_receipt": reconstruction,
        "presentation_receipt": presentation,
    }
