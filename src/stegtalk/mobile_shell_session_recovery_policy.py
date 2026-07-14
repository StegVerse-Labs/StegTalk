from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from .entity_runtime import JsonObject, stable_hash, utc_now, with_receipt_identity
from .local_store import COLLECTIONS, initialize_store
from .mobile_shell_session_checkpoint_rotation import inspect_checkpoint_history, restore_latest_valid_checkpoint
from .mobile_shell_session_recovery_receipt import recover_session_with_receipt

COLLECTION = "mobile_shell_session_recovery_policy_decisions"
DEFAULT_POLICY_VERSION = "stegtalk-recovery-policy-v1"
DEFAULT_MAX_FALLBACK_DEPTH = 1


def classify_recovery_reason(reason: str) -> str:
    normalized = reason.lower()
    if "authority boundary" in normalized:
        return "authority_violation"
    if "session mismatch" in normalized or "cross-session" in normalized:
        return "cross_session_state"
    if "receipt" in normalized:
        return "receipt_chain_failure"
    if "shell" in normalized:
        return "shell_integrity_failure"
    if "integrity" in normalized or "hash" in normalized:
        return "integrity_failure"
    if "missing" in normalized or "not found" in normalized:
        return "missing_state"
    return "invalid_checkpoint"


def evaluate_recovery_policy(
    *,
    store_root: str | Path,
    session_id: str,
    policy_version: str = DEFAULT_POLICY_VERSION,
    max_fallback_depth: int = DEFAULT_MAX_FALLBACK_DEPTH,
) -> JsonObject:
    if not policy_version:
        raise ValueError("recovery policy version is required")
    if max_fallback_depth < 0:
        raise ValueError("maximum fallback depth must be non-negative")

    try:
        history = inspect_checkpoint_history(store_root=store_root, session_id=session_id)
        candidate = restore_latest_valid_checkpoint(store_root=store_root, session_id=session_id)
    except (ValueError, FileNotFoundError) as exc:
        return _decision(
            session_id=session_id,
            policy_version=policy_version,
            max_fallback_depth=max_fallback_depth,
            decision="DENY",
            reason_code="all_retained_generations_failed",
            reason=str(exc),
            history_hash=None,
            retained_generations=[],
            selected_generation=None,
            fallback_depth=None,
            rejected_generations=[],
        )

    retained = list(history["retained_generations"])
    selected = int(candidate["generation"])
    newest = max(retained)
    fallback_depth = newest - selected
    classified_rejections = [
        {
            "generation": item.get("generation"),
            "reason": item.get("reason"),
            "reason_code": classify_recovery_reason(str(item.get("reason", ""))),
        }
        for item in candidate.get("rejected_generations", [])
    ]

    if fallback_depth > max_fallback_depth:
        return _decision(
            session_id=session_id,
            policy_version=policy_version,
            max_fallback_depth=max_fallback_depth,
            decision="DENY",
            reason_code="fallback_depth_exceeded",
            reason=f"fallback depth {fallback_depth} exceeds policy maximum {max_fallback_depth}",
            history_hash=history["history_hash"],
            retained_generations=retained,
            selected_generation=selected,
            fallback_depth=fallback_depth,
            rejected_generations=classified_rejections,
        )

    return _decision(
        session_id=session_id,
        policy_version=policy_version,
        max_fallback_depth=max_fallback_depth,
        decision="ALLOW",
        reason_code="newest_valid_checkpoint" if fallback_depth == 0 else "admissible_fallback",
        reason=None,
        history_hash=history["history_hash"],
        retained_generations=retained,
        selected_generation=selected,
        fallback_depth=fallback_depth,
        rejected_generations=classified_rejections,
    )


