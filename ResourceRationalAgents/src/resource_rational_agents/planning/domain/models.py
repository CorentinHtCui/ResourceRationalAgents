"""Domain values shared by hierarchical planning policies.

The values deliberately distinguish a goal, the uncertain value of that goal,
the value of another computation, and the value of an executable plan. Mixing
those quantities was the main source of ambiguity in the initial design.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class ControllerPhase(str, Enum):
    HIGH = "high"
    LOW = "low"
    EXECUTION = "execution"
    COMPLETE = "complete"
    STOPPED = "stopped"


class MissionStatus(str, Enum):
    COMPLETED = "completed"
    MISSION_CONSTRAINT_REJECTED = "mission_constraint_rejected"
    NO_FEASIBLE_GOAL = "no_feasible_goal"
    NO_FEASIBLE_PLAN = "no_feasible_plan"
    EXECUTION_BUDGET_EXHAUSTED = "execution_budget_exhausted"
    LOOP_GUARD_REACHED = "loop_guard_reached"


@dataclass(frozen=True)
class Goal:
    """A human-approved candidate end state, separate from its value estimate."""

    goal_id: str
    description: str
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.goal_id.strip():
            raise ValueError("goal_id must not be empty")


@dataclass(frozen=True)
class BeliefEstimate:
    """A normal belief used for explicit, bidirectional evidence updates."""

    mean: float
    variance: float

    def __post_init__(self) -> None:
        if self.variance <= 0:
            raise ValueError("variance must be positive")

    def observe(self, value: float, observation_variance: float) -> BeliefEstimate:
        """Return the Bayesian precision-weighted update, including downward evidence."""

        if observation_variance <= 0:
            raise ValueError("observation_variance must be positive")
        prior_precision = 1.0 / self.variance
        evidence_precision = 1.0 / observation_variance
        posterior_variance = 1.0 / (prior_precision + evidence_precision)
        posterior_mean = posterior_variance * (
            self.mean * prior_precision + value * evidence_precision
        )
        return BeliefEstimate(posterior_mean, posterior_variance)


@dataclass(frozen=True)
class HighComputation:
    """A possible goal-value computation in the high-level metalevel MDP."""

    computation_id: str
    goal_id: str
    myopic_voi: float
    vpi: float
    cost: float


@dataclass(frozen=True)
class LowComputation:
    """A possible within-goal computation in the low-level metalevel MDP."""

    computation_id: str
    goal_id: str
    myopic_voi: float
    vpi: float
    subproblem_vpi: float
    computation_cost: float
    myopic_relevant_nodes: int
    vpi_relevant_nodes: int
    subproblem_relevant_nodes: int
    goal_node_count: int = 1

    def __post_init__(self) -> None:
        if self.goal_node_count < 1:
            raise ValueError("goal_node_count must be at least one")
        relevant_counts = (
            self.myopic_relevant_nodes,
            self.vpi_relevant_nodes,
            self.subproblem_relevant_nodes,
        )
        if self.computation_cost < 0 or min(relevant_counts) < 0:
            raise ValueError("computation cost and relevant-node counts must be non-negative")
        if max(relevant_counts) > self.goal_node_count:
            raise ValueError("relevant-node counts cannot exceed the goal node count")


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    goal_id: str
    plan_id: str
    description: str
    expected_value: float = 0.0
    exposure: float = 0.0
    attributes: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanCandidate:
    plan_id: str
    goal_id: str
    expected_return: float
    cost: float
    risk: float
    actions: tuple[ActionCandidate, ...]
    attributes: Mapping[str, object] = field(default_factory=dict)

    @property
    def net_value(self) -> float:
        return self.expected_return - self.cost - self.risk


@dataclass(frozen=True)
class GoalObservation:
    """Evidence about a goal; it is never filtered by an incumbent/hook value."""

    goal_id: str
    observed_value: float
    observation_variance: float
    reachable: bool
    source: str


@dataclass(frozen=True)
class ExecutionObservation:
    action_id: str
    succeeded: bool
    project_complete: bool
    detail: str
    observed_goal_value: float | None = None
    observation_variance: float | None = None

    def __post_init__(self) -> None:
        if (self.observed_goal_value is None) != (self.observation_variance is None):
            raise ValueError("execution value and variance must be provided together")


@dataclass(frozen=True)
class FeedbackProfile:
    """Situation features used by the adaptive receding-horizon rule."""

    consequence: float
    uncertainty: float
    reversibility: float
    feedback_quality: float
    feedback_delay: float
    information_cost: float

    def __post_init__(self) -> None:
        unit_values = {
            "consequence": self.consequence,
            "uncertainty": self.uncertainty,
            "reversibility": self.reversibility,
            "feedback_quality": self.feedback_quality,
        }
        for name, value in unit_values.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between zero and one")
        if self.feedback_delay < 0 or self.information_cost < 0:
            raise ValueError("feedback_delay and information_cost must be non-negative")


@dataclass(frozen=True)
class MissionSpec:
    """Mission and resource limits supplied by the human operator."""

    mission_id: str
    objective: str
    goals: tuple[Goal, ...]
    initial_beliefs: Mapping[str, BeliefEstimate]
    planning_budget: int
    execution_budget: int
    feedback: FeedbackProfile

    def __post_init__(self) -> None:
        goal_ids = [goal.goal_id for goal in self.goals]
        if not self.mission_id.strip() or not self.objective.strip():
            raise ValueError("mission_id and objective must not be empty")
        if not goal_ids or len(goal_ids) != len(set(goal_ids)):
            raise ValueError("goals must be non-empty and have unique ids")
        if set(goal_ids) != set(self.initial_beliefs):
            raise ValueError("initial_beliefs must contain exactly the mission goals")
        if self.planning_budget < 0 or self.execution_budget < 1:
            raise ValueError("budgets must be non-negative and execution must be positive")


@dataclass(frozen=True)
class MissionEvent:
    phase: ControllerPhase
    event: str
    detail: str
    subject_id: str | None = None
    value: float | None = None


@dataclass(frozen=True)
class MissionResult:
    mission_id: str
    status: MissionStatus
    selected_goal_id: str | None
    selected_plan_id: str | None
    actions_executed: tuple[str, ...]
    final_beliefs: Mapping[str, BeliefEstimate]
    events: tuple[MissionEvent, ...]
