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

MIN_DOM_FREQ = 25.0
MAX_DOM_FREQ = 55.0


def test_dominant_frequency_within_bounds_regression():
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert MIN_DOM_FREQ <= f0 <= MAX_DOM_FREQ
    # Ensure the zero-frequency component is effectively removed
    assert spec[0] == pytest.approx(0.0, abs=1e-6)
