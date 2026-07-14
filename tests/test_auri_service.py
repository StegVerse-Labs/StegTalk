from __future__ import annotations

import pytest

from stegtalk.auri.containment import ContainmentState, quarantine_provider
from stegtalk.auri.runtime import AuriRuntime
from stegtalk.auri.service import AuriService


def provider(prompt, context):
    return f"proposal for {context['action']}: {prompt}"


def request():
    return {
        "session": {
            "session_id": "session:service:001",
            "user_entity_id": "stegverse:user:authorized",
            "authenticated": True,
        },
        "instruction": "Prepare a reversible change",
        "target": "StegVerse-Labs/StegTalk",
        "action": "prepare_repository_change",
        "policy_ref": "policy:auri-l1",
        "delegation_ref": "delegation:advisory-only",
        "rollback_ref": "git:revert",
    }


def test_health_is_hash_addressed_and_advisory_only():
    service = AuriService(AuriRuntime(provider, "provider:test"))
    health = service.health()
    assert health.status == "ready"
    assert health.ready_for_advisory_requests is True
    assert health.execution_authority is False
    assert len(health.health_sha256) == 64


def test_submit_never_executes():
    service = AuriService(AuriRuntime(provider, "provider:test"))
    result = service.submit(request())
    assert result.execution_performed is False
    assert result.advisory_receipt["execution_performed"] is False


def test_quarantined_service_fails_closed():
    state = quarantine_provider(ContainmentState(), "provider.failure")
    service = AuriService(AuriRuntime(provider, "provider:test"), containment=state)
    assert service.health().status == "fail_closed"
    with pytest.raises(PermissionError):
        service.submit(request())
