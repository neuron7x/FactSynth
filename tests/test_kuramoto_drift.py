import numpy as np

from factsynth_ultimate.ndmaco.kuramoto import NDMACO


def test_drift_matches_omega() -> None:
    omega = np.array([1.0, 2.0, 3.0])
    model = NDMACO(N=3, M=1, K=1.0, omega=omega, alpha=np.array([0.0]), adjacency=[np.eye(3)], theta0=np.zeros(3))
    drift = model._drift(np.zeros(3))
    assert np.allclose(drift, omega)
