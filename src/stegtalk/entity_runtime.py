from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

JsonObject = dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def stable_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def receipt_id(receipt: JsonObject) -> str:
    payload = {k: v for k, v in receipt.items() if k not in {"id", "receipt_chain_head"}}
    return "rcpt_" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:24]


def with_receipt_identity(receipt: JsonObject, previous_chain_head: str | None = None) -> JsonObject:
    built = deepcopy(receipt)
    built.setdefault("created_at", utc_now())
    built["id"] = receipt_id(built)
    built["receipt_chain_head"] = stable_hash({"previous": previous_chain_head, "receipt": built})
    return built


def create_entity_card(
    *,
    entity_id: str,
    display_name: str,
    entity_type: str,
    purpose: str,
    capabilities: list[str] | None = None,
    boundaries: list[str] | None = None,
    version_policy: str = "pinned",
    lineage: str | None = None,
) -> JsonObject:
    return {
        "identity": {
            "id": entity_id,
            "display_name": display_name,
            "type": entity_type,
            "alias": display_name,
            "lineage": lineage,
        },
        "declarations": {
            "purpose": purpose,
            "capabilities": capabilities or [],
            "boundaries": boundaries or [],
            "promises": [],
            "version_policy": version_policy,
        },
        "relationship": {
            "recognition": {"status": "unrecognized", "since": None},
            "reliance": {"status": "inactive", "scope": None, "terms": None},
            "representation": {"allowed": False, "representative": None},
            "compensation": {"model": "none", "rate": None, "recipient": None},
        },
        "state": {
            "local_status": "created",
            "published_status": "unpublished",
            "active_users": 0,
            "active_reliance_count": 0,
        },
        "receipts": {"latest": None, "chain_head": None},
    }


def build_discovery_record(entity_card: JsonObject) -> JsonObject:
    identity = entity_card["identity"]
    declarations = entity_card["declarations"]
    state = entity_card["state"]
    relationship = entity_card["relationship"]
    return {
        "entity_id": identity["id"],
        "display_name": identity["display_name"],
        "type": identity["type"],
        "purpose": declarations.get("purpose"),
        "capabilities": declarations.get("capabilities", []),
        "boundaries": declarations.get("boundaries", []),
        "lineage": identity.get("lineage"),
        "visibility": state.get("published_status"),
        "recognition_count": state.get("active_users", 0),
        "reliance_count": state.get("active_reliance_count", 0),
        "compensation_model": relationship.get("compensation", {}).get("model", "none"),
        "relationship_contract_template_ref": relationship.get("reliance", {}).get("terms"),
        "latest_public_receipt_ref": entity_card.get("receipts", {}).get("latest"),
    }


def create_relationship_contract(
    *,
    user_identity: str,
    entity_identity: str,
    relationship_type: list[str],
    scope: str,
    permissions: JsonObject | None = None,
    compensation: JsonObject | None = None,
) -> JsonObject:
    return {
        "parties": {"user_identity": user_identity, "entity_identity": entity_identity},
        "relationship_type": relationship_type,
        "scope": scope,
        "permissions": permissions or {
            "may_message": True,
            "may_notify": False,
            "may_read_local_state": [],
            "may_write_local_state": False,
            "may_request_payment": False,
            "may_publish_updates": False,
            "may_represent_user": False,
        },
        "compensation": compensation or {
            "model": "none",
            "rate": None,
            "recipient": None,
            "settlement_token": None,
        },
        "boundaries": {
            "cannot_sell_personal_data": True,
            "cannot_export_private_state_without_permission": True,
            "cannot_execute_consequence_without_authority": True,
        },
        "receipts": {"created": None, "updated": None, "chain_head": None},
    }


def create_change_request(
    *,
    requester: str,
    target_entity: str,
    change_type: str,
    scope: str,
    reason: str,
    relationship_contract_ref: str | None = None,
    required_conditions: list[str] | None = None,
) -> JsonObject:
    return {
        "requester": requester,
        "target_entity": target_entity,
        "relationship_contract_ref": relationship_contract_ref,
        "requested_change": {"type": change_type, "scope": scope, "reason": reason},
        "required_conditions": required_conditions or [],
        "current_readiness": None,
        "evaluation_refs": [],
        "status": "draft",
        "receipts": {"created": None, "committed": None, "executed": None},
    }


def evaluate_readiness(change_request: JsonObject, observed_conditions: dict[str, bool]) -> JsonObject:
    required = change_request.get("required_conditions", [])
    missing = [condition for condition in required if not observed_conditions.get(condition, False)]
    result = "ready" if not missing else "not_ready"
    evaluation = {
        "change_request": stable_hash(change_request),
        "target_entity": change_request["target_entity"],
        "required_conditions": required,
        "observed_conditions": observed_conditions,
        "result": result,
        "missing_conditions": missing,
        "confidence": 1.0,
    }
    return with_receipt_identity({"type": "readiness_evaluation", **evaluation})


def commit_change(
    *,
    change_request: JsonObject,
    readiness_evaluation: JsonObject,
    committed_by: str,
    binding_effect: str,
    authority_evaluation_ref: str | None = None,
) -> JsonObject:
    if readiness_evaluation.get("result") != "ready":
        raise ValueError("cannot commit a change request that is not ready")
    return with_receipt_identity(
        {
            "type": "commitment_receipt",
            "change_request_ref": stable_hash(change_request),
            "readiness_evaluation_ref": readiness_evaluation["id"],
            "authority_evaluation_ref": authority_evaluation_ref,
            "committed_by": committed_by,
            "committed_at": utc_now(),
            "scope": change_request["requested_change"]["scope"],
            "binding_effect": binding_effect,
            "conditions_locked": readiness_evaluation.get("required_conditions", []),
            "expires_at": None,
        }
    )


