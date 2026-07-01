# StegTalk Transport Bearer Status

Done means the current StegTalk repository gains repo-native, no-new-workflow infrastructure for chunked payload transport, optical/light encoding, audio BFSK encoding, transport receipts, reconstruction receipts, destination-controlled render/quarantine gates, replay/TTL enforcement, public transport manifests, and a dependency-free XOR FEC recovery profile.

## Added files

- `src/stegtalk/transport_codec.py`
- `src/stegtalk/visual_light_codec.py`
- `src/stegtalk/audio_codec.py`
- `src/stegtalk/transport_receipts.py`
- `src/stegtalk/transport_pipeline.py`
- `src/stegtalk/transport_replay.py`
- `src/stegtalk/transport_manifest.py`
- `src/stegtalk/transport_admissibility.py`
- `src/stegtalk/transport_fec.py`
- `tests/test_transport_codec.py`
- `tests/test_visual_light_codec.py`
- `tests/test_audio_codec.py`
- `tests/test_transport_pipeline.py`
- `tests/test_transport_replay_manifest.py`
- `tests/test_transport_fec.py`

## Boundary preserved

These files do not add workflows and do not create a production network path. They add local reference primitives and tests only.

Transport receipts are evidence, not authority. Received packages quarantine by default until a destination admissibility layer explicitly allows rendering.

## Current operational coverage

- chunk split/reassembly
- hash verification
- Manchester light bitstream round trip
- BFSK audio sample round trip
- destination manifest compatibility checks
- replay cache denial
- TTL expiration denial
- one-loss-per-group XOR FEC recovery
- quarantine-by-default presentation receipt

## Verification

Run:

```bash
python -m pytest tests/test_transport_codec.py tests/test_visual_light_codec.py tests/test_audio_codec.py tests/test_transport_pipeline.py tests/test_transport_replay_manifest.py tests/test_transport_fec.py
```
