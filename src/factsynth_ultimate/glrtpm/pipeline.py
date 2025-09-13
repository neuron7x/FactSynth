
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


class CriticHandler:
    """Callable returning the critic response."""

    def __call__(self, thesis: str, _: dict[str, str]) -> str:
        return Critic().respond(thesis)


class RationalistAestheteHandler:
    """Callable combining rationalist and aesthete perspectives."""

    def __call__(self, thesis: str, _: dict[str, str]) -> str:
        return " | ".join(
            [Rationalist().respond(thesis), Aesthete().respond(thesis)]
        )


class ProjectionHandler:
    """Callable projecting thesis and counter arguments into meta representation."""

    def __call__(self, thesis: str, results: dict[str, str]) -> str:
        return "[Meta-Projection] Nodes: " + json.dumps(
            {
                "thesis": f"{thesis[:64]}...",
                "counter": f"{results.get('R', '')[:64]}...",
            }
        )


class IntegratorObserverHandler:
    """Callable returning integrator synthesis and observer audit."""

    def __call__(self, thesis: str, _: dict[str, str]) -> str:
        return Integrator().respond(thesis) + " | " + Observer().respond(thesis)


STEP_HANDLERS: dict[GLRTPMStep, Callable[[str, dict[str, str]], str]] = {
    GLRTPMStep.R: CriticHandler(),
    GLRTPMStep.I: RationalistAestheteHandler(),
    GLRTPMStep.P: ProjectionHandler(),
    GLRTPMStep.Omega: IntegratorObserverHandler(),
}


@dataclass
class GLRTPMConfig:
    """Configuration specifying which GLRTPM steps to execute."""

    steps: list[GLRTPMStep | str] = field(
        default_factory=lambda: [
            GLRTPMStep.R,
            GLRTPMStep.I,
            GLRTPMStep.P,
            GLRTPMStep.Omega,
        ]
    )

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
                    raise ValueError(f"Unknown GLRTPM step: {step}") from exc
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
                raise ValueError(f"Unsupported GLRTPM step: {step.value}")
            results[step.value] = handler(thesis, results)

        metrics = {
            "coherence": compute_coherence(thesis, *results.values()),
            "density": cluster_density([thesis, *results.values()]),
            "roles": role_contribution(results),
        }

        return {**results, "metrics": metrics}
