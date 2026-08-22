from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_mirror_handoff_exists_and_preserves_activation_boundary():
    handoff = (ROOT / "STEGTALK_MIRROR_HANDOFF.md").read_text(encoding="utf-8")
    assert "current handoff and task source of truth" in handoff
    assert "StegVerse-Labs/StegTalk" in handoff
    assert "Production ready: false" in handoff
    assert "Active tasks: ST-029, ST-030, ST-031" in handoff
    assert "Production activation: NOT ACTIVE" in handoff
    assert "Claim state: OPEN" in handoff
    assert "Durable continuity host: KnowledgeVault" in handoff
    assert "Device role: EPHEMERAL_TRANSPORT_EDGE" in handoff
    assert "Final bearer admissibility + selection authority: StegTalk" in handoff
    assert "KnowledgeVault = durable intent, attempt, selection receipt, replay, reconstruction authority" in handoff
    assert "ephemeral capability advertisement + execution" in handoff
    assert "capability alone never grants execution authority" in handoff
    assert "INDETERMINATE / timeout-after-dispatch -> VERIFY_EXTERNALLY" in handoff
    assert "DO NOT archive as complete" in handoff
