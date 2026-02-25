# MCP-first Development Model

## Purpose

This document defines how MCP is used as the primary development interface in Helianthus.
It also centralizes the architecture decisions that were previously duplicated as local ADR files in runtime repositories.

## Delivery Order

New capability rollout order is mandatory:

1. MCP-first prototype and stabilization
2. GraphQL parity on top of stable MCP contracts
3. Consumer rollout (Home Assistant and other clients) only after GraphQL parity gates are green

## MCP Contract Baseline

Core MCP tools (`ebus.v1.*`) use a stable envelope:

- `meta`:
  - `contract`
  - `consistency`
  - `data_timestamp`
  - `data_hash`
- `data`
- `error` (null or structured error)

Breaking contract changes require a new major namespace (`ebus.v2.*`).

## Determinism Rules

- Stable ordering for list-like outputs
- Stable schema and field naming for `ebus.v1.*`
- Snapshot mode must produce stable `data_hash` for identical input
- Golden snapshots are required for schemas and representative outputs

Low-level deterministic helpers are implemented first in shared libraries (`helianthus-ebusgo/determinism`) and then consumed by gateway MCP features. This keeps idempotency, retry behavior, and canonical hashing semantics consistent before GraphQL parity.

## Invoke Safety Model

`ebus.v1.rpc.invoke` must enforce explicit intent and guardrails:

- `intent`: `READ_ONLY` or `MUTATE`
- `allow_dangerous=true` for mutating or unknown methods
- `idempotency_key` for mutating intent

Unknown mutability defaults to safe denial unless explicitly allowed.

## Graduation Gates: MCP -> GraphQL

A capability may graduate to GraphQL only when:

1. It is implemented as core stable MCP (`ebus.v1.*`)
2. Determinism + contract + golden tests are green
3. MCP <-> GraphQL parity tests are green

## Experimental Surface and Cleanup

Experimental tools live under `ebus.experimental.*` and are not consumer-facing.
At cycle end, each experimental tool must be:

- promoted to core stable, or
- removed, or
- moved to internal-only with written justification

No temporary/junk tools remain in the showroom MCP surface.

## ADR Set (Centralized)

This document supersedes duplicated local ADR notes previously added to runtime repositories.
Canonical decisions are:

1. MCP-first governance
2. MCP v1 contract envelope
3. Parity gates and cleanup policy
4. Invoke safety and idempotency

## Heat-Source Class Extension Contract (BAI -> VWZ)

To keep implementations equivalent across heat-source classes, each class design MUST document:

1. Domain boundary:
- source-class ownership (`HEAT_SOURCE` vs `REGULATOR`)
- explicit deny rules for cross-domain registers.

2. Plane model:
- cross-device discovery planes vs class-specific planes
- stable plane/group naming and ordering.

3. Snapshot policy:
- total timeout, per-plane budget, and partial mode semantics
- required response fields for partial failures (`error_planes`, `completed_planes`).

4. Scheduling policy:
- queue depth limit
- starvation prevention thresholds
- FIFO behavior within equal effective priority.

5. Common-core governance:
- versioned common-core contract (`common_core_vN`)
- non-regression rule for stable APIs.

No new heat-source class (including VWZ) is considered ready for implementation until these sections are specified in docs with normative behavior (`MUST/SHOULD/MUST NOT`).
