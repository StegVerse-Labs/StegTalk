from copy import deepcopy

import pytest

from stegtalk.discovery_index import build_discovery_index
from stegtalk.entity_runtime import build_discovery_record, create_entity_card
from stegtalk.mobile_shell import create_local_message, create_mobile_shell, run_public_discovery_search
from stegtalk.mobile_shell_session import (
    inspect_mobile_shell_session,
    persist_mobile_shell_session,
    restore_mobile_shell_session,
)


def _shell():
    user = create_entity_card(
        entity_id="rigel",
        display_name="Rigel",
        entity_type="human",
        purpose="local operator",
    )
    contact = create_entity_card(
        entity_id="auri",
        display_name="Auri",
        entity_type="assistant",
        purpose="local routing assistant",
        capabilities=["routing", "messaging"],
    )
    index = build_discovery_index([build_discovery_record(contact)])
    shell = create_mobile_shell(identity_card=user, contacts=[contact], discovery_index=index)
    shell, _ = create_local_message(shell, receiver_hint="Auri", body="Persist this locally")
    shell, _ = run_public_discovery_search(shell, query="routing assistant")
    return shell


def test_mobile_shell_session_round_trip(tmp_path):
    shell = _shell()
    receipt = persist_mobile_shell_session(store_root=tmp_path, shell=shell, session_id="primary")
    restored = restore_mobile_shell_session(store_root=tmp_path, session_id="primary")

    assert receipt["local_only"] is True
    assert receipt["production_ready"] is False
    assert restored["identity_card"] == shell["identity_card"]
    assert restored["shell_state"]["contacts"] == shell["shell_state"]["contacts"]
    assert restored["inbox"] == shell["inbox"]
    assert restored["shell_state"]["discovery_results"] == shell["shell_state"]["discovery_results"]
    assert restored["contact_index"]


def test_mobile_shell_session_inspection_reports_projection_counts(tmp_path):
    shell = _shell()
    persist_mobile_shell_session(store_root=tmp_path, shell=shell, session_id="primary")
    report = inspect_mobile_shell_session(store_root=tmp_path, session_id="primary")

    assert report["contact_count"] == 1
    assert report["inbox_count"] == 1
    assert report["discovery_result_count"] == 1
    assert report["local_only"] is True


def test_mobile_shell_session_rejects_authority_escalation(tmp_path):
    shell = deepcopy(_shell())
    shell["authority"]["network_authority"] = True
    with pytest.raises(ValueError, match="authority boundary violated"):
        persist_mobile_shell_session(store_root=tmp_path, shell=shell, session_id="unsafe")


def test_mobile_shell_session_detects_snapshot_tampering(tmp_path):
    shell = _shell()
    persist_mobile_shell_session(store_root=tmp_path, shell=shell, session_id="primary")
    path = tmp_path / "mobile_shell_sessions" / "primary.json"
    payload = path.read_text(encoding="utf-8").replace("Persist this locally", "Tampered")
    path.write_text(payload, encoding="utf-8")

    with pytest.raises(ValueError, match="snapshot integrity check failed"):
        restore_mobile_shell_session(store_root=tmp_path, session_id="primary")
