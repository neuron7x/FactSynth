from dataclasses import dataclass
from typing import List


@dataclass
class RoleConfig:
    name: str
    goal: str
    style: str
    heuristics: List[str]


DEFAULT_CANON = "ТЕЗА:\n{thesis}\n\nОБҐРУНТУВАННЯ:\n{support}\n\nКОНТРТЕЗА:\n{counter}\n\nРЕЗЮМЕ:\n{summary}"


@dataclass
class Role:
    cfg: RoleConfig

    def format(self, thesis: str, support: str, counter: str, summary: str) -> str:
        return DEFAULT_CANON.format(
            thesis=thesis, support=support, counter=counter, summary=summary
        )

    def instruct(self) -> str:
        h = ", ".join(self.cfg.heuristics) if self.cfg.heuristics else "—"
        return f"[{self.cfg.name}] Мета: {self.cfg.goal}. Стиль: {self.cfg.style}. Евристики: {h}."
