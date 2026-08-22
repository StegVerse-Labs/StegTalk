from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .entity_runtime import JsonObject, stable_hash


class CapabilityResolutionError(ValueError):
    pass


POSTURES = {"AUTO", "MOST_PRIVATE", "FASTEST", "LOWEST_COST", "LOWEST_ENERGY", "LOCAL_ONLY", "EMERGENCY_RESILIENT"}
RECIPIENT_STATES = {"KNOWN", "UNKNOWN", "UNREACHABLE"}
AMBIGUOUS_RESULTS = {"INDETERMINATE", "UNKNOWN_AFTER_DISPATCH", "TIMEOUT_AFTER_DISPATCH"}
TERMINAL_SUCCESS = {"DELIVERED", "ACKNOWLEDGED", "EXECUTED"}

WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "AUTO": {"security":2.0,"privacy":2.0,"recipient_compatibility":2.0,"reliability":1.8,"receipt_quality":1.5,"bidirectionality":1.2,"resilience":1.1,"latency":1.0,"bandwidth":0.7,"cost":0.6,"energy":0.6,"metadata_minimization":1.3},
    "MOST_PRIVATE": {"security":2.4,"privacy":2.6,"recipient_compatibility":1.5,"reliability":1.2,"receipt_quality":1.3,"bidirectionality":1.0,"resilience":0.8,"latency":0.5,"bandwidth":0.4,"cost":0.3,"energy":0.4,"metadata_minimization":2.4},
    "FASTEST": {"security":1.5,"privacy":1.2,"recipient_compatibility":1.8,"reliability":1.4,"receipt_quality":0.8,"bidirectionality":0.8,"resilience":0.7,"latency":2.7,"bandwidth":1.7,"cost":0.2,"energy":0.3,"metadata_minimization":0.9},
    "LOWEST_COST": {"security":1.4,"privacy":1.2,"recipient_compatibility":1.7,"reliability":1.3,"receipt_quality":0.8,"bidirectionality":0.8,"resilience":0.8,"latency":0.6,"bandwidth":0.5,"cost":2.8,"energy":0.5,"metadata_minimization":0.9},
    "LOWEST_ENERGY": {"security":1.4,"privacy":1.2,"recipient_compatibility":1.7,"reliability":1.2,"receipt_quality":0.8,"bidirectionality":0.8,"resilience":0.7,"latency":0.6,"bandwidth":0.4,"cost":0.5,"energy":2.8,"metadata_minimization":0.9},
    "LOCAL_ONLY": {"security":2.0,"privacy":2.2,"recipient_compatibility":1.6,"reliability":1.0,"receipt_quality":0.8,"bidirectionality":0.8,"resilience":0.6,"latency":1.2,"bandwidth":0.7,"cost":1.0,"energy":1.0,"metadata_minimization":2.0},
    "EMERGENCY_RESILIENT": {"security":1.6,"privacy":1.0,"recipient_compatibility":2.0,"reliability":2.5,"receipt_quality":1.2,"bidirectionality":1.0,"resilience":3.0,"latency":1.1,"bandwidth":0.3,"cost":0.2,"energy":0.2,"metadata_minimization":0.7},
}


@dataclass(frozen=True)
class Lease:
    attempt_id: str
    edge_id: str
    lease_epoch: int
    expires_at: str


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _now_utc(now: datetime | None = None) -> datetime:
    current = now or datetime.now(timezone.utc)
    return current if current.tzinfo else current.replace(tzinfo=timezone.utc)


def validate_edge_advertisement(ad: JsonObject, *, now: datetime | None = None) -> None:
    required = {"edge_id","advertisement_id","observed_at","expires_at","attested","available_bearers","metrics","capabilities"}
    missing = sorted(required - ad.keys())
    if missing: raise CapabilityResolutionError(f"edge advertisement missing: {missing}")
    if not ad["attested"]: raise CapabilityResolutionError("edge advertisement is not attested")
    if not ad["available_bearers"]: raise CapabilityResolutionError("edge has no available bearer")
    current = _now_utc(now)
    if _parse_time(ad["expires_at"]) <= current: raise CapabilityResolutionError("edge advertisement expired")
    if _parse_time(ad["observed_at"]) > current: raise CapabilityResolutionError("edge advertisement observed in the future")


