from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mirror_handoff_exists_and_preserves_activation_boundary():
    handoff = (ROOT / "STEGTALK_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    assert "current handoff and task source of truth" in handoff
    assert "StegVerse-Labs/StegTalk" in handoff
    assert "Production ready: `false`" in handoff
    assert "QUEUE_ONLY_NO_DOWNSTREAM_MUTATION" in handoff
    assert "ST-025" in handoff
    assert "mobile_shell_persistent_session_boundary" in handoff
    assert "mobile_shell_session_receipt_chain" in handoff
    assert "network, execution, external-account, or native-platform authority" in handoff
