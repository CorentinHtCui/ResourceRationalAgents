# AGENTS.md — Code Generation Harness

## Purpose

Generate code that is explainable, maintainable, and structurally predictable.
This repository follows domain-first Hexagonal Architecture. Treat architectural
boundaries as constraints, not suggestions.

This file is the operational entry point. Read `ARCHITECTURE.md` before changing
production code.

## Project configuration

Replace every placeholder before using this template in a project.

| Concern | Project value |
|---|---|
| Production source root | `src/` |
| Test root | `tests/` |
| Format command | `python -m ruff format --check .` |
| Lint command | `python -m ruff check .` |
| Type-check command | `python -m mypy src tests` |
| Focused test command | `python -m unittest tests.test_orchestrator -v` |
| Full test command | `python -m unittest discover -s tests -t . -v` |
| Build command | `python -m compileall -q src` |
| Architecture check command | `python tools/check_architecture.py` |

If a required command is not configured, report that limitation. Do not invent a
command or claim that the corresponding check passed.

## Sources of truth

Use this precedence when instructions conflict:

1. The user's current request and acceptance criteria.
2. Tests and public contracts that encode current behavior.
3. `ARCHITECTURE.md` for dependency and placement rules.
4. Existing code patterns within the affected business domain.
5. Other project documentation.

Do not silently change an established public contract to simplify an
implementation. Surface the conflict and explain the smallest viable choices.

## Required workflow

### 1. Inspect before designing

- Locate the affected business domain and its public entry points.
- Trace the current call path from inbound adapter to use case, domain logic,
  outbound port, and adapter as applicable.
- Search for existing ports, adapters, types, utilities, and tests before adding
  new ones.
- Identify the narrowest behavioral seam through which the change can be tested.

Do not infer that something is missing until repository search confirms it.

### 2. Classify the change

State which of these are affected:

- domain behavior;
- application use case;
- inbound port or adapter;
- outbound port or adapter;
- composition root;
- public contract;
- module boundary or dependency edge.

This classification determines placement and validation.

### 3. Explain the intended design

Before a non-trivial implementation, give a short explanation containing:

- the behavior being changed;
- the domain and architectural layers involved;
- the dependency path after the change;
- the test seam;
- any new abstraction and why it improves conceptual clarity.

Do not produce a long speculative design document for a small change.

### 4. Implement the narrowest coherent change

- Keep business rules in the domain layer.
- Keep use-case orchestration in the application layer.
- Keep protocols, frameworks, persistence, and external I/O in adapters.
- Keep construction and dependency injection in the composition root.
- Preserve existing public behavior unless the request explicitly changes it.
- Follow established naming and error-handling conventions in the affected domain.

Adjacent refactoring is allowed only when it is directly necessary to implement
the requested behavior, preserve an architectural boundary, or remove duplication
introduced by the change. Report broader cleanup opportunities without performing
them.

### 5. Validate proportionally

For generated production behavior:

- add or update focused tests through a public use-case API or port;
- add contract or integration coverage when an adapter changes;
- document public API purpose, inputs, outputs, and failure modes;
- run formatting, linting, type checks, focused tests, and the build as applicable;
- run the full test suite when the change has broad or cross-domain impact.

When module boundaries or dependency edges change, also run
`[ARCHITECTURE_CHECK_COMMAND]` and explain the dependency impact. The architecture
check is not mandatory for changes that provably leave boundaries and dependencies
unchanged.

Trivial renames, formatting changes, and mechanical refactors may omit new tests
or documentation when existing checks already cover the behavior. They must still
run the relevant existing checks.

Never weaken, delete, or bypass a failing check merely to obtain a passing result.

### 6. Report evidence

The completion report must state:

- what behavior changed;
- why the code belongs in the chosen locations;
- tests added or updated;
- commands run and their results;
- whether boundaries or dependency edges changed;
- remaining risks, assumptions, or unverified checks.

## Hexagonal boundary rules

The detailed model is defined in `ARCHITECTURE.md`. The non-negotiable summary is:

- organize by business domain first, then by architectural role;
- domain code has no dependencies on application, adapters, frameworks, or I/O;
- application code depends inward on domain code and declares ports for external
  capabilities;
- adapters depend on ports and translate between external representations and
  internal models;
- only the composition root selects concrete adapter implementations;
- cross-domain calls use explicitly published contracts, ports, or events;
- circular dependencies are forbidden;
- framework and transport types must not cross into domain code.

## New abstractions

New abstractions are allowed whenever they materially improve conceptual clarity,
even when only one implementation currently exists. Every new abstraction must
include a short rationale covering:

1. the concept it names or isolates;
2. why the existing structure cannot express that concept clearly;
3. the dependency edges it adds, removes, or redirects;
4. where it belongs under `ARCHITECTURE.md`;
5. why it is simpler to maintain than keeping the behavior local.

Do not create abstractions solely for hypothetical reuse, symmetry, or anticipated
future requirements.

## Explainability standards

- Prefer domain vocabulary over generic names such as `Manager`, `Helper`, or
  `Processor`.
- Make control flow and state transitions explicit.
- Keep functions and modules cohesive; split by responsibility, not arbitrary size.
- Validate and translate data at boundaries.
- Represent expected failures explicitly according to project conventions.
- Avoid hidden global state, service locators, and runtime dependency discovery.
- Comments explain non-obvious reasons, constraints, or tradeoffs. They do not
  narrate code that clear naming can explain.
- Public contracts document observable behavior rather than implementation detail.

## Stop conditions

Pause implementation and request clarification when:

- acceptance criteria permit materially different user-visible behavior;
- a requested shortcut would violate a hexagonal boundary;
- a public contract or persistent data shape must change but migration or
  compatibility expectations are unknown;
- the relevant validation command is destructive or requires authority not given;
- repository evidence contradicts the requested design.

When stopping, present the concrete evidence, the blocked decision, and a
recommended resolution.
