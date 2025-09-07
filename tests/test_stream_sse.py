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


def test_stream_sse():
    port = 8003
    proc = start_server(port)
    url = f"http://127.0.0.1:{port}/v1/stream"
    r = requests.post(url, headers={"x-api-key": "change-me"}, json={"text": "abc"}, stream=True)
    body = b"".join(r.iter_lines())
    proc.terminate(); proc.join()
    assert r.status_code == 200
    assert b"event: start" in body and b"event: end" in body
