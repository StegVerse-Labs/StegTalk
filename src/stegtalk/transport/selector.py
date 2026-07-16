from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

BearerKind = Literal[
    "same_device",
    "ble",
    "wifi_peer",
    "local_network",
    "internet",
    "satellite_gateway",
    "nearby_relay",
    "store_and_forward",
    "qr_optical",
    "acoustic",
]

PreferenceMode = Literal[
    "auto",
    "nearby_only",
    "most_private",
    "lowest_battery",
    "fastest_admissible",
    "emergency_resilient",
    "no_relays",
]


@dataclass(frozen=True)
class TransportRequest:
    message_id: str
    preference: PreferenceMode = "auto"
    urgency: int = 0
    expires_in_seconds: int = 3600
    allow_relays: bool = True
    require_receipt: bool = False
    local_only: bool = False
    max_metadata_exposure: int = 5
    max_energy_cost: int = 5

    def __post_init__(self) -> None:
        if not self.message_id.strip():
            raise ValueError("message_id is required")
        if not 0 <= self.urgency <= 5:
            raise ValueError("urgency must be between 0 and 5")
        if self.expires_in_seconds <= 0:
            raise ValueError("expires_in_seconds must be positive")
        if not 0 <= self.max_metadata_exposure <= 5:
            raise ValueError("max_metadata_exposure must be between 0 and 5")
        if not 0 <= self.max_energy_cost <= 5:
            raise ValueError("max_energy_cost must be between 0 and 5")


@dataclass(frozen=True)
class BearerObservation:
    bearer_id: str
    kind: BearerKind
    available: bool
    latency_ms: int
    bandwidth_kbps: int
    reliability: int
    privacy: int
    metadata_exposure: int
    energy_cost: int
    congestion: int = 0
    supports_receipts: bool = True
    uses_relay: bool = False
    local_path: bool = False
    reasons: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.bearer_id.strip():
            raise ValueError("bearer_id is required")
        if self.latency_ms < 0 or self.bandwidth_kbps < 0:
            raise ValueError("latency and bandwidth cannot be negative")
        for name in (
            "reliability",
            "privacy",
            "metadata_exposure",
            "energy_cost",
            "congestion",
        ):
            value = getattr(self, name)
            if not 0 <= value <= 5:
                raise ValueError(f"{name} must be between 0 and 5")


@dataclass(frozen=True)
class SelectionPolicy:
    policy_version: str = "stegtalk.transport.v0.1"
    minimum_reliability: int = 1
    fail_closed: bool = True


@dataclass(frozen=True)
class TransportDecision:
    message_id: str
    result: Literal["SELECT", "DEFER", "DENY"]
    selected_bearer_id: str | None
    selected_kind: BearerKind | None
    score: int | None
    policy_version: str
    rejected: tuple[tuple[str, str], ...]
    reasons: tuple[str, ...]


def select_transport(
    request: TransportRequest,
    observations: list[BearerObservation],
    *,
    policy: SelectionPolicy | None = None,
) -> TransportDecision:
    """Select the highest-scoring admissible bearer deterministically.

    The selector only chooses among observed bearers that satisfy declared request
    constraints. It cannot promote urgency into responder authority, relax consent,
    enable relays, or broaden locality on its own.
    """
    active_policy = policy or SelectionPolicy()
    admissible: list[tuple[int, BearerObservation]] = []
    rejected: list[tuple[str, str]] = []

    for bearer in observations:
        reason = _rejection_reason(request, bearer, active_policy)
        if reason is not None:
            rejected.append((bearer.bearer_id, reason))
            continue
        admissible.append((_score(request, bearer), bearer))

    if not admissible:
        result: Literal["DEFER", "DENY"] = "DENY" if active_policy.fail_closed else "DEFER"
        return TransportDecision(
            message_id=request.message_id,
            result=result,
            selected_bearer_id=None,
            selected_kind=None,
            score=None,
            policy_version=active_policy.policy_version,
            rejected=tuple(sorted(rejected)),
            reasons=("no_admissible_bearer",),
        )

    score, selected = sorted(
        admissible,
        key=lambda item: (-item[0], item[1].kind, item[1].bearer_id),
    )[0]
    return TransportDecision(
        message_id=request.message_id,
        result="SELECT",
        selected_bearer_id=selected.bearer_id,
        selected_kind=selected.kind,
        score=score,
        policy_version=active_policy.policy_version,
        rejected=tuple(sorted(rejected)),
        reasons=("highest_scoring_admissible_bearer",),
    )


def _rejection_reason(
    request: TransportRequest,
    bearer: BearerObservation,
    policy: SelectionPolicy,
) -> str | None:
    if not bearer.available:
        return "unavailable"
    if bearer.reliability < policy.minimum_reliability:
        return "below_minimum_reliability"
    if request.require_receipt and not bearer.supports_receipts:
        return "receipt_support_required"
    if request.local_only and not bearer.local_path:
        return "local_only_constraint"
    if (not request.allow_relays or request.preference == "no_relays") and bearer.uses_relay:
        return "relay_not_permitted"
    if request.preference == "nearby_only" and bearer.kind not in {
        "same_device",
        "ble",
        "wifi_peer",
        "nearby_relay",
        "qr_optical",
        "acoustic",
    }:
        return "nearby_only_constraint"
    if bearer.metadata_exposure > request.max_metadata_exposure:
        return "metadata_exposure_limit"
    if bearer.energy_cost > request.max_energy_cost:
        return "energy_cost_limit"
    return None


def _score(request: TransportRequest, bearer: BearerObservation) -> int:
    latency_score = max(0, 5 - min(5, bearer.latency_ms // 250))
    bandwidth_score = min(5, bearer.bandwidth_kbps // 256)
    base = (
        bearer.reliability * 8
        + bearer.privacy * 6
        + latency_score * 4
        + bandwidth_score * 2
        - bearer.metadata_exposure * 5
        - bearer.energy_cost * 3
        - bearer.congestion * 4
    )

    if request.preference == "most_private":
        base += bearer.privacy * 8 - bearer.metadata_exposure * 6
    elif request.preference == "lowest_battery":
        base -= bearer.energy_cost * 10
    elif request.preference == "fastest_admissible":
        base += latency_score * 10 + bandwidth_score * 4
    elif request.preference == "emergency_resilient":
        base += bearer.reliability * 10
        if bearer.kind in {"satellite_gateway", "store_and_forward", "nearby_relay"}:
            base += 8
    elif request.preference == "nearby_only" and bearer.local_path:
        base += 12

    # Urgency changes performance weighting only. It never creates network priority
    # or responder authority.
    base += request.urgency * (bearer.reliability + latency_score)
    return base
