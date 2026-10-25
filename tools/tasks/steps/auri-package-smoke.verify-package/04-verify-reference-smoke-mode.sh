docker run -d --rm --name auri-reference -e AURI_PROVIDER_MODE=reference_echo -e AURI_PROVIDER_ID=provider:ci-reference -p 18081:8080 auri-l1:smoke
python - <<'PY'
import json, time, urllib.request
for _ in range(30):
    try:
        with urllib.request.urlopen('http://127.0.0.1:18081/health') as response:
            body = json.load(response)
        assert body['status'] == 'ready'
        assert body['execution_authority'] is False
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit('reference health endpoint not observed')
payload = json.dumps({
    'session': {
        'session_id': 'session:ci',
        'user_entity_id': 'stegverse:user:ci',
        'authenticated': True
    },
    'instruction': 'Prepare a reversible repository advisory',
    'target': 'StegVerse-Labs/StegTalk',
    'action': 'prepare_repository_change',
    'evidence_refs': ['auri/identity.v1.json'],
    'reversible': True,
    'rollback_ref': 'git:revert'
}).encode()
request = urllib.request.Request('http://127.0.0.1:18081/advisory', data=payload, headers={'Content-Type': 'application/json'})
with urllib.request.urlopen(request) as response:
    result = json.load(response)
assert result['execution_performed'] is False
assert result['candidate']['auri_posture']['execution_authority'] is False
PY
docker stop auri-reference
