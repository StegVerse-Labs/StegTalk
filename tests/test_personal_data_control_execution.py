from __future__ import annotations

from pathlib import Path

import pytest

from stegtalk.local_store import initialize_store, read_record, write_record
from stegtalk.personal_data_control import (
    create_personal_data_request,
    execute_local_deletion,
    inventory_local_account_data,
    mark_processor_propagation,
    restrict_processing,
    verify_request_identity,
)


def test_verified_request_inventory_deletion_and_receipt(tmp_path: Path) -> None:
    initialize_store(tmp_path)
    write_record(
        tmp_path,
        "mobile_shell_sessions",
        "session-1",
        {"account_id": "acct-1", "payload": "eligible-local-data"},
    )
    write_record(
        tmp_path,
        "receipts",
        "continuity-1",
        {"account_id": "acct-1", "purpose": "continuity evidence"},
    )

    request = create_personal_data_request(
        request_id="pdcr-1",
        account_id="acct-1",
        identity_verified=False,
    )
    assert request["state"] == "IDENTITY_VERIFICATION_REQUIRED"

    request = verify_request_identity(request, verification_ref="local-biometric:1")
    request = restrict_processing(request)
    request = inventory_local_account_data(tmp_path, request)
    assert request["state"] == "INVENTORY_COMPLETE"
    assert {item["collection"] for item in request["inventory"]} == {
        "mobile_shell_sessions",
        "receipts",
    }

    request, receipt = execute_local_deletion(tmp_path, request)

    assert request["state"] == "COMPLETED"
    assert not (tmp_path / "mobile_shell_sessions" / "session-1.json").exists()
    assert (tmp_path / "receipts" / "continuity-1.json").exists()
    assert request["retained_data"][0]["basis"] == "continuity_or_request_audit_required"
    assert receipt["type"] == "personal_data_control_completion_receipt"
    assert receipt["authority"] == {
        "external_deletion": False,
        "legal_adjudication": False,
        "processor_completion": False,
    }
    assert read_record(tmp_path, "personal_data_control_requests", "pdcr-1")["record"]["state"] == "COMPLETED"
    assert read_record(tmp_path, "personal_data_control_receipts", receipt["id"])["record"]["id"] == receipt["id"]


def test_processor_propagation_is_pending_not_external_task(tmp_path: Path) -> None:
    initialize_store(tmp_path)
    write_record(
        tmp_path,
        "mobile_shell_sessions",
        "session-2",
        {"account_id": "acct-2"},
    )
    request = create_personal_data_request(
        request_id="pdcr-2",
        account_id="acct-2",
        identity_verified=True,
    )
    request = inventory_local_account_data(tmp_path, request)
    request, receipt = execute_local_deletion(
        tmp_path,
        request,
        processor_refs=["processor:supabase"],
    )

    assert request["state"] == "PROCESSOR_PROPAGATION_PENDING"
    assert receipt["result_state"] == "PROCESSOR_PROPAGATION_PENDING"
    assert request["processor_propagation"]["processors"] == [
        {"processor_ref": "processor:supabase", "state": "PENDING"}
    ]

    request = mark_processor_propagation(
        request,
        processor_ref="processor:supabase",
        state="COMPLETE",
        evidence_ref="receipt:processor-delete-1",
    )
    assert request["state"] == "COMPLETED"
    assert request["processor_propagation"]["state"] == "COMPLETE"


def test_unverified_request_fails_closed(tmp_path: Path) -> None:
    initialize_store(tmp_path)
    request = create_personal_data_request(
        request_id="pdcr-3",
        account_id="acct-3",
    )
    with pytest.raises(ValueError, match="identity verification is required"):
        inventory_local_account_data(tmp_path, request)
