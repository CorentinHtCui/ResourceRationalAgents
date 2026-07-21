"""Paper-aligned high- and low-level value-of-computation approximations."""

from __future__ import annotations

from dataclasses import dataclass

from resource_rational_agents.planning.domain.models import HighComputation, LowComputation


@dataclass(frozen=True)
class HighVocWeights:
    myopic_voi: float
    vpi: float
    cost: float

    def validate(self, goal_count: int) -> None:
        if goal_count < 1:
            raise ValueError("goal_count must be positive")
        if min(self.myopic_voi, self.vpi) < 0:
            raise ValueError("high information weights must be non-negative")
        if abs(self.myopic_voi + self.vpi - 1.0) > 1e-9:
            raise ValueError("high information weights must lie on the probability simplex")
        if not 1 <= self.cost <= goal_count:
            raise ValueError("high cost weight must be in [1, number of goals]")


@dataclass(frozen=True)
class LowVocWeights:
    myopic_voi: float
    vpi: float
    subproblem_vpi: float
    cost: float

    def validate(self, goal_node_count: int) -> None:
        information_weights = (self.myopic_voi, self.vpi, self.subproblem_vpi)
        if min(information_weights) < 0:
            raise ValueError("low information weights must be non-negative")
        if abs(sum(information_weights) - 1.0) > 1e-9:
            raise ValueError("low information weights must lie on the probability simplex")
        if not 1 <= self.cost <= goal_node_count:
            raise ValueError("low cost weight must be in [1, goal node count]")


class HighVocPolicy:
    def __init__(self, weights: HighVocWeights) -> None:
        self._weights = weights

    def score(self, computation: HighComputation, goal_count: int) -> float:
        self._weights.validate(goal_count)
        return (
            self._weights.myopic_voi * computation.myopic_voi
            + self._weights.vpi * computation.vpi
            - self._weights.cost * computation.cost
        )


class LowVocPolicy:
    def __init__(self, weights: LowVocWeights) -> None:
        self._weights = weights

    def score(self, computation: LowComputation) -> float:
        self._weights.validate(computation.goal_node_count)
        anticipated_cost = computation.computation_cost * (
            self._weights.myopic_voi * computation.myopic_relevant_nodes
            + self._weights.vpi * computation.vpi_relevant_nodes
            + self._weights.subproblem_vpi * computation.subproblem_relevant_nodes
        )
        return (
            self._weights.myopic_voi * computation.myopic_voi
            + self._weights.vpi * computation.vpi
            + self._weights.subproblem_vpi * computation.subproblem_vpi
            - self._weights.cost * anticipated_cost
        )
