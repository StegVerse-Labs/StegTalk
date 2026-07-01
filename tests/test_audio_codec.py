from stegtalk.audio_codec import decode_bfsk_samples, encode_bfsk_samples


def test_bfsk_samples_round_trip():
    payload = b"audio bearer"
    samples = encode_bfsk_samples(payload)
    assert decode_bfsk_samples(samples) == payload
