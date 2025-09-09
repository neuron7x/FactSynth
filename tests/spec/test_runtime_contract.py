import os, pytest, requests

BASE = os.getenv("BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")

def _get(path, **kw):
    headers = kw.pop("headers", {})
    if API_KEY:
        headers.setdefault("x-api-key", API_KEY)
    return requests.get(BASE + path, headers=headers, timeout=10, **kw)

def _post(path, json=None, **kw):
    headers = kw.pop("headers", {})
    if API_KEY:
        headers.setdefault("x-api-key", API_KEY)
    return requests.post(BASE + path, json=json, headers=headers, timeout=15, **kw)

def test_healthz_ok():
    r = _get("/v1/healthz")
    assert r.status_code == 200
    ct = r.headers.get("content-type","").lower()
    assert "application" in ct or "text" in ct

@pytest.mark.parametrize("path", ["/v1/version"])
def test_version_endpoint_shape(path):
    r = _get(path)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, dict)
    assert any(k in data for k in ("version","app_version","build","tag"))

def test_problem_json_forbidden_without_key():
    # перевірка Problem+JSON: спроба без ключа на захищений ендпойнт
    r = requests.post(BASE + "/v1/generate", json={"prompt":"hi"}, timeout=10)
    assert r.status_code in (401, 403)
    ct = r.headers.get("content-type","").lower()
    assert "application/problem+json" in ct or "application/json" in ct
    body = r.json()
    assert any(k in body for k in ("type","title","detail","status"))
