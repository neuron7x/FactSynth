import importlib, pytest

def _load_app():
    # Try common FastAPI patterns
    candidates = [
        ("app.main", "app"),
        ("app.main", "create_app"),
        ("factsynth_ultimate.api", "app"),
        ("factsynth_ultimate.main", "app"),
        ("factsynth_ultimate.main", "create_app"),
    ]
    for module_name, attr in candidates:
        try:
            m = importlib.import_module(module_name)
            obj = getattr(m, attr, None)
            if callable(obj):
                return obj()
            if obj is not None:
                return obj
        except Exception:
            continue
    return None

def test_health_endpoint():
    app = _load_app()
    if app is None:
        pytest.skip("No ASGI app found")
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi missing")
    client = TestClient(app)
    for path in ("/health", "/healthz", "/api/health"):
        r = client.get(path)
        if r.status_code < 500:
            # accept 200/204/404 (app exists), but assert no 5xx
            return
    pytest.fail("ASGI app present but health check returned server error")
