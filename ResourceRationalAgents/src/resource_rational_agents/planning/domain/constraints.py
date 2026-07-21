"""System-wide hard-constraint contracts and the authoritative judge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping, Protocol, Sequence

from resource_rational_agents.planning.domain.models import BeliefEstimate, ControllerPhase


class ConstraintScope(str, Enum):
    MISSION = "mission"
    GOAL = "goal"
    COMPUTATION = "computation"
    PLAN = "plan"
    ACTION = "action"


@dataclass(frozen=True)
class ConstraintContext:
    mission_id: str
    phase: ControllerPhase
    planning_remaining: int
    execution_remaining: int
    beliefs: Mapping[str, BeliefEstimate]


class ConstraintRule(Protocol):
    constraint_id: str
    description: str
    scopes: frozenset[ConstraintScope]

    def allows(self, candidate: object, context: ConstraintContext) -> bool: ...


@dataclass(frozen=True)
class RuleConstraint:
    """A human/operator constraint expressed as a deterministic boundary predicate."""

    constraint_id: str
    description: str
    scopes: frozenset[ConstraintScope]
    evaluator: Callable[[object, ConstraintContext], bool]

    def allows(self, candidate: object, context: ConstraintContext) -> bool:
        return self.evaluator(candidate, context)


@dataclass(frozen=True)
class ConstraintViolation:
    constraint_id: str
    description: str
    scope: ConstraintScope


@dataclass(frozen=True)
class ConstraintDecision:
    allowed: bool
    violations: tuple[ConstraintViolation, ...]


class ConstraintJudge:
    """The single hard-constraint authority delivered to every controller boundary."""

    def __init__(self, constraints: Sequence[ConstraintRule] = ()) -> None:
        ids = [constraint.constraint_id for constraint in constraints]
        if len(ids) != len(set(ids)):
            raise ValueError("constraint ids must be unique")
        self._constraints = tuple(constraints)

    def evaluate(
        self, scope: ConstraintScope, candidate: object, context: ConstraintContext
    ) -> ConstraintDecision:
        violations = tuple(
            ConstraintViolation(rule.constraint_id, rule.description, scope)
            for rule in self._constraints
            if scope in rule.scopes and not rule.allows(candidate, context)
        )
        return ConstraintDecision(not violations, violations)

    def allowed(
        self, scope: ConstraintScope, candidate: object, context: ConstraintContext
    ) -> bool:
        return self.evaluate(scope, candidate, context).allowed

