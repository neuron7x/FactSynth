from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field, constr

from factsynth.models import feedback as fb

router = APIRouter(prefix="/v1/feedback", tags=["feedback"])


class FeedbackIn(BaseModel):
    session_id: constr(min_length=1)  # type: ignore[call-arg]
    request_id: constr(min_length=1)  # type: ignore[call-arg]
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    tags: str = ""


@router.post("", status_code=201)
def submit(payload: FeedbackIn) -> dict[str, int | bool]:
    rid = fb.insert(
        payload.session_id, payload.request_id, payload.rating, payload.comment, payload.tags
    )
    return {"id": rid, "ok": True}


@router.get("", summary="Latest feedback")
def list_feedback(limit: int = 50) -> dict:
    rows = fb.latest(limit)
    return {
        "items": [
            {
                "id": r[0],
                "ts": r[1],
                "session_id": r[2],
                "request_id": r[3],
                "rating": r[4],
                "comment": r[5],
                "tags": r[6],
            }
            for r in rows
        ]
    }
