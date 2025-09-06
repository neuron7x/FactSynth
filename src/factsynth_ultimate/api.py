from __future__ import annotations
import time, logging, orjson, json
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, ValidationError
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .generator import FSUInput, FSUConfig, generate_insight
from .metrics import j_index
from .settings import Settings
from .security import api_key_auth, rate_limiter
from .middleware import BodySizeLimitMiddleware
from .orchestrator.roles import RoleConfig
from .orchestrator.pipeline import ProjectSpec, Orchestrator

app = FastAPI(title="FactSynth Ultimate API", version="2.0.0")
CFG = FSUConfig()
S = Settings()

app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(BodySizeLimitMiddleware, max_content_length=S.MAX_BODY_BYTES)
app.add_middleware(CORSMiddleware, allow_origins=S.CORS_ALLOW_ORIGINS, allow_methods=["POST","GET","OPTIONS"], allow_headers=["*"])

logging.basicConfig(level=getattr(logging, S.LOG_LEVEL.upper(), logging.INFO))
logger = logging.getLogger("fsu")

class InsightResponse(BaseModel): text: str
class ScoreResponse(BaseModel): text: str; F: float; R: float; D: float; A: float; N: float; J: float
class GLRequest(BaseModel):
    title: str; thesis: str; rounds: int = 2; roles: list[RoleConfig]
class GLResponse(BaseModel):
    markdown: str; html: str; metrics: dict

@app.post("/v1/insight", response_model=InsightResponse, dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def insight(inp: FSUInput) -> InsightResponse:
    t0 = time.time(); out = generate_insight(inp, CFG)
    logger.info(orjson.dumps({"route":"insight","ms":int((time.time()-t0)*1000)}).decode())
    return InsightResponse(text=out)

@app.post("/v1/intent_reflector", response_model=InsightResponse, dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def intent_reflector(inp: FSUInput) -> InsightResponse:
    data = inp.model_dump(); data["length"] = data.get("length") or CFG.length
    return InsightResponse(text=generate_insight(FSUInput(**data), CFG))

@app.post("/v1/score", response_model=ScoreResponse, dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def score(inp: FSUInput) -> ScoreResponse:
    txt = generate_insight(inp, CFG); s = j_index(inp.intent, txt, CFG.start_phrase, facts=inp.facts, knowledge=inp.knowledge)
    return ScoreResponse(text=txt, **s)

@app.post("/v1/stream", dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
async def stream(inp: FSUInput):
    txt = generate_insight(inp, CFG)
    async def it(): yield f"data: {txt}\n\n"
    return StreamingResponse(it(), media_type="text/event-stream")

@app.post("/v1/glrtpm/run", response_model=GLResponse, dependencies=[Depends(api_key_auth), Depends(rate_limiter)])
def glrtpm_run(req: GLRequest) -> GLResponse:
    spec = ProjectSpec(title=req.title, thesis=req.thesis, roles=req.roles, rounds=req.rounds)
    orch = Orchestrator(spec); res = orch.run()
    return GLResponse(markdown=res["markdown"], html=res["html"], metrics=res["metrics"])

@app.get("/v1/healthz")
def healthz(): return {"status":"ok","version":app.version}

@app.get("/metrics")
def metrics(): return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.exception_handler(ValidationError)
async def verror(_: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error":"validation_error","detail":exc.errors()})

def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
