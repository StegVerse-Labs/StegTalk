from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from .selector import BearerObservation


@dataclass(frozen=True)
class RawBearerObservation:
    bearer_id: str
    kind: str
    observed_at: str
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
    permission_granted: bool = True
    capability_verified: bool = True


def normalize_observation(
    raw: RawBearerObservation,
    *,
    now: datetime | None = None,
    max_age_seconds: int = 30,
) -> BearerObservation:
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    observed = _parse_time(raw.observed_at)
    current = now or datetime.now(timezone.utc)
    age = (current - observed).total_seconds()
    if age < 0:
        raise ValueError("observation timestamp cannot be in the future")
    if age > max_age_seconds:
        raise ValueError("stale_observation")
    if not raw.permission_granted:
        raise ValueError("bearer_permission_not_granted")
    if not raw.capability_verified:
        raise ValueError("bearer_capability_unverified")

    values = asdict(raw)
    for key in ("observed_at", "permission_granted", "capability_verified"):
        values.pop(key)
    return BearerObservation(**values)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observed_at must include timezone")
    return parsed.astimezone(timezone.utc)
