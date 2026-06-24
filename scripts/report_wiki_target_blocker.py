from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUEST_PATH = ROOT / "wiki-staging" / "data" / "target-repo-request.json"
CHECKLIST_PATH = ROOT / "wiki-staging" / "data" / "install-checklist.json"


def build_blocker_report() -> dict:
    request = json.loads(REQUEST_PATH.read_text(encoding="utf-8"))
    checklist = json.loads(CHECKLIST_PATH.read_text(encoding="utf-8"))
    open_checks = [check for check in checklist["checks"] if check["status"] != "complete"]
    return {
        "ok": request["staged_package_ready"] is True,
        "preferred_repo": request["preferred_repo"],
        "current_status": request["current_status"],
        "open_check_count": len(open_checks),
        "open_checks": open_checks,
        "manual_inventory_required": request["manual_inventory_required"],
        "manual_tasks_remaining": checklist["manual_tasks_remaining"],
    }


def main() -> None:
    print(json.dumps(build_blocker_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
