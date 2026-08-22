from datetime import datetime, timezone
import unittest

from stegtalk.cross_edge_resolver import (
    CapabilityResolutionError,
    fallback_action,
    issue_execution_lease,
    resolve_cross_edge_path,
)


NOW = datetime(2026, 8, 22, 22, 0, tzinfo=timezone.utc)


def edge(edge_id, bearer, score=0.8, *, expires="2026-08-22T23:00:00Z", attested=True, local=False):
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
        "advertisement_id": f"adv:{edge_id}",
        "observed_at": "2026-08-22T21:59:00Z",
        "expires_at": expires,
        "attested": attested,
        "available_bearers": [bearer],
        "metrics": metrics,
        "capabilities": {"local_bearers": [bearer] if local else [], "requires_relay": False, "store_and_forward": False},
    }


class CrossEdgeResolverTests(unittest.TestCase):
    def test_auto_selects_highest_capability_edge(self):
        result = resolve_cross_edge_path(
            attempt_id="attempt:1",
            posture="AUTO",
            edge_advertisements=[edge("phone", "sms", .4), edge("gateway", "stegtalk-ip", .95)],
            recipient={"state":"KNOWN","accepted_bearers":["sms","stegtalk-ip"]},
            now=NOW,
        )
        self.assertEqual(result["selected_edge_id"], "gateway")
        self.assertEqual(result["selected_bearer"], "stegtalk-ip")
        self.assertEqual(result["fallback_order"][0]["edge_id"], "phone")
        self.assertEqual(len(result["selection_sha256"]), 64)

    def test_expired_advertisement_is_excluded(self):
        result = resolve_cross_edge_path(
            attempt_id="attempt:2",
            posture="AUTO",
            edge_advertisements=[edge("old", "wifi", .99, expires="2026-08-22T21:00:00Z"), edge("fresh", "sms", .5)],
            recipient={"state":"KNOWN","accepted_bearers":["wifi","sms"]},
            now=NOW,
        )
        self.assertEqual(result["selected_edge_id"], "fresh")
        self.assertEqual(result["excluded_paths"][0]["edge_id"], "old")

    def test_local_only_removes_nonlocal_edge(self):
        result = resolve_cross_edge_path(
            attempt_id="attempt:3",
            posture="LOCAL_ONLY",
            edge_advertisements=[edge("cell", "cellular", .9), edge("near", "bluetooth", .6, local=True)],
            recipient={"state":"KNOWN","accepted_bearers":["cellular","bluetooth"]},
            now=NOW,
        )
        self.assertEqual(result["selected_edge_id"], "near")

    def test_unknown_recipient_uses_only_safe_fallback(self):
        result = resolve_cross_edge_path(
            attempt_id="attempt:4",
            posture="AUTO",
            edge_advertisements=[edge("native", "stegtalk-ip", .95), edge("sms", "sms", .5)],
            recipient={"state":"UNKNOWN","safe_fallback_bearers":["sms"]},
            now=NOW,
        )
        self.assertEqual(result["selected_edge_id"], "sms")

    def test_ambiguous_dispatch_never_falls_through(self):
        selection = resolve_cross_edge_path(
            attempt_id="attempt:5",
            posture="AUTO",
            edge_advertisements=[edge("a", "wifi", .8), edge("b", "sms", .7)],
            recipient={"state":"KNOWN","accepted_bearers":["wifi","sms"]},
            now=NOW,
        )
        action = fallback_action(outcome="INDETERMINATE", selection_receipt=selection)
        self.assertEqual(action["action"], "VERIFY_EXTERNALLY")

    def test_confirmed_no_side_effect_allows_next_fallback(self):
        selection = resolve_cross_edge_path(
            attempt_id="attempt:6",
            posture="AUTO",
            edge_advertisements=[edge("a", "wifi", .8), edge("b", "sms", .7)],
            recipient={"state":"KNOWN","accepted_bearers":["wifi","sms"]},
            now=NOW,
        )
        action = fallback_action(outcome="FAILED", selection_receipt=selection, side_effect_absence_confirmed=True)
        self.assertEqual(action["action"], "TRY_FALLBACK")
        self.assertEqual(action["fallback"]["edge_id"], "b")

    def test_lease_binds_only_selected_edge(self):
        selection = resolve_cross_edge_path(
            attempt_id="attempt:7",
            posture="AUTO",
            edge_advertisements=[edge("a", "wifi", .8)],
            recipient={"state":"KNOWN","accepted_bearers":["wifi"]},
            now=NOW,
        )
        lease = issue_execution_lease(
            attempt_id="attempt:7", selection_receipt=selection, lease_epoch=1,
            expires_at="2026-08-22T22:10:00Z", now=NOW,
        )
        self.assertEqual(lease.edge_id, "a")

    def test_no_admissible_path_fails_closed(self):
        with self.assertRaises(CapabilityResolutionError):
            resolve_cross_edge_path(
                attempt_id="attempt:8", posture="AUTO",
                edge_advertisements=[edge("a", "wifi", .8, attested=False)],
                recipient={"state":"KNOWN","accepted_bearers":["wifi"]}, now=NOW,
            )


if __name__ == "__main__":
    unittest.main()
