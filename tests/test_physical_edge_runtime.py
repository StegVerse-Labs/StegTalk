from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from stegtalk.physical_edge_runtime import (
    RuntimeExecutionError,
    dispatch_selected_sms,
    prepare_runtime_attempt,
    record_runtime_outcome,
)


class FakeStore:
    def __init__(self) -> None:
        self.attempts = []
        self.receipts = []
        self.recovery = []

    def append_attempt(self, attempt_id, record):
        self.attempts.append((attempt_id, record))
        return Path(f"/tmp/{attempt_id}.attempt")

    def append_receipt(self, stream_id, record):
        self.receipts.append((stream_id, record))
        return Path(f"/tmp/{stream_id}.receipt")

    def append_recovery(self, attempt_id, record):
        self.recovery.append((attempt_id, record))
        return Path(f"/tmp/{attempt_id}.recovery")


def ad(edge_id: str, bearer: str, score: float, *, modem_path: str | None = None):
    capabilities = {
        "local_bearers": [bearer],
        "requires_relay": False,
        "store_and_forward": False,
    }
    if modem_path:
        capabilities["modem_path"] = modem_path
    metrics = {
        "security": score,
        "privacy": score,
        "recipient_compatibility": score,
        "reliability": score,
        "receipt_quality": score,
        "bidirectionality": score,
        "resilience": score,
        "latency": score,
        "bandwidth": score,
        "cost": score,
        "energy": score,
        "metadata_minimization": score,
    }
    return {
        "edge_id": edge_id,
        "advertisement_id": f"ad-{edge_id}",
        "observed_at": "2026-08-22T23:59:00Z",
        "expires_at": "2026-08-23T00:10:00Z",
        "attested": True,
        "available_bearers": [bearer],
        "metrics": metrics,
        "capabilities": capabilities,
    }


NOW = datetime(2026, 8, 23, 0, 0, 0, tzinfo=timezone.utc)
RECIPIENT = {"state": "KNOWN", "accepted_bearers": ["stegtalk-ip", "sms"]}
CONSTRAINTS = {
    "remote_edge_execution_authorized": True,
    "bearer_preference": ["stegtalk-ip", "sms"],
}


