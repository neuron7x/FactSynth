from factsynth_ultimate.glrtpm.pipeline import GLRTPMPipeline


def test_glrtpm_roundtrip():
    out = GLRTPMPipeline().run("Test thesis about identity reconstruction.")
    assert {"R", "I", "P", "Omega", "metrics"}.issubset(out.keys())
    m = out["metrics"]
    assert "coherence" in m and "density" in m and "roles" in m
