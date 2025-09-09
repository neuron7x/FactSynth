from dataclasses import dataclass
from typing import Protocol


class Role(Protocol):
    name: str
    def respond(self, thesis: str) -> str: ...

@dataclass
class Rationalist:
    name: str = "Rationalist"
    def respond(self, thesis: str) -> str:
        return f"[Rationalist] Formalize: {thesis}. Provide premises, inference, conclusion."

@dataclass
class Critic:
    name: str = "Critic"
    def respond(self, thesis: str) -> str:
        return f"[Critic] Counter-arguments to: {thesis}. Attack assumptions, show contradictions."

@dataclass
class Aesthete:
    name: str = "Aesthete"
    def respond(self, thesis: str) -> str:
        return f"[Aesthete] Metaphor & imagery for: {thesis}."

@dataclass
class Integrator:
    name: str = "Integrator"
    def respond(self, thesis: str) -> str:
        return f"[Integrator] Synthesize viable position from debate about: {thesis}."

@dataclass
class Observer:
    name: str = "Observer"
    def respond(self, thesis: str) -> str:
        return f"[Observer] Ethics & epistemic audit for: {thesis}."
