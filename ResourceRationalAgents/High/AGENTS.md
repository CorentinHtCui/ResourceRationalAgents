# High controller rules

High operates only on the goal-selection metalevel MDP. It does not execute
project actions or plan detailed paths.

For each constraint-approved high-level computation, calculate:

```text
VOC_H = w1 * VOI1_H + w2 * VPI_H - w3 * cost_H
```

Select one computation with maximum positive VOC, perform it through the project
observation port, and send all evidence to Meta. When no permitted computation
has positive VOC or the computation budget is exhausted, emit `GoalSelected` for
the feasible goal with maximum current expected value.

The incumbent goal value may be used for reporting, but never as a gate that
discards downward evidence. Hard constraints gate goal and computation candidates
before optimization. High must not import project adapters or Low internals.

