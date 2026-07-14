from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

ContainmentStatus = Literal["healthy", "quarantined", "revoked", "recovering"]


@dataclass(frozen=True)
class ContainmentState:
    entity_id: str = "stegverse:auri"
    activation_level: str = "AURI-L1"
    status: ContainmentStatus = "healthy"
    provider_enabled: bool = True
    credential_valid: bool = True
    session_allowed: bool = True
    execution_allowed: bool = False
    known_good_identity_ref: str = "auri/identity.v1.json"
    rollback_ref: str | None = None
    reason_code: str | None = None

    @property
    def fail_closed(self) -> bool:
        return (
            self.status != "healthy"
            or not self.provider_enabled
            or not self.credential_valid
            or not self.session_allowed
        )


def quarantine_provider(state: ContainmentState, reason_code: str) -> ContainmentState:
    return replace(
        state,
        status="quarantined",
        provider_enabled=False,
        session_allowed=False,
        execution_allowed=False,
        reason_code=reason_code,
    )


def revoke_credentials(state: ContainmentState, reason_code: str) -> ContainmentState:
    return replace(
        state,
        status="revoked",
        provider_enabled=False,
        credential_valid=False,
        session_allowed=False,
        execution_allowed=False,
        reason_code=reason_code,
    )


def begin_recovery(
    state: ContainmentState,
    *,
    known_good_identity_ref: str,
    rollback_ref: str,
) -> ContainmentState:
    if state.status not in {"quarantined", "revoked"}:
        raise ValueError("recovery requires quarantined or revoked state")
    if not known_good_identity_ref or not rollback_ref:
        raise ValueError("known-good identity and rollback references are required")
    return replace(
        state,
        status="recovering",
        provider_enabled=False,
        session_allowed=False,
        execution_allowed=False,
        known_good_identity_ref=known_good_identity_ref,
        rollback_ref=rollback_ref,
        reason_code="recovery.in_progress",
    )


def complete_recovery(
    state: ContainmentState,
    *,
    identity_verified: bool,
    rollback_verified: bool,
    credential_reissued: bool,
    provider_verified: bool,
) -> ContainmentState:
    if state.status != "recovering":
        raise ValueError("state must be recovering")
    gates = {
        "identity_verified": identity_verified,
        "rollback_verified": rollback_verified,
        "credential_reissued": credential_reissued,
        "provider_verified": provider_verified,
    }
    if not all(gates.values()):
        return replace(
            state,
            provider_enabled=False,
            credential_valid=False,
            session_allowed=False,
            execution_allowed=False,
            reason_code="recovery.gate_failed",
        )
    return replace(
        state,
        status="healthy",
        provider_enabled=True,
        credential_valid=True,
        session_allowed=True,
        execution_allowed=False,
        reason_code="recovery.verified",
    )
