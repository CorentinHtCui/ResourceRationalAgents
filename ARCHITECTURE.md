# ARCHITECTURE.md — Domain-First Hexagonal Architecture

## Architectural objective

Make code generation reliable by giving every business concept a predictable home
and limiting the dependency edges an implementation may create.

The architecture separates business policy from delivery mechanisms, frameworks,
storage, and external services. Dependencies point toward stable business concepts;
external technologies attach through ports and adapters.

## Repository shape

Use this domain-first structure as the default. Adapt folder names to the language
only when the dependency roles remain unambiguous.

```text
[SOURCE_ROOT]/
  <business-domain>/
    domain/
      entities/
      value-objects/
      services/
      events/
    application/
      use-cases/
      ports/
        inbound/
        outbound/
    adapters/
      inbound/
      outbound/
    composition/
    public/
  shared/
    domain/
    contracts/
  composition/
```

Create only folders that contain real concepts. Empty structural folders are not
required. `shared/` is reserved for concepts with demonstrated cross-domain meaning;
it is not a miscellaneous utility directory.

## Dependency model

An arrow means “may import or call.”

```text
Inbound Adapter ──→ Inbound Port / Application Use Case ──→ Domain
                          │
                          └──→ Outbound Port ←── Outbound Adapter

Composition Root ──→ Application + Adapters
```

The application owns the ports. Outbound adapters implement those ports. The
application never selects or imports a concrete adapter.

### Allowed dependency edges

| Source | May depend on |
|---|---|
| Domain | Its own domain code; deliberately shared domain primitives |
| Application | Its domain; application-owned inbound/outbound ports; published contracts |
| Inbound adapter | Inbound ports/use cases; adapter-local framework and transport code |
| Outbound adapter | Outbound ports; adapter-local technology code; mapping types needed at the boundary |
| Domain composition | Application and adapters from that domain for wiring only |
| Application-wide composition | Domain composition modules and application entry points for wiring only |
| Public contracts | Stable data and protocol definitions; no concrete adapter implementation |
| Tests | The subject under test plus test doubles and fixtures |

### Forbidden dependency edges

- Domain to application, adapters, composition, frameworks, databases, networks,
  filesystems, clocks, random generators, or process environment.
- Application to concrete adapters or framework-specific types.
- One adapter to another adapter.
- Business logic inside adapters or the composition root.
- Direct imports into another domain's internal folders.
- Circular dependencies between any modules or domains.
- Runtime service lookup that hides dependencies from constructors or function
  signatures.

Time, randomness, identifiers, persistence, messaging, and external APIs are
external capabilities when business behavior depends on them. Model them as
outbound ports and inject them.

## Layer responsibilities

### Domain

The domain contains business meaning and invariants:

- entities and value objects;
- state transitions;
- domain policies and calculations;
- domain services when behavior does not belong to one entity;
- domain events expressed in business vocabulary.

Domain behavior must be deterministic given explicit inputs. Domain types do not
contain HTTP, database, UI, serialization, or dependency-injection concepts.

### Application

The application layer exposes and coordinates use cases:

- authorize and sequence a business operation;
- load or save through outbound ports;
- invoke domain behavior;
- establish transaction or idempotency boundaries through abstractions;
- map domain outcomes to use-case results;
- define inbound and outbound ports.

Application code may coordinate policy but must not duplicate domain invariants.

### Inbound ports and adapters

Inbound ports describe operations offered by the application. Inbound adapters
translate an external trigger into a port call, for example:

- HTTP or RPC handlers;
- command-line commands;
- message consumers;
- scheduled jobs;
- user-interface controllers.

Inbound adapters validate transport shape, authenticate using established project
mechanisms, translate values, call one or more use cases, and translate results.
They do not decide business policy.

### Outbound ports and adapters

Outbound ports describe capabilities required by the application, using domain
language rather than vendor terminology. Examples include repositories, message
publishers, clocks, identity generators, and external service gateways.

