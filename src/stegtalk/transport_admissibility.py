from __future__ import annotations

from .entity_runtime import JsonObject


def decide_presentation(
    *,
    allow_render: bool = False,
    destination_policy: JsonObject | None = None,
    package: JsonObject | None = None,
) -> tuple[str, str]:
    """Destination-controlled presentation decision.

    This does not claim content safety. It encodes the rule that successful
    transport/reconstruction is never enough to render by default.
    """

    policy = destination_policy or {}
    if policy.get("force_reject"):
        return "reject", "destination_policy_force_reject"
    if package is not None and package.get("transport_receipt", {}).get("result") == "rejected":
        return "reject", "origin_transport_receipt_rejected"
    if allow_render or policy.get("allow_render") is True:
        return "render", "destination_admissibility_allowed_render"
    return "quarantine", "render_requires_destination_admissibility"
