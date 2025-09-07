from __future__ import annotations
from fastapi import APIRouter, BackgroundTasks, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse, HTMLResponse
import json, time, httpx
from ..schemas.requests import IntentReq, ScoreReq, ScoreBatchReq, GLRTPMReq
from ..services.runtime import reflect_intent, score_payload, tokenize_preview
from ..core.metrics import SSE_TOKENS
from ..core.audit import audit_event

api=APIRouter()

@api.get('/v1/version')
def version(): return {'name':'factsynth-ultimate-pro','version':'1.0.1'}

@api.post('/v1/intent_reflector')
def intent_reflector(req: IntentReq, request: Request):
    audit_event("intent_reflector", request.client.host if request.client else "unknown")
    return {'insight': reflect_intent(req.intent, req.length)}

@api.post('/v1/score')
def score(req: ScoreReq, request: Request, background_tasks: BackgroundTasks):
    audit_event("score", request.client.host if request.client else "unknown")
    result = {'score': score_payload(req.model_dump())}
    if req.callback_url:
        background_tasks.add_task(_post_callback, req.callback_url, result)
    return result

@api.post('/v1/score/batch')
def score_batch(batch: ScoreBatchReq, request: Request, background_tasks: BackgroundTasks):
    audit_event("score_batch", request.client.host if request.client else "unknown")
    items = batch.items[:batch.limit]
    results = [{'score': score_payload(it.model_dump())} for it in items]
    out = {'results': results, 'count': len(results)}
    if batch.callback_url:
        background_tasks.add_task(_post_callback, batch.callback_url, out)
    return out

@api.post('/v1/stream')
def stream(req: ScoreReq):
    tokens = tokenize_preview(req.text, max_tokens=256) or ["factsynth"]
    def gen():
        yield 'event: start\n'+'data: {}\n\n'
        for i, t in enumerate(tokens, 1):
            time.sleep(0.002)
            SSE_TOKENS.inc()
            yield 'event: token\n'+'data: '+json.dumps({'t':t,'n':i})+'\n\n'
        yield 'event: end\n'+'data: {}\n\n'
    return StreamingResponse(gen(), media_type='text/event-stream')

@api.websocket("/ws/stream")
async def ws_stream(ws: WebSocket):
    # простий auth: очікуємо x-api-key у headers
    key = ws.headers.get("x-api-key")
    await ws.accept()
    if not key:
        await ws.close(code=4401); return
    try:
        while True:
            data = await ws.receive_text()
            for t in tokenize_preview(data, 128):
                await ws.send_json({"t": t})
            await ws.send_json({"end": True})
    except WebSocketDisconnect:
        return

async def _post_callback(url: str, data: dict, attempts: int = 3):
    delay = 0.2
    async with httpx.AsyncClient(timeout=2.0) as client:
        for _ in range(attempts):
            try:
                r = await client.post(url, json=data)
                if r.status_code < 500: return
            except Exception:
                pass
            await _sleep(delay); delay *= 2

async def _sleep(s: float):
    # виділено для тестів/патчу
    time.sleep(s)
