from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_device_continuity_receipt_validates() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, str(root / "tools" / "validate_device_continuity_receipt.py")],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
