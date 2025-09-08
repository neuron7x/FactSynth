
from dataclasses import dataclass, field
from typing import List, Dict, Any
from .roles import Rationalist, Critic, Aesthete, Integrator, Observer
from .metrics import compute_coherence, cluster_density, role_contribution

@dataclass
class GLRTPMConfig:
    steps: List[str] = field(default_factory=lambda: ["R","I","P","Omega"])

@dataclass
class GLRTPMPipeline:
    config: GLRTPMConfig = field(default_factory=GLRTPMConfig)
    def run(self, thesis: str) -> Dict[str, Any]:
        r = Critic().respond(thesis)
        i = " | ".join([Rationalist().respond(thesis), Aesthete().respond(thesis)])
        p = f"[Meta-Projection] Nodes: {{'thesis': '{thesis[:64]}...', 'counter': '{r[:64]}...'}}"
        omega = Integrator().respond(thesis) + " | " + Observer().respond(thesis)
        metrics = {
            "coherence": compute_coherence(thesis, r, i, p, omega),
            "density": cluster_density([thesis, r, i, p, omega]),
            "roles": role_contribution({"R": r, "I": i, "P": p, "Omega": omega})
        }
        return {"R": r, "I": i, "P": p, "Omega": omega, "metrics": metrics}
