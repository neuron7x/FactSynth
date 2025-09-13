
"""Simple pipeline orchestrating GLRTPM role interactions."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .metrics import cluster_density, compute_coherence, role_contribution
from .roles import Aesthete, Critic, Integrator, Observer, Rationalist


class GLRTPMStep(str, Enum):
    """Enumeration of supported pipeline steps."""

    R = "R"
    I = "I"  # noqa: E741
    P = "P"
    Omega = "Omega"


class UnknownGLRTPMStepError(ValueError):
    """Raised when an unknown GLRTPM step is encountered."""


def handle_critic(thesis: str, _: dict[str, str]) -> str:
    """Return the critic response."""

    return Critic().respond(thesis)


def handle_rationalist_aesthete(thesis: str, _: dict[str, str]) -> str:
    """Combine rationalist and aesthete perspectives."""

    return " | ".join(
        [Rationalist().respond(thesis), Aesthete().respond(thesis)]
    )


def handle_projection(thesis: str, results: dict[str, str]) -> str:
    """Project thesis and counter arguments into meta representation."""

    return "[Meta-Projection] Nodes: " + json.dumps(
        {
            "thesis": f"{thesis[:64]}...",
            "counter": f"{results.get('R', '')[:64]}...",
        }
    )


def handle_integrator_observer(thesis: str, _: dict[str, str]) -> str:
    """Return integrator synthesis and observer audit."""

    return Integrator().respond(thesis) + " | " + Observer().respond(thesis)


STEP_HANDLERS: dict[GLRTPMStep, Callable[[str, dict[str, str]], str]] = {
    GLRTPMStep.R: handle_critic,
    GLRTPMStep.I: handle_rationalist_aesthete,
    GLRTPMStep.P: handle_projection,
    GLRTPMStep.Omega: handle_integrator_observer,
}


def default_steps() -> list[GLRTPMStep]:
    """Return default GLRTPM steps."""

    return [
        GLRTPMStep.R,
        GLRTPMStep.I,
        GLRTPMStep.P,
        GLRTPMStep.Omega,
    ]


@dataclass
class GLRTPMConfig:
    """Configuration specifying which GLRTPM steps to execute."""

    steps: list[GLRTPMStep | str] = field(default_factory=default_steps)

    def __post_init__(self) -> None:
        """Validate and normalize *steps* to ``GLRTPMStep`` members."""

        validated: list[GLRTPMStep] = []
        for step in self.steps:
            if isinstance(step, GLRTPMStep):
                validated.append(step)
            else:
                try:
                    validated.append(GLRTPMStep(step))
                except ValueError as exc:  # pragma: no cover - defensive
                    raise UnknownGLRTPMStepError(
                        f"Unknown GLRTPM step: {step}"
                    ) from exc
        self.steps = validated

@dataclass
class GLRTPMPipeline:
    """Pipeline executing configured GLRTPM roles in sequence."""

    config: GLRTPMConfig = field(default_factory=GLRTPMConfig)

    def run(self, thesis: str) -> dict[str, Any]:
        """Execute all configured steps for *thesis* and compute metrics."""

        results: dict[str, str] = {}
        for step in self.config.steps:
            handler = STEP_HANDLERS.get(step)
            if handler is None:
                raise UnknownGLRTPMStepError(
                    f"Unsupported GLRTPM step: {step.value}"
                )
            results[step.value] = handler(thesis, results)

        metrics = {
            "coherence": compute_coherence(thesis, *results.values()),
            "density": cluster_density([thesis, *results.values()]),
            "roles": role_contribution(results),
        }

        return {**results, "metrics": metrics}
