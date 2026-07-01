from stegtalk.visual_light_codec import decode_light_bits, encode_light_bits


def test_light_bits_round_trip():
    payload = b"light bearer payload"
    bits = encode_light_bits(payload)
    assert decode_light_bits(bits) == payload
