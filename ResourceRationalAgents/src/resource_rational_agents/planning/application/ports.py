"""Outbound capabilities required by hierarchical planning."""

from __future__ import annotations

from typing import Mapping, Protocol, Sequence

from resource_rational_agents.planning.domain.models import (
    ActionCandidate,
    BeliefEstimate,
    ExecutionObservation,
    GoalObservation,
    HighComputation,
    LowComputation,
    MissionSpec,
    PlanCandidate,
)


class ProjectObservationPort(Protocol):
    """Expose costly project-model computations without leaking adapter details inward."""

    def high_computations(
        self, mission: MissionSpec, beliefs: Mapping[str, BeliefEstimate]
    ) -> Sequence[HighComputation]: ...

    def perform_high_computation(self, computation: HighComputation) -> GoalObservation: ...

    def low_computations(
        self,
        mission: MissionSpec,
        goal_id: str,
        beliefs: Mapping[str, BeliefEstimate],
    ) -> Sequence[LowComputation]: ...

    def perform_low_computation(self, computation: LowComputation) -> GoalObservation: ...

    def plans(
        self,
        mission: MissionSpec,
        goal_id: str,
        beliefs: Mapping[str, BeliefEstimate],
    ) -> Sequence[PlanCandidate]: ...


class ProjectExecutionPort(Protocol):
    """Perform an already selected and constraint-approved object-level action."""

    def execute(self, action: ActionCandidate) -> ExecutionObservation: ...

    def is_complete(self, mission: MissionSpec, plan: PlanCandidate) -> bool: ...

