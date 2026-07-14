from __future__ import annotations

import json
from pathlib import Path

import pytest

from stegtalk.entity_runtime import create_entity_card, stable_hash
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import rotate_managed_checkpoint
from stegtalk.mobile_shell_session_recovery_policy import (
    classify_recovery_reason,
    evaluate_recovery_policy,
    inspect_recovery_policy_decisions,
    recover_session_under_policy,
)


def _shell():
    return create_mobile_shell(
        identity_card=create_entity_card(
            entity_id="rigel",
            display_name="Rigel",
            entity_type="human",
            purpose="local recovery policy test",
        )
    )


def _rotate(root: Path, count: int = 3) -> None:
    shell = _shell()
    for _ in range(count):
        rotate_managed_checkpoint(store_root=root, shell=shell, session_id="primary", retention=3)


def _corrupt_generations(root: Path, generations: set[int]) -> None:
    path = root / "mobile_shell_session_checkpoint_history" / "primary.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    for entry in record["entries"]:
        if entry["generation"] in generations:
            entry["checkpoint_hash"] = "sha256:tampered"
    record["history_hash"] = stable_hash({key: value for key, value in record.items() if key != "history_hash"})
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_reason_classification_is_deterministic():
    assert classify_recovery_reason("checkpoint entry authority boundary violated") == "authority_violation"
    assert classify_recovery_reason("checkpoint entry receipt head mismatch") == "receipt_chain_failure"
    assert classify_recovery_reason("checkpoint entry shell integrity check failed") == "shell_integrity_failure"
    assert classify_recovery_reason("checkpoint history session mismatch") == "cross_session_state"


def test_policy_allows_newest_valid_checkpoint(tmp_path):
    _rotate(tmp_path, 1)
    decision = evaluate_recovery_policy(store_root=tmp_path, session_id="primary")
    assert decision["decision"] == "ALLOW"
    assert decision["reason_code"] == "newest_valid_checkpoint"
    assert decision["fallback_depth"] == 0
    assert decision["policy_version"] == "stegtalk-recovery-policy-v1"


def test_policy_allows_fallback_within_limit_and_binds_receipt(tmp_path):
    _rotate(tmp_path)
    _corrupt_generations(tmp_path, {3})
    recovered, decision = recover_session_under_policy(
        store_root=tmp_path,
        session_id="primary",
        policy_version="test-policy-v1",
        max_fallback_depth=1,
    )
    assert recovered is not None
    assert decision["decision"] == "ALLOW"
    assert decision["reason_code"] == "admissible_fallback"
    assert decision["fallback_depth"] == 1
    assert decision["recovery_receipt_id"]
    assert decision["recovery_receipt_chain_head"]
    assert decision["checkpoint_history_hash"]


def test_policy_denies_fallback_beyond_limit_without_recovery_receipt(tmp_path):
    _rotate(tmp_path)
    _corrupt_generations(tmp_path, {2, 3})
    recovered, decision = recover_session_under_policy(
        store_root=tmp_path,
        session_id="primary",
        max_fallback_depth=1,
    )
    assert recovered is None
    assert decision["decision"] == "DENY"
    assert decision["reason_code"] == "fallback_depth_exceeded"
    assert decision["fallback_depth"] == 2
    assert decision["recovery_receipt_id"] is None


def test_policy_denies_when_all_retained_generations_fail(tmp_path):
    _rotate(tmp_path)
    _corrupt_generations(tmp_path, {1, 2, 3})
    recovered, decision = recover_session_under_policy(store_root=tmp_path, session_id="primary")
    assert recovered is None
    assert decision["decision"] == "DENY"
    assert decision["reason_code"] == "all_retained_generations_failed"


def test_policy_version_is_required(tmp_path):
    _rotate(tmp_path, 1)
    with pytest.raises(ValueError, match="policy version"):
        evaluate_recovery_policy(store_root=tmp_path, session_id="primary", policy_version="")


def test_policy_decision_history_is_chained_and_payload_free(tmp_path):
    _rotate(tmp_path, 1)
    recover_session_under_policy(store_root=tmp_path, session_id="primary")
    recover_session_under_policy(store_root=tmp_path, session_id="primary")
    summary = inspect_recovery_policy_decisions(store_root=tmp_path, session_id="primary")
    assert summary["decision_count"] == 2
    assert summary["decisions"] == ["ALLOW", "ALLOW"]
    assert summary["chain_head"].startswith("sha256:")
    assert summary["authorizing"] is False
    assert "shell" not in summary


def test_policy_decision_history_tampering_fails_closed(tmp_path):
    _rotate(tmp_path, 1)
    recover_session_under_policy(store_root=tmp_path, session_id="primary")
    path = tmp_path / "mobile_shell_session_recovery_policy_decisions" / "primary.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"decision": "ALLOW"', '"decision": "DENY"', 1), encoding="utf-8")
    with pytest.raises(ValueError, match="integrity"):
        inspect_recovery_policy_decisions(store_root=tmp_path, session_id="primary")
