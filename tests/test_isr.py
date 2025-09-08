
import pytest

jax = pytest.importorskip("jax")
pytest.importorskip("diffrax")
import jax.numpy as jnp

from factsynth_ultimate.isr import (
    simulate_isr,
    ISRParams,
    gamma_spectrum,
    dominant_freq,
    estimate_fs,
)

def test_isr_shapes_and_peak():
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert 25.0 <= f0 <= 55.0
