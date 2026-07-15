"""Transport selection primitives for StegTalk.

This package evaluates already-declared message constraints against observed bearer
conditions. It does not create network, execution, identity, or emergency authority.
"""

from .selector import (
    BearerObservation,
    SelectionPolicy,
    TransportDecision,
    TransportRequest,
    select_transport,
)

__all__ = [
    "BearerObservation",
    "SelectionPolicy",
    "TransportDecision",
    "TransportRequest",
    "select_transport",
]
