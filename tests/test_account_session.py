from stegtalk.account_model import create_account_profile, link_account_entity
from stegtalk.account_session import create_account_session, record_session_event, summarize_account_session
from stegtalk.shell_state import create_shell_state


def test_account_session_tracks_shell_and_events():
    profile = create_account_profile(
        account_id="rigel-local",
        display_name="Rigel Local",
        owner_entity="Rigel",
    )
    profile = link_account_entity(profile, entity_id="auri", role="assistant")
    shell = create_shell_state(user_entity="Rigel", active_view="home")
    session = create_account_session(profile=profile, shell_state=shell)
    session = record_session_event(session, event_type="view", event_ref="home")
    summary = summarize_account_session(session)
    assert summary["account_id"] == "rigel-local"
    assert summary["active_view"] == "home"
    assert summary["event_count"] == 1
    assert summary["session_hash"].startswith("sha256:")