def recover_session_under_policy(
    *,
    store_root: str | Path,
    session_id: str,
    policy_version: str = DEFAULT_POLICY_VERSION,
    max_fallback_depth: int = DEFAULT_MAX_FALLBACK_DEPTH,
) -> tuple[JsonObject | None, JsonObject]:
    decision = evaluate_recovery_policy(
        store_root=store_root,
        session_id=session_id,
        policy_version=policy_version,
        max_fallback_depth=max_fallback_depth,
    )
    previous = _load_decisions(store_root, session_id)
    previous_head = previous[-1]["receipt_chain_head"] if previous else None

    recovered: JsonObject | None = None
    recovery_receipt: JsonObject | None = None
    if decision["decision"] == "ALLOW":
        recovered, recovery_receipt = recover_session_with_receipt(
            store_root=store_root,
            session_id=session_id,
        )
        if recovered is None:
            decision = {
                **decision,
                "decision": "DENY",
                "reason_code": "recovery_execution_failed",
                "reason": recovery_receipt.get("reason"),
            }

    record = with_receipt_identity(
        {
            "type": "stegtalk_mobile_shell_session_recovery_policy_decision",
            **decision,
            "recovery_receipt_id": recovery_receipt.get("id") if recovery_receipt else None,
            "recovery_receipt_chain_head": recovery_receipt.get("receipt_chain_head") if recovery_receipt else None,
            "selected_checkpoint_hash": recovery_receipt.get("selected_checkpoint_hash") if recovery_receipt else None,
            "selected_receipt_chain_head": recovery_receipt.get("selected_receipt_chain_head") if recovery_receipt else None,
            "production_ready": False,
            "local_only": True,
            "authorizing": False,
            "decided_at": utc_now(),
            "previous_chain_head": previous_head,
        },
        previous_chain_head=previous_head,
    )
    _persist_decisions(store_root, session_id, [*previous, record])
    return recovered if record["decision"] == "ALLOW" else None, record


def inspect_recovery_policy_decisions(*, store_root: str | Path, session_id: str) -> JsonObject:
    decisions = _load_decisions(store_root, session_id)
    return {
        "session_id": session_id,
        "decision_count": len(decisions),
        "decisions": [item["decision"] for item in decisions],
        "reason_codes": [item["reason_code"] for item in decisions],
        "policy_versions": [item["policy_version"] for item in decisions],
        "chain_head": decisions[-1]["receipt_chain_head"] if decisions else None,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


def _decision(
    *,
    session_id: str,
    policy_version: str,
    max_fallback_depth: int,
    decision: str,
    reason_code: str,
    reason: str | None,
    history_hash: str | None,
    retained_generations: list[int],
    selected_generation: int | None,
    fallback_depth: int | None,
    rejected_generations: list[JsonObject],
) -> JsonObject:
    value = {
        "session_id": session_id,
        "policy_version": policy_version,
        "max_fallback_depth": max_fallback_depth,
        "decision": decision,
        "reason_code": reason_code,
        "reason": reason,
        "checkpoint_history_hash": history_hash,
        "retained_generations": retained_generations,
        "selected_generation": selected_generation,
        "fallback_depth": fallback_depth,
        "rejected_generations": rejected_generations,
    }
    value["decision_hash"] = stable_hash(value)
    return value


def _load_decisions(store_root: str | Path, session_id: str) -> list[JsonObject]:
    path = _decision_path(store_root, session_id)
    if not path.exists():
        initialize_store(store_root)
        return []
    record = json.loads(path.read_text(encoding="utf-8"))
    expected = stable_hash({key: value for key, value in record.items() if key != "record_hash"})
    if record.get("record_hash") != expected:
        raise ValueError("recovery policy decision history integrity check failed")
    if record.get("session_id") != session_id:
        raise ValueError("recovery policy decision history session mismatch")
    decisions = list(record.get("decisions", []))
    previous = None
    for index, decision in enumerate(decisions):
        if decision.get("previous_chain_head") != previous:
            raise ValueError(f"recovery policy decision chain discontinuity at index {index}")
        rebuilt = {key: value for key, value in decision.items() if key not in {"id", "receipt_chain_head"}}
        expected_receipt = with_receipt_identity(rebuilt, previous_chain_head=previous)
        if decision.get("id") != expected_receipt["id"] or decision.get("receipt_chain_head") != expected_receipt["receipt_chain_head"]:
            raise ValueError(f"recovery policy decision integrity check failed at index {index}")
        if decision.get("production_ready") is not False or decision.get("local_only") is not True or decision.get("authorizing") is not False:
            raise ValueError("recovery policy decision authority boundary violated")
        previous = decision["receipt_chain_head"]
    return decisions


def _persist_decisions(store_root: str | Path, session_id: str, decisions: list[JsonObject]) -> None:
    record = {
        "schema_version": "1.0.0",
        "record_type": "stegtalk_mobile_shell_session_recovery_policy_decision_history",
        "session_id": session_id,
        "decisions": decisions,
        "decision_count": len(decisions),
        "chain_head": decisions[-1]["receipt_chain_head"] if decisions else None,
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "updated_at": utc_now(),
    }
    record["record_hash"] = stable_hash(record)
    _atomic_write_json(_decision_path(store_root, session_id), record)


def _decision_path(store_root: str | Path, session_id: str) -> Path:
    if not session_id or any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for character in session_id):
        raise ValueError("session_id contains unsupported characters")
    return Path(store_root) / COLLECTIONS[COLLECTION] / f"{session_id}.json"


def _atomic_write_json(path: Path, value: JsonObject) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
