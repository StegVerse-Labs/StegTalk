from __future__ import annotations

import pytest

from stegtalk.auri import AuriRuntime, AuriSession


def provider(prompt, context):
    return f"proposal for {context['action']}: {prompt}"


def test_runtime_prepares_but_never_executes():
    runtime = AuriRuntime(provider, "test-provider")
    session = AuriSession("session-1", "stegverse:user:test", True)

    result = runtime.propose(
        session=session,
        instruction="Prepare a reversible repository change",
        target="StegVerse-Labs/StegTalk",
        action="prepare_repository_change",
        evidence_refs=["auri/identity.v1.json"],
        policy_ref="policy:test",
        delegation_ref="delegation:prepare-only",
        rollback_ref="git:revert",
    )

    assert result.execution_performed is False
    assert result.candidate["auri_posture"]["execution_authority"] is False
    assert result.candidate["proposal"]["classification"] == "untrusted_candidate_until_evaluated"
    assert result.advisory_receipt["execution_performed"] is False
    assert result.advisory_receipt["authority_decision_ref"] is None


def test_runtime_rejects_unauthenticated_session():
    runtime = AuriRuntime(provider, "test-provider")
    session = AuriSession("session-2", "stegverse:user:test", False)

    with pytest.raises(PermissionError):
        runtime.propose(
            session=session,
            instruction="Prepare a change",
            target="StegVerse-Labs/StegTalk",
            action="prepare_repository_change",
        )


def test_provider_must_return_text():
    runtime = AuriRuntime(lambda _prompt, _context: {"bad": "output"}, "bad-provider")
    session = AuriSession("session-3", "stegverse:user:test", True)

    with pytest.raises(TypeError):
        runtime.propose(
            session=session,
            instruction="Prepare a change",
            target="StegVerse-Labs/StegTalk",
            action="prepare_repository_change",
        )
