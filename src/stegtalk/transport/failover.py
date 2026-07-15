from __future__ import annotations

from dataclasses import dataclass

from .selector import BearerObservation, SelectionPolicy, TransportDecision, TransportRequest, select_transport


@dataclass(frozen=True)
class FailoverPlan:
    request: TransportRequest
    ordered_bearer_ids: tuple[str, ...]
    decisions: tuple[TransportDecision, ...]


def build_failover_plan(
    request: TransportRequest,
    observations: list[BearerObservation],
    *,
    policy: SelectionPolicy | None = None,
    max_attempts: int = 3,
) -> FailoverPlan:
    if max_attempts <= 0:
        raise ValueError("max_attempts must be positive")

    remaining = list(observations)
    decisions: list[TransportDecision] = []
    ordered: list[str] = []

    while remaining and len(ordered) < max_attempts:
        decision = select_transport(request, remaining, policy=policy)
        decisions.append(decision)
        if decision.result != "SELECT" or decision.selected_bearer_id is None:
            break
        ordered.append(decision.selected_bearer_id)
        remaining = [item for item in remaining if item.bearer_id != decision.selected_bearer_id]

    return FailoverPlan(
        request=request,
        ordered_bearer_ids=tuple(ordered),
        decisions=tuple(decisions),
    )


def next_failover_bearer(plan: FailoverPlan, *, failed_bearer_ids: set[str]) -> str | None:
    for bearer_id in plan.ordered_bearer_ids:
        if bearer_id not in failed_bearer_ids:
            return bearer_id
    return None
