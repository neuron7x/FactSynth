from __future__ import annotations

import asyncio
import json
import logging
import random
import time
from http import HTTPStatus

import httpx
from fastapi import APIRouter, BackgroundTasks, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from factsynth_ultimate import VERSION

from ..core.audit import audit_event
from ..core.metrics import SSE_TOKENS
from ..core.secrets import read_api_key
from ..schemas.requests import IntentReq, ScoreBatchReq, ScoreReq
from ..services.runtime import reflect_intent, score_payload, tokenize_preview

logger=logging.getLogger(__name__)

API_KEY = read_api_key("API_KEY", "API_KEY_FILE", "change-me", "API_KEY")

api=APIRouter()

@api.get("/v1/version")
def version() -> dict[str, str]:
    return {"name": "factsynth-ultimate-pro", "version": VERSION}

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
async def stream(req: ScoreReq):
    tokens = tokenize_preview(req.text, max_tokens=256) or ["factsynth"]
    async def event_stream():
        sent = 0
        try:
            yield 'event: start\n' + 'data: {}\n\n'
            for t in tokens:
                await asyncio.sleep(0.002)
                sent += 1
                yield 'event: token\n' + 'data: ' + json.dumps({'t': t, 'n': sent}) + '\n\n'
            yield 'event: end\n' + 'data: {}\n\n'
        except asyncio.CancelledError:
            logger.info("SSE stream cancelled after %d tokens", sent)
        finally:
            SSE_TOKENS.inc(sent)
    return StreamingResponse(event_stream(), media_type='text/event-stream')

@api.websocket("/ws/stream")
async def ws_stream(ws: WebSocket):
    """Stream tokenization results over WebSocket.

    The client establishes a WebSocket connection and the server first checks
    the ``x-api-key`` header before completing the handshake. If the header is
    missing or does not match the configured key, the connection is closed with
    code ``4401`` and reason ``"Unauthorized"`` without accepting. Once the key
    is verified, the connection is accepted and incoming text messages are
    tokenized and each token is emitted back to the client as JSON messages.
    """
    key = ws.headers.get("x-api-key")
    if key != API_KEY:
        await ws.close(code=4401, reason="Unauthorized")
        return
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            for t in tokenize_preview(data, 128):
                await ws.send_json({"t": t})
            await ws.send_json({"end": True})
    except WebSocketDisconnect:
        return

async def _post_callback(  # noqa: PLR0913
    url: str,
    data: dict,
    attempts: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 5.0,
    max_elapsed: float = 15.0,
):
    delay = base_delay
    last_err = None
    start = time.monotonic()
    attempt_num = 0
    async with httpx.AsyncClient(timeout=2.0) as client:
        for i in range(1, attempts + 1):
            elapsed = time.monotonic() - start
            if elapsed >= max_elapsed:
                break
            attempt_num = i
            try:
                r = await client.post(url, json=data)
                if HTTPStatus.OK <= r.status_code < HTTPStatus.MULTIPLE_CHOICES:
                    return
                last_err = f"HTTP {r.status_code}"
            except Exception as e:  # noqa: BLE001
                last_err = str(e)
            logger.warning("Callback attempt %d/%d failed: %s", i, attempts, last_err)
            if i < attempts:
                elapsed = time.monotonic() - start
                if elapsed >= max_elapsed:
                    break
                jittered = delay * random.uniform(0.8, 1.2)
                remaining = max_elapsed - elapsed
                await _sleep(min(jittered, remaining))
                delay = min(delay * 2, max_delay)
    if last_err is not None:
        logger.error("Callback failed after %d attempts: %s", attempt_num, last_err)

async def _sleep(s: float):
    # виділено для тестів/патчу
    await asyncio.sleep(s)
