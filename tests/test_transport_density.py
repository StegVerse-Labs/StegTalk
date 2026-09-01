from datetime import datetime, timedelta, timezone

from stegtalk.transport.density import (
    RelayCandidate,
    RelayContext,
    RelayPolicy,
    govern_relay,
    message_fingerprint,
    relay_scan_interval_seconds,
)


def context(**overrides):
    now = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
    values = {
        "message_id": "m-density",
        "created_at": now,
        "expires_at": now + timedelta(minutes=10),
        "hop_count": 0,
        "copies_released": 0,
        "observed_peer_count": 10,
        "device_battery_percent": 80,
        "recent_message_hashes": frozenset(),
    }
    values.update(overrides)
    return RelayContext(**values), now


def candidate(peer_id, **overrides):
    values = {
        "peer_id": peer_id,
        "reliability": 4,
        "energy_cost": 2,
        "proximity": 4,
        "already_has_message": False,
    }
    values.update(overrides)
    return RelayCandidate(**values)


def test_relay_selection_obeys_copy_budget_and_is_deterministic():
    ctx, now = context()
    decision = govern_relay(
        ctx,
        [candidate("b"), candidate("a"), candidate("c", reliability=3)],
        now=now,
        policy=RelayPolicy(max_relay_copies=2),
    )
    assert decision.result == "RELAY"
    assert decision.selected_peer_ids == ("a", "b")


def test_duplicate_is_suppressed_before_relay():
    fingerprint = message_fingerprint("m-density")
    ctx, now = context(recent_message_hashes=frozenset({fingerprint}))
    decision = govern_relay(ctx, [candidate("a")], now=now)
    assert decision.result == "SUPPRESS"
    assert decision.duplicate_suppressed is True


def test_expiry_hop_and_copy_limits_fail_closed():
    ctx, now = context(expires_at=datetime(2026, 7, 15, 11, 59, tzinfo=timezone.utc))
    assert govern_relay(ctx, [], now=now).reasons == ("message_expired",)

    ctx, now = context(hop_count=4)
    assert govern_relay(ctx, [], now=now).reasons == ("hop_limit_reached",)

    ctx, now = context(copies_released=3)
    assert govern_relay(ctx, [], now=now).reasons == ("relay_copy_budget_exhausted",)


def test_low_battery_defers_and_extends_scan_interval():
    ctx, now = context(device_battery_percent=10, observed_peer_count=120)
    decision = govern_relay(ctx, [candidate("a")], now=now)
    assert decision.result == "DEFER"
    assert decision.scan_interval_seconds == 180


def test_candidates_that_already_have_message_are_skipped():
    ctx, now = context()
    decision = govern_relay(
        ctx,
        [candidate("a", already_has_message=True), candidate("b")],
        now=now,
    )
    assert decision.selected_peer_ids == ("b",)


def test_density_increases_scan_interval():
    assert relay_scan_interval_seconds(peer_count=5, battery_percent=100) == 5
    assert relay_scan_interval_seconds(peer_count=30, battery_percent=100) == 20
    assert relay_scan_interval_seconds(peer_count=120, battery_percent=100) == 60
