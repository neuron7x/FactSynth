from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import CollectorRegistry, generate_latest, Counter, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from .service import synthesize

app = FastAPI(title="FactSynth API", version="")
registry = CollectorRegistry()
REQUESTS = Counter("factsynth_requests_total", "Total API requests", ["endpoint"], registry=registry)


class GenerateIn(BaseModel):
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(128, ge=1, le=4096)


class GenerateOut(BaseModel):
    output: str


@app.get("/healthz")
def healthz() -> dict:
    REQUESTS.labels("/healthz").inc()
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


@app.post("/v1/generate", response_model=GenerateOut)
def generate(body: GenerateIn):
    REQUESTS.labels("/v1/generate").inc()
    try:
        return {"output": synthesize(body.prompt, body.max_tokens)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
