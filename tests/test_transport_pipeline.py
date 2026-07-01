from stegtalk.transport_pipeline import build_transport_package, receive_transport_package


def test_transport_pipeline_quarantines_by_default():
    payload = b"governed payload"
    package = build_transport_package(payload, bearer="light", chunk_size=7)
    result = receive_transport_package(package)
    assert result["payload"] == payload
    assert package["transport_receipt"]["type"] == "stegtalk_transport_receipt"
    assert result["reconstruction_receipt"]["result"] == "complete"
    assert result["presentation_receipt"]["decision"] == "quarantine"
    assert result["presentation_receipt"]["reason"] == "render_requires_destination_admissibility"


def test_transport_pipeline_can_render_when_explicitly_allowed():
    payload = b"renderable payload"
    package = build_transport_package(payload, bearer="audio")
    result = receive_transport_package(package, allow_render=True)
    assert result["presentation_receipt"]["decision"] == "render"
