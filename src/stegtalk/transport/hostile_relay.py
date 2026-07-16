from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .attestation import AttestationDecision, PeerPosture


class RelayBehavior(StrEnum):
    HONEST = "HONEST"
    ACCEPT_WITHOUT_CONFIRM = "ACCEPT_WITHOUT_CONFIRM"
    FALSE_CONFIRM = "FALSE_CONFIRM"
    WITHHOLD_CUSTODY = "WITHHOLD_CUSTODY"


@dataclass(frozen=True)
class RelayCandidate:
    peer_id: str
    reliability: int
    attestation: AttestationDecision
    behavior: RelayBehavior = RelayBehavior.HONEST


@dataclass(frozen=True)
class RelaySimulationResult:
    selected_peer_id: str | None
    quarantined_peer_ids: tuple[str, ...]
    attempted_peer_ids: tuple[str, ...]
    outcome: str
    upstream_retains_message: bool
    reasons: tuple[str, ...]


def simulate_relay_recovery(candidates: list[RelayCandidate]) -> RelaySimulationResult:
    eligible = sorted(
        (item for item in candidates if item.attestation.posture == PeerPosture.ELIGIBLE),
        key=lambda item: (-item.reliability, item.peer_id),
    )
    attempted: list[str] = []
    quarantined: list[str] = [
        item.peer_id for item in candidates if item.attestation.posture != PeerPosture.ELIGIBLE
    ]
    reasons: list[str] = []

    for candidate in eligible:
        attempted.append(candidate.peer_id)
        if candidate.behavior == RelayBehavior.HONEST:
            return RelaySimulationResult(
                selected_peer_id=candidate.peer_id,
                quarantined_peer_ids=tuple(sorted(set(quarantined))),
                attempted_peer_ids=tuple(attempted),
                outcome="TRANSFER_CONFIRMED",
                upstream_retains_message=True,
                reasons=tuple(reasons + ["alternate_peer_confirmed"]),
            )
        quarantined.append(candidate.peer_id)
        if candidate.behavior == RelayBehavior.ACCEPT_WITHOUT_CONFIRM:
            reasons.append("confirmation_timeout")
        elif candidate.behavior == RelayBehavior.FALSE_CONFIRM:
            reasons.append("false_confirmation_detected")
        else:
            reasons.append("custody_withheld")

    return RelaySimulationResult(
        selected_peer_id=None,
        quarantined_peer_ids=tuple(sorted(set(quarantined))),
        attempted_peer_ids=tuple(attempted),
        outcome="ROLLED_BACK",
        upstream_retains_message=True,
        reasons=tuple(reasons or ["no_eligible_peer"]),
    )
