
from factsynth_ultimate.akpshi.metrics import rmse, fcr, pfi
def test_metrics():
    assert round(rmse([0,1],[0,1]),6)==0.0
    assert fcr(9,10)==0.9
    assert 0<=pfi([0.4,0.6,0.5])<=1
