from factsynth_ultimate.glrtpm.pipeline import GLRTPMPipeline
from factsynth_ultimate.core.cache import get_cache


def test_glrtpm_roundtrip():
    out = GLRTPMPipeline().run("Test thesis about identity reconstruction.")
    assert set(["R","I","P","Omega","metrics"]).issubset(out.keys())
    m = out["metrics"]
    assert "coherence" in m and "density" in m and "roles" in m


def test_glrtpm_cache():
    thesis = "Caching thesis"
    cache = get_cache()
    cache.clear()
    pipeline = GLRTPMPipeline()
    first = pipeline.run(thesis)
    assert cache.get(f"glrtpm:{thesis}") == first
    second = pipeline.run(thesis)
    assert second == first
