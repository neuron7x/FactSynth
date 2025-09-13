import pytest

from factsynth_ultimate.glrtpm.pipeline import (
    GLRTPMConfig,
    GLRTPMPipeline,
    GLRTPMStep,
    STEP_HANDLERS,
    CriticHandler,
    IntegratorObserverHandler,
    ProjectionHandler,
    RationalistAestheteHandler,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


def test_step_handlers_mapping_matches_enum():
    """Each enum member should map to its dedicated handler class."""

    expected = {
        GLRTPMStep.R: CriticHandler,
        GLRTPMStep.I: RationalistAestheteHandler,
        GLRTPMStep.P: ProjectionHandler,
        GLRTPMStep.Omega: IntegratorObserverHandler,
    }

    assert set(STEP_HANDLERS) == set(expected)
    for step, cls in expected.items():
        assert isinstance(STEP_HANDLERS[step], cls)


def test_run_raises_for_unsupported_step(monkeypatch):
    """Pipeline should raise a clear error when handler is missing."""

    pipeline = GLRTPMPipeline(GLRTPMConfig(steps=[GLRTPMStep.R]))
    monkeypatch.delitem(STEP_HANDLERS, GLRTPMStep.R, raising=False)

    with pytest.raises(ValueError, match="Unsupported GLRTPM step: R"):
        pipeline.run("thesis")