class PhysicalEdgeRuntimeTests(unittest.TestCase):
    def test_prepare_persists_selection_and_lease_before_dispatch(self):
        store = FakeStore()
        attempt, selection, lease = prepare_runtime_attempt(
            attempt_id="attempt-001",
            posture="AUTO",
            edge_advertisements=[ad("phone-a", "stegtalk-ip", 0.95), ad("modem-b", "sms", 0.75)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            lease_seconds=120,
            now=NOW,
        )

        self.assertEqual(attempt["state"], "SELECTED_NOT_DISPATCHED")
        self.assertEqual(selection["selected_edge_id"], "phone-a")
        self.assertEqual(selection["selected_bearer"], "stegtalk-ip")
        self.assertFalse(attempt["physical_bearer_execution_proven"])
        self.assertFalse(attempt["delivery_proven"])
        self.assertFalse(attempt["production_active"])
        self.assertEqual(lease["edge_id"], "phone-a")
        self.assertFalse(lease["dispatch_authorized_by_receipt"])
        self.assertEqual(len(store.attempts), 1)
        self.assertEqual([item[1]["type"] for item in store.receipts], ["CROSS_EDGE_SELECTION", "ST031_EXECUTION_LEASE"])

    def test_ambiguous_outcome_requires_external_verification_and_recovery_record(self):
        store = FakeStore()
        _, selection, _ = prepare_runtime_attempt(
            attempt_id="attempt-002",
            posture="AUTO",
            edge_advertisements=[ad("modem-a", "sms", 0.9), ad("modem-b", "sms", 0.8)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        outcome = record_runtime_outcome(
            attempt_id="attempt-002",
            selection_receipt=selection,
            outcome="TIMEOUT_AFTER_DISPATCH",
            store=store,
        )
        self.assertEqual(outcome["next_action"]["action"], "VERIFY_EXTERNALLY")
        self.assertFalse(outcome["delivery_proven"])
        self.assertEqual(len(store.recovery), 1)
        self.assertEqual(store.recovery[0][1]["reason"], "AMBIGUOUS_AFTER_DISPATCH")

    def test_failed_outcome_allows_fallback_only_after_confirmed_no_side_effect(self):
        store = FakeStore()
        _, selection, _ = prepare_runtime_attempt(
            attempt_id="attempt-003",
            posture="AUTO",
            edge_advertisements=[ad("edge-a", "sms", 0.9), ad("edge-b", "sms", 0.8)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        blocked = record_runtime_outcome(
            attempt_id="attempt-003",
            selection_receipt=selection,
            outcome="FAILED",
            store=store,
            side_effect_absence_confirmed=False,
        )
        self.assertEqual(blocked["next_action"]["action"], "VERIFY_EXTERNALLY")

        allowed = record_runtime_outcome(
            attempt_id="attempt-003",
            selection_receipt=selection,
            outcome="FAILED",
            store=store,
            side_effect_absence_confirmed=True,
        )
        self.assertEqual(allowed["next_action"]["action"], "TRY_FALLBACK")
        self.assertEqual(allowed["next_action"]["fallback"]["edge_id"], "edge-b")

    def test_sms_dispatch_refuses_non_sms_selection(self):
        store = FakeStore()
        edges = [ad("phone-a", "stegtalk-ip", 0.9)]
        _, selection, _ = prepare_runtime_attempt(
            attempt_id="attempt-004",
            posture="AUTO",
            edge_advertisements=edges,
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        with self.assertRaisesRegex(RuntimeExecutionError, "selected bearer is not sms"):
            dispatch_selected_sms(
                attempt_id="attempt-004",
                selection_receipt=selection,
                edge_advertisements=edges,
                envelope={"envelope_hash": "sha256:test", "body": "test"},
                to_number="+15555550123",
                store=store,
                journal_path="/tmp/unused.jsonl",
            )

    def test_sms_dispatch_binds_selected_modem_and_keeps_delivery_unproven(self):
        store = FakeStore()
        edges = [ad("modem-a", "sms", 0.9, modem_path="/dev/ttyUSB9")]
        _, selection, _ = prepare_runtime_attempt(
            attempt_id="attempt-005",
            posture="AUTO",
            edge_advertisements=edges,
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )

        @dataclass
        class Result:
            reference: str = "17"

        class FakeSession:
            opened_candidate = None

            def __init__(self, candidate, journal=None):
                FakeSession.opened_candidate = candidate

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return None

            def send(self, *, envelope, to_number, allow_plaintext_external=False):
                return (
                    Result(),
                    {"type": "external_sms_transport_receipt", "direction": "outbound"},
                    {"type": "sovereign_sms_session_submission_receipt", "delivery_proven": False},
                )

        with tempfile.TemporaryDirectory() as tmp, patch(
            "stegtalk.physical_edge_runtime.SovereignSmsSession", FakeSession
        ):
            dispatch = dispatch_selected_sms(
                attempt_id="attempt-005",
                selection_receipt=selection,
                edge_advertisements=edges,
                envelope={"envelope_hash": "sha256:test", "body": "test"},
                to_number="+15555550123",
                store=store,
                journal_path=Path(tmp) / "sms.jsonl",
            )

        self.assertEqual(FakeSession.opened_candidate.path, "/dev/ttyUSB9")
        self.assertEqual(dispatch["state"], "DISPATCHED_DELIVERY_UNPROVEN")
        self.assertFalse(dispatch["delivery_proven"])
        self.assertFalse(dispatch["production_active"])
        self.assertEqual(dispatch["modem_reference"], "17")


if __name__ == "__main__":
    unittest.main()
