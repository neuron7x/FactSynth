"""Role definitions used by the GLRTPM pipeline."""

from dataclasses import dataclass
from typing import Protocol


class Role(Protocol):
    """Protocol describing a role participant."""

    name: str

    def respond(self, thesis: str) -> str:
        """Generate text in response to *thesis*."""


@dataclass
class Rationalist:
    """Analytical role that formalizes arguments."""

    name: str = "Rationalist"

    def respond(self, thesis: str) -> str:
        """Return a rationalist perspective on ``thesis``."""

        return f"[Rationalist] Formalize: {thesis}. Provide premises, inference, conclusion."


@dataclass
class Critic:
    """Role providing counter-arguments."""

    name: str = "Critic"

    def respond(self, thesis: str) -> str:
        """Return critical feedback for ``thesis``."""

        return f"[Critic] Counter-arguments to: {thesis}. Attack assumptions, show contradictions."


@dataclass
class Aesthete:
    """Role focused on metaphorical imagery."""

    name: str = "Aesthete"

    def respond(self, thesis: str) -> str:
        """Return an aesthetic view of ``thesis``."""

        return f"[Aesthete] Metaphor & imagery for: {thesis}."


@dataclass
class Integrator:
    """Role that synthesizes arguments."""

    name: str = "Integrator"

    def respond(self, thesis: str) -> str:
        """Return a synthesis for ``thesis``."""

        return f"[Integrator] Synthesize viable position from debate about: {thesis}."


@dataclass
class Observer:
    """Role auditing ethics and epistemics."""

    name: str = "Observer"

    def respond(self, thesis: str) -> str:
        """Return an audit for ``thesis``."""

        return f"[Observer] Ethics & epistemic audit for: {thesis}."
