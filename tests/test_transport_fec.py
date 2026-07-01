from stegtalk.transport_fec import chunk_payload_with_xor_fec, recover_reassemble_xor_fec
from stegtalk.transport_pipeline import build_transport_package, receive_transport_package


def test_xor_fec_recovers_one_missing_chunk_per_group():
    payload = b"abcdefg" * 23
    chunks = chunk_payload_with_xor_fec(payload, chunk_size=17, group_size=4)
    damaged = [chunk for chunk in chunks if chunk.get("chunk_index") != 2]
    assert recover_reassemble_xor_fec(damaged) == payload


def test_pipeline_uses_xor_fec_profile():
    payload = b"pipeline fec payload" * 9
    package = build_transport_package(payload, bearer="light", chunk_size=19, fec_profile="xor-one-loss-v1")
    package["chunks"] = [chunk for chunk in package["chunks"] if chunk.get("chunk_index") != 1]
    result = receive_transport_package(package)
    assert result["payload"] == payload
    assert result["presentation_receipt"]["decision"] == "quarantine"
