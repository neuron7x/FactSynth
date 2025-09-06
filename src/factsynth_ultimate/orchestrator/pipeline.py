from dataclasses import dataclass
from typing import List, Dict, Any
from .roles import Role, RoleConfig
from .llm_offline import OfflineLLM
from .memory import VectorMemory
from .metrics_glrtpm import coherence, diversity, contradiction_rate, acceptance
from .exporter import to_markdown, to_html

@dataclass
class ProjectSpec:
    title: str
    thesis: str
    roles: List[RoleConfig]
    rounds: int = 2

class Orchestrator:
    def __init__(self, spec: ProjectSpec):
        self.spec = spec
        self.roles = [Role(r) for r in spec.roles]
        self.vm = VectorMemory()
        self.llm = OfflineLLM()

    def _gen(self, system: str, prompt: str, temp: float = 0.2) -> str:
        return self.llm.generate(prompt=system + "\n\n" + prompt, system=system, temperature=temp)

    def run(self) -> Dict[str, Any]:
        thesis_blocks, counter_blocks, role_outputs = [], [], []
        for r in self.roles:
            sys = r.instruct()
            t = self._gen(sys, f"Сформуй тезу за темою: {self.spec.thesis}")
            c = self._gen(sys, f"Сформуй контртезу до: {self.spec.thesis}")
            s = self._gen(sys, f"Стислий висновок з критеріями валідації для читача.")
            block = r.format(thesis=t, support="Аргументи й приклади (синтез).", counter=c, summary=s)
            self.vm.add(block)
            thesis_blocks.append(t); counter_blocks.append(c); role_outputs.append((r.cfg.name, block))

        coh = coherence([b for _, b in role_outputs])
        div = diversity([b for _, b in role_outputs])
        contra = contradiction_rate(thesis_blocks, counter_blocks)
        acc = acceptance(coh, div, contra)

        integr = self._gen("Інтегратор", "Синтезуй єдину позицію з урахуванням тез і контртез.")
        sections = [("Маніфест", integr)]
        for name, block in role_outputs: sections.append((f"Роль: {name}", block))
        sections.append(("Метрики", f"- Coherence: {coh:.3f}\n- Diversity: {div:.3f}\n- Contradiction: {contra:.3f}"))

        md = to_markdown(self.spec.title, sections); html = to_html(md)
        return {"markdown": md, "html": html, "metrics": acc, "sections": sections}
