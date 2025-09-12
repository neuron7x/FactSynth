"""Endpoints exposing the :class:`GLRTPMPipeline` via FastAPI."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from .glrtpm.pipeline import GLRTPMPipeline

router = APIRouter(prefix="/v1/glrtpm", tags=["glrtpm"])


class RunReq(BaseModel):
    """Request body containing the thesis to evaluate."""

    thesis: str


@router.post("/run")
def run(req: RunReq) -> dict[str, Any]:
    """Execute the pipeline on the provided thesis."""

    return GLRTPMPipeline().run(req.thesis)
