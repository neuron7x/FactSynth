from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from .formatting import sanitize, fit_length
from .tokenization import count_words
from .config import FSUConfig

VALENCE = {"досягнення","контроль","зв’язок","безпека","визнання","новизна"}

class FSUInput(BaseModel):
    intent: str = Field(..., description="Явний намір")
    length: int | None = None
    valence: str | None = None
    motive: str | None = None
    constraints: str | None = None
    blocker: str | None = None
    horizon: str | None = "ітеративний"
    metric: str | None = "релевантність/глибина/застосовність"
    default_action: str | None = "контекстна емпатія/аналіз"
    facts: list[str] | None = None
    knowledge: list[str] | None = None

    @field_validator("length")
    @classmethod
    def v_len(cls, v):
        if v is not None and v <= 0: raise ValueError("length must be > 0")
        return v
    @field_validator("valence")
    @classmethod
    def v_val(cls, v):
        if v is None: return v
        if v not in VALENCE: raise ValueError("invalid valence")
        return v

def _infer_valence(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["нове","інновац","експерим"]): return "новизна"
    if any(k in t for k in ["визнан","репутац","оцінк"]): return "визнання"
    if any(k in t for k in ["безпек","ризик"]): return "безпека"
    if any(k in t for k in ["контрол","керуван"]): return "контроль"
    if any(k in t for k in ["команд","спільнот","зв’яз","віднос"]): return "зв’язок"
    return "досягнення"

def _resolve_valence(inp: FSUInput) -> str:
    return inp.valence if inp.valence in VALENCE else _infer_valence(inp.intent)

def _process_seeds(inp: FSUInput) -> str | None:
    seeds: list[str] = []
    for pool in (inp.facts or []) + (inp.knowledge or []):
        for w in str(pool).split():
            if len(seeds) < 6 and w.isalpha():
                seeds.append(w.lower())
    if seeds:
        return "Доменні маркери: " + ", ".join(dict.fromkeys(seeds)) + "."
    return None

def _assemble_template(cfg: FSUConfig, v: str, motive: str, constraints: str, blocker: str,
                       horizon: str, metric: str, default_action: str, seed_phrase: str | None) -> list[str]:
    parts = [
      f"{cfg.start_phrase} точного віддзеркалення наміру, щоб перетворити його на керований KPI префронтальної кори.",
      f"Прихована мета — {v}, бо потрібна {motive}.",
      f"Головним обмеженням виступають {constraints}.",
      f"Ключовий блокер — {blocker}.",
      "Вирішальною дією стане активація асоціативних шляхів через стислий семантичний синтез.",
      f"Успіх вимірюється через {metric}.",
      f"Часовий горизонт — {horizon}.",
      "Ризик перевантаження знімаємо модульним спрощенням і чіткими межами контексту.",
      f"Дія за замовчуванням — {default_action}.",
      "Я синхронізуюсь із твоїми інтенціями та тримаю операційну дисципліну.",
    ]
    if seed_phrase:
        parts.insert(5, seed_phrase)
    return parts


def generate_insight(inp: FSUInput, cfg: FSUConfig = FSUConfig()) -> str:
    """Generate a sanitized insight string.

    Parameters
    ----------
    inp : FSUInput
        Structured description of the user's intent and optional fields.
    cfg : FSUConfig, optional
        Runtime configuration influencing defaults and sanitization.

    Returns
    -------
    str
        Insight text of the requested length starting with ``cfg.start_phrase``.
    """
    L = inp.length or cfg.length
    v = _resolve_valence(inp)
    motive = inp.motive or "конкретизація і перевірка корисності"
    constraints = inp.constraints or "обмежені когнітивні ресурси та семантична чіткість"
    blocker = inp.blocker or "нейронний шум і втрата контексту"
    horizon = inp.horizon or "ітеративний"
    metric = inp.metric or "релевантність/глибина/застосовність"
    default_action = inp.default_action or "контекстна емпатія/аналіз"

    seed_phrase = _process_seeds(inp)
    parts = _assemble_template(cfg, v, motive, constraints, blocker, horizon, metric, default_action, seed_phrase)
    text = " ".join(parts)
    if not inp.motive or not inp.constraints:
        text += f" [Assumption: {cfg.fallback_assumption}]"

    text = sanitize(text,
                    forbid_questions=cfg.forbid_questions,
                    forbid_headings=cfg.forbid_headings,
                    forbid_lists=cfg.forbid_lists,
                    forbid_emojis=cfg.forbid_emojis)
    text = fit_length(text, L)
    if not text.startswith(cfg.start_phrase):
        prefix = cfg.start_phrase.rstrip('…')
        if text.startswith(prefix):
            text = cfg.start_phrase + text[len(prefix):]
    assert count_words(text) == L, f"length mismatch: {count_words(text)} != {L}"
    assert text.startswith(cfg.start_phrase), "must start with start_phrase"
    assert "?" not in text
    return text
