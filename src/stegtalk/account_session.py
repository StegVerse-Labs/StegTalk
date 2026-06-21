from __future__ import annotations

from .account_model import summarize_account_profile
from .entity_runtime import JsonObject, stable_hash, utc_now


def create_account_session(*, profile: JsonObject, shell_state: JsonObject) -> JsonObject:
    session = {
        "schema_version": "1.0.0",
        "session_type": "stegtalk_account_session",
        "account": summarize_account_profile(profile),
        "shell_state_hash": shell_state["state_hash"],
        "active_view": shell_state["active_view"],
        "started_at": utc_now(),
        "last_seen_at": utc_now(),
        "events": [],
    }
    session["session_hash"] = stable_hash(session)
    return session


def record_session_event(session: JsonObject, *, event_type: str, event_ref: str) -> JsonObject:
    updated = {**session, "events": list(session.get("events", []))}
    updated["events"].append({"event_type": event_type, "event_ref": event_ref, "recorded_at": utc_now()})
    updated["last_seen_at"] = utc_now()
    updated["session_hash"] = stable_hash({key: value for key, value in updated.items() if key != "session_hash"})
    return updated


def summarize_account_session(session: JsonObject) -> JsonObject:
    return {
        "account_id": session["account"]["account_id"],
        "active_view": session["active_view"],
        "event_count": len(session.get("events", [])),
        "session_hash": session["session_hash"],
    }
