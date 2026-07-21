"""Run a deterministic demonstration of downward evidence causing a goal switch."""

from __future__ import annotations

import json

from resource_rational_agents.planning.adapters.in_memory_project import GoalScenario
from resource_rational_agents.planning.composition.root import build_in_memory_harness
from resource_rational_agents.planning.domain.models import (
    ActionCandidate,
    BeliefEstimate,
    FeedbackProfile,
    Goal,
    MissionSpec,
    PlanCandidate,
)


def _plan(goal_id: str, plan_id: str, action_descriptions: tuple[str, ...]) -> PlanCandidate:
    actions = tuple(
        ActionCandidate(
            f"{plan_id}:action:{index}",
            goal_id,
            plan_id,
            description,
            expected_value=10.0,
            exposure=0.2,
        )
        for index, description in enumerate(action_descriptions, start=1)
    )
    return PlanCandidate(plan_id, goal_id, 80.0, 10.0, 2.0, actions)


def demo() -> dict[str, object]:
    ambitious_plan = _plan("ambitious", "plan:ambitious", ("Prototype", "Integrate"))
    usable_plan = _plan("usable", "plan:usable", ("Build vertical slice", "Verify behavior"))
    scenarios = (
        GoalScenario(
            "ambitious",
            110.0,
            2.0,
            12.0,
            20.0,
            1.0,
            35.0,
            1.0,
            True,
            15.0,
            20.0,
            10.0,
            2.0,
            2,
            4,
            (ambitious_plan,),
        ),
        GoalScenario(
            "usable",
            90.0,
            2.0,
            10.0,
            18.0,
            1.0,
            82.0,
            1.0,
            True,
            12.0,
            18.0,
            9.0,
            2.0,
            2,
            4,
            (usable_plan,),
        ),
    )
    mission = MissionSpec(
        "demo",
        "Build usable software within the human operator's constraints",
        (
            Goal("ambitious", "Build the largest possible feature set"),
            Goal("usable", "Build a small verified vertical slice"),
        ),
        {
            "ambitious": BeliefEstimate(105.0, 20.0),
            "usable": BeliefEstimate(85.0, 20.0),
        },
        planning_budget=8,
        execution_budget=6,
        feedback=FeedbackProfile(0.8, 0.7, 0.8, 0.9, 0.1, 0.2),
    )
    result = build_in_memory_harness(scenarios).orchestrator.run(mission)
    return {
        "mission_id": result.mission_id,
        "status": result.status.value,
        "selected_goal_id": result.selected_goal_id,
        "selected_plan_id": result.selected_plan_id,
        "actions_executed": result.actions_executed,
        "beliefs": {
            goal_id: {"mean": belief.mean, "variance": belief.variance}
            for goal_id, belief in result.final_beliefs.items()
        },
        "events": [
            {
                "phase": event.phase.value,
                "event": event.event,
                "subject_id": event.subject_id,
                "value": event.value,
                "detail": event.detail,
            }
            for event in result.events
        ],
    }


def main() -> None:
    print(json.dumps(demo(), indent=2))


if __name__ == "__main__":
    main()
