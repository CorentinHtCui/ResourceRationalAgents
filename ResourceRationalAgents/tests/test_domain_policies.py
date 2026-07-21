from __future__ import annotations

import unittest

from resource_rational_agents.planning.domain.adaptive import RecedingHorizonAdaptiveRule
from resource_rational_agents.planning.domain.models import (
    BeliefEstimate,
    FeedbackProfile,
    HighComputation,
    LowComputation,
)
from resource_rational_agents.planning.domain.voc import (
    HighVocPolicy,
    HighVocWeights,
    LowVocPolicy,
    LowVocWeights,
)


class BeliefTests(unittest.TestCase):
    def test_downward_evidence_is_retained(self) -> None:
        posterior = BeliefEstimate(100.0, 10.0).observe(20.0, 1.0)

        self.assertLess(posterior.mean, 100.0)
        self.assertGreater(posterior.mean, 20.0)
        self.assertLess(posterior.variance, 10.0)


class VocTests(unittest.TestCase):
    def test_high_formula_matches_paper_feature_split(self) -> None:
        policy = HighVocPolicy(HighVocWeights(0.25, 0.75, 1.0))
        computation = HighComputation("c", "g", 8.0, 12.0, 2.0)

        self.assertAlmostEqual(policy.score(computation, goal_count=2), 9.0)

    def test_low_formula_includes_subproblem_vpi_and_anticipated_cost(self) -> None:
        policy = LowVocPolicy(LowVocWeights(0.2, 0.3, 0.5, 2.0))
        computation = LowComputation("c", "g", 10.0, 20.0, 30.0, 4.0, 1, 3, 2, 3)

        self.assertAlmostEqual(policy.score(computation), 6.2)

    def test_non_positive_voc_is_not_worth_computing(self) -> None:
        policy = HighVocPolicy(HighVocWeights(0.5, 0.5, 1.0))
        computation = HighComputation("c", "g", 1.0, 1.0, 1.0)

        self.assertEqual(policy.score(computation, goal_count=1), 0.0)


class AdaptiveRuleTests(unittest.TestCase):
    def test_noisy_delayed_feedback_increases_hysteresis_and_reduces_batch(self) -> None:
        rule = RecedingHorizonAdaptiveRule()
        clean = rule.settings(FeedbackProfile(0.5, 0.5, 0.9, 1.0, 0.0, 0.1))
        noisy = rule.settings(FeedbackProfile(0.5, 0.5, 0.9, 0.2, 1.0, 0.1))

        self.assertGreater(noisy.switch_margin, clean.switch_margin)
        self.assertLess(noisy.execution_batch_size, clean.execution_batch_size)

    def test_uncertain_irreversible_consequence_increases_planning_budget(self) -> None:
        rule = RecedingHorizonAdaptiveRule()
        low_stakes = rule.settings(FeedbackProfile(0.1, 0.1, 1.0, 1.0, 0.0, 0.0))
        high_stakes = rule.settings(FeedbackProfile(1.0, 1.0, 0.0, 1.0, 0.0, 0.0))

        low_total = low_stakes.high_computation_budget + low_stakes.low_computation_budget
        high_total = high_stakes.high_computation_budget + high_stakes.low_computation_budget
        self.assertGreater(high_total, low_total)


if __name__ == "__main__":
    unittest.main()
