from datetime import datetime, timedelta, timezone

from stegtalk.transport.attestation import (
    AttestationPolicy,
    PeerAttestation,
    PeerPosture,
    evaluate_peer_attestation,
)
from stegtalk.transport.hostile_relay import (
    RelayBehavior,
    RelayCandidate,
    simulate_relay_recovery,
)


def attestation(peer_id: str, *, nonce: str, verified: bool = True) -> PeerAttestation:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    return PeerAttestation(
        peer_id=peer_id,
        device_binding=f"device:{peer_id}",
        protocol_version="0.1.0",
        issued_at=now - timedelta(seconds=5),
        expires_at=now + timedelta(minutes=5),
        nonce=nonce,
        capability_claims=("custody_transfer",),
        signature_verified=verified,
    )


def test_valid_attestation_is_eligible() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    decision = evaluate_peer_attestation(attestation("peer-a", nonce="n1"), now=now, seen_nonces=set())
    assert decision.posture == PeerPosture.ELIGIBLE


def test_replayed_attestation_is_rejected() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    decision = evaluate_peer_attestation(attestation("peer-a", nonce="n1"), now=now, seen_nonces={"n1"})
    assert decision.posture == PeerPosture.REJECTED
    assert "attestation_replay_detected" in decision.reasons


def test_missing_capability_is_quarantined() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    item = attestation("peer-a", nonce="n1")
    item = PeerAttestation(**{**item.__dict__, "capability_claims": ()})
    decision = evaluate_peer_attestation(item, now=now, seen_nonces=set())
    assert decision.posture == PeerPosture.QUARANTINED


def test_hostile_peer_rolls_to_honest_alternate() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    bad = evaluate_peer_attestation(attestation("peer-a", nonce="n1"), now=now, seen_nonces=set())
    good = evaluate_peer_attestation(attestation("peer-b", nonce="n2"), now=now, seen_nonces=set())
    result = simulate_relay_recovery([
        RelayCandidate("peer-a", 100, bad, RelayBehavior.FALSE_CONFIRM),
        RelayCandidate("peer-b", 90, good, RelayBehavior.HONEST),
    ])
    assert result.selected_peer_id == "peer-b"
    assert result.attempted_peer_ids == ("peer-a", "peer-b")
    assert "peer-a" in result.quarantined_peer_ids
    assert result.upstream_retains_message is True


def test_all_hostile_peers_roll_back() -> None:
    now = datetime(2026, 7, 15, 12, tzinfo=timezone.utc)
    first = evaluate_peer_attestation(attestation("peer-a", nonce="n1"), now=now, seen_nonces=set())
    second = evaluate_peer_attestation(attestation("peer-b", nonce="n2"), now=now, seen_nonces=set())
    result = simulate_relay_recovery([
        RelayCandidate("peer-a", 100, first, RelayBehavior.ACCEPT_WITHOUT_CONFIRM),
        RelayCandidate("peer-b", 90, second, RelayBehavior.WITHHOLD_CUSTODY),
    ])
    assert result.outcome == "ROLLED_BACK"
    assert result.selected_peer_id is None
    assert result.upstream_retains_message is True
