import json

import pytest

from factsynth_ultimate.glrtpm.pipeline import (
    GLRTPMConfig,
    GLRTPMPipeline,
    GLRTPMStep,
    UnknownGLRTPMStepError,
)
from factsynth_ultimate.glrtpm.roles import (
    Aesthete,
    Critic,
    Integrator,
    Observer,
    Rationalist,
)

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)

THESIS = "Test thesis"


def test_critic_step() -> None:
    pipeline = GLRTPMPipeline(GLRTPMConfig([GLRTPMStep.R]))
    result = pipeline.run(THESIS)
    assert result[GLRTPMStep.R.value] == Critic().respond(THESIS)


def test_rationalist_aesthete_step() -> None:
    pipeline = GLRTPMPipeline(GLRTPMConfig([GLRTPMStep.I]))
    result = pipeline.run(THESIS)
    expected = " | ".join([Rationalist().respond(THESIS), Aesthete().respond(THESIS)])
    assert result[GLRTPMStep.I.value] == expected


def test_projection_step() -> None:
    pipeline = GLRTPMPipeline(GLRTPMConfig([GLRTPMStep.R, GLRTPMStep.P]))
    result = pipeline.run(THESIS)
    projection = result[GLRTPMStep.P.value]
    assert projection.startswith("[Meta-Projection] Nodes:")
    data = json.loads(projection.split("Nodes: ")[1])
    assert data["thesis"].startswith(THESIS)
    assert data["counter"].startswith("[Critic]")


def test_integrator_observer_step() -> None:
    pipeline = GLRTPMPipeline(GLRTPMConfig([GLRTPMStep.Omega]))
    result = pipeline.run(THESIS)
    expected = Integrator().respond(THESIS) + " | " + Observer().respond(THESIS)
    assert result[GLRTPMStep.Omega.value] == expected


def test_unknown_step() -> None:
    with pytest.raises(UnknownGLRTPMStepError):
        GLRTPMPipeline(GLRTPMConfig(["X"]))
