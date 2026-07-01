from __future__ import annotations

from .entity_runtime import JsonObject, stable_hash, utc_now

DEFAULT_SUPPORTED_BEARERS = ["audio", "image", "ip", "light", "local_mock", "video"]
DEFAULT_REQUIRED_RECEIPTS = [
    "stegtalk_transport_receipt",
    "stegtalk_reconstruction_receipt",
    "stegtalk_presentation_receipt",
]


def create_transport_manifest(
    *,
    ecosystem: str = "StegTalk",
    profile: str = "transport-prototype-v1",
    supported_bearers: list[str] | None = None,
    required_receipts: list[str] | None = None,
    boundary_terms: list[str] | None = None,
) -> JsonObject:
    """Create a public capability manifest without exposing verifier internals."""

    manifest = {
        "schema_version": "1.0.0",
        "manifest_type": "stegtalk_transport_manifest",
        "ecosystem": ecosystem,
        "profile": profile,
        "supported_bearers": supported_bearers or DEFAULT_SUPPORTED_BEARERS,
        "required_receipts": required_receipts or DEFAULT_REQUIRED_RECEIPTS,
        "boundary_terms": boundary_terms
        or [
            "origin_validity_is_not_destination_admissibility",
            "receipts_are_evidence_not_authority",
            "rendering_requires_destination_admissibility",
            "unknown_or_replayed_packages_fail_closed",
        ],
        "published_at": utc_now(),
    }
    manifest["manifest_hash"] = stable_hash(manifest)
    return manifest


def assert_manifest_compatible(package: JsonObject, manifest: JsonObject) -> None:
    bearer = package.get("bearer")
    if bearer not in set(manifest.get("supported_bearers", [])):
        raise ValueError("package bearer is not allowed by destination manifest")
    if package.get("package_type") != "stegtalk_transport_package":
        raise ValueError("unsupported package type")
