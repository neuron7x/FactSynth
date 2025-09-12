"""Simplified Kuramoto-style oscillator network."""

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np


@dataclass
class NDMACO:
    """Neural dynamical model with adaptive coupling oscillators."""

    N: int = 5
    M: int = 2
    K: float = 1.8
    sigma: float = 0.0
    omega: np.ndarray | None = None
    alpha: np.ndarray | None = None
    adjacency: List[np.ndarray] = field(default_factory=list)
    theta0: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Initialize defaults for optional arrays."""

        if self.omega is None:
            self.omega = np.ones(self.N)
        if self.alpha is None:
            self.alpha = np.zeros(self.M)
        if not self.adjacency:
            self.adjacency = [np.eye(self.N) for _ in range(self.M)]
        if self.theta0 is None:
            self.theta0 = np.linspace(0, 2 * np.pi, self.N, endpoint=False)

    def _drift(self, theta: np.ndarray) -> np.ndarray:
        """Return instantaneous angular velocity for each oscillator."""

        assert self.omega is not None and self.alpha is not None
        drift = np.zeros(self.N)
        for i in range(self.N):
            s = 0.0
            for m in range(self.M):
                s += np.sum(
                    self.adjacency[m][i, :] * np.sin(theta - theta[i] - self.alpha[m])
                )
            drift[i] = self.omega[i] + (self.K / self.N) * s
        return drift

    def simulate(self, t_max: float = 5.0, dt: float = 0.01) -> Tuple[np.ndarray, np.ndarray]:
        """Integrate oscillator phases over time."""

        steps = int(t_max / dt)
        t = np.linspace(0, t_max, steps)
        theta = np.zeros((steps, self.N))
        theta[0] = self.theta0
        for s in range(1, steps):
            theta[s] = theta[s - 1] + self._drift(theta[s - 1]) * dt
        return t, theta % (2 * np.pi)
