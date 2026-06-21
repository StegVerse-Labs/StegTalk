import pytest

from stegtalk.account_model import create_account_profile, link_account_entity, summarize_account_profile


def test_account_profile_links_entities_and_summarizes():
    profile = create_account_profile(
        account_id="rigel-local",
        display_name="Rigel Local",
        owner_entity="Rigel",
    )
    updated = link_account_entity(profile, entity_id="auri", role="assistant")
    summary = summarize_account_profile(updated)
    assert summary["account_id"] == "rigel-local"
    assert summary["linked_entity_count"] == 1
    assert updated["linked_entities"][0]["entity_id"] == "auri"
    assert updated["profile_hash"].startswith("sha256:")


def test_account_profile_requires_core_fields():
    with pytest.raises(ValueError):
        create_account_profile(account_id="", display_name="Rigel", owner_entity="Rigel")
    with pytest.raises(ValueError):
        create_account_profile(account_id="rigel", display_name="Rigel", owner_entity="")
