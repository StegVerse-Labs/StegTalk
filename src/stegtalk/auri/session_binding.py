"""Activation-gated binding between authenticated StegTalk sessions and AURI-L1.

The binding is dormant unless a canonical activation state proves Auri is active.
It never grants execution authority and never treats session authentication alone as
sufficient authority for consequential action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .runtime import AuriSession, canonical_sha256
from .service import AuriService, ProposalResult


@dataclass(frozen=True)
class StegTalkSessionContext:
    session_id: str
    user_entity_id: str
    authenticated: bool
    device_attested: bool
    relationship_contract_ref: str | None
    activation_receipt_ref: str | None


@dataclass(frozen=True)
class SessionBindingResult:
    bound: bool
    reason_code: str
    binding_receipt: dict[str, Any]


class AuriStegTalkBinding:
    """Bind Auri advisory access to authenticated, attested StegTalk sessions."""

    def __init__(self, service: AuriService, activation_state: Mapping[str, Any]) -> None:
        self.service = service
        self.activation_state = dict(activation_state)

    def _receipt(
        self,
        *,
        context: StegTalkSessionContext,
        bound: bool,
        reason_code: str,
    ) -> dict[str, Any]:
        body = {
            "schema_version": "1.0.0",
            "receipt_type": "auri_stegtalk_session_binding",
            "auri_entity_id": "stegverse:auri",
            "activation_level": "AURI-L1",
            "session_id": context.session_id,
            "user_entity_id": context.user_entity_id,
            "authenticated": context.authenticated,
            "device_attested": context.device_attested,
            "relationship_contract_ref": context.relationship_contract_ref,
            "activation_receipt_ref": context.activation_receipt_ref,
            "bound": bound,
            "reason_code": reason_code,
            "execution_authority": False,
            "execution_performed": False,
        }
        return {**body, "receipt_sha256": canonical_sha256(body)}

    def bind(self, context: StegTalkSessionContext) -> SessionBindingResult:
        if self.activation_state.get("active") is not True:
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="auri.activation.inactive",
            )
            return SessionBindingResult(False, "auri.activation.inactive", receipt)
        if self.activation_state.get("activation_level") != "AURI-L1":
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="auri.activation_level.invalid",
            )
            return SessionBindingResult(False, "auri.activation_level.invalid", receipt)
        if not context.activation_receipt_ref:
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="auri.activation_receipt.missing",
            )
            return SessionBindingResult(False, "auri.activation_receipt.missing", receipt)
        if not context.authenticated:
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="session.authentication.required",
            )
            return SessionBindingResult(False, "session.authentication.required", receipt)
        if not context.device_attested:
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="session.device_attestation.required",
            )
            return SessionBindingResult(False, "session.device_attestation.required", receipt)
        if not context.relationship_contract_ref:
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="session.relationship_contract.required",
            )
            return SessionBindingResult(False, "session.relationship_contract.required", receipt)
        if not context.session_id.strip() or not context.user_entity_id.strip():
            receipt = self._receipt(
                context=context,
                bound=False,
                reason_code="session.identity.invalid",
            )
            return SessionBindingResult(False, "session.identity.invalid", receipt)

        receipt = self._receipt(context=context, bound=True, reason_code="ok")
        return SessionBindingResult(True, "ok", receipt)

    def submit_advisory(
        self,
        context: StegTalkSessionContext,
        request: Mapping[str, Any],
    ) -> ProposalResult:
        result = self.bind(context)
        if not result.bound:
            raise PermissionError(result.reason_code)

        enriched = dict(request)
        enriched["session"] = {
            "session_id": context.session_id,
            "user_entity_id": context.user_entity_id,
            "authenticated": True,
            "relationship_contract_ref": context.relationship_contract_ref,
        }
        proposal = self.service.submit(enriched)
        if proposal.execution_performed is not False:
            raise RuntimeError("AURI-L1 session binding must never execute")
        return proposal
