from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mirror_handoff_exists_and_preserves_activation_boundary():
    handoff = (ROOT / "STEGTALK_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    assert "current handoff and task source of truth" in handoff
    assert "StegVerse-Labs/StegTalk" in handoff
    assert "Production ready: false" in handoff
    assert "Active tasks: ST-029, ST-030" in handoff
    assert "Production activation: NOT ACTIVE" in handoff
    assert "Claim state: OPEN" in handoff
    assert "KnowledgeVault" in handoff
    assert "device_authority = false" in handoff
    assert "device_continuity_authority = false" in handoff
    assert "vault_continuity_authority = true" in handoff
    assert "source implementation != validation" in handoff
    assert "DO NOT archive as complete" in handoff
