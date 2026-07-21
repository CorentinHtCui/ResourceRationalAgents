# Low controller rules

Low operates on the goal-achievement metalevel MDP for the goal selected by High.
Use `DecisionRule.md`, beginning at its practical execution algorithm, as a
real-life context and feedback reference. It does not replace the MDP.

For each constraint-approved low-level computation, calculate:

```text
VOC_L = w1 * VOI1_L + w2 * VPI_L + w3 * VPI_sub_L
        - w4 * anticipated_cost_L
```

Select one computation at a time and update the belief state. Do not generate an
entire decision tree before pruning, and do not substitute a Markov chain for a
decision process. When no permitted computation has positive VOC, emit the best
feasible `PlanSelected` candidate.

Send `ReconsiderGoal` to Meta immediately when evidence makes the goal unreachable,
prohibitively costly, or constraint-violating. Validate cumulative plan constraints
and action preconditions. Low proposes plans; the application execution use case
performs actions through a project execution port.

