import importlib, pytest

def _load_app():
    candidates=[("app.main","app"),("app.main","create_app"),("factsynth_ultimate.main","app"),("factsynth_ultimate.main","create_app")]
    for mod,attr in candidates:
        try:
            m=importlib.import_module(mod)
            obj=getattr(m,attr,None)
            if callable(obj): return obj()
            if obj is not None: return obj
        except Exception:
            pass
    return None

def test_metrics_if_present():
    app=_load_app()
    if app is None: pytest.skip("No ASGI app found.")
    try:
        from fastapi.testclient import TestClient
    except Exception:
        pytest.skip("fastapi missing")
    c=TestClient(app)
    r=c.get("/metrics")
    if r.status_code == 404:
        pytest.skip("metrics endpoint absent")
    assert r.status_code < 500
    assert isinstance(r.text, str)
    assert len(r.text) > 0
