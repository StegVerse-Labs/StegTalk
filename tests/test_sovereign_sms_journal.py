import json

import pytest

from stegtalk.sms_transport import SmsTransportError
from stegtalk.sovereign_sms_journal import SovereignSmsJournal, journal_receipts


def inbound_receipt(correlation_hash="corr-1"):
    return {
        "type": "external_sms_transport_receipt",
        "direction": "inbound",
        "correlation_hash": correlation_hash,
        "result": "accepted",
    }


def test_journal_hash_chains_receipts_and_reconstructs_after_restart(tmp_path):
    path = tmp_path / "sms.jsonl"
    journal = SovereignSmsJournal(path)
    first = journal.append({"type": "sovereign_sms_runtime_readiness_receipt"})
    second = journal.append({"type": "sovereign_sms_session_submission_receipt"})
    journal.append(inbound_receipt())

    assert first["sequence"] == 1
    assert first["previous_record_hash"] is None
    assert second["previous_record_hash"] == first["record_hash"]

    recovered = SovereignSmsJournal(path)
    summary = recovered.reconstruct_summary()
    assert summary["journal_records"] == 3
    assert summary["readiness_receipts"] == 1
    assert summary["session_submission_receipts"] == 1
    assert summary["inbound_transport_receipts"] == 1
    assert summary["head_hash"] == recovered.records[-1]["record_hash"]
    assert recovered.replay_receipts()[2]["correlation_hash"] == "corr-1"


def test_inbound_duplicate_suppression_survives_restart(tmp_path):
    path = tmp_path / "sms.jsonl"
    journal = SovereignSmsJournal(path)
    assert journal.append_inbound_once(inbound_receipt("same")) is True
    assert journal.append_inbound_once(inbound_receipt("same")) is False
    assert len(journal.records) == 1

    recovered = SovereignSmsJournal(path)
    assert recovered.append_inbound_once(inbound_receipt("same")) is False
    assert recovered.append_inbound_once(inbound_receipt("new")) is True
    assert len(recovered.records) == 2


def test_journal_detects_tampering_on_restart(tmp_path):
    path = tmp_path / "sms.jsonl"
    journal = SovereignSmsJournal(path)
    journal.append({"type": "sovereign_sms_runtime_readiness_receipt", "value": 1})

    record = json.loads(path.read_text(encoding="utf-8"))
    record["receipt"]["value"] = 999
    path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(SmsTransportError, match="receipt hash mismatch"):
        SovereignSmsJournal(path)


def test_append_inbound_once_requires_transport_correlation_hash(tmp_path):
    journal = SovereignSmsJournal(tmp_path / "sms.jsonl")
    with pytest.raises(SmsTransportError, match="missing correlation_hash"):
        journal.append_inbound_once({"type": "external_sms_transport_receipt", "direction": "inbound"})


def test_journal_receipts_preserves_order(tmp_path):
    journal = SovereignSmsJournal(tmp_path / "sms.jsonl")
    records = journal_receipts(journal, [{"type": "one"}, {"type": "two"}])
    assert [record["sequence"] for record in records] == [1, 2]
    assert [receipt["type"] for receipt in journal.replay_receipts()] == ["one", "two"]
