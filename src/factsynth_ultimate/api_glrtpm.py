from fastapi import APIRouter
from pydantic import BaseModel

from .glrtpm.pipeline import GLRTPMPipeline

router = APIRouter(prefix="/v1/glrtpm", tags=["glrtpm"])


class RunReq(BaseModel):
    thesis: str


@router.post("/run")
def run(req: RunReq):
    return GLRTPMPipeline().run(req.thesis)
