from fastapi.testclient import TestClient
from factsynth_ultimate.app import app
def test_health():
 c=TestClient(app); assert c.get('/v1/healthz').status_code==200
