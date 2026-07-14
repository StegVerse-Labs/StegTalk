from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.entity_runtime import create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_receipts import (
    persist_session_with_receipt,
    restore_session_with_receipt,
    summarize_session_receipts,
)


def verify() -> dict[str, object]:
    shell = create_mobile_shell(
        identity_card=create_entity_card(
            entity_id="verification-user",
            display_name="Verification User",
            entity_type="human",
            purpose="unattended receipt verification",
        )
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        persisted, chain = persist_session_with_receipt(
            store_root=root,
            shell=shell,
            session_id="verification-session",
        )
        restored, chain = restore_session_with_receipt(
            store_root=root,
            session_id="verification-session",
            chain=chain,
        )
    summary = summarize_session_receipts(chain)
    return {
        "ok": persisted is not None and restored is not None and summary["verified"] is True,
        "receipt_count": summary["receipt_count"],
        "events": summary["events"],
        "chain_head": summary["chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
