from __future__ import annotations

import unittest

from resource_rational_agents.planning.adapters.in_memory_project import GoalScenario
from resource_rational_agents.planning.composition.root import build_in_memory_harness
from resource_rational_agents.planning.domain.constraints import (
    ConstraintScope,
    RuleConstraint,
)
from resource_rational_agents.planning.domain.models import (
    ActionCandidate,
    BeliefEstimate,
    FeedbackProfile,
    Goal,
    MissionSpec,
    MissionStatus,
    PlanCandidate,
)


def make_plan(goal_id: str, plan_id: str, action_count: int = 1) -> PlanCandidate:
    actions = tuple(
        ActionCandidate(
            f"{plan_id}:a{index}",
            goal_id,
            plan_id,
            f"action {index}",
            expected_value=10.0,
            exposure=0.1,
        )
        for index in range(action_count)
    )
    return PlanCandidate(plan_id, goal_id, 80.0, 5.0, 1.0, actions)


def make_scenario(
    goal_id: str,
    goal_value: float,
    plan_return: float,
    *,
    reachable: bool = True,
    high_information_value: float = 20.0,
    low_information_value: float = 20.0,
    plan_id: str | None = None,
) -> GoalScenario:
    plan = make_plan(goal_id, plan_id or f"plan:{goal_id}")
    return GoalScenario(
        goal_id,
        goal_value,
        0.5,
        high_information_value,
        high_information_value,
        1.0,
        plan_return,
        0.1,
        reachable,
        low_information_value,
        low_information_value,
        low_information_value,
        1.0,
        2,
        3,
        (plan,),
    )


def make_mission(
    goal_ids: tuple[str, ...],
    beliefs: dict[str, float],
    *,
    planning_budget: int = 10,
    execution_budget: int = 5,
) -> MissionSpec:
    return MissionSpec(
        "mission",
        "Build usable software",
        tuple(Goal(goal_id, goal_id) for goal_id in goal_ids),
        {goal_id: BeliefEstimate(beliefs[goal_id], 10.0) for goal_id in goal_ids},
        planning_budget,
        execution_budget,
        FeedbackProfile(0.8, 0.8, 0.8, 1.0, 0.0, 0.0),
    )


class MissionOrchestratorTests(unittest.TestCase):
    def test_downward_low_evidence_triggers_high_meta_low_meta_high_switch(self) -> None:
        scenarios = (
            make_scenario("ambitious", 100.0, 20.0),
            make_scenario("usable", 80.0, 75.0),
        )
        harness = build_in_memory_harness(scenarios)
        mission = make_mission(
            ("ambitious", "usable"),
            {"ambitious": 100.0, "usable": 80.0},
        )

        result = harness.orchestrator.run(mission)

        self.assertEqual(result.status, MissionStatus.COMPLETED)
        self.assertEqual(result.selected_goal_id, "usable")
        self.assertLess(result.final_beliefs["ambitious"].mean, 80.0)
        selected_goals = [
            event.subject_id for event in result.events if event.event == "goal_selected"
        ]
        self.assertEqual(selected_goals, ["ambitious", "usable"])
        self.assertIn("goal_reconsidered", [event.event for event in result.events])

    def test_constraint_judge_gates_plan_before_execution(self) -> None:
        scenario = make_scenario("goal", 50.0, 45.0, plan_id="unsafe")
        constraint = RuleConstraint(
            "no-unsafe-plan",
            "Unsafe plans are forbidden",
            frozenset({ConstraintScope.PLAN}),
            lambda candidate, context: getattr(candidate, "plan_id", None) != "unsafe",
        )
        harness = build_in_memory_harness((scenario,), (constraint,))
        mission = make_mission(("goal",), {"goal": 50.0})

        result = harness.orchestrator.run(mission)

        self.assertEqual(result.status, MissionStatus.NO_FEASIBLE_GOAL)
        self.assertFalse(harness.project.actions_executed)
        self.assertIn("plan_stopped", [event.event for event in result.events])

    def test_constraint_judge_can_reject_the_human_mission_before_optimization(self) -> None:
        scenario = make_scenario("goal", 50.0, 45.0)
        constraint = RuleConstraint(
            "operator-stop",
            "The human operator stopped this mission",
            frozenset({ConstraintScope.MISSION}),
            lambda candidate, context: False,
        )
        harness = build_in_memory_harness((scenario,), (constraint,))

        result = harness.orchestrator.run(make_mission(("goal",), {"goal": 50.0}))

        self.assertEqual(result.status, MissionStatus.MISSION_CONSTRAINT_REJECTED)
        self.assertFalse(harness.project.high_computations_performed)
        self.assertFalse(harness.project.actions_executed)

    def test_planning_budget_causes_incremental_not_exhaustive_search(self) -> None:
        scenarios = (
            make_scenario("a", 60.0, 55.0, high_information_value=40.0),
            make_scenario("b", 50.0, 45.0, high_information_value=10.0),
        )
        harness = build_in_memory_harness(scenarios)
        mission = make_mission(
            ("a", "b"),
            {"a": 60.0, "b": 50.0},
            planning_budget=1,
        )

        result = harness.orchestrator.run(mission)

        self.assertEqual(result.status, MissionStatus.COMPLETED)
        self.assertEqual(len(harness.project.high_computations_performed), 1)
        self.assertEqual(len(harness.project.low_computations_performed), 0)

    def test_unreachable_goal_is_blocked_and_alternative_is_executed(self) -> None:
        scenarios = (
            make_scenario("unreachable", 100.0, 90.0, reachable=False),
            make_scenario("reachable", 70.0, 65.0),
        )
        harness = build_in_memory_harness(scenarios)
        mission = make_mission(
            ("unreachable", "reachable"),
            {"unreachable": 100.0, "reachable": 70.0},
        )

        result = harness.orchestrator.run(mission)

        self.assertEqual(result.status, MissionStatus.COMPLETED)
        self.assertEqual(result.selected_goal_id, "reachable")
        self.assertFalse(
            any(action.startswith("plan:unreachable") for action in result.actions_executed)
        )


if __name__ == "__main__":
    unittest.main()
