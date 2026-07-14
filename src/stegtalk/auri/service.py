"""Deployment-neutral AURI-L1 service boundary.

This module exposes health and advisory request handling without binding Auri to a
web framework, hosting provider, model vendor, or execution authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .containment import ContainmentState
from .runtime import AuriRuntime, AuriSession, ProposalResult, canonical_sha256


@dataclass(frozen=True)
class ServiceHealth:
    entity_id: str
    activation_level: str
    status: str
    ready_for_advisory_requests: bool
    execution_authority: bool
    containment_fail_closed: bool
    provider_id: str
    identity_ref: str
    health_sha256: str


class AuriService:
    """Provider-neutral service facade for the governed advisory runtime."""

    def __init__(
        self,
        runtime: AuriRuntime,
        *,
        containment: ContainmentState | None = None,
        identity_ref: str = "auri/identity.v1.json",
    ) -> None:
        self.runtime = runtime
        self.containment = containment or ContainmentState()
        self.identity_ref = identity_ref

    def health(self) -> ServiceHealth:
        ready = not self.containment.fail_closed
        body = {
            "entity_id": self.runtime.entity_id,
            "activation_level": self.runtime.activation_level,
            "status": "ready" if ready else "fail_closed",
            "ready_for_advisory_requests": ready,
            "execution_authority": False,
            "containment_fail_closed": self.containment.fail_closed,
            "provider_id": self.runtime.provider_id,
            "identity_ref": self.identity_ref,
        }
        return ServiceHealth(**body, health_sha256=canonical_sha256(body))

    def submit(self, request: Mapping[str, Any]) -> ProposalResult:
        health = self.health()
        if not health.ready_for_advisory_requests:
            raise PermissionError("Auri service is fail-closed")

        session_data = request.get("session")
        if not isinstance(session_data, Mapping):
            raise ValueError("session object is required")
        session = AuriSession(
            session_id=str(session_data.get("session_id", "")),
            user_entity_id=str(session_data.get("user_entity_id", "")),
            authenticated=session_data.get("authenticated") is True,
            relationship_contract_ref=session_data.get("relationship_contract_ref"),
        )
        return self.runtime.propose(
            session=session,
            instruction=str(request.get("instruction", "")),
            target=str(request.get("target", "")),
            action=str(request.get("action", "")),
            scope=str(request.get("scope", "advisory_only")),
            evidence_refs=list(request.get("evidence_refs") or []),
            policy_ref=request.get("policy_ref"),
            delegation_ref=request.get("delegation_ref"),
            consequential=request.get("consequential") is True,
            reversible=request.get("reversible") is not False,
            rollback_ref=request.get("rollback_ref"),
        )

    def health_document(self) -> dict[str, Any]:
        return asdict(self.health())
