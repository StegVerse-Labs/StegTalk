from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import build_discovery_record, create_entity_card
from stegtalk.mobile_shell import create_local_message, create_mobile_shell
from stegtalk.mobile_shell_session_receipts import (
    persist_session_with_receipt,
    restore_session_with_receipt,
    summarize_session_receipts,
)


def verify() -> dict[str, object]:
    user = create_entity_card(
        entity_id="verification-user",
        display_name="Verification User",
        entity_type="human",
        purpose="unattended local verification",
    )
    contact = create_entity_card(
        entity_id="verification-assistant",
        display_name="Verification Assistant",
        entity_type="assistant",
        purpose="local verification contact",
    )
    shell = create_mobile_shell(
        identity_card=user,
        contacts=[contact],
        discovery_index=build_discovery_index([build_discovery_record(contact)]),
    )
    shell, _ = create_local_message(
        shell,
        receiver_hint="Verification Assistant",
        body="unattended receipt verification",
    )
    with tempfile.TemporaryDirectory() as directory:
        persisted, chain = persist_session_with_receipt(
            store_root=Path(directory),
            shell=shell,
            session_id="verification-session",
        )
        restored, chain = restore_session_with_receipt(
            store_root=Path(directory),
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
