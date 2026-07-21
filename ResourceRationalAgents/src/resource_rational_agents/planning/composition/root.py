"""Composition root for the in-memory reference application."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from resource_rational_agents.planning.adapters.in_memory_project import (
    GoalScenario,
    InMemoryProjectAdapter,
)
from resource_rational_agents.planning.application.orchestrator import MissionOrchestrator
from resource_rational_agents.planning.domain.adaptive import RecedingHorizonAdaptiveRule
from resource_rational_agents.planning.domain.constraints import ConstraintJudge, ConstraintRule
from resource_rational_agents.planning.domain.controllers import (
    HighController,
    LowController,
    MetaController,
)
from resource_rational_agents.planning.domain.voc import (
    HighVocPolicy,
    HighVocWeights,
    LowVocPolicy,
    LowVocWeights,
)


@dataclass(frozen=True)
class InMemoryHarness:
    orchestrator: MissionOrchestrator
    project: InMemoryProjectAdapter


def build_in_memory_harness(
    scenarios: Sequence[GoalScenario],
    constraints: Sequence[ConstraintRule] = (),
    high_weights: HighVocWeights = HighVocWeights(0.5, 0.5, 1.0),
    low_weights: LowVocWeights = LowVocWeights(0.34, 0.33, 0.33, 1.0),
    adaptive_rule: RecedingHorizonAdaptiveRule = RecedingHorizonAdaptiveRule(),
) -> InMemoryHarness:
    judge = ConstraintJudge(constraints)
    project = InMemoryProjectAdapter(scenarios)
    high = HighController(HighVocPolicy(high_weights), judge)
    low = LowController(LowVocPolicy(low_weights), judge)
    meta = MetaController(judge)
    orchestrator = MissionOrchestrator(
        high,
        low,
        meta,
        adaptive_rule,
        judge,
        project,
        project,
    )
    return InMemoryHarness(orchestrator, project)

