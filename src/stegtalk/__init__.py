"""StegTalk managed-completion bootstrap and entity-runtime slice.

This package establishes repository-managed continuation state for the StegTalk build lane
and a minimal local-first entity runtime. It does not claim production secure messaging,
production cryptography, production token settlement, or completed activation.
"""

from .entity_runtime import (
    build_discovery_record,
    commit_change,
    create_change_request,
    create_entity_card,
    create_relationship_contract,
    evaluate_readiness,
    fork_entity,
    recognize_entity,
    rely_on_entity,
    revoke_reliance,
    transition_entity,
)

__version__ = "entity-runtime-v1"

__all__ = [
    "build_discovery_record",
    "commit_change",
    "create_change_request",
    "create_entity_card",
    "create_relationship_contract",
    "evaluate_readiness",
    "fork_entity",
    "recognize_entity",
    "rely_on_entity",
    "revoke_reliance",
    "transition_entity",
]
