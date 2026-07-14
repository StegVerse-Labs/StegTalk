from __future__ import annotations

from stegtalk.auri.containment import (
    ContainmentState,
    begin_recovery,
    complete_recovery,
    quarantine_provider,
    revoke_credentials,
)


def test_provider_quarantine_is_fail_closed():
    state = quarantine_provider(ContainmentState(), "provider.output.invalid")
    assert state.status == "quarantined"
    assert state.provider_enabled is False
    assert state.session_allowed is False
    assert state.execution_allowed is False
    assert state.fail_closed is True


def test_credential_revocation_is_fail_closed():
    state = revoke_credentials(ContainmentState(), "credential.compromised")
    assert state.status == "revoked"
    assert state.credential_valid is False
    assert state.session_allowed is False
    assert state.fail_closed is True


def test_recovery_fails_closed_until_all_gates_pass():
    state = quarantine_provider(ContainmentState(), "provider.output.invalid")
    recovering = begin_recovery(
        state,
        known_good_identity_ref="auri/identity.v1.json",
        rollback_ref="git:known-good",
    )
    failed = complete_recovery(
        recovering,
        identity_verified=True,
        rollback_verified=True,
        credential_reissued=False,
        provider_verified=True,
    )
    assert failed.status == "recovering"
    assert failed.fail_closed is True
    assert failed.execution_allowed is False


def test_verified_recovery_restores_advisory_session_only():
    state = revoke_credentials(ContainmentState(), "credential.compromised")
    recovering = begin_recovery(
        state,
        known_good_identity_ref="auri/identity.v1.json",
        rollback_ref="git:known-good",
    )
    restored = complete_recovery(
        recovering,
        identity_verified=True,
        rollback_verified=True,
        credential_reissued=True,
        provider_verified=True,
    )
    assert restored.status == "healthy"
    assert restored.provider_enabled is True
    assert restored.session_allowed is True
    assert restored.execution_allowed is False
    assert restored.fail_closed is False
