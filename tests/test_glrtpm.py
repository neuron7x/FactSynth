import pytest

from factsynth_ultimate.glrtpm.pipeline import GLRTPMConfig, GLRTPMPipeline, GLRTPMStep

def test_glrtpm_roundtrip():
    out = GLRTPMPipeline().run("Test thesis about identity reconstruction.")
    assert {"R", "I", "P", "Omega", "metrics"}.issubset(out.keys())
    m = out["metrics"]
    assert {"coherence", "density", "roles"}.issubset(m)

def test_unknown_step_raises_error():
    with pytest.raises(ValueError, match="Unknown GLRTPM step: X"):
        GLRTPMPipeline(GLRTPMConfig(steps=["X"]))

def test_unknown_step_in_mixed_sequence_raises_error():
    """Ensure error is raised when sequence contains an unknown step."""

    with pytest.raises(ValueError, match="Unknown GLRTPM step: Z"):
        GLRTPMPipeline(GLRTPMConfig(steps=[GLRTPMStep.R, "Z"]))
