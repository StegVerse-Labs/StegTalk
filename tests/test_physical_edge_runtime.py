from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from stegtalk.edge_runtime import EdgeExecutionRequest
from stegtalk.physical_edge_runtime import (
    execute_persisted_selected_edge,
    load_runtime_binding,
    prepare_runtime_attempt,
    sovereign_sms_executor,
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

    def read_stream(self, category, stream_id):
        source = {
            "Attempts": self.attempts,
            "Receipts": self.receipts,
            "Recovery": self.recovery,
        }[category]
        return [record for current_stream, record in source if current_stream == stream_id]


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
    def test_prepare_persists_st031_selection_and_lease_before_dispatch(self):
        store = FakeStore()
        attempt, selection, lease, lease_record = prepare_runtime_attempt(
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
        self.assertEqual(lease.edge_id, "phone-a")
        self.assertFalse(lease_record["dispatch_authorized_by_receipt"])
        self.assertFalse(attempt["delivery_proven"])
        self.assertEqual(
            [item[1].get("receipt_type") or item[1].get("type") for item in store.receipts],
            ["CROSS_EDGE_SELECTION", "ST031_EXECUTION_LEASE"],
        )

    def test_runtime_binding_reconstructs_from_kv_receipts(self):
        store = FakeStore()
        _, selection, lease, lease_record = prepare_runtime_attempt(
            attempt_id="attempt-002",
            posture="AUTO",
            edge_advertisements=[ad("edge-a", "sms", 0.9)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        recovered_selection, recovered_lease, recovered_record = load_runtime_binding(
            store=store, attempt_id="attempt-002"
        )
        self.assertEqual(recovered_selection["selection_sha256"], selection["selection_sha256"])
        self.assertEqual(recovered_lease, lease)
        self.assertEqual(recovered_record, lease_record)

    def test_st032_execution_receipt_is_persisted_and_restart_does_not_redispatch(self):
        store = FakeStore()
        _, selection, lease, _ = prepare_runtime_attempt(
            attempt_id="attempt-003",
            posture="AUTO",
            edge_advertisements=[ad("edge-a", "sms", 0.9), ad("edge-b", "sms", 0.8)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        request = EdgeExecutionRequest(
            attempt_id="attempt-003",
            selection_sha256=selection["selection_sha256"],
            edge_id=selection["selected_edge_id"],
            bearer=selection["selected_bearer"],
            payload_ref="kv:payload:3",
            idempotency_key="idem-003",
            lease_epoch=lease.lease_epoch,
        )
        calls = {"count": 0}

        def executor(_request):
            calls["count"] += 1
            return {
                "dispatch_state": "DISPATCHED",
                "outcome": "FAILED",
                "side_effect_absence_confirmed": True,
                "observed_at": "2026-08-23T00:00:01Z",
            }

        receipt1, action1, replayed1 = execute_persisted_selected_edge(
            selection_receipt=selection,
            lease=lease,
            request=request,
            executors={request.edge_id: executor},
            store=store,
        )
        self.assertFalse(replayed1)
        self.assertEqual(calls["count"], 1)
        self.assertEqual(action1["action"], "TRY_FALLBACK")

        # Simulate a new process: no in-memory cache is passed. The KV receipt stream
        # reconstructs the idempotency cache and suppresses a second dispatch.
        receipt2, action2, replayed2 = execute_persisted_selected_edge(
            selection_receipt=selection,
            lease=lease,
            request=request,
            executors={request.edge_id: executor},
            store=store,
        )
        self.assertTrue(replayed2)
        self.assertEqual(calls["count"], 1)
        self.assertEqual(receipt2.receipt_sha256, receipt1.receipt_sha256)
        self.assertEqual(action2, action1)
        edge_receipts = [record for _, record in store.receipts if record.get("receipt_type") == "EDGE_EXECUTION"]
        self.assertEqual(len(edge_receipts), 1)

    def test_ambiguous_st032_dispatch_writes_recovery_and_never_allows_fallback(self):
        store = FakeStore()
        _, selection, lease, _ = prepare_runtime_attempt(
            attempt_id="attempt-004",
            posture="AUTO",
            edge_advertisements=[ad("edge-a", "sms", 0.9), ad("edge-b", "sms", 0.8)],
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        request = EdgeExecutionRequest(
            attempt_id="attempt-004",
            selection_sha256=selection["selection_sha256"],
            edge_id=selection["selected_edge_id"],
            bearer="sms",
            payload_ref="kv:payload:4",
            idempotency_key="idem-004",
            lease_epoch=lease.lease_epoch,
        )

        receipt, action, replayed = execute_persisted_selected_edge(
            selection_receipt=selection,
            lease=lease,
            request=request,
            executors={
                request.edge_id: lambda _request: {
                    "dispatch_state": "DISPATCHED",
                    "outcome": "TIMEOUT_AFTER_DISPATCH",
                    "side_effect_absence_confirmed": False,
                    "observed_at": "2026-08-23T00:00:01Z",
                }
            },
            store=store,
        )
        self.assertFalse(replayed)
        self.assertEqual(receipt.outcome, "TIMEOUT_AFTER_DISPATCH")
        self.assertEqual(action["action"], "VERIFY_EXTERNALLY")
        self.assertEqual(len(store.recovery), 1)
        self.assertEqual(store.recovery[0][1]["reason"], "AMBIGUOUS_AFTER_DISPATCH")

    def test_st029_adapter_is_an_st032_executor_and_submission_remains_indeterminate(self):
        store = FakeStore()
        edges = [ad("modem-a", "sms", 0.9, modem_path="/dev/ttyUSB9")]
        _, selection, lease, _ = prepare_runtime_attempt(
            attempt_id="attempt-005",
            posture="AUTO",
            edge_advertisements=edges,
            recipient=RECIPIENT,
            constraints=CONSTRAINTS,
            store=store,
            now=NOW,
        )
        request = EdgeExecutionRequest(
            attempt_id="attempt-005",
            selection_sha256=selection["selection_sha256"],
            edge_id="modem-a",
            bearer="sms",
            payload_ref="kv:payload:5",
            idempotency_key="idem-005",
            lease_epoch=lease.lease_epoch,
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
            executor = sovereign_sms_executor(
                edge_advertisements=edges,
                envelope={"envelope_hash": "sha256:test", "body": "test"},
                to_number="+15555550123",
                store=store,
                journal_path=Path(tmp) / "sms.jsonl",
            )
            receipt, action, replayed = execute_persisted_selected_edge(
                selection_receipt=selection,
                lease=lease,
                request=request,
                executors={"modem-a": executor},
                store=store,
            )

        self.assertFalse(replayed)
        self.assertEqual(FakeSession.opened_candidate.path, "/dev/ttyUSB9")
        self.assertEqual(receipt.dispatch_state, "DISPATCHED")
        self.assertEqual(receipt.outcome, "INDETERMINATE")
        self.assertFalse(receipt.side_effect_absence_confirmed)
        self.assertEqual(action["action"], "VERIFY_EXTERNALLY")
        self.assertTrue(any(record.get("type") == "ST029_MODEM_SUBMISSION_EVIDENCE" for _, record in store.receipts))


if __name__ == "__main__":
    unittest.main()
