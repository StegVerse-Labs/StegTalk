from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import rotate_managed_checkpoint
from stegtalk.mobile_shell_session_recovery_receipt import recover_session_with_receipt


def verify() -> dict[str, object]:
    shell = create_mobile_shell(identity_card=create_entity_card(entity_id="verification-user", display_name="Verification User", entity_type="human", purpose="unattended recovery verification"))
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        rotate_managed_checkpoint(store_root=root, shell=shell, session_id="verification-session")
        recovered, receipt = recover_session_with_receipt(store_root=root, session_id="verification-session")
    return {
        "ok": recovered is not None and receipt["result"] == "recovered",
        "selected_generation": receipt["selected_generation"],
        "fallback_used": receipt["fallback_used"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
