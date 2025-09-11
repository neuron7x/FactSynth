import pytest

from factsynth_ultimate.isr import (
    ISRParams,
    dominant_freq,
    estimate_fs,
    gamma_spectrum,
    simulate_isr,
)

jax = pytest.importorskip("jax")
pytest.importorskip("diffrax")

jnp = jax.numpy

MIN_DOM_FREQ = 0.0
MAX_DOM_FREQ = 55.0

def test_isr_shapes_and_peak():
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert MIN_DOM_FREQ <= f0 <= MAX_DOM_FREQ
