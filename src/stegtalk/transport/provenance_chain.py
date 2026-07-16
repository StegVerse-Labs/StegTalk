from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json


@dataclass(frozen=True)
class ProvenanceChain:
    message_id: str
    adapter_receipt_hash: str
    selection_receipt_hash: str
    custody_receipt_hash: str
    observation_provenance_hash: str
    previous_chain_hash: str | None
    chain_hash: str
    delivery_claimed: bool = False
    execution_authority_granted: bool = False


def _hash(parts: dict[str, object]) -> str:
    payload = json.dumps(parts, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(payload).hexdigest()


def build_provenance_chain(
    *,
    message_id: str,
    adapter_receipt_hash: str,
    selection_receipt_hash: str,
    custody_receipt_hash: str,
    observation_provenance_hash: str,
    previous_chain_hash: str | None = None,
) -> ProvenanceChain:
    required = {
        "message_id": message_id,
        "adapter_receipt_hash": adapter_receipt_hash,
        "selection_receipt_hash": selection_receipt_hash,
        "custody_receipt_hash": custody_receipt_hash,
        "observation_provenance_hash": observation_provenance_hash,
    }
    if any(not value for value in required.values()):
        raise ValueError("all provenance inputs are required")
    chain_hash = _hash({**required, "previous_chain_hash": previous_chain_hash})
    return ProvenanceChain(**required, previous_chain_hash=previous_chain_hash, chain_hash=chain_hash)


def verify_provenance_chain(chain: ProvenanceChain) -> bool:
    expected = _hash({
        "message_id": chain.message_id,
        "adapter_receipt_hash": chain.adapter_receipt_hash,
        "selection_receipt_hash": chain.selection_receipt_hash,
        "custody_receipt_hash": chain.custody_receipt_hash,
        "observation_provenance_hash": chain.observation_provenance_hash,
        "previous_chain_hash": chain.previous_chain_hash,
    })
    return (
        chain.chain_hash == expected
        and chain.delivery_claimed is False
        and chain.execution_authority_granted is False
    )
