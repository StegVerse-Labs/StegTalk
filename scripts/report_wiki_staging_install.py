from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "wiki-staging" / "data" / "install-manifest.json"


def build_install_report() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    missing = [item["source"] for item in manifest["copy_map"] if not (ROOT / item["source"]).exists()]
    return {
        "ok": not missing,
        "target_repo_status": manifest["target_repo_status"],
        "candidate_targets": manifest["target_repo_candidates"],
        "copy_count": len(manifest["copy_map"]),
        "missing_sources": missing,
        "manual_tasks_remaining": manifest["manual_tasks_remaining"],
    }


def main() -> None:
    print(json.dumps(build_install_report(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
