from __future__ import annotations

from typing import Any

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity


def settle_compensation(
    *,
    reliance_contract: JsonObject,
    entity_identity: str,
    amount: float,
    period: str,
    result: str = "success",
) -> JsonObject:
    compensation = reliance_contract.get("compensation", {})
    return with_receipt_identity(
        {
            "type": "compensation_settlement_receipt",
            "reliance_contract_ref": stable_hash(reliance_contract),
            "payer_identity": reliance_contract["parties"]["user_identity"],
            "recipient_identity": compensation.get("recipient"),
            "entity_identity": entity_identity,
            "settlement_model": compensation.get("model", "none"),
            "token": compensation.get("settlement_token"),
            "amount": amount,
            "period": period,
            "settled_at": utc_now(),
            "result": result,
        }
    )


def create_scoped_message_receipt(
    *,
    sender_entity: str,
    message_ref: str,
    scope_used: str,
    recipient_basis: str,
    recipient_count: int,
    delivery_result: str = "success",
    private_recipient_list_ref: str = "local_or_encrypted_only",
) -> JsonObject:
    if recipient_count < 0:
        raise ValueError("recipient_count cannot be negative")
    return with_receipt_identity(
        {
            "type": "scoped_message_receipt",
            "sender_entity": sender_entity,
            "message_ref": message_ref,
            "scope_used": scope_used,
            "recipient_basis": recipient_basis,
            "recipient_count": recipient_count,
            "sent_at": utc_now(),
            "delivery_result": delivery_result,
            "private_recipient_list_ref": private_recipient_list_ref,
        }
    )


def create_feed_item_receipt(
    *,
    feed_type: str,
    source_type: str,
    source_ref: str,
    visible_to_basis: str,
    author_entity: str,
) -> JsonObject:
    return with_receipt_identity(
        {
            "type": "feed_item_receipt",
            "feed_type": feed_type,
            "source": {"source_type": source_type, "source_ref": source_ref},
            "visible_to_basis": visible_to_basis,
            "author_entity": author_entity,
            "created_at": utc_now(),
        }
    )


def explain_visibility(feed_item_receipt: JsonObject) -> JsonObject:
    basis = feed_item_receipt.get("visible_to_basis", "unknown")
    author = feed_item_receipt.get("author_entity", "this entity")
    text_by_basis = {
        "public": f"You are seeing this because {author} posted it to a public feed.",
        "reliance_contract": f"You are seeing this because you rely on {author} under an active relationship contract.",
        "region_scope": f"You are seeing this because your local scope is included by {author}.",
        "group_membership": f"You are seeing this because your group relationship includes {author}.",
        "developer_relationship": f"You are seeing this because you have a developer relationship with {author}.",
        "authority_scope": f"You are seeing this because the item is relevant to your authority scope for {author}.",
    }
    return {
        "feed_item_ref": feed_item_receipt["id"],
        "visible_because": [basis],
        "user_facing_text": text_by_basis.get(basis, "You are seeing this because a receipt-backed feed rule made it visible."),
        "receipt_ref": feed_item_receipt["id"],
    }


def create_attention_receipt(
    *,
    user_identity: str,
    source_entity: str,
    feed_item_ref: str,
    delivery_scope: str,
    feed_control_rule_applied: str,
    attention_reason: str,
    user_action: str = "delivered",
) -> JsonObject:
    return with_receipt_identity(
        {
            "type": "attention_receipt",
            "user_identity": user_identity,
            "source_entity": source_entity,
            "feed_item_ref": feed_item_ref,
            "delivery_scope": delivery_scope,
            "feed_control_rule_applied": feed_control_rule_applied,
            "attention_reason": attention_reason,
            "delivered_at": utc_now(),
            "user_action": user_action,
        }
    )


def settle_contributor_splits(
    *,
    entity: str,
    revenue_source: str,
    settlement_period: str,
    gross_amount: float,
    token: str,
    split_policy_ref: str,
    distributions: list[dict[str, Any]],
    upstream_distributions: list[dict[str, Any]] | None = None,
    infrastructure_distribution: dict[str, Any] | None = None,
) -> JsonObject:
    total_share = 0.0
    normalized_distributions = []
    for distribution in distributions:
        share = float(distribution["share"])
        total_share += share
        normalized_distributions.append({**distribution, "amount": round(gross_amount * share, 8), "result": distribution.get("result", "success")})
    normalized_upstream = []
    for distribution in upstream_distributions or []:
        share = float(distribution["share"])
        total_share += share
        normalized_upstream.append({**distribution, "amount": round(gross_amount * share, 8), "result": distribution.get("result", "success")})
    normalized_infrastructure = None
    if infrastructure_distribution:
        share = float(infrastructure_distribution["share"])
        total_share += share
        normalized_infrastructure = {**infrastructure_distribution, "amount": round(gross_amount * share, 8), "result": infrastructure_distribution.get("result", "success")}
    if round(total_share, 8) > 1.0:
        raise ValueError("split shares cannot exceed 1.0")
    return with_receipt_identity(
        {
            "type": "split_settlement_receipt",
            "entity": entity,
            "revenue_source": revenue_source,
            "settlement_period": settlement_period,
            "gross_amount": gross_amount,
            "token": token,
            "active_split_policy_ref": split_policy_ref,
            "distributions": normalized_distributions,
            "upstream_distributions": normalized_upstream,
            "infrastructure_distribution": normalized_infrastructure,
            "settled_at": utc_now(),
        }
    )
