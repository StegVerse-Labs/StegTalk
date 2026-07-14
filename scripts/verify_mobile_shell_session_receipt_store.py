from __future__ import annotations

import json
import tempfile
from pathlib import Path

from stegtalk.mobile_shell_session_receipt_store import (
    append_and_restore_receipt,
    inspect_persisted_receipt_chain,
)
from stegtalk.mobile_shell_session_receipts import create_session_event_receipt


def verify() -> dict[str, object]:
    first = create_session_event_receipt(
        session_id="verification-session",
        event="persist",
        result="success",
    )
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        record, restored = append_and_restore_receipt(
            store_root=root,
            session_id="verification-session",
            receipt=first,
        )
        second = create_session_event_receipt(
            session_id="verification-session",
            event="restore",
            result="success",
            previous_chain_head=restored[-1]["receipt_chain_head"],
        )
        record, restored = append_and_restore_receipt(
            store_root=root,
            session_id="verification-session",
            receipt=second,
        )
        report = inspect_persisted_receipt_chain(
            store_root=root,
            session_id="verification-session",
        )
    return {
        "ok": record["receipt_count"] == 2 and len(restored) == 2,
        "receipt_count": report["receipt_count"],
        "events": report["events"],
        "chain_head": report["chain_head"],
        "production_ready": False,
        "local_only": True,
        "authorizing": False,
        "manual_tasks_required": [],
    }


if __name__ == "__main__":
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)
