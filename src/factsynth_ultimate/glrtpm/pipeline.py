
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


def handle_r(thesis: str, _: dict[str, str]) -> str:
    """Return critic response for thesis."""

    return Critic().respond(thesis)


def handle_i(thesis: str, _: dict[str, str]) -> str:
    """Return combined rationalist and aesthete perspectives."""

    return " | ".join([Rationalist().respond(thesis), Aesthete().respond(thesis)])


def handle_p(thesis: str, results: dict[str, str]) -> str:
    """Project thesis and counter arguments into a meta representation."""

    return "[Meta-Projection] Nodes: " + json.dumps(
        {
            "thesis": f"{thesis[:64]}...",
            "counter": f"{results.get('R', '')[:64]}...",
        }
    )


def handle_omega(thesis: str, _: dict[str, str]) -> str:
    """Return integrator synthesis and observer audit."""

    return Integrator().respond(thesis) + " | " + Observer().respond(thesis)


STEP_HANDLERS: dict[GLRTPMStep, Callable[[str, dict[str, str]], str]] = {
    GLRTPMStep.R: handle_r,
    GLRTPMStep.I: handle_i,
    GLRTPMStep.P: handle_p,
    GLRTPMStep.Omega: handle_omega,
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
            if handler:
                results[step.value] = handler(thesis, results)

        metrics = {
            "coherence": compute_coherence(thesis, *results.values()),
            "density": cluster_density([thesis, *results.values()]),
            "roles": role_contribution(results),
        }

        return {**results, "metrics": metrics}
