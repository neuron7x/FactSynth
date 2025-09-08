
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import jax.numpy as jnp
from .isr.sim import simulate_isr, ISRParams, gamma_spectrum, dominant_freq, estimate_fs

router = APIRouter(prefix="/v1/isr", tags=["isr"])

class SimRequest(BaseModel):
    S0: List[float] = Field(default=[1.0, 0.8, 0.5, 0.3, 0.2, 0.1, 0.05], min_items=3)
    alpha: float = 1.0
    beta: float = 0.4
    gamma_param: float = 1.2
    delta: float = 0.05
    steps: int = 1000
    t1: float = 10.0

@router.post("/simulate")
def simulate(req: SimRequest) -> Dict[str, Any]:
    params = ISRParams(alpha=req.alpha, beta=req.beta, gamma_param=req.gamma_param, delta=req.delta, steps=req.steps, t1=req.t1)
    out = simulate_isr(jnp.array(req.S0), params=params)
    return {"t": [float(x) for x in out["t"]], "y": [[float(v) for v in row] for row in out["y"]]}

class SpectrumRequest(BaseModel):
    series: List[List[float]]
    channel_idx: int = 5
    fs: Optional[float] = None
    ts: Optional[List[float]] = None

@router.post("/spectrum")
def spectrum(req: SpectrumRequest) -> Dict[str, Any]:
    y = jnp.array(req.series)
    ts = jnp.array(req.ts) if req.ts is not None else None
    if req.fs is None and ts is None:
        raise ValueError("Provide fs or ts")
    fs = float(req.fs) if req.fs is not None else estimate_fs(ts)
    spec = gamma_spectrum(y, idx=req.channel_idx, fs=fs, ts=ts)
    dom = dominant_freq(spec, fs=fs)
    return {"dominant_freq": dom, "spec_len": int(spec.shape[0])}
