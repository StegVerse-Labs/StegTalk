"""Provider-neutral, no-execution AURI-L1 advisory runtime."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Mapping

ModelProvider = Callable[[str, Mapping[str, Any]], str]


@dataclass(frozen=True)
class AuriSession:
    session_id: str
    user_entity_id: str
    authenticated: bool
    relationship_contract_ref: str | None = None


@dataclass(frozen=True)
class ProposalResult:
    candidate: dict[str, Any]
    advisory_receipt: dict[str, Any]
    execution_performed: bool = False


class AuriRuntime:
    """Prepare governed advisory candidates without executing them."""

    entity_id = "stegverse:auri"
    activation_level = "AURI-L1"

    def __init__(self, provider: ModelProvider, provider_id: str) -> None:
        if not callable(provider):
            raise TypeError("provider must be callable")
        if not provider_id.strip():
            raise ValueError("provider_id must be non-empty")
        self._provider = provider
        self.provider_id = provider_id

    def propose(
        self,
        *,
        session: AuriSession,
        instruction: str,
        target: str,
        action: str,
        scope: str = "advisory_only",
        evidence_refs: list[str] | None = None,
        policy_ref: str | None = None,
        delegation_ref: str | None = None,
        consequential: bool = False,
        reversible: bool = True,
        rollback_ref: str | None = None,
    ) -> ProposalResult:
        if not session.authenticated:
            raise PermissionError("authenticated session required")
        if not instruction.strip() or not target.strip() or not action.strip():
            raise ValueError("instruction, target, and action are required")

        evidence = list(evidence_refs or [])
        provider_context = {
            "auri_entity_id": self.entity_id,
            "activation_level": self.activation_level,
            "session_id": session.session_id,
            "user_entity_id": session.user_entity_id,
            "target": target,
            "action": action,
            "scope": scope,
            "evidence_refs": evidence,
            "model_output_classification": "untrusted_candidate_until_evaluated",
        }
        model_output = self._provider(instruction, provider_context)
        if not isinstance(model_output, str):
            raise TypeError("provider output must be text")

        digest_input = "\n".join(
            [self.entity_id, session.session_id, session.user_entity_id, instruction, model_output]
        ).encode("utf-8")
        candidate_id = f"auri:{sha256(digest_input).hexdigest()}"

        candidate = {
            "schema_version": "1.0.0",
            "candidate_id": candidate_id,
            "actor": {
                "entity_id": session.user_entity_id,
                "authenticated": True,
            },
            "prepared_by": self.entity_id,
            "action": action,
            "target": target,
            "scope": scope,
            "policy_ref": policy_ref,
            "delegation_ref": delegation_ref,
            "evidence_refs": evidence,
            "execution_context": {
                "environment": "runtime",
                "consequential": consequential,
            },
            "recoverability": {
                "reversible": reversible,
                "rollback_ref": rollback_ref,
            },
            "requested_authority_class": (
                "consequential" if consequential else "advisory"
            ),
            "auri_posture": {
                "execution_authority": False,
                "final_consequence_authority": False,
                "requires_external_admissibility": True,
            },
            "proposal": {
                "instruction": instruction,
                "model_output": model_output,
                "classification": "untrusted_candidate_until_evaluated",
            },
        }

        receipt = {
            "schema_version": "1.0.0",
            "receipt_type": "auri_advisory_output",
            "auri_entity_id": self.entity_id,
            "session_id": session.session_id,
            "user_entity_id": session.user_entity_id,
            "provider_id": self.provider_id,
            "candidate_id": candidate_id,
            "candidate_sha256": sha256(
                repr(sorted(candidate.items())).encode("utf-8")
            ).hexdigest(),
            "execution_performed": False,
            "authority_decision_ref": None,
        }
        return ProposalResult(candidate=candidate, advisory_receipt=receipt)
