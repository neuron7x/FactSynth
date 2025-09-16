"""HTTP API routers exposing scoring and streaming endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import time
from collections import deque
from collections.abc import AsyncGenerator
from functools import lru_cache
from http import HTTPStatus
from typing import Any, Mapping

import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.websockets import WebSocketState

from factsynth_ultimate import VERSION
from facts import FactPipeline, FactPipelineError
from factsynth_ultimate.stream import stream_facts

from ..auth.ws import WebSocketAuthError, authenticate_ws
from ..config import (
    ConfigError,
    add_callback_host,
    remove_callback_host,
    set_callback_hosts,
)
from ..core.audit import audit_event
from ..core.metrics import (
    CITATION_PRECISION,
    EXPLANATION_SATISFACTION,
    SSE_TOKENS,
)
from ..core.problem_details import ProblemDetails, bad_request
from ..core.settings import load_settings
from ..validators.callback import validate_callback_url
from ..schemas.callbacks import (
    CallbackAllowlistResponse,
    CallbackAllowlistSetRequest,
    CallbackHostRequest,
)
from ..schemas.requests import FeedbackReq, IntentReq, ScoreBatchReq, ScoreReq
from ..services.runtime import reflect_intent, score_payload
from .v1 import generate_router
from .v1.generate import get_fact_pipeline

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 160


class SessionRateLimiter:
    """Simple fixed-window rate limiter used for WebSocket sessions."""

    def __init__(self, limit: int = 0, window: float = 60.0) -> None:
        self.limit = int(limit)
        self.window = float(window)
        self._events: dict[str, deque[float]] = {}

    def allow(self, client_id: str) -> tuple[bool, int]:
        """Record an event for ``client_id`` and return allowance/remaining."""

        if self.limit <= 0 or self.window <= 0:
            return True, self.limit

        now = time.monotonic()
        bucket = self._events.setdefault(client_id, deque())
        while bucket and now - bucket[0] > self.window:
            bucket.popleft()
        if len(bucket) >= self.limit:
            return False, 0
        bucket.append(now)
        remaining = max(0, self.limit - len(bucket))
        return True, remaining

    def retry_after(self, client_id: str) -> int:
        """Return seconds until another event is allowed for ``client_id``."""

        if self.limit <= 0 or self.window <= 0:
            return 0
        bucket = self._events.get(client_id)
        if not bucket:
            return 0
        now = time.monotonic()
        oldest = bucket[0]
        wait = self.window - (now - oldest)
        if wait <= 0:
            return 0
        return max(1, int(math.ceil(wait)))

    def reset(self, client_id: str) -> None:
        """Clear tracking data for ``client_id``."""

        self._events.pop(client_id, None)


def _client_identifier(ws: WebSocket) -> str:
    client = ws.client
    if client is None:
        return "unknown:0"
    host = getattr(client, "host", None)
    port = getattr(client, "port", None)
    if host is None and isinstance(client, tuple):
        host, port = client
    host_str = host or "unknown"
    port_val = port if port is not None else 0
    return f"{host_str}:{port_val}"


def _session_limiter(ws: WebSocket) -> SessionRateLimiter:
    existing = getattr(ws.app.state, "ws_rate_limiter", None)
    if isinstance(existing, SessionRateLimiter):
        return existing
    settings = load_settings()
    burst = getattr(settings.rates_ip, "burst", 0)
    sustain = getattr(settings.rates_ip, "sustain", 1.0) or 1.0
    window = max(1.0, float(burst) / float(sustain)) if burst > 0 else 60.0
    limiter = SessionRateLimiter(limit=int(burst), window=window)
    ws.app.state.ws_rate_limiter = limiter
    return limiter


def _last_event_id(request: Request) -> int | None:
    raw = request.headers.get("last-event-id")
    if raw is None:
        return None
    try:
        return max(0, int(raw))
    except ValueError:
        return None


def _sse_message(event: str, data: dict[str, Any], event_id: str | None = None) -> str:
    payload = [f"event: {event}"]
    if event_id is not None:
        payload.append(f"id: {event_id}")
    payload.append("data: " + json.dumps(data, ensure_ascii=False))
    return "\n".join(payload) + "\n\n"


def _client_host(request: Request) -> str:
    """Best-effort retrieval of the requesting client's host."""

    return getattr(getattr(request, "client", None), "host", "unknown")