def validate_recipient_capability(recipient: JsonObject) -> None:
    state = recipient.get("state")
    if state not in RECIPIENT_STATES: raise CapabilityResolutionError("invalid recipient capability state")
    if state == "KNOWN" and not recipient.get("accepted_bearers"): raise CapabilityResolutionError("known recipient must advertise an accepted bearer")


def _hard_exclusion_reasons(ad: JsonObject, recipient: JsonObject, constraints: JsonObject, posture: str) -> list[str]:
    reasons: list[str] = []
    bearers = set(ad["available_bearers"])
    allowed = set(constraints.get("allowed_bearers") or bearers)
    prohibited = set(constraints.get("prohibited_bearers") or [])
    candidate = bearers & allowed - prohibited
    if not candidate: reasons.append("NO_ALLOWED_BEARER")

    remote_allowed = bool(constraints.get("remote_edge_execution_authorized", True))
    current_edge_id = constraints.get("current_edge_id")
    if not remote_allowed:
        if not current_edge_id:
            reasons.append("CURRENT_EDGE_REQUIRED_WHEN_REMOTE_DENIED")
        elif ad["edge_id"] != current_edge_id:
            reasons.append("REMOTE_EDGE_DENIED")

    if posture == "LOCAL_ONLY" or constraints.get("local_only"):
        local = set(ad["capabilities"].get("local_bearers") or [])
        if not candidate & local: reasons.append("LOCALITY_REQUIRED")

    relay_denied = bool(constraints.get("relay_denied")) or constraints.get("relay_permission") == "denied"
    if relay_denied and ad["capabilities"].get("requires_relay"): reasons.append("RELAY_DENIED")

    saf_denied = bool(constraints.get("store_and_forward_denied")) or constraints.get("allow_store_and_forward") is False
    if saf_denied and ad["capabilities"].get("store_and_forward"): reasons.append("STORE_AND_FORWARD_DENIED")

    emergency_authority = bool(constraints.get("emergency_authority") or constraints.get("emergency_authorized"))
    if posture == "EMERGENCY_RESILIENT" and not emergency_authority: reasons.append("EMERGENCY_AUTHORITY_REQUIRED")

    state = recipient["state"]
    if state == "UNREACHABLE": reasons.append("RECIPIENT_UNREACHABLE")
    elif state == "KNOWN":
        accepted = set(recipient.get("accepted_bearers") or [])
        if not candidate & accepted: reasons.append("RECIPIENT_INCOMPATIBLE")
    elif state == "UNKNOWN":
        safe = set(recipient.get("safe_fallback_bearers") or [])
        if not safe: reasons.append("UNKNOWN_RECIPIENT_REQUIRES_SAFE_FALLBACK")
        elif not candidate & safe: reasons.append("UNKNOWN_RECIPIENT_NO_SAFE_FALLBACK")

    for metric, floor in (constraints.get("minimum_metrics") or {}).items():
        if float(ad["metrics"].get(metric, 0.0)) < float(floor): reasons.append(f"METRIC_BELOW_MINIMUM:{metric}")
    return reasons


def _score(ad: JsonObject, posture: str) -> tuple[float, dict[str, float]]:
    weights = WEIGHT_PROFILES[posture]; metrics = ad["metrics"]; components: dict[str,float] = {}; total = 0.0
    for key, weight in weights.items():
        value = float(metrics.get(key, 0.0))
        if not 0.0 <= value <= 1.0: raise CapabilityResolutionError(f"metric outside [0,1]: {key}")
        components[key] = round(value * weight, 6); total += components[key]
    return round(total, 6), components


def _select_bearer(available: list[str], recipient: JsonObject, constraints: JsonObject) -> str:
    allowed = set(constraints.get("allowed_bearers") or available)
    candidates = [b for b in available if b in allowed]
    if recipient["state"] == "KNOWN":
        accepted = set(recipient.get("accepted_bearers") or []); candidates = [b for b in candidates if b in accepted]
    elif recipient["state"] == "UNKNOWN":
        safe = set(recipient.get("safe_fallback_bearers") or []); candidates = [b for b in candidates if b in safe]
    if not candidates: raise CapabilityResolutionError("candidate edge has no recipient-compatible bearer")
    ordering = {name: idx for idx, name in enumerate(constraints.get("bearer_preference") or [])}
    return sorted(candidates, key=lambda b: (ordering.get(b, len(ordering)), b))[0]


