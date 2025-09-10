from __future__ import annotations
import uvicorn
from fastapi import FastAPI
from prometheus_client import Counter, Histogram
from time import time
from app.api.verify import router as verify_router

app = FastAPI(title="FactSynth")
app.include_router(verify_router)

REQS = Counter("factsynth_verify_total","Count of verify requests")
LAT  = Histogram("factsynth_verify_latency_ms","Verify latency (ms)")

@app.middleware("http")
async def metrics_mw(request, call_next):
    if request.url.path == "/v1/verify":
        REQS.inc()
        t0 = time()
        resp = await call_next(request)
        LAT.observe((time()-t0)*1000.0)
        return resp
    return await call_next(request)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
