from dataclasses import dataclass
from typing import List, Dict, Any
import logging

from .roles import Role, RoleConfig
from .llm_offline import OfflineLLM
from .memory import VectorMemory
from .metrics_glrtpm import coherence, diversity, contradiction_rate, acceptance
from .exporter import to_markdown, to_html

logger = logging.getLogger(__name__)

@dataclass
class ProjectSpec:
    """Specification for a factsynthesis project.

    Attributes:
        title: Title of the generated manifesto.
        thesis: Core thesis that roles will explore.
        roles: Configuration for each participating role.
        rounds: Number of generation rounds for each role.
    """

    title: str
    thesis: str
    roles: List[RoleConfig]
    rounds: int = 2

class Orchestrator:
    def __init__(self, spec: ProjectSpec):
        """Initialize the orchestrator with a project specification.

        Args:
            spec: Project configuration defining thesis and roles.
        """

        self.spec = spec
        self.roles = [Role(r) for r in spec.roles]
        self.vm = VectorMemory()
        self.llm = OfflineLLM()

    def _gen(self, system: str, prompt: str, temp: float = 0.2) -> str:
        """Generate text using the offline LLM.

        Args:
            system: System prompt defining role behaviour.
            prompt: User prompt to append to the system prompt.
            temp: Sampling temperature for generation.

        Returns:
            The generated text.
        """

        return self.llm.generate(prompt=system + "\n\n" + prompt, system=system, temperature=temp)

    def run(self) -> Dict[str, Any]:
        """Execute the orchestration pipeline.

        Returns:
            Dictionary containing markdown, html, metrics and sections.

        Raises:
            RuntimeError: If generation fails at any stage.
        """

        thesis_blocks, counter_blocks, role_outputs = [], [], []
        for r in self.roles:
            sys = r.instruct()
            try:
                t = self._gen(sys, f"Сформуй тезу за темою: {self.spec.thesis}")
            except Exception as e:
                logger.error("Thesis generation failed for %s: %s", r.cfg.name, e)
                raise RuntimeError(
                    f"Thesis generation failed for role {r.cfg.name}"
                ) from e
            try:
                c = self._gen(sys, f"Сформуй контртезу до: {self.spec.thesis}")
            except Exception as e:
                logger.error(
                    "Counter-thesis generation failed for %s: %s", r.cfg.name, e
                )
                raise RuntimeError(
                    f"Counter-thesis generation failed for role {r.cfg.name}"
                ) from e
            try:
                s = self._gen(
                    sys,
                    "Стислий висновок з критеріями валідації для читача.",
                )
            except Exception as e:
                logger.error("Summary generation failed for %s: %s", r.cfg.name, e)
                raise RuntimeError(
                    f"Summary generation failed for role {r.cfg.name}"
                ) from e
            block = r.format(
                thesis=t,
                support="Аргументи й приклади (синтез).",
                counter=c,
                summary=s,
            )
            self.vm.add(block)
            thesis_blocks.append(t)
            counter_blocks.append(c)
            role_outputs.append((r.cfg.name, block))

        coh = coherence([b for _, b in role_outputs])
        div = diversity([b for _, b in role_outputs])
        contra = contradiction_rate(thesis_blocks, counter_blocks)
        acc = acceptance(coh, div, contra)

        try:
            integr = self._gen(
                "Інтегратор", "Синтезуй єдину позицію з урахуванням тез і контртез."
            )
        except Exception as e:
            logger.error("Integrator generation failed: %s", e)
            raise RuntimeError("Integrator generation failed") from e
        sections = [("Маніфест", integr)]
        for name, block in role_outputs:
            sections.append((f"Роль: {name}", block))
        sections.append(
            (
                "Метрики",
                f"- Coherence: {coh:.3f}\n- Diversity: {div:.3f}\n- Contradiction: {contra:.3f}",
            )
        )

        md = to_markdown(self.spec.title, sections)
        html = to_html(md)
        return {"markdown": md, "html": html, "metrics": acc, "sections": sections}
