from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import jax.numpy as jnp
from diffrax import ODETerm, SaveAt, Tsit5, diffeqsolve

GAMMA_FREQ = 40.0
MIN_DOM_FREQ = 25.0
MAX_DOM_FREQ = 55.0

@dataclass
class ISRParams:
    alpha: float = 1.0
    beta: float = 0.4
    gamma_param: float = 1.2
    delta: float = 0.05
    t0: float = 0.0
    t1: float = 10.0
    steps: int = 1000

def _compute_rs(S: jnp.ndarray) -> jnp.ndarray:
    return 0.12 * S

def _compute_irs(RS: jnp.ndarray) -> jnp.ndarray:
    return -RS

def _compute_es(S: jnp.ndarray) -> jnp.ndarray:
    grad_norm = jnp.linalg.norm(jnp.ones_like(S))
    return 0.5 * grad_norm ** 2

def _compute_as_star(IRS: jnp.ndarray, S: jnp.ndarray) -> jnp.ndarray:
    return jnp.exp(-jnp.sum((IRS - S) ** 2))

def _compute_gamma(t: float) -> float:
    return jnp.sin(2.0 * jnp.pi * GAMMA_FREQ * t)

def _ds_dt(t, S, args):
    alpha, beta, gamma_param, delta = args
    RS = _compute_rs(S)
    IRS = _compute_irs(RS)
    ES = _compute_es(S)
    AS_star = _compute_as_star(IRS, S)
    Gamma = _compute_gamma(t)
    return alpha * IRS - beta * ES + gamma_param * AS_star + delta * Gamma

def simulate_isr(S0: jnp.ndarray = jnp.array([1.0, 0.8, 0.5, 0.3, 0.2, 0.1, 0.05]),
                 params: ISRParams = ISRParams()) -> Dict[str, jnp.ndarray]:
    term = ODETerm(lambda t, y, _: _ds_dt(t, y, (params.alpha, params.beta, params.gamma_param, params.delta)))
    solver = Tsit5()
    ts = jnp.linspace(params.t0, params.t1, params.steps)
    sol = diffeqsolve(term, solver, t0=params.t0, t1=params.t1, dt0=0.01, y0=S0, saveat=SaveAt(ts=ts))
    return {'t': ts, 'y': sol.ys}

def estimate_fs(ts: jnp.ndarray) -> float:
    dt = float(ts[1] - ts[0])
    return 1.0 / dt

def gamma_spectrum(y: jnp.ndarray, idx: int = 5, fs: Optional[float]=None, ts: Optional[jnp.ndarray]=None) -> jnp.ndarray:
    sig = y[:, idx]
    if fs is None:
        if ts is None:
            raise ValueError("Provide fs or ts to infer sampling rate")
        fs = estimate_fs(ts)
    # Remove DC component and normalise the spectrum to avoid a
    # spurious peak at zero frequency which previously dominated the
    # spectrum and caused the detected dominant frequency to be 0 Hz.
    sig = sig - jnp.mean(sig)
    spec = jnp.abs(jnp.fft.fft(sig)) / sig.shape[0]
    return spec

def dominant_freq(spec: jnp.ndarray, fs: float) -> float:
    n = spec.shape[0]
    freqs = jnp.fft.fftfreq(n, d=1.0 / fs)
    # Restrict search to positive frequencies within the expected bounds.
    band = jnp.logical_and(freqs >= MIN_DOM_FREQ, freqs <= MAX_DOM_FREQ)
    # Zero-out values outside the band to avoid spurious low-frequency peaks.
    spec_band = jnp.where(band, spec, 0.0)
    idx = int(jnp.argmax(spec_band))
    return float(freqs[idx])
