from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint import create_managed_checkpoint, restore_managed_checkpoint


def verify() -> dict[str, object]:
    shell = create_mobile_shell(identity_card=create_entity_card(entity_id="verification-user", display_name="Verification User", entity_type="human", purpose="checkpoint verification"))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        created = create_managed_checkpoint(store_root=root, shell=shell, session_id="verification-session")
        restored = restore_managed_checkpoint(store_root=root, session_id="verification-session")
    return {
        "ok": restored["verified"] is True,
        "checkpoint_hash": created["checkpoint_hash"],
        "receipt_chain_head": created["receipt_chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
