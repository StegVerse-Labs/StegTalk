from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256


@dataclass(frozen=True)
class RelayPolicy:
    max_relay_copies: int = 3
    max_hops: int = 4
    duplicate_window_seconds: int = 900
    dense_peer_threshold: int = 25
    severe_peer_threshold: int = 100
    low_battery_floor_percent: int = 20

    def __post_init__(self) -> None:
        if self.max_relay_copies < 0:
            raise ValueError("max_relay_copies cannot be negative")
        if self.max_hops < 0:
            raise ValueError("max_hops cannot be negative")
        if self.duplicate_window_seconds <= 0:
            raise ValueError("duplicate_window_seconds must be positive")
        if not 0 <= self.low_battery_floor_percent <= 100:
            raise ValueError("low_battery_floor_percent must be between 0 and 100")
        if self.severe_peer_threshold < self.dense_peer_threshold:
            raise ValueError("severe_peer_threshold cannot be below dense_peer_threshold")


@dataclass(frozen=True)
class RelayCandidate:
    peer_id: str
    reliability: int
    energy_cost: int
    proximity: int
    already_has_message: bool = False

    def __post_init__(self) -> None:
        if not self.peer_id.strip():
            raise ValueError("peer_id is required")
        for name in ("reliability", "energy_cost", "proximity"):
            value = getattr(self, name)
            if not 0 <= value <= 5:
                raise ValueError(f"{name} must be between 0 and 5")


@dataclass(frozen=True)
class RelayContext:
    message_id: str
    created_at: datetime
    expires_at: datetime
    hop_count: int
    copies_released: int
    observed_peer_count: int
    device_battery_percent: int
    recent_message_hashes: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not self.message_id.strip():
            raise ValueError("message_id is required")
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("timestamps must be timezone-aware")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")
        if self.hop_count < 0 or self.copies_released < 0 or self.observed_peer_count < 0:
            raise ValueError("counts cannot be negative")
        if not 0 <= self.device_battery_percent <= 100:
            raise ValueError("device_battery_percent must be between 0 and 100")


@dataclass(frozen=True)
class RelayDecision:
    result: str
    selected_peer_ids: tuple[str, ...]
    duplicate_suppressed: bool
    scan_interval_seconds: int
    reasons: tuple[str, ...]


def message_fingerprint(message_id: str) -> str:
    return sha256(message_id.encode("utf-8")).hexdigest()


def classify_density(peer_count: int, policy: RelayPolicy | None = None) -> str:
    active = policy or RelayPolicy()
    if peer_count >= active.severe_peer_threshold:
        return "severe"
    if peer_count >= active.dense_peer_threshold:
        return "dense"
    return "normal"


def relay_scan_interval_seconds(
    *,
    peer_count: int,
    battery_percent: int,
    policy: RelayPolicy | None = None,
) -> int:
    active = policy or RelayPolicy()
    density = classify_density(peer_count, active)
    interval = {"normal": 5, "dense": 20, "severe": 60}[density]
    if battery_percent < active.low_battery_floor_percent:
        interval *= 3
    return interval


def govern_relay(
    context: RelayContext,
    candidates: list[RelayCandidate],
    *,
    now: datetime | None = None,
    policy: RelayPolicy | None = None,
) -> RelayDecision:
    active = policy or RelayPolicy()
    current = now or datetime.now(timezone.utc)
    fingerprint = message_fingerprint(context.message_id)
    interval = relay_scan_interval_seconds(
        peer_count=context.observed_peer_count,
        battery_percent=context.device_battery_percent,
        policy=active,
    )

    if current >= context.expires_at:
        return RelayDecision("DENY", (), False, interval, ("message_expired",))
    if context.hop_count >= active.max_hops:
        return RelayDecision("DENY", (), False, interval, ("hop_limit_reached",))
    if context.copies_released >= active.max_relay_copies:
        return RelayDecision("DENY", (), False, interval, ("relay_copy_budget_exhausted",))
    if fingerprint in context.recent_message_hashes:
        return RelayDecision("SUPPRESS", (), True, interval, ("duplicate_message_suppressed",))
    if context.device_battery_percent < active.low_battery_floor_percent:
        return RelayDecision("DEFER", (), False, interval, ("battery_floor_active",))

    remaining_budget = active.max_relay_copies - context.copies_released
    eligible = [item for item in candidates if not item.already_has_message]
    ranked = sorted(
        eligible,
        key=lambda item: (
            -(item.reliability * 5 + item.proximity * 3 - item.energy_cost * 2),
            item.peer_id,
        ),
    )
    selected = tuple(item.peer_id for item in ranked[:remaining_budget])
    if not selected:
        return RelayDecision("DEFER", (), False, interval, ("no_eligible_relay_peer",))

    return RelayDecision(
        "RELAY",
        selected,
        False,
        interval,
        ("bounded_relay_selection", classify_density(context.observed_peer_count, active)),
    )
