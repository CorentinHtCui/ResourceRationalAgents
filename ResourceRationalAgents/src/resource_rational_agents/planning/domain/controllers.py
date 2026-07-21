"""Pure decisions made by the High, Low, and Meta controllers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from resource_rational_agents.planning.domain.constraints import (
    ConstraintContext,
    ConstraintJudge,
    ConstraintScope,
)
from resource_rational_agents.planning.domain.models import (
    BeliefEstimate,
    Goal,
    HighComputation,
    LowComputation,
    PlanCandidate,
)
from resource_rational_agents.planning.domain.voc import HighVocPolicy, LowVocPolicy


@dataclass(frozen=True)
class ComputeHigh:
    computation: HighComputation
    voc: float


@dataclass(frozen=True)
class SelectGoal:
    goal_id: str
    expected_value: float


@dataclass(frozen=True)
class StopHigh:
    reason: str


HighDecision = ComputeHigh | SelectGoal | StopHigh


@dataclass(frozen=True)
class ComputeLow:
    computation: LowComputation
    voc: float


@dataclass(frozen=True)
class SelectPlan:
    plan: PlanCandidate


@dataclass(frozen=True)
class RequestGoalReconsideration:
    reason: str


LowDecision = ComputeLow | SelectPlan | RequestGoalReconsideration


class HighController:
    """Select the next goal computation, or stop and choose the best feasible goal."""

    def __init__(
        self,
        voc_policy: HighVocPolicy,
        constraint_judge: ConstraintJudge,
        minimum_voc: float = 0.0,
    ) -> None:
        self._voc_policy = voc_policy
        self._constraint_judge = constraint_judge
        self._minimum_voc = minimum_voc

    def decide(
        self,
        goals: Sequence[Goal],
        beliefs: Mapping[str, BeliefEstimate],
        computations: Sequence[HighComputation],
        blocked_goal_ids: frozenset[str],
        context: ConstraintContext,
        computation_budget_remaining: int,
    ) -> HighDecision:
        feasible_goals = tuple(
            goal
            for goal in goals
            if goal.goal_id not in blocked_goal_ids
            and self._constraint_judge.allowed(ConstraintScope.GOAL, goal, context)
        )
        if not feasible_goals:
            return StopHigh("no candidate goal satisfies the active constraints")

        feasible_ids = {goal.goal_id for goal in feasible_goals}
        if computation_budget_remaining > 0:
            scored = tuple(
                (self._voc_policy.score(computation, len(goals)), computation)
                for computation in computations
                if computation.goal_id in feasible_ids
                and self._constraint_judge.allowed(
                    ConstraintScope.COMPUTATION, computation, context
                )
            )
            if scored:
                voc, computation = max(scored, key=lambda item: item[0])
                if voc > self._minimum_voc:
                    return ComputeHigh(computation, voc)

        selected = max(feasible_goals, key=lambda goal: beliefs[goal.goal_id].mean)
        return SelectGoal(selected.goal_id, beliefs[selected.goal_id].mean)


class LowController:
    """Select within-goal computations incrementally, then choose a feasible plan."""

    def __init__(
        self,
        voc_policy: LowVocPolicy,
        constraint_judge: ConstraintJudge,
        minimum_voc: float = 0.0,
    ) -> None:
        self._voc_policy = voc_policy
        self._constraint_judge = constraint_judge
        self._minimum_voc = minimum_voc

    def decide(
        self,
        goal_id: str,
        computations: Sequence[LowComputation],
        plans: Sequence[PlanCandidate],
        context: ConstraintContext,
        computation_budget_remaining: int,
    ) -> LowDecision:
        if computation_budget_remaining > 0:
            scored = tuple(
                (self._voc_policy.score(computation), computation)
                for computation in computations
                if computation.goal_id == goal_id
                and self._constraint_judge.allowed(
                    ConstraintScope.COMPUTATION, computation, context
                )
            )
            if scored:
                voc, computation = max(scored, key=lambda item: item[0])
                if voc > self._minimum_voc:
                    return ComputeLow(computation, voc)

        feasible_plans = tuple(
            plan
            for plan in plans
            if plan.goal_id == goal_id
            and self._constraint_judge.allowed(ConstraintScope.PLAN, plan, context)
        )
        if not feasible_plans:
            return RequestGoalReconsideration("no feasible plan remains for the selected goal")
        return SelectPlan(max(feasible_plans, key=lambda plan: plan.net_value))


class MetaController:
    """Switch between High and Low without owning mission or project I/O."""

    def __init__(self, constraint_judge: ConstraintJudge) -> None:
        self._constraint_judge = constraint_judge

    def should_reconsider_goal(
        self,
        current_goal_id: str,
        goals: Sequence[Goal],
        beliefs: Mapping[str, BeliefEstimate],
        blocked_goal_ids: frozenset[str],
        switch_margin: float,
        context: ConstraintContext,
    ) -> bool:
        if current_goal_id in blocked_goal_ids:
            return True
        current_goal = next(goal for goal in goals if goal.goal_id == current_goal_id)
        if not self._constraint_judge.allowed(ConstraintScope.GOAL, current_goal, context):
            return True

        alternative_values = tuple(
            beliefs[goal.goal_id].mean
            for goal in goals
            if goal.goal_id != current_goal_id
            and goal.goal_id not in blocked_goal_ids
            and self._constraint_judge.allowed(ConstraintScope.GOAL, goal, context)
        )
        if not alternative_values:
            return False
        return max(alternative_values) > beliefs[current_goal_id].mean + switch_margin