@lru_cache(maxsize=1)
def get_allowed_hosts() -> tuple[str, ...]:
    """Return the tuple of allowed callback hosts."""

    hosts = load_settings().callback_url_allowed_hosts
    unique: dict[str, None] = {}
    for host in hosts:
        if not host:
            continue
        normalized = host.lower()
        unique.setdefault(normalized, None)
    return tuple(unique.keys())


def reload_allowed_hosts() -> None:
    """Clear the allowed hosts cache to reload settings."""
    get_allowed_hosts.cache_clear()


def _allowlist_response() -> CallbackAllowlistResponse:
    return CallbackAllowlistResponse(hosts=list(get_allowed_hosts()))

api: APIRouter = APIRouter()
api.include_router(generate_router)


def _config_problem(detail: str) -> JSONResponse:
    return bad_request("Invalid configuration", detail).to_response()


def _persist_problem(detail: str) -> JSONResponse:
    problem = ProblemDetails(
        title="Failed to update configuration",
        detail=detail,
        status=int(HTTPStatus.INTERNAL_SERVER_ERROR),
    )
    return problem.to_response()


@api.get("/v1/callbacks/allowlist", response_model=CallbackAllowlistResponse)
def callback_allowlist_get() -> CallbackAllowlistResponse:
    """Return the configured callback host allowlist."""

    return _allowlist_response()


@api.post("/v1/callbacks/allowlist", response_model=CallbackAllowlistResponse)
def callback_allowlist_add(payload: CallbackHostRequest) -> CallbackAllowlistResponse | JSONResponse:
    """Add a hostname to the callback allowlist."""

    try:
        add_callback_host(payload.host)
    except ConfigError as exc:
        return _config_problem(str(exc))
    except OSError as exc:  # pragma: no cover - filesystem failures
        logger.error("Failed to persist callback allowlist", exc_info=exc)
        return _persist_problem("Could not persist callback allowlist.")

    reload_allowed_hosts()
    logger.info("Callback host allowed", extra={"callback_host": payload.host})
    return _allowlist_response()


@api.put("/v1/callbacks/allowlist", response_model=CallbackAllowlistResponse)
def callback_allowlist_replace(
    payload: CallbackAllowlistSetRequest,
) -> CallbackAllowlistResponse | JSONResponse:
    """Replace the callback allowlist."""

    try:
        set_callback_hosts(payload.hosts)
    except ConfigError as exc:
        return _config_problem(str(exc))
    except OSError as exc:  # pragma: no cover - filesystem failures
        logger.error("Failed to persist callback allowlist", exc_info=exc)
        return _persist_problem("Could not persist callback allowlist.")

    reload_allowed_hosts()
    logger.info("Callback allowlist replaced", extra={"callback_hosts": payload.hosts})
    return _allowlist_response()


@api.delete("/v1/callbacks/allowlist/{host}", response_model=CallbackAllowlistResponse)
def callback_allowlist_remove(host: str) -> CallbackAllowlistResponse | JSONResponse:
    """Remove a hostname from the callback allowlist."""

    normalized = host.strip().lower()
    if not normalized:
        return _config_problem("Host must not be empty")

    try:
        remove_callback_host(normalized)
    except ConfigError as exc:
        return _config_problem(str(exc))
    except OSError as exc:  # pragma: no cover - filesystem failures
        logger.error("Failed to persist callback allowlist", exc_info=exc)
        return _persist_problem("Could not persist callback allowlist.")

    reload_allowed_hosts()
    logger.info("Callback host removed", extra={"callback_host": normalized})
    return _allowlist_response()


@api.get("/v1/version")
def version() -> dict[str, str]:
    """Return package name and semantic version."""

    return {"name": "factsynth-ultimate-pro", "version": VERSION}


@api.post("/v1/intent_reflector")
def intent_reflector(req: IntentReq, request: Request) -> dict[str, str]:
    """Reflect user intent into a concise insight string."""

    audit_event("intent_reflector", _client_host(request))
    return {"insight": reflect_intent(req.intent, req.length)}


