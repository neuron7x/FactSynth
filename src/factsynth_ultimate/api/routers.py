"""HTTP API routers exposing scoring and streaming endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import random
import string
import time
from collections.abc import AsyncGenerator
from functools import lru_cache
from http import HTTPStatus
from typing import Any
from urllib.parse import urlparse

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import StreamingResponse
from starlette.websockets import WebSocketState

from factsynth_ultimate import VERSION

from ..core.audit import audit_event
from ..core.metrics import (
    CITATION_PRECISION,
    EXPLANATION_SATISFACTION,
    SSE_TOKENS,
)
from ..core.settings import load_settings
from ..schemas.requests import (
    FeedbackReq,
    GenerateReq,
    IntentReq,
    ScoreBatchReq,
    ScoreReq,
)
from ..services.runtime import reflect_intent, score_payload, tokenize_preview

logger = logging.getLogger(__name__)

ALLOWED_CALLBACK_SCHEMES = {"http", "https"}


@lru_cache(maxsize=1)
def get_allowed_hosts() -> set[str]:
    """Return the set of allowed callback hosts."""
    hosts = load_settings().callback_url_allowed_hosts
    return set(filter(None, hosts.split(",")))


def reload_allowed_hosts() -> None:
    """Clear the allowed hosts cache to reload settings."""
    get_allowed_hosts.cache_clear()


def validate_callback_url(url: str) -> None:
    """Validate that a callback URL uses an allowed scheme and host.

    Args:
        url: URL provided by the client.

    Raises:
        HTTPException: If the URL uses a disallowed scheme or host or the
            allowlist is empty.
    """
    allowed_hosts = get_allowed_hosts()
    try:
        parsed = urlparse(url)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST, detail="Invalid callback URL"
        ) from exc

    if parsed.scheme not in ALLOWED_CALLBACK_SCHEMES:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Callback URL scheme must be http or https",
        )

    if not parsed.hostname:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Missing callback URL host",
        )

    if not allowed_hosts:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Callback URL host allowlist is empty",
        )

    if parsed.hostname not in allowed_hosts:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Callback URL host not in allowlist",
        )


api = APIRouter()


@api.get("/v1/version")
def version() -> dict[str, str]:
    """Return package name and semantic version."""

    return {"name": "factsynth-ultimate-pro", "version": VERSION}


@api.post("/v1/intent_reflector")
def intent_reflector(req: IntentReq, request: Request) -> dict[str, str]:
    """Reflect user intent into a concise insight string."""

    audit_event("intent_reflector", request.client.host if request.client else "unknown")
    return {"insight": reflect_intent(req.intent, req.length)}


@api.post("/v1/score")
def score(
    req: ScoreReq,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, float]:
    """Calculate a score for the provided request body."""

    audit_event("score", request.client.host if request.client else "unknown")
    result: dict[str, float] = {"score": score_payload(req.model_dump())}
    if req.callback_url:
        validate_callback_url(req.callback_url)
        request_id = getattr(request.state, "request_id", "")
        background_tasks.add_task(_post_callback, req.callback_url, result, request_id=request_id)
    return result


@api.post("/v1/score/batch")
def score_batch(
    batch: ScoreBatchReq,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict[str, Any]:
    """Score multiple payloads in a single request."""

    audit_event("score_batch", request.client.host if request.client else "unknown")
    items = batch.items[: batch.limit]
    results = [{"score": score_payload(it.model_dump())} for it in items]
    out: dict[str, Any] = {"results": results, "count": len(results)}
    if batch.callback_url:
        validate_callback_url(batch.callback_url)
        request_id = getattr(request.state, "request_id", "")
        background_tasks.add_task(_post_callback, batch.callback_url, out, request_id=request_id)
    return out


@api.post("/v1/generate")
def generate(req: GenerateReq, request: Request) -> dict[str, dict[str, str]]:
    """Produce a deterministic pseudo-random string matching the input length."""

    audit_event("generate", request.client.host if request.client else "unknown")
    rng = random.Random(req.seed)
    alphabet = string.ascii_letters + string.digits + " "
    out = "".join(rng.choice(alphabet) for _ in req.text)
    return {"output": {"text": out}}


@api.post("/v1/feedback")
def feedback(req: FeedbackReq, request: Request) -> dict[str, str]:
    """Record user feedback on explanation clarity and citation accuracy."""

    audit_event("feedback", request.client.host if request.client else "unknown")
    EXPLANATION_SATISFACTION.observe(req.explanation_satisfaction)
    CITATION_PRECISION.observe(req.citation_precision)
    return {"status": "recorded"}


@api.post("/v1/stream")
async def stream(  # noqa: C901
    req: ScoreReq, request: Request, token_delay: float | None = None
) -> StreamingResponse:
    """Stream tokenized preview of ``req.text`` using Server-Sent Events."""

    delay = token_delay if token_delay is not None else load_settings().token_delay
    tokens = tokenize_preview(req.text, max_tokens=256) or ["factsynth"]
    resources: list[object] = []
    for obj in (
        tokens,
        getattr(tokens, "tokenizer", None),
        getattr(tokens, "retriever", None),
    ):
        if obj and (hasattr(obj, "close") or hasattr(obj, "aclose")):
            resources.append(obj)

    request_id = getattr(request.state, "request_id", "")

    async def event_stream() -> AsyncGenerator[str, None]:
        """Yield SSE events for each produced token."""

        sent = 0
        try:
            yield "event: start\n" + "data: {}\n\n"
            for t in tokens:
                await asyncio.sleep(delay)
                if await request.is_disconnected():
                    break
                sent += 1
                yield "event: token\n" + "data: " + json.dumps({"t": t, "n": sent}) + "\n\n"
            yield "event: end\n" + "data: {}\n\n"
        except asyncio.CancelledError:
            logger.info(
                "SSE stream cancelled after %d tokens", sent, extra={"request_id": request_id}
            )
            raise
        finally:
            SSE_TOKENS.inc(sent)
            for obj in resources:
                try:
                    aclose = getattr(obj, "aclose", None)
                    if callable(aclose):
                        await aclose()
                        continue
                    close = getattr(obj, "close", None)
                    if callable(close):
                        close()
                except Exception:  # noqa: BLE001
                    logger.debug(
                        "Error closing resource",
                        exc_info=True,
                        extra={"request_id": request_id},
                    )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def is_client_connected(ws: WebSocket) -> bool:
    """Return ``True`` if the WebSocket connection is still active."""

    return (
        ws.client_state == WebSocketState.CONNECTED
        and ws.application_state == WebSocketState.CONNECTED
    )


@api.websocket("/ws/stream")
async def ws_stream(ws: WebSocket) -> None:  # noqa: C901, PLR0912
    """Stream tokenization results over WebSocket with API-key auth."""

    cfg = load_settings()
    key = ws.headers.get(cfg.auth_header_name)
    if key != cfg.api_key:
        await ws.close(code=4401, reason="Unauthorized")
        return
    await ws.accept()
    try:
        while True:
            data = await ws.receive_text()
            tokens = tokenize_preview(data, 128)
            resources: list[object] = []
            for obj in (
                tokens,
                getattr(tokens, "tokenizer", None),
                getattr(tokens, "retriever", None),
            ):
                if obj and (hasattr(obj, "close") or hasattr(obj, "aclose")):
                    resources.append(obj)
            sent = 0
            try:
                for t in tokens:
                    if not is_client_connected(ws):
                        break
                    await ws.send_json({"t": t})
                    sent += 1
                if is_client_connected(ws):
                    await ws.send_json({"end": True})
            finally:
                SSE_TOKENS.inc(sent)
                for obj in resources:
                    try:
                        aclose = getattr(obj, "aclose", None)
                        if callable(aclose):
                            await aclose()
                            continue
                        close = getattr(obj, "close", None)
                        if callable(close):
                            close()
                    except Exception:  # noqa: BLE001
                        logger.debug("Error closing resource", exc_info=True)
    except WebSocketDisconnect:
        return


async def _post_callback(  # noqa: PLR0913
    url: str,
    data: dict,
    attempts: int = 3,
    base_delay: float = 0.2,
    max_delay: float = 5.0,
    max_elapsed: float = 15.0,
    request_id: str = "",
) -> None:
    """POST ``data`` to ``url`` using exponential backoff."""

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
            logger.warning(
                "Callback attempt %d/%d failed: %s",
                i,
                attempts,
                last_err,
                extra={"request_id": request_id},
            )
            if i < attempts:
                elapsed = time.monotonic() - start
                if elapsed >= max_elapsed:
                    break
                jittered = delay * random.uniform(0.8, 1.2)
                remaining = max_elapsed - elapsed
                await _sleep(min(jittered, remaining))
                delay = min(delay * 2, max_delay)
    if last_err is not None:
        logger.error(
            "Callback failed after %d attempts: %s",
            attempt_num,
            last_err,
            extra={"request_id": request_id},
        )


async def _sleep(s: float) -> None:
    """Async sleep exposed for tests and patching."""

    await asyncio.sleep(s)
