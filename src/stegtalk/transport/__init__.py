"""Transport selection and relay-governance primitives for StegTalk.

This package evaluates declared message constraints against observed bearer state.
It does not create network, execution, identity, responder, or emergency authority.
"""

from .density import (
    RelayCandidate,
    RelayContext,
    RelayDecision,
    RelayPolicy,
    classify_density,
    govern_relay,
    message_fingerprint,
    relay_scan_interval_seconds,
)
from .selector import (
    BearerObservation,
    SelectionPolicy,
    TransportDecision,
    TransportRequest,
    select_transport,
)

__all__ = [
    "BearerObservation",
    "RelayCandidate",
    "RelayContext",
    "RelayDecision",
    "RelayPolicy",
    "SelectionPolicy",
    "TransportDecision",
    "TransportRequest",
    "classify_density",
    "govern_relay",
    "message_fingerprint",
    "relay_scan_interval_seconds",
    "select_transport",
]
