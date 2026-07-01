from stegtalk.transport_manifest import create_transport_manifest
from stegtalk.transport_pipeline import build_transport_package, receive_transport_package
from stegtalk.transport_replay import InMemoryReplayCache


def test_manifest_allows_supported_bearer_and_rejects_unsupported_destination():
    package = build_transport_package(b"manifest-boundary", bearer="light")
    manifest = create_transport_manifest(supported_bearers=["audio"])
    try:
        receive_transport_package(package, destination_manifest=manifest)
    except ValueError as exc:
        assert "not allowed" in str(exc)
    else:
        raise AssertionError("unsupported bearer should fail destination manifest")


def test_replay_cache_rejects_second_receive():
    package = build_transport_package(b"one-time", bearer="audio")
    cache = InMemoryReplayCache()
    receive_transport_package(package, replay_cache=cache)
    try:
        receive_transport_package(package, replay_cache=cache)
    except ValueError as exc:
        assert "replayed" in str(exc)
    else:
        raise AssertionError("replay should fail")
