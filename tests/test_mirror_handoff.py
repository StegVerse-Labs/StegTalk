from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mirror_handoff_exists_and_preserves_activation_boundary():
    handoff = (ROOT / "STEGTALK_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    assert "current handoff and task source of truth" in handoff
    assert "StegVerse-Labs/StegTalk" in handoff
    assert "production_ready` remains false" in handoff
    assert "account-lane release handoff refresh" in handoff
