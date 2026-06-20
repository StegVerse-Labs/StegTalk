from stegtalk.shell_state import (
    add_shell_contact,
    add_shell_inbox_item,
    create_shell_state,
    set_active_view,
    set_shell_discovery_results,
    summarize_shell_state,
)


def test_shell_state_tracks_contacts_inbox_and_discovery():
    state = create_shell_state(user_entity="Rigel")
    state = add_shell_contact(state, {"entity_id": "auri", "display_name": "Auri"})
    state = add_shell_inbox_item(state, {"item_hash": "sha256:item", "sender_entity": "Auri"})
    state = set_shell_discovery_results(
        state,
        {"results": [{"entity_id": "stegweather", "display_name": "StegWeather"}]},
    )
    summary = summarize_shell_state(state)
    assert summary["contact_count"] == 1
    assert summary["inbox_count"] == 1
    assert summary["discovery_result_count"] == 1
    assert summary["state_hash"].startswith("sha256:")


def test_shell_state_can_change_active_view():
    state = create_shell_state(user_entity="Rigel")
    updated = set_active_view(state, "discovery")
    assert updated["active_view"] == "discovery"
    assert updated["state_hash"] != state["state_hash"]