@api.post("/v1/score")
def score(
    req: ScoreReq,
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse | dict[str, float]:
    """Calculate a score for the provided request body."""

    audit_event("score", _client_host(request))
    result: dict[str, float] = {"score": score_payload(req.model_dump())}
    if req.callback_url:
        problem = validate_callback_url(req.callback_url, get_allowed_hosts())
        if problem:
            return problem.to_response()
        request_id = getattr(request.state, "request_id", "")
        background_tasks.add_task(_post_callback, req.callback_url, result, request_id=request_id)
    return result


@api.post("/v1/score/batch")
def score_batch(
    batch: ScoreBatchReq,
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse | dict[str, Any]:
    """Score multiple payloads in a single request."""

    audit_event("score_batch", _client_host(request))
    items = batch.items[: batch.limit]
    results = [{"score": score_payload(it.model_dump())} for it in items]
    out: dict[str, Any] = {"results": results, "count": len(results)}
    if batch.callback_url:
        problem = validate_callback_url(batch.callback_url, get_allowed_hosts())
        if problem:
            return problem.to_response()
        request_id = getattr(request.state, "request_id", "")
        background_tasks.add_task(_post_callback, batch.callback_url, out, request_id=request_id)
    return out


@api.post("/v1/feedback")
def feedback(req: FeedbackReq, request: Request) -> dict[str, str]:
    """Record user feedback on explanation clarity and citation accuracy."""

    audit_event("feedback", _client_host(request))
    EXPLANATION_SATISFACTION.observe(req.explanation_satisfaction)
    CITATION_PRECISION.observe(req.citation_precision)
    return {"status": "recorded"}


async def _sse_stream(
    req: ScoreReq,
    request: Request,
    pipeline: FactPipeline,
    *,
    token_delay: float | None,
    chunk_size: int | None,
    cursor: int | None,
) -> StreamingResponse:
    delay = token_delay if token_delay is not None else load_settings().token_delay
    size = max(1, chunk_size or DEFAULT_CHUNK_SIZE)
    start_at = max(0, cursor or 0)
    last_id = _last_event_id(request)
    if cursor is None and last_id is not None:
        start_at = last_id + 1
    replay = start_at > 0
    state = getattr(request, "state", None)
    request_id = getattr(state, "request_id", "")

    async def is_disconnected() -> bool:
        return await request.is_disconnected()

    async def event_stream() -> AsyncGenerator[str, None]:
        sent = 0
        try:
            yield _sse_message("start", {"cursor": start_at, "replay": replay})
            async for chunk in stream_facts(
                pipeline,
                req.text,
                chunk_size=size,
                start_at=start_at,
                delay=delay,
                is_disconnected=is_disconnected,
            ):
                sent += 1
                yield _sse_message(
                    "chunk",
                    {"id": chunk.index, "text": chunk.text, "replay": replay},
                    event_id=str(chunk.index),
                )
            yield _sse_message("end", {"cursor": start_at + sent, "replay": replay})
        except FactPipelineError as exc:
            yield _sse_message("error", {"message": str(exc), "replay": replay})
        except asyncio.CancelledError:
            logger.info(
                "SSE stream cancelled after %d chunks", sent, extra={"request_id": request_id}
            )
            raise
        finally:
            SSE_TOKENS.inc(sent)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@api.post("/sse/stream")
async def sse_stream(
    req: ScoreReq,
    request: Request,
    token_delay: float | None = None,
    chunk_size: int | None = None,
    cursor: int | None = None,
    pipeline: FactPipeline = Depends(get_fact_pipeline),
) -> StreamingResponse:
    """Stream fact synthesis results over Server-Sent Events."""

    return await _sse_stream(
        req,
        request,
        pipeline,
        token_delay=token_delay,
        chunk_size=chunk_size,
        cursor=cursor,
    )


@api.post("/v1/stream")
async def stream(
    req: ScoreReq,
    request: Request,
    token_delay: float | None = None,
    chunk_size: int | None = None,
    cursor: int | None = None,
    pipeline: FactPipeline = Depends(get_fact_pipeline),
) -> StreamingResponse:
    """Backward compatible SSE endpoint for streaming fact synthesis."""

    return await _sse_stream(
        req,
        request,
        pipeline,
        token_delay=token_delay,
        chunk_size=chunk_size,
        cursor=cursor,
    )


def is_client_connected(ws: WebSocket) -> bool:
    """Return ``True`` if the WebSocket connection is still active."""

    return (
        ws.client_state == WebSocketState.CONNECTED
        and ws.application_state == WebSocketState.CONNECTED
    )


@api.websocket("/ws/stream")
async def ws_stream(
    ws: WebSocket, pipeline: FactPipeline = Depends(get_fact_pipeline)
) -> None:  # noqa: C901, PLR0912
    """Stream fact synthesis results over WebSocket with API-key auth."""

    cfg = load_settings()
    key = ws.headers.get(cfg.auth_header_name)
    client_id = _client_identifier(ws)
    try:
        user = authenticate_ws(key)
    except WebSocketAuthError as exc:
        audit_event("ws_denied", f"{client_id} reason={exc.reason}")
        await ws.close(code=exc.code, reason=exc.reason)
        return

    ws.scope["user"] = user
    limiter = _session_limiter(ws)

    await ws.accept()
    audit_event("ws_connect", f"{client_id} org={user.organization}")
    default_delay = cfg.token_delay
    rate_limited = False
    try:
        while True:
            message = await ws.receive_text()
            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                payload = {"text": message}

            if not isinstance(payload, dict):
                payload = {"text": str(payload)}

            query = str(payload.get("text", "") or "")
            if not query.strip():
                await ws.send_json({"event": "error", "message": "Query must not be empty"})
                continue

            start_at = payload.get("cursor")
            chunk_size = payload.get("chunk_size")
            delay_override = payload.get("delay")

            allowed, _remaining = limiter.allow(client_id)
            if not allowed:
                retry_after = limiter.retry_after(client_id)
                audit_event(
                    "ws_rate_limit",
                    f"{client_id} org={user.organization} retry={retry_after}",
                )
                error_payload: dict[str, Any] = {
                    "event": "error",
                    "message": "Rate limit exceeded",
                    "replay": False,
                }
                if retry_after:
                    error_payload["retry_after"] = retry_after
                await ws.send_json(error_payload)
                await ws.close(code=4429, reason="Rate limit exceeded")
                rate_limited = True
                break

            try:
                start_index = max(0, int(start_at)) if start_at is not None else 0
            except (TypeError, ValueError):
                start_index = 0
            try:
                size = int(chunk_size) if chunk_size is not None else DEFAULT_CHUNK_SIZE
            except (TypeError, ValueError):
                size = DEFAULT_CHUNK_SIZE
            size = max(1, size)
            try:
                delay = float(delay_override) if delay_override is not None else default_delay
            except (TypeError, ValueError):
                delay = default_delay
            delay = max(0.0, delay)

            replay = start_index > 0

            async def is_disconnected() -> bool:
                return not is_client_connected(ws)

            sent = 0
            await ws.send_json({"event": "start", "cursor": start_index, "replay": replay})
            try:
                async for chunk in stream_facts(
                    pipeline,
                    query,
                    chunk_size=size,
                    start_at=start_index,
                    delay=delay,
                    is_disconnected=is_disconnected,
                ):
                    await ws.send_json(
                        {
                            "event": "chunk",
                            "id": chunk.index,
                            "text": chunk.text,
                            "replay": replay,
                        }
                    )
                    sent += 1
                await ws.send_json(
                    {"event": "end", "cursor": start_index + sent, "replay": replay}
                )
            except FactPipelineError as exc:
                await ws.send_json({"event": "error", "message": str(exc), "replay": replay})
            finally:
                SSE_TOKENS.inc(sent)
    except WebSocketDisconnect:
        pass
    finally:
        limiter.reset(client_id)
        event = "ws_disconnect_rate_limited" if rate_limited else "ws_disconnect"
        audit_event(event, f"{client_id} org={user.organization}")
        # Restore a default loop so tests using get_event_loop() do not fail
        asyncio.set_event_loop(asyncio.new_event_loop())


async def _post_callback(  # noqa: PLR0913
    url: str,
    data: Mapping[str, Any],
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
