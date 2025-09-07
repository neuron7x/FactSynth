from __future__ import annotations
import json, time
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ..schemas.models import (
    IntentReq,
    ScoreRequest,
    ScoreResponse,
    StreamRequest,
    GLRTPMRequest,
)
from ..services.runtime import reflect_intent, score_payload, glrtpm_run

api_router = APIRouter()

@api_router.post("/v1/intent_reflector")
def intent_reflector(req: IntentReq):
    return {"insight": reflect_intent(req.intent, req.length)}

@api_router.post("/v1/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    return ScoreResponse(score=score_payload(req.dict(exclude_none=True)))

@api_router.post("/v1/stream")
def stream(req: StreamRequest | None = None):
    payload = req.dict(exclude_none=True) if req else {}
    tokens = list(str(payload.get("text", "")))[:50] or list("factsynth")
    def gen():
        yield "event: start\n" + "data: {}\n\n"
        # Simulate token streaming
        buf = []
        for t in tokens:
            buf.append(t)
            time.sleep(0.01)
            yield "event: token\n" + "data: " + json.dumps({"t": t, "len": len(buf)}) + "\n\n"
        yield "event: end\n" + "data: {}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream")

@api_router.post("/v1/glrtpm/run")
def glrtpm(req: GLRTPMRequest) -> dict:
    return glrtpm_run(req.dict(exclude_none=True))
