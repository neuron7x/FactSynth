
import pytest

pytest.importorskip("numpy")

from factsynth_ultimate.ndmaco.kuramoto import NDMACO

MIN_TIME_POINTS = 10
EXPECTED_CHANNELS = 5


def test_ndmaco_sim():
    t, theta = NDMACO().simulate(1.0, 0.01)
    assert len(t) > MIN_TIME_POINTS and theta.shape[1] == EXPECTED_CHANNELS
