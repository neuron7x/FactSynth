import pytest

from factsynth_ultimate.glrtpm.pipeline import GLRTPMConfig, GLRTPMPipeline

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_glrtpm_roundtrip():
    out = GLRTPMPipeline().run("Test thesis about identity reconstruction.")
    assert {"R", "I", "P", "Omega", "metrics"}.issubset(out.keys())
    m = out["metrics"]
    assert {"coherence", "density", "roles"}.issubset(m)


def test_unknown_step_raises_error():
    with pytest.raises(ValueError, match="Unknown GLRTPM step: X"):
        GLRTPMPipeline(GLRTPMConfig(steps=["X"]))
