
"""API wrapper for the GLRTPM pipeline."""

from fastapi import APIRouter
from pydantic import BaseModel

from .glrtpm.pipeline import GLRTPMPipeline

router = APIRouter(prefix="/v1/glrtpm", tags=["glrtpm"])

class RunReq(BaseModel):
    """Request body for :func:`run`."""

    thesis: str


@router.post("/run")
def run(req: RunReq) -> dict[str, object]:
    """Execute the GLRTPM pipeline for a thesis."""

    return GLRTPMPipeline().run(req.thesis)
