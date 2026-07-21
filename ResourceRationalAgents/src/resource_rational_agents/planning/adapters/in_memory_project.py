"""Deterministic project adapter for tests, demonstrations, and contract examples."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

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


@dataclass(frozen=True)
class GoalScenario:
    """External/project facts intentionally kept out of the domain model."""

    goal_id: str
    observed_goal_value: float
    goal_observation_variance: float
    high_myopic_voi: float
    high_vpi: float
    high_cost: float
    observed_plan_return: float
    plan_observation_variance: float
    reachable: bool
    low_myopic_voi: float
    low_vpi: float
    low_subproblem_vpi: float
    low_computation_cost: float
    low_subproblem_relevant_nodes: int
    goal_node_count: int
    plans: tuple[PlanCandidate, ...]


class InMemoryProjectAdapter:
    """Implement both project ports while preserving their separate contracts."""

    def __init__(self, scenarios: Sequence[GoalScenario]) -> None:
        self._scenarios = {scenario.goal_id: scenario for scenario in scenarios}
        if len(self._scenarios) != len(tuple(scenarios)):
            raise ValueError("scenario goal ids must be unique")
        self._high_performed: set[str] = set()
        self._low_performed: set[str] = set()
        self._executed_actions: set[str] = set()

    @property
    def high_computations_performed(self) -> frozenset[str]:
        return frozenset(self._high_performed)

    @property
    def low_computations_performed(self) -> frozenset[str]:
        return frozenset(self._low_performed)

    @property
    def actions_executed(self) -> frozenset[str]:
        return frozenset(self._executed_actions)

    def high_computations(
        self, mission: MissionSpec, beliefs: Mapping[str, BeliefEstimate]
    ) -> Sequence[HighComputation]:
        del beliefs
        return tuple(
            HighComputation(
                f"high:{goal.goal_id}",
                goal.goal_id,
                scenario.high_myopic_voi,
                scenario.high_vpi,
                scenario.high_cost,
            )
            for goal in mission.goals
            if (scenario := self._scenarios[goal.goal_id]).goal_id not in self._high_performed
        )

    def perform_high_computation(self, computation: HighComputation) -> GoalObservation:
        scenario = self._scenarios[computation.goal_id]
        self._high_performed.add(computation.goal_id)
        return GoalObservation(
            computation.goal_id,
            scenario.observed_goal_value,
            scenario.goal_observation_variance,
            True,
            f"Observed goal value with {computation.computation_id}",
        )

    def low_computations(
        self,
        mission: MissionSpec,
        goal_id: str,
        beliefs: Mapping[str, BeliefEstimate],
    ) -> Sequence[LowComputation]:
        del mission, beliefs
        scenario = self._scenarios[goal_id]
        if goal_id in self._low_performed:
            return ()
        return (
            LowComputation(
                f"low:{goal_id}",
                goal_id,
                scenario.low_myopic_voi,
                scenario.low_vpi,
                scenario.low_subproblem_vpi,
                scenario.low_computation_cost,
                1,
                scenario.goal_node_count,
                scenario.low_subproblem_relevant_nodes,
                scenario.goal_node_count,
            ),
        )

    def perform_low_computation(self, computation: LowComputation) -> GoalObservation:
        scenario = self._scenarios[computation.goal_id]
        self._low_performed.add(computation.goal_id)
        return GoalObservation(
            computation.goal_id,
            scenario.observed_plan_return,
            scenario.plan_observation_variance,
            scenario.reachable,
            f"Observed reachability and net path value with {computation.computation_id}",
        )

    def plans(
        self,
        mission: MissionSpec,
        goal_id: str,
        beliefs: Mapping[str, BeliefEstimate],
    ) -> Sequence[PlanCandidate]:
        del mission, beliefs
        scenario = self._scenarios[goal_id]
        return scenario.plans if scenario.reachable else ()

    def execute(self, action: ActionCandidate) -> ExecutionObservation:
        self._executed_actions.add(action.action_id)
        plan = self._find_plan(action.plan_id)
        complete = all(item.action_id in self._executed_actions for item in plan.actions)
        scenario = self._scenarios[action.goal_id]
        return ExecutionObservation(
            action.action_id,
            True,
            complete,
            f"Executed: {action.description}",
            scenario.observed_plan_return,
            scenario.plan_observation_variance,
        )

    def is_complete(self, mission: MissionSpec, plan: PlanCandidate) -> bool:
        del mission
        return all(action.action_id in self._executed_actions for action in plan.actions)

    def _find_plan(self, plan_id: str) -> PlanCandidate:
        for scenario in self._scenarios.values():
            for plan in scenario.plans:
                if plan.plan_id == plan_id:
                    return plan
        raise KeyError(f"unknown plan: {plan_id}")
