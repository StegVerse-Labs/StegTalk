from copy import deepcopy

import pytest

from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import build_discovery_record, create_entity_card
from stegtalk.mobile_shell import create_mobile_shell
from stegtalk.mobile_shell_session_receipts import (
    create_session_event_receipt,
    persist_session_with_receipt,
    restore_session_with_receipt,
    summarize_session_receipts,
    verify_session_receipt_chain,
)


def _shell():
    user = create_entity_card(entity_id="rigel", display_name="Rigel", entity_type="human", purpose="local operator")
    contact = create_entity_card(entity_id="auri", display_name="Auri", entity_type="assistant", purpose="local assistant")
    return create_mobile_shell(identity_card=user, contacts=[contact], discovery_index=build_discovery_index([build_discovery_record(contact)]))


def test_persist_restore_chain_is_automatic(tmp_path):
    persisted, chain = persist_session_with_receipt(store_root=tmp_path, shell=_shell(), session_id="primary")
    restored, chain = restore_session_with_receipt(store_root=tmp_path, session_id="primary", chain=chain)
    assert persisted is not None and restored is not None
    assert [item["event"] for item in chain] == ["persist", "restore"]
    assert chain[1]["previous_chain_head"] == chain[0]["receipt_chain_head"]
    assert verify_session_receipt_chain(chain)["verified"] is True


def test_authority_rejection_becomes_receipt(tmp_path):
    shell = deepcopy(_shell())
    shell["authority"]["network_authority"] = True
    persisted, chain = persist_session_with_receipt(store_root=tmp_path, shell=shell, session_id="unsafe")
    assert persisted is None
    assert chain[0]["event"] == "rejection"
    assert "authority boundary violated" in chain[0]["reason"]


def test_integrity_failure_becomes_chained_receipt(tmp_path):
    _, chain = persist_session_with_receipt(store_root=tmp_path, shell=_shell(), session_id="primary")
    path = tmp_path / "mobile_shell_sessions" / "primary.json"
    path.write_text(path.read_text(encoding="utf-8").replace('"local_only": true', '"local_only": false', 1), encoding="utf-8")
    restored, chain = restore_session_with_receipt(store_root=tmp_path, session_id="primary", chain=chain)
    assert restored is None
    assert chain[-1]["event"] == "integrity_failure"
    assert verify_session_receipt_chain(chain)["verified"] is True


def test_replay_detects_discontinuity():
    first = create_session_event_receipt(session_id="primary", event="persist", result="success")
    second = create_session_event_receipt(session_id="primary", event="restore", result="success", previous_chain_head=first["receipt_chain_head"])
    broken = deepcopy([first, second])
    broken[1]["previous_chain_head"] = "sha256:wrong"
    with pytest.raises(ValueError, match="discontinuity"):
        verify_session_receipt_chain(broken)


def test_summary_is_payload_free_and_non_authorizing(tmp_path):
    _, chain = persist_session_with_receipt(store_root=tmp_path, shell=_shell(), session_id="primary")
    summary = summarize_session_receipts(chain)
    assert summary["authorizing"] is False
    assert summary["production_ready"] is False
    assert summary["local_only"] is True
    assert "identity_card" not in summary
