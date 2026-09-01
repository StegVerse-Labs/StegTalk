from datetime import datetime, timedelta, timezone

import pytest

from stegtalk.transport.failover import build_failover_plan, next_failover_bearer
from stegtalk.transport.observations import RawBearerObservation, normalize_observation
from stegtalk.transport.selector import TransportRequest


def raw(bearer_id: str, kind: str, now: datetime, **overrides):
    values = {
        "bearer_id": bearer_id,
        "kind": kind,
        "observed_at": now.isoformat(),
        "available": True,
        "latency_ms": 100,
        "bandwidth_kbps": 1024,
        "reliability": 4,
        "privacy": 4,
        "metadata_exposure": 1,
        "energy_cost": 2,
        "congestion": 1,
        "supports_receipts": True,
        "uses_relay": False,
        "local_path": True,
        "permission_granted": True,
        "capability_verified": True,
    }
    values.update(overrides)
    return RawBearerObservation(**values)


def test_normalizes_fresh_verified_observation():
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    observation = normalize_observation(raw("wifi", "wifi_peer", now), now=now)
    assert observation.bearer_id == "wifi"
    assert observation.kind == "wifi_peer"


def test_rejects_stale_observation():
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="stale_observation"):
        normalize_observation(raw("ble", "ble", now - timedelta(seconds=31)), now=now)


def test_rejects_ungranted_permission_and_unverified_capability():
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    with pytest.raises(ValueError, match="permission"):
        normalize_observation(raw("ble", "ble", now, permission_granted=False), now=now)
    with pytest.raises(ValueError, match="unverified"):
        normalize_observation(raw("wifi", "wifi_peer", now, capability_verified=False), now=now)


def test_builds_deterministic_failover_order():
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    observations = [
        normalize_observation(raw("wifi", "wifi_peer", now, latency_ms=20), now=now),
        normalize_observation(raw("ble", "ble", now, latency_ms=250, bandwidth_kbps=128), now=now),
        normalize_observation(raw("store", "store_and_forward", now, reliability=5, uses_relay=True), now=now),
    ]
    plan = build_failover_plan(TransportRequest(message_id="m-1"), observations, max_attempts=3)
    assert len(plan.ordered_bearer_ids) == 3
    assert plan.ordered_bearer_ids[0] == "wifi"
    assert next_failover_bearer(plan, failed_bearer_ids={"wifi"}) in {"ble", "store"}


def test_failover_never_reintroduces_rejected_relay():
    now = datetime(2026, 7, 15, tzinfo=timezone.utc)
    observations = [
        normalize_observation(raw("ble", "ble", now), now=now),
        normalize_observation(raw("relay", "nearby_relay", now, uses_relay=True), now=now),
    ]
    plan = build_failover_plan(
        TransportRequest(message_id="m-2", allow_relays=False),
        observations,
    )
    assert plan.ordered_bearer_ids == ("ble",)
    assert next_failover_bearer(plan, failed_bearer_ids={"ble"}) is None
