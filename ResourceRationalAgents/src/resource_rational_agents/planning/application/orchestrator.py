"""Public mission use case coordinating High -> Meta -> Low -> Meta -> High."""

from __future__ import annotations

from typing import Mapping

from resource_rational_agents.planning.application.ports import (
    ProjectExecutionPort,
    ProjectObservationPort,
)
from resource_rational_agents.planning.domain.adaptive import RecedingHorizonAdaptiveRule
from resource_rational_agents.planning.domain.constraints import (
    ConstraintContext,
    ConstraintJudge,
    ConstraintScope,
)
from resource_rational_agents.planning.domain.controllers import (
    ComputeHigh,
    ComputeLow,
    HighController,
    LowController,
    MetaController,
    RequestGoalReconsideration,
    SelectGoal,
    SelectPlan,
)
from resource_rational_agents.planning.domain.models import (
    BeliefEstimate,
    ControllerPhase,
    MissionEvent,
    MissionResult,
    MissionSpec,
    MissionStatus,
    PlanCandidate,
)


class MissionOrchestrator:
    """Run one bounded mission through stable domain and port seams.

    Failure modes are explicit in MissionStatus. The use case never executes an
    action before the shared constraint judge approves it, and it applies all
    evidence to the belief state regardless of direction.
    """

    def __init__(
        self,
        high: HighController,
        low: LowController,
        meta: MetaController,
        adaptive_rule: RecedingHorizonAdaptiveRule,
        constraint_judge: ConstraintJudge,
        observations: ProjectObservationPort,
        execution: ProjectExecutionPort,
    ) -> None:
        self._high = high
        self._low = low
        self._meta = meta
        self._adaptive_rule = adaptive_rule
        self._constraint_judge = constraint_judge
        self._observations = observations
        self._execution = execution

    def run(self, mission: MissionSpec) -> MissionResult:
        beliefs = dict(mission.initial_beliefs)
        settings = self._adaptive_rule.settings(mission.feedback)
        planning_remaining = mission.planning_budget
        execution_remaining = mission.execution_budget
        high_phase_remaining = settings.high_computation_budget
        low_phase_remaining = settings.low_computation_budget
        blocked_goal_ids: set[str] = set()
        events: list[MissionEvent] = []
        actions_executed: list[str] = []
        phase = ControllerPhase.HIGH
        current_goal_id: str | None = None
        selected_plan: PlanCandidate | None = None

        mission_context = self._context(
            mission,
            ControllerPhase.HIGH,
            planning_remaining,
            execution_remaining,
            beliefs,
        )
        mission_constraint_decision = self._constraint_judge.evaluate(
            ConstraintScope.MISSION, mission, mission_context
        )
        if not mission_constraint_decision.allowed:
            constraint_ids = ", ".join(
                violation.constraint_id
                for violation in mission_constraint_decision.violations
            )
            events.append(
                MissionEvent(
                    ControllerPhase.STOPPED,
                    "mission_rejected",
                    f"Mission constraints rejected the mission: {constraint_ids}",
                    mission.mission_id,
                )
            )
            return self._result(
                mission,
                MissionStatus.MISSION_CONSTRAINT_REJECTED,
                None,
                None,
                actions_executed,
                beliefs,
                events,
            )

        maximum_iterations = 20 + 4 * (
            mission.planning_budget + mission.execution_budget + len(mission.goals)
        )
        for _ in range(maximum_iterations):
            context = self._context(
                mission, phase, planning_remaining, execution_remaining, beliefs
            )

            if phase is ControllerPhase.HIGH:
                computations = self._observations.high_computations(mission, beliefs)
                decision = self._high.decide(
                    mission.goals,
                    beliefs,
                    computations,
                    frozenset(blocked_goal_ids),
                    context,
                    min(planning_remaining, high_phase_remaining),
                )
                if isinstance(decision, ComputeHigh):
                    observation = self._observations.perform_high_computation(
                        decision.computation
                    )
                    beliefs[observation.goal_id] = beliefs[observation.goal_id].observe(
                        observation.observed_value, observation.observation_variance
                    )
                    if not observation.reachable:
                        blocked_goal_ids.add(observation.goal_id)
                    planning_remaining -= 1
                    high_phase_remaining -= 1
                    events.append(
                        MissionEvent(
                            phase,
                            "high_computation",
                            observation.source,
                            observation.goal_id,
                            beliefs[observation.goal_id].mean,
                        )
                    )
                    continue
                if isinstance(decision, SelectGoal):
                    current_goal_id = decision.goal_id
                    selected_plan = None
                    low_phase_remaining = settings.low_computation_budget
                    phase = ControllerPhase.LOW
                    events.append(
                        MissionEvent(
                            ControllerPhase.HIGH,
                            "goal_selected",
                            "High stopped deliberating and Meta switched control to Low",
                            decision.goal_id,
                            decision.expected_value,
                        )
                    )
                    continue
                return self._result(
                    mission,
                    MissionStatus.NO_FEASIBLE_GOAL,
                    current_goal_id,
                    selected_plan,
                    actions_executed,
                    beliefs,
                    events,
                )

            if phase is ControllerPhase.LOW:
                assert current_goal_id is not None
                if self._meta.should_reconsider_goal(
                    current_goal_id,
                    mission.goals,
                    beliefs,
                    frozenset(blocked_goal_ids),
                    settings.switch_margin,
                    context,
                ):
                    events.append(
                        MissionEvent(
                            ControllerPhase.LOW,
                            "goal_reconsidered",
                            "Meta returned control to High after a lower or infeasible estimate",
                            current_goal_id,
                            beliefs[current_goal_id].mean,
                        )
                    )
                    current_goal_id = None
                    selected_plan = None
                    high_phase_remaining = settings.high_computation_budget
                    phase = ControllerPhase.HIGH
                    continue

                computations = self._observations.low_computations(
                    mission, current_goal_id, beliefs
                )
                plans = self._observations.plans(mission, current_goal_id, beliefs)
                decision = self._low.decide(
                    current_goal_id,
                    computations,
                    plans,
                    context,
                    min(planning_remaining, low_phase_remaining),
                )
                if isinstance(decision, ComputeLow):
                    observation = self._observations.perform_low_computation(
                        decision.computation
                    )
                    beliefs[observation.goal_id] = beliefs[observation.goal_id].observe(
                        observation.observed_value, observation.observation_variance
                    )
                    if not observation.reachable:
                        blocked_goal_ids.add(observation.goal_id)
                    planning_remaining -= 1
                    low_phase_remaining -= 1
                    events.append(
                        MissionEvent(
                            phase,
                            "low_computation",
                            observation.source,
                            observation.goal_id,
                            beliefs[observation.goal_id].mean,
                        )
                    )
                    continue
                if isinstance(decision, RequestGoalReconsideration):
                    blocked_goal_ids.add(current_goal_id)
                    events.append(
                        MissionEvent(
                            phase,
                            "plan_stopped",
                            decision.reason,
                            current_goal_id,
                            beliefs[current_goal_id].mean,
                        )
                    )
                    current_goal_id = None
                    selected_plan = None
                    high_phase_remaining = settings.high_computation_budget
                    phase = ControllerPhase.HIGH
                    continue
                if isinstance(decision, SelectPlan):
                    selected_plan = decision.plan
                    phase = ControllerPhase.EXECUTION
                    events.append(
                        MissionEvent(
                            ControllerPhase.LOW,
                            "plan_selected",
                            "Low stopped deliberating and submitted a feasible plan",
                            selected_plan.plan_id,
                            selected_plan.net_value,
                        )
                    )
                    continue

            if phase is ControllerPhase.EXECUTION:
                assert current_goal_id is not None and selected_plan is not None
                if self._execution.is_complete(mission, selected_plan):
                    return self._result(
                        mission,
                        MissionStatus.COMPLETED,
                        current_goal_id,
                        selected_plan,
                        actions_executed,
                        beliefs,
                        events,
                    )
                if execution_remaining <= 0:
                    return self._result(
                        mission,
                        MissionStatus.EXECUTION_BUDGET_EXHAUSTED,
                        current_goal_id,
                        selected_plan,
                        actions_executed,
                        beliefs,
                        events,
                    )

                pending = tuple(
                    action
                    for action in selected_plan.actions
                    if action.action_id not in actions_executed
                )
                if not pending:
                    blocked_goal_ids.add(current_goal_id)
                    events.append(
                        MissionEvent(
                            phase,
                            "plan_stopped",
                            "The plan has no executable action and the project is incomplete",
                            selected_plan.plan_id,
                        )
                    )
                    phase = ControllerPhase.HIGH
                    continue

                constraint_failed = False
                for action in pending[: settings.execution_batch_size]:
                    context = self._context(
                        mission, phase, planning_remaining, execution_remaining, beliefs
                    )
                    decision = self._constraint_judge.evaluate(
                        ConstraintScope.ACTION, action, context
                    )
                    if not decision.allowed:
                        blocked_goal_ids.add(current_goal_id)
                        details = ", ".join(
                            violation.constraint_id for violation in decision.violations
                        )
                        events.append(
                            MissionEvent(
                                phase,
                                "action_rejected",
                                f"Constraint judge rejected the action: {details}",
                                action.action_id,
                            )
                        )
                        constraint_failed = True
                        break

                    observation = self._execution.execute(action)
                    actions_executed.append(action.action_id)
                    execution_remaining -= 1
                    events.append(
                        MissionEvent(
                            phase,
                            "action_executed",
                            observation.detail,
                            action.action_id,
                        )
                    )
                    if observation.observed_goal_value is not None:
                        assert observation.observation_variance is not None
                        beliefs[current_goal_id] = beliefs[current_goal_id].observe(
                            observation.observed_goal_value,
                            observation.observation_variance,
                        )
                    if observation.project_complete:
                        return self._result(
                            mission,
                            MissionStatus.COMPLETED,
                            current_goal_id,
                            selected_plan,
                            actions_executed,
                            beliefs,
                            events,
                        )
                    if execution_remaining <= 0:
                        break

                if constraint_failed:
                    selected_plan = None
                    current_goal_id = None
                    high_phase_remaining = settings.high_computation_budget
                    phase = ControllerPhase.HIGH
                else:
                    low_phase_remaining = settings.low_computation_budget
                    phase = ControllerPhase.LOW
                continue

        return self._result(
            mission,
            MissionStatus.LOOP_GUARD_REACHED,
            current_goal_id,
            selected_plan,
            actions_executed,
            beliefs,
            events,
        )

    @staticmethod
    def _context(
        mission: MissionSpec,
        phase: ControllerPhase,
        planning_remaining: int,
        execution_remaining: int,
        beliefs: Mapping[str, BeliefEstimate],
    ) -> ConstraintContext:
        return ConstraintContext(
            mission.mission_id,
            phase,
            planning_remaining,
            execution_remaining,
            beliefs,
        )

    @staticmethod
    def _result(
        mission: MissionSpec,
        status: MissionStatus,
        goal_id: str | None,
        plan: PlanCandidate | None,
        actions_executed: list[str],
        beliefs: Mapping[str, BeliefEstimate],
        events: list[MissionEvent],
    ) -> MissionResult:
        return MissionResult(
            mission.mission_id,
            status,
            goal_id,
            None if plan is None else plan.plan_id,
            tuple(actions_executed),
            dict(beliefs),
            tuple(events),
        )
