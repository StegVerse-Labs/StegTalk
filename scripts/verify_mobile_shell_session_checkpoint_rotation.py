from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card, stable_hash
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_checkpoint_rotation import (
    inspect_checkpoint_history,
    restore_latest_valid_checkpoint,
    rotate_managed_checkpoint,
)


def _shell(view: str):
    shell = create_mobile_shell(
        identity_card=create_entity_card(
            entity_id="verification-user",
            display_name="Verification User",
            entity_type="human",
            purpose="checkpoint rotation verification",
        )
    )
    shell["shell_state"]["active_view"] = view
    shell["mobile_shell_hash"] = stable_hash({key: value for key, value in shell.items() if key != "mobile_shell_hash"})
    return shell


def verify() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for view in ("home", "contacts", "inbox", "discovery"):
            rotate_managed_checkpoint(store_root=root, shell=_shell(view), session_id="verification-session", retention=3)
        inspection = inspect_checkpoint_history(store_root=root, session_id="verification-session")
        restored = restore_latest_valid_checkpoint(store_root=root, session_id="verification-session")
    return {
        "ok": inspection["retained_generations"] == [2, 3, 4] and restored["generation"] == 4 and restored["verified"] is True,
        "retained_generations": inspection["retained_generations"],
        "restored_generation": restored["generation"],
        "fallback_used": restored["fallback_used"],
        "manual_tasks_required": [],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
