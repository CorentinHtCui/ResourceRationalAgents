# Project environment rules

This folder represents the interactive environment modified by the agent. The
root `AGENTS.md` and `ARCHITECTURE.md` still apply to all production work here.

High and Low may inspect the environment only through an application-owned
observation port. Object-level mutations may occur only through the execution port
after Meta has received a feasible plan and the shared constraint judge has
approved the action.

Every project operation must return structured feedback containing its outcome,
the evidence it produced, and whether the mission is complete. Do not attribute an
external change to the agent without evidence. Prefer bounded, reversible actions
and preserve enough information to update the counterfactual baseline defined in
`../DecisionRule.md`.

Project adapters translate filesystem, process, network, framework, or tool data.
They contain no goal-selection, VOC, constraint, or switching policy.

