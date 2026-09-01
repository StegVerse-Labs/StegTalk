import pytest

from stegtalk.transport.custody_transfer import (
    accept_transfer,
    confirm_transfer,
    create_transfer,
    deletion_eligible,
    expire_transfer,
    release_upstream,
    rollback_transfer,
)


def transfer():
    return create_transfer(
        transfer_id="t-1",
        message_id="m-1",
        upstream_peer_id="peer-a",
        downstream_peer_id="peer-b",
        offered_at="2026-07-15T22:00:00Z",
        expires_at="2026-07-15T22:05:00Z",
    )


def test_confirmed_transfer_decrements_budget_but_retains_upstream_until_release():
    offered = transfer()
    accepted = accept_transfer(offered, accepted_at="2026-07-15T22:01:00Z", state_hash="h1")
    confirmed = confirm_transfer(accepted, confirmed_at="2026-07-15T22:02:00Z", state_hash="h2")
    assert confirmed.copy_budget_decremented is True
    assert confirmed.upstream_retains_payload is True
    assert deletion_eligible(confirmed) is False

    released = release_upstream(confirmed, released_at="2026-07-15T22:03:00Z", state_hash="h3")
    assert released.upstream_retains_payload is False
    assert deletion_eligible(released) is True


def test_timeout_preserves_upstream_and_does_not_spend_copy_budget():
    expired = expire_transfer(
        transfer(), observed_at="2026-07-15T22:06:00Z", state_hash="h1"
    )
    assert expired.state == "EXPIRED"
    assert expired.upstream_retains_payload is True
    assert expired.copy_budget_decremented is False
    assert deletion_eligible(expired) is False


def test_rollback_preserves_upstream_custody():
    accepted = accept_transfer(
        transfer(), accepted_at="2026-07-15T22:01:00Z", state_hash="h1"
    )
    rolled_back = rollback_transfer(
        accepted, reason="peer_attestation_failed", state_hash="h2"
    )
    assert rolled_back.state == "ROLLED_BACK"
    assert rolled_back.upstream_retains_payload is True
    assert rolled_back.copy_budget_decremented is False


def test_cannot_confirm_without_acceptance():
    with pytest.raises(ValueError, match="invalid custody transition"):
        confirm_transfer(
            transfer(), confirmed_at="2026-07-15T22:02:00Z", state_hash="h1"
        )


def test_cannot_accept_after_expiry():
    with pytest.raises(ValueError, match="validity window expired"):
        accept_transfer(
            transfer(), accepted_at="2026-07-15T22:06:00Z", state_hash="h1"
        )


def test_cannot_release_before_confirmation():
    accepted = accept_transfer(
        transfer(), accepted_at="2026-07-15T22:01:00Z", state_hash="h1"
    )
    with pytest.raises(ValueError, match="invalid custody transition"):
        release_upstream(
            accepted, released_at="2026-07-15T22:02:00Z", state_hash="h2"
        )
