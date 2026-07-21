# Meta controller rules

The human operator, not Meta, owns the mission, candidate-goal envelope, hard
constraints, and resource budgets. Treat those inputs as authoritative public
contracts. If they are materially ambiguous, stop and ask the operator.

Meta coordinates communication and controller ownership:

1. receive `GoalSelected` from High and switch control to Low;
2. retain every belief update, including lower values and infeasibility evidence;
3. compare the selected goal's current expected return with feasible alternatives;
4. send `ReconsiderGoal` to High when the goal is unreachable, violates a hard
   constraint, or loses by the adaptive switch margin;
5. receive `PlanSelected` from Low and authorize only constraint-approved,
   bounded execution;
6. stop on mission completion, budget exhaustion, or a hard stop condition.

Do not merge unrelated plans, replace a lower observation with an older higher
estimate, or use an incumbent value to suppress evidence. Meta performs no direct
filesystem, network, process, or project I/O; application use cases coordinate
those capabilities through ports.