Outbound adapters implement those capabilities using a database, filesystem,
network service, SDK, or platform API. They own technology-specific mapping,
timeouts, retries, and error translation according to the port's contract.

### Composition roots

Composition roots construct concrete adapters and inject them into application
services or use cases. Wiring is their only responsibility.

Do not place feature logic, fallback policy, validation, or technology mapping in a
composition root. Prefer one domain composition module plus a thin application-wide
root when the program contains multiple domains.

### Public contracts and cross-domain communication

Another domain may use only an explicitly published contract. Prefer, in order:

1. an inbound application port for a synchronous capability;
2. a published domain/application event for asynchronous collaboration;
3. a stable contract type when data must cross the boundary.

Do not import another domain's entities, internal use cases, repositories, or
adapters. If two domains require orchestration, place it in an application-level
workflow that calls their published ports. Reject any design that creates a domain
cycle.

## Designing ports

A good port:

- names one business capability;
- uses domain or application-owned types;
- exposes only operations required by use cases;
- defines observable success and failure semantics;
- avoids transport, database, SDK, and framework types;
- can be replaced by a deterministic test double.

Do not mirror an entire vendor SDK or database client behind an interface. Model the
capability the application needs.

## New abstraction decision record

New abstractions may be introduced for conceptual clarity with one current
implementation. Add the rationale to the change description using this form:

```text
Abstraction: <name>
Concept isolated: <business or architectural concept>
Clarity gained: <why the prior placement or API obscured the concept>
Placement: <domain/application port/adapter/composition/public contract>
Dependency impact: <edges added, removed, or redirected>
Alternative rejected: <why keeping the behavior local was less maintainable>
```

The abstraction is invalid if it exists only for hypothetical reuse, creates a
forbidden edge, leaks technology inward, or lacks a stable concept to name.

## Change placement guide

| Change | Placement |
|---|---|
| Business invariant or calculation | Domain entity, value object, or domain service |
| User/application action | Application use case and inbound port |
| Required external capability | Application-owned outbound port |
| HTTP, CLI, queue, scheduler, or UI translation | Inbound adapter |
| Database, filesystem, vendor API, or message broker integration | Outbound adapter |
| Object construction and dependency injection | Composition root |
| Cross-domain callable surface | Published inbound port or public contract |
| Cross-domain notification | Published event |

If a change appears to belong in several layers, separate business policy from
translation and I/O. Do not collapse boundaries for convenience.

## Testing strategy

Test through stable seams rather than private implementation details.

| Subject | Required evidence |
|---|---|
| Domain rule | Fast unit tests using domain values only |
| Application use case | Tests through its inbound port with outbound port fakes |
| Outbound adapter | Contract/integration tests proving it satisfies its port |
| Inbound adapter | Translation, validation, authorization, and error-mapping tests |
| Cross-domain workflow | Tests through published ports or events |
| Critical user behavior | Focused end-to-end test when lower seams cannot prove it |

An adapter contract test should be reusable across implementations where practical.
Do not mock domain logic. Do not assert private call sequences unless ordering is an
observable requirement.

## Architecture validation

`[ARCHITECTURE_CHECK_COMMAND]` must mechanically reject forbidden imports or
dependency edges.

Run it when a change:

- moves code between architectural roles;
- adds a module, package, port, adapter, or public contract;
- changes imports across modules or business domains;
- changes composition or dependency injection;
- introduces a new external dependency used by production code.

When none of these occur, the completion report may state that architecture checks
were not run because boundaries and dependency edges were unchanged.

## Boundary-change checklist

Before accepting a boundary or dependency change, verify:

- the business domain remains the primary unit of organization;
- every new edge appears in the allowed dependency table;
- domain and application code remain technology-independent;
- external data is validated and translated at an adapter boundary;
- composition remains explicit;
- cross-domain internals are not imported;
- no cycle is introduced;
- the new abstraction rationale and dependency impact are recorded;
- `[ARCHITECTURE_CHECK_COMMAND]` passes;
- tests cover the behavior through the narrowest stable seam.