def transition_entity(
    *,
    entity_card: JsonObject,
    commitment_receipt: JsonObject,
    transition_type: str,
    new_state_patch: JsonObject,
    executed_by: str,
    execution_location: str = "local_device",
) -> tuple[JsonObject, JsonObject]:
    previous_state_ref = stable_hash(entity_card)
    updated = deepcopy(entity_card)
    for section, patch in new_state_patch.items():
        if isinstance(patch, dict) and isinstance(updated.get(section), dict):
            updated[section].update(patch)
        else:
            updated[section] = patch
    new_state_ref = stable_hash(updated)
    receipt = with_receipt_identity(
        {
            "type": "transition_receipt",
            "commitment_receipt_ref": commitment_receipt["id"],
            "target_entity": updated["identity"]["id"],
            "transition_type": transition_type,
            "previous_state_ref": previous_state_ref,
            "new_state_ref": new_state_ref,
            "executed_by": executed_by,
            "executed_at": utc_now(),
            "execution_location": execution_location,
            "witnesses": [],
            "result": "success",
            "consequence_summary": f"{transition_type} applied to {updated['identity']['id']}",
        },
        previous_chain_head=entity_card.get("receipts", {}).get("chain_head"),
    )
    updated["receipts"] = {"latest": receipt["id"], "chain_head": receipt["receipt_chain_head"]}
    return updated, receipt


def recognize_entity(entity_card: JsonObject, recognized_by: str, local_alias: str | None = None) -> tuple[JsonObject, JsonObject]:
    updated = deepcopy(entity_card)
    updated["identity"]["alias"] = local_alias or updated["identity"]["display_name"]
    updated["relationship"]["recognition"] = {"status": "recognized", "since": utc_now()}
    updated["state"]["active_users"] = int(updated["state"].get("active_users", 0)) + 1
    receipt = with_receipt_identity(
        {
            "type": "recognition_receipt",
            "entity": updated["identity"]["id"],
            "recognized_by": recognized_by,
            "local_alias": updated["identity"]["alias"],
            "reliance_status": updated["relationship"]["reliance"]["status"],
            "compensation_status": "inactive",
        },
        previous_chain_head=entity_card.get("receipts", {}).get("chain_head"),
    )
    updated["receipts"] = {"latest": receipt["id"], "chain_head": receipt["receipt_chain_head"]}
    return updated, receipt


def rely_on_entity(entity_card: JsonObject, contract: JsonObject) -> tuple[JsonObject, JsonObject]:
    updated = deepcopy(entity_card)
    contract_ref = stable_hash(contract)
    updated["relationship"]["reliance"] = {
        "status": "active",
        "scope": contract["scope"],
        "terms": contract_ref,
    }
    updated["relationship"]["compensation"] = contract.get("compensation", {})
    updated["state"]["active_reliance_count"] = int(updated["state"].get("active_reliance_count", 0)) + 1
    receipt = with_receipt_identity(
        {
            "type": "reliance_receipt",
            "entity": updated["identity"]["id"],
            "relied_upon_by": contract["parties"]["user_identity"],
            "scope": contract["scope"],
            "contract_ref": contract_ref,
            "compensation_status": "active" if contract.get("compensation", {}).get("model") != "none" else "inactive",
            "reliance_status": "active",
        },
        previous_chain_head=entity_card.get("receipts", {}).get("chain_head"),
    )
    updated["receipts"] = {"latest": receipt["id"], "chain_head": receipt["receipt_chain_head"]}
    return updated, receipt


def revoke_reliance(entity_card: JsonObject, preserve_recognition: bool = True) -> tuple[JsonObject, JsonObject]:
    updated = deepcopy(entity_card)
    updated["relationship"]["reliance"]["status"] = "inactive"
    updated["relationship"]["compensation"]["model"] = "none"
    updated["state"]["active_reliance_count"] = max(0, int(updated["state"].get("active_reliance_count", 0)) - 1)
    if not preserve_recognition:
        updated["relationship"]["recognition"] = {"status": "revoked", "since": None}
    receipt = with_receipt_identity(
        {
            "type": "revocation_receipt",
            "entity": updated["identity"]["id"],
            "reliance_status": updated["relationship"]["reliance"]["status"],
            "compensation_status": "stopped",
            "recognition_status": updated["relationship"]["recognition"]["status"],
            "local_data_status": "user_owned",
        },
        previous_chain_head=entity_card.get("receipts", {}).get("chain_head"),
    )
    updated["receipts"] = {"latest": receipt["id"], "chain_head": receipt["receipt_chain_head"]}
    return updated, receipt


def fork_entity(entity_card: JsonObject, *, new_entity_id: str, new_display_name: str, upstream_compensation_status: str = "renegotiated") -> tuple[JsonObject, JsonObject]:
    forked = deepcopy(entity_card)
    source_entity = entity_card["identity"]["id"]
    forked["identity"].update({"id": new_entity_id, "display_name": new_display_name, "alias": new_display_name, "lineage": source_entity})
    forked["relationship"]["reliance"]["status"] = "independent"
    forked["state"].update({"published_status": "unpublished", "active_users": 1, "active_reliance_count": 0})
    receipt = with_receipt_identity(
        {
            "type": "fork_receipt",
            "source_entity": source_entity,
            "new_entity": new_entity_id,
            "lineage_ref": source_entity,
            "reliance_status": "independent",
            "upstream_compensation_status": upstream_compensation_status,
        },
        previous_chain_head=entity_card.get("receipts", {}).get("chain_head"),
    )
    forked["receipts"] = {"latest": receipt["id"], "chain_head": receipt["receipt_chain_head"]}
    return forked, receipt
