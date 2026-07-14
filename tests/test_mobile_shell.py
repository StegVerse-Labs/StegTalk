from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import build_discovery_record, create_entity_card
from stegtalk.mobile_shell import (
    create_local_message,
    create_mobile_shell,
    load_local_identity,
    run_public_discovery_search,
    show_local_contacts,
    show_local_inbox,
    summarize_mobile_shell,
)


def _fixture_shell():
    user = create_entity_card(
        entity_id="rigel",
        display_name="Rigel",
        entity_type="human",
        purpose="local StegTalk operator",
    )
    contact = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="local routing assistant",
        capabilities=["routing", "messaging"],
    )
    index = build_discovery_index([build_discovery_record(contact)])
    return create_mobile_shell(identity_card=user, contacts=[contact], discovery_index=index)


def test_mobile_shell_starts_local_and_non_authorizing():
    shell = _fixture_shell()
    summary = summarize_mobile_shell(shell)
    assert summary["state_type"] == "stegtalk_mobile_shell"
    assert summary["mode"] == "local_prototype"
    assert summary["production_ready"] is False
    assert all(value is False for value in summary["authority"].values())
    assert shell["mobile_shell_hash"].startswith("sha256:")


def test_mobile_shell_loads_identity_and_contacts():
    shell = _fixture_shell()
    assert load_local_identity(shell)["identity"]["id"] == "rigel"
    contacts = show_local_contacts(shell)
    assert [card["identity"]["id"] for card in contacts] == ["auri"]


def test_mobile_shell_routes_message_into_local_projection():
    shell = _fixture_shell()
    updated, result = create_local_message(shell, receiver_hint="Auri", body="Local hello")
    assert result["decision"]["result"] == "routed"
    assert result["envelope"]["sender_entity"] == "rigel"
    assert result["envelope"]["receiver_entity"] == "auri"
    assert len(show_local_inbox(updated)) == 1
    assert updated["last_action"]["result"] == "routed"


def test_mobile_shell_fails_closed_for_unknown_contact():
    shell = _fixture_shell()
    updated, result = create_local_message(shell, receiver_hint="Unknown", body="Do not route")
    assert result["decision"]["result"] == "unresolved"
    assert result["envelope"] == {}
    assert show_local_inbox(updated) == []


def test_mobile_shell_runs_local_public_discovery_search():
    shell = _fixture_shell()
    updated, result = run_public_discovery_search(shell, query="routing assistant")
    assert result["result_count"] == 1
    assert result["results"][0]["entity_id"] == "auri"
    assert updated["shell_state"]["active_view"] == "discovery"
