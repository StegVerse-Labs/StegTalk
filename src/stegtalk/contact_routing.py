from __future__ import annotations

from typing import Iterable

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .message_envelope import build_local_message


def build_contact_index(entity_cards: Iterable[JsonObject]) -> dict[str, JsonObject]:
    index: dict[str, JsonObject] = {}
    for card in entity_cards:
        identity = card["identity"]
        keys = {identity["id"], identity["display_name"], identity.get("alias")}
        for key in keys:
            if key:
                index[str(key).lower()] = card
    return index


def route_contact(
    *,
    sender_entity: str,
    receiver_hint: str,
    body: str,
    contact_index: dict[str, JsonObject],
    scope: str = "private",
) -> tuple[JsonObject, JsonObject, JsonObject]:
    candidates = [card for key, card in contact_index.items() if receiver_hint.lower() in key]
    unique: dict[str, JsonObject] = {card["identity"]["id"]: card for card in candidates}
    if not unique:
        decision = _routing_decision(
            sender_entity=sender_entity,
            receiver_hint=receiver_hint,
            result="unresolved",
            reason="no recognized contact matched receiver hint",
            candidate_count=0,
        )
        return decision, {}, {}
    if len(unique) > 1:
        decision = _routing_decision(
            sender_entity=sender_entity,
            receiver_hint=receiver_hint,
            result="clarification_required",
            reason="multiple recognized contacts matched receiver hint",
            candidate_count=len(unique),
            candidates=sorted(unique.keys()),
        )
        return decision, {}, {}
    card = next(iter(unique.values()))
    receiver_entity = card["identity"]["id"]
    envelope, receipt = build_local_message(
        sender_entity=sender_entity,
        receiver_entity=receiver_entity,
        body=body,
        scope=scope,
        metadata={"receiver_hint": receiver_hint, "routed_by": "contact_routing"},
    )
    decision = _routing_decision(
        sender_entity=sender_entity,
        receiver_hint=receiver_hint,
        result="routed",
        reason="one recognized contact matched receiver hint",
        candidate_count=1,
        selected_entity=receiver_entity,
        envelope_hash=envelope["envelope_hash"],
    )
    return decision, envelope, receipt


def _routing_decision(
    *,
    sender_entity: str,
    receiver_hint: str,
    result: str,
    reason: str,
    candidate_count: int,
    candidates: list[str] | None = None,
    selected_entity: str | None = None,
    envelope_hash: str | None = None,
) -> JsonObject:
    decision = {
        "type": "contact_routing_decision",
        "sender_entity": sender_entity,
        "receiver_hint": receiver_hint,
        "result": result,
        "reason": reason,
        "candidate_count": candidate_count,
        "candidates": candidates or [],
        "selected_entity": selected_entity,
        "envelope_hash": envelope_hash,
        "decided_at": utc_now(),
    }
    decision["decision_hash"] = stable_hash(decision)
    receipt = with_receipt_identity({"type": "contact_routing_receipt", **decision})
    decision["receipt_ref"] = receipt["id"]
    decision["receipt_chain_head"] = receipt["receipt_chain_head"]
    return decision
