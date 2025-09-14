import importlib
import sys

import pytest

try:  # optional runtime deps
    import jax  # noqa: F401
    import diffrax  # noqa: F401
except ImportError:  # pragma: no cover - handled in tests
    jax = diffrax = None

MIN_DOM_FREQ = 0.0
MAX_DOM_FREQ = 55.0


@pytest.fixture(autouse=True)
def _stub_external_api():
    """Override global HTTP stubs; no network calls here."""
    pass


@pytest.mark.skipif(jax is None or diffrax is None, reason="requires jax and diffrax")
def test_isr_shapes_and_peak():
    from factsynth_ultimate.isr import (
        ISRParams,
        dominant_freq,
        estimate_fs,
        gamma_spectrum,
        simulate_isr,
    )

    jnp = jax.numpy
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert MIN_DOM_FREQ <= f0 <= MAX_DOM_FREQ


@pytest.mark.parametrize("missing_module, err_msg", [("jax", "JAX"), ("diffrax", "Diffrax")])
def test_simulate_isr_missing_dependencies(monkeypatch, missing_module, err_msg):
    if missing_module == "diffrax" and jax is None:
        pytest.skip("requires jax to test diffrax absence")
    monkeypatch.setitem(sys.modules, missing_module, None)
    if missing_module == "jax":
        monkeypatch.setitem(sys.modules, "jax.numpy", None)
    monkeypatch.delitem(sys.modules, "factsynth_ultimate.isr", raising=False)
    monkeypatch.delitem(sys.modules, "factsynth_ultimate.isr.sim", raising=False)
    with pytest.raises(RuntimeError, match=err_msg):
        importlib.import_module("factsynth_ultimate.isr.sim")
