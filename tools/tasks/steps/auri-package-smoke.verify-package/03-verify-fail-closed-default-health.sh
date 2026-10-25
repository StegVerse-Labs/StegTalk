docker run -d --rm --name auri-disabled -p 18080:8080 auri-l1:smoke
python - <<'PY'
import json, time, urllib.error, urllib.request
for _ in range(30):
    try:
        urllib.request.urlopen('http://127.0.0.1:18080/health')
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read())
        assert exc.code == 503
        assert body['status'] == 'fail_closed'
        assert body['execution_authority'] is False
        break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit('fail-closed health endpoint not observed')
PY
docker stop auri-disabled
