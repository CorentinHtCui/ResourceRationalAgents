# Resource Rational Agents

This repository is an executable reference harness for a human-directed software
agent. The human operator supplies the mission, candidate goals, hard constraints,
and resource budgets. The system then uses hierarchical metareasoning to decide
what to compute, when to stop planning, when to switch goals, and which bounded
project action to execute.

The implementation follows the decomposition in `improveing human.pdf` while
using the practical situation and feedback guidance in `DecisionRule.md` as an
explicitly documented heuristic layer.

## Control loop

1. **High** selects one goal-value computation with maximum positive high-level
   VOC. If no computation has positive VOC, it selects the feasible goal with the
   highest current expected value.
2. **Meta** switches control to Low. It does not define the mission and does not
   discard evidence; the human operator owns mission and constraints.
3. **Low** selects one within-goal computation with maximum positive low-level
   VOC. If no computation has positive VOC, it selects the best feasible plan.
4. **Meta** returns control to High whenever the current goal is unreachable,
   violates a constraint, or falls below a feasible alternative by the adaptive
   switch margin.
5. **Execution** rechecks each action with the shared constraint judge, executes
   a bounded batch through the project port, applies feedback to the belief state,
   and replans at the next horizon.

This produces the approved loop:

```text
Human mission + constraints
           |
           v
High -> Meta -> Low -> Meta -> High
                   |
                   v
          bounded project execution
                   |
                   +---- observations ----+
```

## Value-of-computation policies

High and Low use different paper-aligned approximations:

```text
VOC_H = w1 * VOI1_H + w2 * VPI_H - w3 * cost_H

VOC_L = w1 * VOI1_L + w2 * VPI_L + w3 * VPI_sub_L
        - w4 * cost_L(c, g, w)
```

The Low cost is calculated from the cost of one computation multiplied by the
weighted number of nodes relevant to `VOI1_L`, `VPI_L`, and `VPI_sub_L`. It
therefore represents the computations assumed by the information features, not
only the current computation. Weight validation enforces the
probability-simplex and cost-weight bounds described in the paper. Production
weights should be learned or calibrated for the target environment; the included
weights are deterministic demonstration defaults.

## Adaptive rule

`RecedingHorizonAdaptiveRule` implements a bounded heuristic derived from
`DecisionRule.md`:

- uncertainty, consequence, and irreversibility increase the useful planning
  budget;
- information cost decreases it;
- noisy or delayed feedback increases goal-switch hysteresis to avoid thrashing;
- weak, delayed feedback and low reversibility reduce the execution batch size.

Hard constraints remain gates and are never converted into utility penalties.
The same `ConstraintJudge` is delivered to goal, computation, plan, and action
boundaries.

## Architecture

Production code is under `src/resource_rational_agents/planning/` and is organized
by the planning business domain, then by hexagonal role:

```text
domain/       beliefs, constraints, VOC, adaptive and controller policies
application/  mission orchestration and outbound ports
adapters/     external project observation/execution implementations
composition/  explicit construction and dependency injection
```

The root `Meta/`, `High/`, `Low/`, and `project/` folders contain scoped agent
rules. They describe runtime roles; they are not separate business domains.

## Run

The package has no runtime dependencies. From an installed editable checkout:

```powershell
python -m pip install -e .
resource-rational-agents
```

Without installing it:

```powershell
$env:PYTHONPATH = "src"
python -m resource_rational_agents.cli
```

The demonstration begins with an apparently valuable ambitious goal, retains
downward Low-level evidence about its true path return, switches to a smaller
usable goal, and executes that goal's verified plan.

## Validate

```powershell
python -m compileall -q src
python -m unittest discover -s tests -t . -v
python tools/check_architecture.py
```

Install the optional `dev` dependencies to run formatting, linting, and static
type checking:

```powershell
python -m pip install -e ".[dev]"
python -m ruff format --check .
python -m ruff check .
python -m mypy src tests
```

##Prompt
Read and follow:
Meta/AGENTS.md
High/AGENTS.md
Low/AGENTS.md
project/AGENTS.md
DecisionRule.md, especially the practical algorithm beginning at line 1405
Human mission:
Build a usable command-line calculator under project/calculator.
Candidate goals:
Basic calculator:
addition, subtraction, multiplication, division, parentheses,
clear errors, and automated tests.

Scientific calculator:
everything above plus trigonometry, logarithms, powers, and memory.

Hard constraints:
Use only the Python standard library.
Do not use eval().
Division by zero must return an explicit error.
Business calculation logic must be separate from the CLI.
Add automated tests through the public calculator API.
Run only bounded and reversible project actions.
Do not modify files outside project/calculator.
Planning budget:
8 metalevel computations.
Execution budget:
10 bounded actions.
Use the control loop:
High -> Meta -> Low -> Meta -> High.
Record:
each computation and its VOC;
belief updates, including lower values;
constraint decisions;
goal switches;
selected plan;
executed actions and test results.
Now inspect the repository and implement the mission.