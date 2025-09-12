
"""API surface for interactive stochastic resonance utilities."""

from __future__ import annotations

from typing import Any, Optional

import jax.numpy as jnp
from fastapi import APIRouter
from pydantic import BaseModel, Field

from .isr.sim import ISRParams, dominant_freq, estimate_fs, gamma_spectrum, simulate_isr

router = APIRouter(prefix="/v1/isr", tags=["isr"])


class SimRequest(BaseModel):
    """Parameters governing the ISR simulation."""

    S0: list[float] = Field(
        default=[1.0, 0.8, 0.5, 0.3, 0.2, 0.1, 0.05], min_length=3
    )
    alpha: float = 1.0
    beta: float = 0.4
    gamma_param: float = 1.2
    delta: float = 0.05
    steps: int = 1000
    t1: float = 10.0


@router.post("/simulate")
def simulate(req: SimRequest) -> dict[str, Any]:
    """Run the stochastic resonance simulation and return the time series."""

    params = ISRParams(
        alpha=req.alpha,
        beta=req.beta,
        gamma_param=req.gamma_param,
        delta=req.delta,
        steps=req.steps,
        t1=req.t1,
    )
    out = simulate_isr(jnp.array(req.S0), params=params)
    return {
        "t": [float(x) for x in out["t"]],
        "y": [[float(v) for v in row] for row in out["y"]],
    }


class SpectrumRequest(BaseModel):
    """Request body for computing a gamma spectrum."""

    series: list[list[float]]
    channel_idx: int = 5
    fs: Optional[float] = None
    ts: Optional[list[float]] = None


@router.post("/spectrum")
def spectrum(req: SpectrumRequest) -> dict[str, Any]:
    """Compute spectrum and dominant frequency from series data."""

    y = jnp.array(req.series)
    ts = jnp.array(req.ts) if req.ts is not None else None
    if req.fs is None and ts is None:
        raise ValueError("Provide fs or ts")
    fs = float(req.fs) if req.fs is not None else estimate_fs(ts)
    spec = gamma_spectrum(y, idx=req.channel_idx, fs=fs, ts=ts)
    dom = dominant_freq(spec, fs=fs)
    return {"dominant_freq": dom, "spec_len": int(spec.shape[0])}
