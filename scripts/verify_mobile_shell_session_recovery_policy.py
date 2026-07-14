from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import rotate_managed_checkpoint
from stegtalk.mobile_shell_session_recovery_policy import recover_session_under_policy


def verify() -> dict[str, object]:
    shell = create_mobile_shell(
        identity_card=create_entity_card(
            entity_id="verification-user",
            display_name="Verification User",
            entity_type="human",
            purpose="unattended recovery policy verification",
        )
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        rotate_managed_checkpoint(store_root=root, shell=shell, session_id="verification-session")
        recovered, decision = recover_session_under_policy(
            store_root=root,
            session_id="verification-session",
            policy_version="stegtalk-recovery-policy-v1",
            max_fallback_depth=1,
        )
    return {
        "ok": recovered is not None and decision["decision"] == "ALLOW",
        "policy_version": decision["policy_version"],
        "decision": decision["decision"],
        "reason_code": decision["reason_code"],
        "decision_hash": decision["decision_hash"],
        "recovery_receipt_bound": bool(decision["recovery_receipt_id"]),
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
