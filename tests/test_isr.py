import importlib
import sys

import pytest

diffrax = pytest.importorskip("diffrax")
jax = pytest.importorskip("jax")

from factsynth_ultimate.isr import (  # noqa: E402
    ISRParams,
    dominant_freq,
    estimate_fs,
    gamma_spectrum,
    simulate_isr,
)

jnp = jax.numpy
_ = diffrax

MIN_DOM_FREQ = 0.0
MAX_DOM_FREQ = 55.0


@pytest.fixture(autouse=True)
def _stub_external_api():
    """Override global HTTP stubs; no network calls here."""
    pass


def test_isr_shapes_and_peak():
    out = simulate_isr(params=ISRParams(steps=512, t1=5.12))
    fs = estimate_fs(out["t"])
    spec = gamma_spectrum(out["y"], idx=5, fs=fs, ts=out["t"])
    f0 = dominant_freq(spec, fs=fs)
    assert MIN_DOM_FREQ <= f0 <= MAX_DOM_FREQ


@pytest.mark.parametrize("missing_module, err_msg", [("jax", "JAX"), ("diffrax", "Diffrax")])
def test_simulate_isr_missing_dependencies(monkeypatch, missing_module, err_msg):
    monkeypatch.setitem(sys.modules, missing_module, None)
    if missing_module == "jax":
        monkeypatch.setitem(sys.modules, "jax.numpy", None)
    monkeypatch.delitem(sys.modules, "factsynth_ultimate.isr", raising=False)
    monkeypatch.delitem(sys.modules, "factsynth_ultimate.isr.sim", raising=False)
    with pytest.raises(RuntimeError, match=err_msg):
        importlib.import_module("factsynth_ultimate.isr.sim")
