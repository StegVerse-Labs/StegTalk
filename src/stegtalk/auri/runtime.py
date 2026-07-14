"""Provider-neutral, no-execution AURI-L1 advisory runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Mapping

ModelProvider = Callable[[str, Mapping[str, Any]], str]


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for cross-runtime receipt hashing."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


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


class AuriProviderError(RuntimeError):
    """Fail-closed provider failure carrying machine-readable quarantine evidence."""

    def __init__(self, classification: str, receipt: dict[str, Any]) -> None:
        super().__init__(classification)
        self.classification = classification
        self.receipt = receipt
        self.quarantine_required = True


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

    def _provider_failure_receipt(
        self,
        *,
        session: AuriSession,
        classification: str,
        detail: str,
    ) -> dict[str, Any]:
        body = {
            "schema_version": "1.0.0",
            "receipt_type": "auri_provider_failure",
            "auri_entity_id": self.entity_id,
            "activation_level": self.activation_level,
            "session_id": session.session_id,
            "user_entity_id": session.user_entity_id,
            "provider_id": self.provider_id,
            "classification": classification,
            "detail": detail,
            "quarantine_signal": True,
            "provider_disabled_for_session": True,
            "execution_performed": False,
            "retry_performed": False,
        }
        return {**body, "receipt_sha256": canonical_sha256(body)}

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
        if not session.session_id.strip() or not session.user_entity_id.strip():
            raise ValueError("session_id and user_entity_id are required")
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
        try:
            model_output = self._provider(instruction, provider_context)
        except Exception as exc:
            receipt = self._provider_failure_receipt(
                session=session,
                classification="provider_exception",
                detail=f"{type(exc).__name__}: {exc}",
            )
            raise AuriProviderError("provider_exception", receipt) from exc

        if not isinstance(model_output, str):
            receipt = self._provider_failure_receipt(
                session=session,
                classification="invalid_provider_output_type",
                detail=type(model_output).__name__,
            )
            raise AuriProviderError("invalid_provider_output_type", receipt)
        if not model_output.strip():
            receipt = self._provider_failure_receipt(
                session=session,
                classification="empty_provider_output",
                detail="provider returned empty text",
            )
            raise AuriProviderError("empty_provider_output", receipt)

        candidate_seed = {
            "auri_entity_id": self.entity_id,
            "session_id": session.session_id,
            "user_entity_id": session.user_entity_id,
            "instruction": instruction,
            "model_output": model_output,
            "target": target,
            "action": action,
        }
        candidate_id = f"auri:{canonical_sha256(candidate_seed)}"

        candidate = {
            "schema_version": "1.0.0",
            "candidate_id": candidate_id,
            "actor": {
                "entity_id": session.user_entity_id,
                "authenticated": True,
            },
            "prepared_by": self.entity_id,
            "relationship_contract_ref": session.relationship_contract_ref,
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

        candidate_hash = canonical_sha256(candidate)
        receipt_body = {
            "schema_version": "1.0.0",
            "receipt_type": "auri_advisory_output",
            "auri_entity_id": self.entity_id,
            "session_id": session.session_id,
            "user_entity_id": session.user_entity_id,
            "provider_id": self.provider_id,
            "candidate_id": candidate_id,
            "candidate_sha256": candidate_hash,
            "canonicalization": "RFC8785-compatible-json-subset-v1",
            "execution_performed": False,
            "authority_decision_ref": None,
            "quarantine_signal": False,
        }
        receipt = {**receipt_body, "receipt_sha256": canonical_sha256(receipt_body)}
        return ProposalResult(candidate=candidate, advisory_receipt=receipt)
