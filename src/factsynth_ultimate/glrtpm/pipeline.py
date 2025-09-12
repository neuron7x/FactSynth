import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .metrics import cluster_density, compute_coherence, role_contribution
from .roles import Aesthete, Critic, Integrator, Observer, Rationalist


@dataclass
class GLRTPMConfig:
    steps: list[str] = field(default_factory=lambda: ["R", "I", "P", "Omega"])


@dataclass
class GLRTPMPipeline:
    config: GLRTPMConfig = field(default_factory=GLRTPMConfig)

    def run(self, thesis: str) -> dict[str, Any]:
        """Execute the configured GLRTPM steps for the given thesis."""
        handlers: dict[str, Callable[[str, dict[str, str]], str]] = {
            "R": lambda t, _: Critic().respond(t),
            "I": lambda t, _: " | ".join([Rationalist().respond(t), Aesthete().respond(t)]),
            "P": lambda t, res: (
                "[Meta-Projection] Nodes: "
                + json.dumps(
                    {
                        "thesis": f"{t[:64]}...",
                        "counter": f"{res.get('R', '')[:64]}...",
                    }
                )
            ),
            "Omega": lambda t, _: Integrator().respond(t) + " | " + Observer().respond(t),
        }

        results: dict[str, str] = {}
        for step in self.config.steps:
            handler = handlers.get(step)
            if handler:
                results[step] = handler(thesis, results)

        metrics = {
            "coherence": compute_coherence(thesis, *results.values()),
            "density": cluster_density([thesis, *results.values()]),
            "roles": role_contribution(results),
        }

        return {**results, "metrics": metrics}
