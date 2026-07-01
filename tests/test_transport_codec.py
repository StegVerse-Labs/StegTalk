from stegtalk.transport_codec import (
    chunk_payload,
    from_bits,
    manchester_decode,
    manchester_encode,
    reassemble_chunks,
    to_bits,
)


def test_bits_round_trip():
    payload = b"StegTalk optical/audio bearer seed"
    assert from_bits(to_bits(payload)) == payload


def test_manchester_round_trip():
    bits = to_bits(b"ok")
    encoded = manchester_encode(bits)
    assert manchester_decode(encoded) == bits


def test_chunk_payload_reassembles_and_detects_missing():
    payload = b"abc" * 100
    chunks = chunk_payload(payload, chunk_size=31, ttl_seconds=60)
    assert len(chunks) > 1
    assert reassemble_chunks(list(reversed(chunks))) == payload
    try:
        reassemble_chunks(chunks[:-1])
    except ValueError as exc:
        assert "missing chunks" in str(exc)
    else:
        raise AssertionError("missing chunk should fail")
