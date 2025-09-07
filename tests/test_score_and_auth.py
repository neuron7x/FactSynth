from multiprocessing import Process
import time
import requests
import uvicorn
from factsynth_ultimate.app import create_app


def run_server(port: int):
    uvicorn.run(create_app(), host="127.0.0.1", port=port, log_level="warning")


def start_server(port: int) -> Process:
    proc = Process(target=run_server, args=(port,), daemon=True)
    proc.start()
    for _ in range(50):
        try:
            requests.get(f"http://127.0.0.1:{port}/v1/healthz")
            break
        except requests.ConnectionError:
            time.sleep(0.1)
    return proc


def test_auth_required():
    port = 8001
    proc = start_server(port)
    url = f"http://127.0.0.1:{port}/v1/score"
    assert requests.post(url, json={"text": "x"}).status_code == 401
    assert requests.post(url, headers={"x-api-key": "change-me"}, json={"text": "x"}).status_code == 200
    proc.terminate(); proc.join()


def test_score_values():
    port = 8002
    proc = start_server(port)
    url = f"http://127.0.0.1:{port}/v1/score"
    r = requests.post(url, headers={"x-api-key": "change-me"}, json={"text": "hello world", "targets": ["hello", "x"]})
    proc.terminate(); proc.join()
    assert r.status_code == 200
    s = r.json()["score"]
    assert 0.0 <= s <= 1.0
