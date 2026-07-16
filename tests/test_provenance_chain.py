from dataclasses import replace

from stegtalk.transport.provenance_chain import build_provenance_chain, verify_provenance_chain


def test_provenance_chain_binds_all_receipts() -> None:
    chain = build_provenance_chain(
        message_id="msg-1",
        adapter_receipt_hash="a" * 64,
        selection_receipt_hash="b" * 64,
        custody_receipt_hash="c" * 64,
        observation_provenance_hash="d" * 64,
    )
    assert verify_provenance_chain(chain)
    assert not verify_provenance_chain(replace(chain, custody_receipt_hash="e" * 64))


def test_provenance_chain_denies_authority_escalation() -> None:
    chain = build_provenance_chain(
        message_id="msg-1",
        adapter_receipt_hash="a" * 64,
        selection_receipt_hash="b" * 64,
        custody_receipt_hash="c" * 64,
        observation_provenance_hash="d" * 64,
    )
    assert not verify_provenance_chain(replace(chain, delivery_claimed=True))
    assert not verify_provenance_chain(replace(chain, execution_authority_granted=True))


def test_provenance_chain_requires_complete_inputs() -> None:
    try:
        build_provenance_chain(
            message_id="msg-1",
            adapter_receipt_hash="",
            selection_receipt_hash="b" * 64,
            custody_receipt_hash="c" * 64,
            observation_provenance_hash="d" * 64,
        )
    except ValueError as exc:
        assert "required" in str(exc)
    else:
        raise AssertionError("missing adapter receipt must fail closed")
