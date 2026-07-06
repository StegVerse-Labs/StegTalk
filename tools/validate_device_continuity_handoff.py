#!/usr/bin/env python3
"""Validate installed Device Continuity Layer handoff payload for StegTalk."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "fixtures" / "device-continuity" / "stegtalk-device-continuity-handoff.json"

ALLOWED = {
    "accepted_observe_only",
    "accepted_read_control",
    "manual_review_required",
    "denied",
}


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    if payload["destination_repo"] != "StegVerse-Labs/StegTalk":
        raise SystemExit("wrong destination repo")
    if payload["status"] != "installed_non_authorizing_handoff":
        raise SystemExit("unexpected handoff status")
    contract = ROOT / payload["contract"]
    if not contract.exists():
        raise SystemExit("missing handoff contract")
    receipt = ROOT / payload["sample_receipt"]
    if not receipt.exists():
        raise SystemExit("missing sample receipt")
    decisions = set(payload["allowed_destination_decisions"])
    if not decisions <= ALLOWED:
        raise SystemExit("unexpected destination decision")
    if "handoff candidates only" not in payload["non_authority_rule"]:
        raise SystemExit("missing non-authority rule")
    print("StegTalk Device Continuity handoff validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
