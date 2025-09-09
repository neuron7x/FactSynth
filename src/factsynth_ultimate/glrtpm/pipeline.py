
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

from ..core.cache import get_cache
from .metrics import cluster_density, compute_coherence, role_contribution
from .roles import Aesthete, Critic, Integrator, Observer, Rationalist


@dataclass
class GLRTPMConfig:
    steps: List[str] = field(default_factory=lambda: ["R","I","P","Omega"])

@dataclass
class GLRTPMPipeline:
    config: GLRTPMConfig = field(default_factory=GLRTPMConfig)
    def run(self, thesis: str) -> Dict[str, Any]:
        """Execute the configured GLRTPM steps for the given thesis."""
        cache = get_cache()
        key = f"glrtpm:{thesis}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        handlers: Dict[str, Callable[[str, Dict[str, str]], str]] = {
            "R": lambda t, _: Critic().respond(t),
            "I": lambda t, _: " | ".join(
                [Rationalist().respond(t), Aesthete().respond(t)]
            ),
            "P": lambda t, res: (
                "[Meta-Projection] Nodes: "
                + json.dumps(
                    {
                        "thesis": f"{t[:64]}...",
                        "counter": f"{res.get('R', '')[:64]}...",
                    }
                )
            ),
            "Omega": lambda t, _: Integrator().respond(t)
            + " | "
            + Observer().respond(t),
        }

        results: Dict[str, str] = {}
        for step in self.config.steps:
            handler = handlers.get(step)
            if handler:
                results[step] = handler(thesis, results)

        metrics = {
            "coherence": compute_coherence(thesis, *results.values()),
            "density": cluster_density([thesis, *results.values()]),
            "roles": role_contribution(results),
        }

        output = {**results, "metrics": metrics}
        cache.set(key, output)
        return output
