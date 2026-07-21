"""Adaptive, resource-bounded receding-horizon policy.

This is an explicit operationalization of DecisionRule.md rather than a claim
that the heuristic itself appears in the BMPS paper. It spends more planning
effort on uncertain, consequential, hard-to-reverse decisions; increases switch
hysteresis for noisy/delayed feedback; and reduces the execution batch when
feedback is weak, delayed, or actions are difficult to reverse.
"""

from __future__ import annotations

from dataclasses import dataclass

from resource_rational_agents.planning.domain.models import FeedbackProfile


@dataclass(frozen=True)
class AdaptiveSettings:
    high_computation_budget: int
    low_computation_budget: int
    switch_margin: float
    execution_batch_size: int


@dataclass(frozen=True)
class RecedingHorizonAdaptiveRule:
    base_planning_budget: int = 4
    maximum_planning_budget: int = 20
    base_switch_margin: float = 1.0
    maximum_execution_batch: int = 5

    def __post_init__(self) -> None:
        if self.base_planning_budget < 1:
            raise ValueError("base_planning_budget must be positive")
        if self.maximum_planning_budget < self.base_planning_budget:
            raise ValueError("maximum planning budget must cover the base budget")
        if self.base_switch_margin < 0 or self.maximum_execution_batch < 1:
            raise ValueError("adaptive settings must be non-negative")

    def settings(self, profile: FeedbackProfile) -> AdaptiveSettings:
        risk_load = profile.consequence * profile.uncertainty * (2.0 - profile.reversibility)
        information_discount = 1.0 / (1.0 + profile.information_cost)
        total = round(self.base_planning_budget * (1.0 + risk_load) * information_discount)
        total = max(1, min(self.maximum_planning_budget, total))

        high_budget = max(1, round(total * 0.4))
        low_budget = max(1, total - high_budget)

        noise = 1.0 - profile.feedback_quality
        bounded_delay = min(profile.feedback_delay, 1.0)
        switch_margin = self.base_switch_margin * (1.0 + noise + bounded_delay)

        batch_factor = (
            profile.feedback_quality
            * max(profile.reversibility, 0.1)
            / (1.0 + profile.feedback_delay)
        )
        batch_size = round(self.maximum_execution_batch * batch_factor)
        batch_size = max(1, min(self.maximum_execution_batch, batch_size))

        return AdaptiveSettings(high_budget, low_budget, switch_margin, batch_size)

