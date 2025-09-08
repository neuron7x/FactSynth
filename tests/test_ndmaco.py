
from factsynth_ultimate.ndmaco.kuramoto import NDMACO
def test_ndmaco_sim():
    t, theta = NDMACO().simulate(1.0, 0.01)
    assert len(t)>10 and theta.shape[1]==5
