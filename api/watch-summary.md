# Watch Summary API Contract

## Current Status

No watch-summary API surface is implemented on `main`.

This page exists only to reserve ownership and identifiers before the M5
runtime lands. It does not pre-freeze behavior, payload shape, query semantics,
or Portal transport details.

## Reserved Ownership

| Surface | Reserved name | Runtime lane | Freeze lane | Reservation state |
| --- | --- | --- | --- | --- |
| MCP | `ebus.v1.watch.summary.get` | `ISSUE-GW-11` | `ISSUE-DOC-09` | identifier reserved now; behavior deferred, non-frozen |
| GraphQL | `watchSummary` | `ISSUE-GW-11` | `ISSUE-DOC-09` | identifier reserved now; behavior deferred, non-frozen |
| Portal | none yet | `ISSUE-GW-11`, `ISSUE-GW-14` | `ISSUE-DOC-10` | no Portal-specific identifier reserved here; behavior deferred, non-frozen |

## Deferred v1 Scope

The shared watch-summary lane reserves only the high-level topic area for the
future summary surface: activation counts, freshness classes, direct-apply
eligibility classes, and degraded capability markers.

## Not Frozen Yet

Until the runtime exists, `ISSUE-DOC-09` owns only the later freeze of the
shared MCP/GraphQL watch-summary contract after the M5 implementation lands.
That later freeze may define names, shape, and semantics for the shared
MCP/GraphQL contract.

Portal-specific watch-summary behavior stays entirely with `ISSUE-DOC-10`.
That later Portal lane owns any dedicated endpoint names, bootstrap flags, SSE
payloads, refresh cadence, and UI-facing semantics. This page does not assign
or freeze any of those Portal details.

## Current Discovery Rule

Until the runtime lands:

- [`mcp.md`](./mcp.md) documents only implemented MCP tools
- [`graphql.md`](./graphql.md) documents only implemented GraphQL schema
- [`portal.md`](./portal.md) documents only implemented Portal endpoints
- [`../architecture/observability.md`](../architecture/observability.md) and
  [`../deployment/full-stack.md`](../deployment/full-stack.md) remain the
  authoritative docs for current bus observability and passive-capability
  behavior
