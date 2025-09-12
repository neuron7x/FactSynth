
import pytest

try:
    import numpy as np
except ModuleNotFoundError:
    pytest.skip("numpy not installed", allow_module_level=True)

from factsynth_ultimate.ndmaco.kuramoto import NDMACO

MIN_TIME_POINTS = 10
EXPECTED_CHANNELS = 5


def test_ndmaco_sim():
    t, theta = NDMACO().simulate(1.0, 0.01)
    assert len(t) > MIN_TIME_POINTS and theta.shape[1] == EXPECTED_CHANNELS


def test_ndmaco_drift_no_coupling():
    model = NDMACO(K=0)
    theta = np.zeros(model.N)
    drift = model._drift(theta)
    assert np.allclose(drift, model.omega)
