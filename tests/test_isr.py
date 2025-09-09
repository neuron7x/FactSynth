import pytest

from factsynth_ultimate.isr import (
    ISRParams,
    dominant_freq,
    estimate_fs,
    gamma_spectrum,
    simulate_isr,
)
from factsynth_ultimate.isr.sim import GAMMA_FREQ, LOW_FREQ_CUTOFF

jax = pytest.importorskip("jax")
pytest.importorskip("diffrax")
jnp = jax.numpy

MIN_DOM_FREQ = 25.0
MAX_DOM_FREQ = 55.0
TOL = 0.5
LOW_FREQ = 10.0


def test_isr_shapes_and_peak():
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert MIN_DOM_FREQ <= f0 <= MAX_DOM_FREQ


def test_dominant_freq_prefers_gamma():
    fs = 256.0
    t = jnp.linspace(0.0, 1.0, int(fs), endpoint=False)
    sig = jnp.sin(2 * jnp.pi * LOW_FREQ * t) + jnp.sin(2 * jnp.pi * GAMMA_FREQ * t)
    y = sig[:, None]
    spec = gamma_spectrum(y, idx=0, fs=fs)
    f0 = dominant_freq(spec, fs=fs)
    assert abs(f0 - GAMMA_FREQ) <= TOL
    n = (spec.shape[0] - 1) * 2
    freqs = jnp.fft.rfftfreq(n, d=1.0 / fs)
    filtered = spec.at[freqs < LOW_FREQ_CUTOFF].set(0)
    amp_high = filtered[freqs == GAMMA_FREQ][0]
    amp_low = filtered[freqs == LOW_FREQ][0]
    assert amp_high > amp_low
