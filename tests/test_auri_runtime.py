from __future__ import annotations

import pytest

from stegtalk.auri import (
    AuriProviderError,
    AuriRuntime,
    AuriSession,
    canonical_sha256,
)


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
    assert result.advisory_receipt["quarantine_signal"] is False
    assert result.advisory_receipt["candidate_sha256"] == canonical_sha256(result.candidate)


def test_canonical_hash_is_order_independent():
    assert canonical_sha256({"b": 2, "a": 1}) == canonical_sha256({"a": 1, "b": 2})


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


def test_provider_invalid_output_fails_closed_and_signals_quarantine():
    runtime = AuriRuntime(lambda _prompt, _context: {"bad": "output"}, "bad-provider")
    session = AuriSession("session-3", "stegverse:user:test", True)

    with pytest.raises(AuriProviderError) as captured:
        runtime.propose(
            session=session,
            instruction="Prepare a change",
            target="StegVerse-Labs/StegTalk",
            action="prepare_repository_change",
        )

    error = captured.value
    assert error.classification == "invalid_provider_output_type"
    assert error.quarantine_required is True
    assert error.receipt["quarantine_signal"] is True
    assert error.receipt["provider_disabled_for_session"] is True
    assert error.receipt["execution_performed"] is False
    assert error.receipt["retry_performed"] is False


def test_provider_exception_fails_closed_without_retry():
    def broken_provider(_prompt, _context):
        raise TimeoutError("provider unavailable")

    runtime = AuriRuntime(broken_provider, "timeout-provider")
    session = AuriSession("session-4", "stegverse:user:test", True)

    with pytest.raises(AuriProviderError) as captured:
        runtime.propose(
            session=session,
            instruction="Prepare a change",
            target="StegVerse-Labs/StegTalk",
            action="prepare_repository_change",
        )

    assert captured.value.classification == "provider_exception"
    assert captured.value.receipt["retry_performed"] is False
    assert captured.value.receipt["execution_performed"] is False
