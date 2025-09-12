from factsynth_ultimate.llm_ifc.arbitrator import Candidate, choose


def test_arbitration():
    c = [Candidate("A", 0.6, 0.6, "a"), Candidate("B", 0.9, 0.4, "b")]
    out = choose(c, 0.5, 0.5)
    assert out["winner"] in ("A", "B")
    assert 0.0 <= out["score"] <= 1.0
