import threading, time, httpx
from src.factsynth_ultimate.api import run

def _spawn():
    th = threading.Thread(target=run, daemon=True); th.start(); time.sleep(0.8)

def test_endpoints_ok():
    _spawn()
    base = "http://127.0.0.1:8000"
    H = {"x-api-key":"change-me","content-type":"application/json"}
    r = httpx.get(base+"/v1/healthz")
    assert r.status_code == 200
    r2 = httpx.post(base+"/v1/intent_reflector", headers=H, json={"intent":"Тест","length":100})
    assert r2.status_code == 200 and "text" in r2.json()