def resolve_cross_edge_path(*, attempt_id: str, posture: str, edge_advertisements: Iterable[JsonObject], recipient: JsonObject, constraints: JsonObject | None = None, policy_version: str = "stegtalk.cross-edge.v0.1", now: datetime | None = None) -> JsonObject:
    if posture not in POSTURES: raise CapabilityResolutionError("unsupported communication posture")
    validate_recipient_capability(recipient); constraints = constraints or {}; current = _now_utc(now)
    evaluated: list[JsonObject] = []; exclusions: list[JsonObject] = []; ads = list(edge_advertisements)
    for ad in ads:
        try: validate_edge_advertisement(ad, now=current)
        except CapabilityResolutionError as exc:
            exclusions.append({"edge_id":ad.get("edge_id"),"reasons":[str(exc)]}); continue
        reasons = _hard_exclusion_reasons(ad, recipient, constraints, posture)
        if reasons:
            exclusions.append({"edge_id":ad["edge_id"],"reasons":sorted(reasons)}); continue
        score, components = _score(ad, posture)
        evaluated.append({"edge_id":ad["edge_id"],"advertisement_id":ad["advertisement_id"],"advertisement_sha256":stable_hash(ad),"available_bearers":sorted(ad["available_bearers"]),"score":score,"score_components":components})
    if not evaluated: raise CapabilityResolutionError("no admissible cross-edge path")
    evaluated.sort(key=lambda item:(-item["score"],item["edge_id"],item["advertisement_id"]))
    primary, fallback = evaluated[0], evaluated[1:]
    candidate_set_hash = stable_hash({"attempt_id":attempt_id,"posture":posture,"recipient":recipient,"constraints":constraints,"ads":sorted(stable_hash(ad) for ad in ads),"policy_version":policy_version})
    receipt: JsonObject = {
        "schema_version":"0.1","receipt_type":"CROSS_EDGE_SELECTION","attempt_id":attempt_id,"policy_version":policy_version,"posture":posture,"recipient_state":recipient["state"],"candidate_set_sha256":candidate_set_hash,
        "selected_edge_id":primary["edge_id"],"selected_bearer":_select_bearer(primary["available_bearers"],recipient,constraints),"primary_score":primary["score"],"primary_score_components":primary["score_components"],
        "fallback_order":[{"edge_id":item["edge_id"],"score":item["score"],"bearer":_select_bearer(item["available_bearers"],recipient,constraints)} for item in fallback],
        "excluded_paths":sorted(exclusions,key=lambda item:str(item["edge_id"])),"selected_advertisement_sha256":primary["advertisement_sha256"],"decided_at":current.isoformat().replace("+00:00","Z"),
        "multipath_authorized":bool(constraints.get("multipath_authorized",False)),"remote_edge_execution_authorized":bool(constraints.get("remote_edge_execution_authorized",True)),
    }
    receipt["selection_sha256"] = stable_hash(receipt); return receipt


def issue_execution_lease(*, attempt_id: str, selection_receipt: JsonObject, lease_epoch: int, expires_at: str, now: datetime | None = None) -> Lease:
    if selection_receipt.get("attempt_id") != attempt_id: raise CapabilityResolutionError("selection receipt attempt mismatch")
    if _parse_time(expires_at) <= _now_utc(now): raise CapabilityResolutionError("lease must expire in the future")
    if lease_epoch < 1: raise CapabilityResolutionError("lease epoch must be positive")
    return Lease(attempt_id, selection_receipt["selected_edge_id"], lease_epoch, expires_at)


def fallback_action(*, outcome: str, selection_receipt: JsonObject, next_fallback_index: int = 0, side_effect_absence_confirmed: bool = False) -> JsonObject:
    if outcome in TERMINAL_SUCCESS: return {"action":"STOP","reason":"TERMINAL_SUCCESS"}
    if outcome in AMBIGUOUS_RESULTS: return {"action":"VERIFY_EXTERNALLY","reason":"AMBIGUOUS_AFTER_DISPATCH"}
    if outcome == "FAILED" and not side_effect_absence_confirmed: return {"action":"VERIFY_EXTERNALLY","reason":"SIDE_EFFECT_ABSENCE_NOT_CONFIRMED"}
    fallbacks = selection_receipt.get("fallback_order") or []
    if next_fallback_index >= len(fallbacks): return {"action":"STOP","reason":"NO_FALLBACK_REMAINING"}
    return {"action":"TRY_FALLBACK","reason":"CONFIRMED_NO_SIDE_EFFECT","fallback":fallbacks[next_fallback_index]}
