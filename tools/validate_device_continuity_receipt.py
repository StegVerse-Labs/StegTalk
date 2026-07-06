#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "fixtures" / "device-continuity" / "stegtalk-device-continuity-handoff.json"
RECEIPT = ROOT / "receipts" / "device-continuity" / "stegtalk-device-continuity-receipt.json"


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    if receipt["payload_id"] != payload["payload_id"]:
        raise SystemExit("payload mismatch")
    if receipt["destination_repo"] != payload["destination_repo"]:
        raise SystemExit("destination mismatch")
    if receipt["decision"] not in payload["allowed_destination_decisions"]:
        raise SystemExit("decision not allowed")
    if receipt.get("reconstructable") is not True:
        raise SystemExit("receipt must be reconstructable")
    print("StegTalk Device Continuity receipt validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
