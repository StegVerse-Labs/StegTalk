import json
from copy import deepcopy

import pytest

from stegtalk.mobile_shell_session_receipt_store import (
    append_and_restore_receipt,
    append_receipt_atomic,
    inspect_persisted_receipt_chain,
    persist_receipt_chain,
    restore_receipt_chain,
)
from stegtalk.mobile_shell_session_receipts import create_session_event_receipt


def _chain():
    first = create_session_event_receipt(
        session_id="primary",
        event="persist",
        result="success",
    )
    second = create_session_event_receipt(
        session_id="primary",
        event="restore",
        result="success",
        previous_chain_head=first["receipt_chain_head"],
    )
    return [first, second]


def test_receipt_chain_persists_restores_and_replays(tmp_path):
    chain = _chain()
    record = persist_receipt_chain(store_root=tmp_path, session_id="primary", chain=chain)
    restored = restore_receipt_chain(store_root=tmp_path, session_id="primary")
    report = inspect_persisted_receipt_chain(store_root=tmp_path, session_id="primary")

    assert restored == chain
    assert record["receipt_count"] == 2
    assert report["events"] == ["persist", "restore"]
    assert report["chain_head"] == chain[-1]["receipt_chain_head"]
    assert report["authorizing"] is False


def test_atomic_append_requires_current_head_and_leaves_no_temp_files(tmp_path):
    first = _chain()[0]
    persist_receipt_chain(store_root=tmp_path, session_id="primary", chain=[first])
    second = create_session_event_receipt(
        session_id="primary",
        event="restore",
        result="success",
        previous_chain_head=first["receipt_chain_head"],
    )
    record = append_receipt_atomic(
        store_root=tmp_path,
        session_id="primary",
        receipt=second,
        expected_chain_head=first["receipt_chain_head"],
    )

    assert record["receipt_count"] == 2
    directory = tmp_path / "mobile_shell_session_receipt_chains"
    assert list(directory.glob("*.tmp")) == []
    assert restore_receipt_chain(store_root=tmp_path, session_id="primary")[-1] == second


def test_stale_append_fails_closed_without_overwriting_chain(tmp_path):
    chain = _chain()
    persist_receipt_chain(store_root=tmp_path, session_id="primary", chain=chain)
    third = create_session_event_receipt(
        session_id="primary",
        event="restore",
        result="success",
        previous_chain_head=chain[-1]["receipt_chain_head"],
    )

    with pytest.raises(ValueError, match="head changed"):
        append_receipt_atomic(
            store_root=tmp_path,
            session_id="primary",
            receipt=third,
            expected_chain_head=chain[0]["receipt_chain_head"],
        )

    assert restore_receipt_chain(store_root=tmp_path, session_id="primary") == chain


def test_one_call_append_restores_and_replays(tmp_path):
    first = _chain()[0]
    record, restored = append_and_restore_receipt(
        store_root=tmp_path,
        session_id="primary",
        receipt=first,
    )

    assert record["receipt_count"] == 1
    assert restored == [first]


def test_persisted_wrapper_tampering_is_rejected(tmp_path):
    persist_receipt_chain(store_root=tmp_path, session_id="primary", chain=_chain())
    path = tmp_path / "mobile_shell_session_receipt_chains" / "primary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["authorizing"] = True
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="authority boundary violated"):
        restore_receipt_chain(store_root=tmp_path, session_id="primary")


def test_persisted_chain_tampering_is_rejected(tmp_path):
    persist_receipt_chain(store_root=tmp_path, session_id="primary", chain=_chain())
    path = tmp_path / "mobile_shell_session_receipt_chains" / "primary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["chain"][0]["result"] = "tampered"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="integrity check failed"):
        restore_receipt_chain(store_root=tmp_path, session_id="primary")


def test_invalid_session_id_cannot_escape_collection(tmp_path):
    with pytest.raises(ValueError, match="unsupported characters"):
        persist_receipt_chain(store_root=tmp_path, session_id="../escape", chain=[])
