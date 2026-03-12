# Watch Summary API Contract

## Current Status

No watch-summary API surface is implemented on `main`.

This page exists because `ISSUE-DOC-02` must reserve the cross-surface
watch-summary contract before M5 without pretending the contract is already
frozen.

## Reserved Ownership

| Surface | Reserved name | Runtime lane | Freeze lane | State |
| --- | --- | --- | --- | --- |
| MCP | `ebus.v1.watch.summary.get` | `ISSUE-GW-11` | `ISSUE-DOC-09` | deferred, non-frozen |
| GraphQL | `watchSummary` | `ISSUE-GW-11` | `ISSUE-DOC-09` | deferred, non-frozen |
| Portal | none yet | `ISSUE-GW-11`, `ISSUE-GW-14` | `ISSUE-DOC-10` | deferred, non-frozen |

## Deferred v1 Scope

When the M5 runtime exists, the shared watch-summary contract is expected to
cover:

- activation counts
- freshness classes
- direct-apply eligibility classes
- degraded capability markers

Those topic names come from
`observe-first-bus-observability.implementing/15-execution-m2-m5.md`. They
reserve the topic area only; they do not freeze field names, output shape,
query filters, or delivery semantics on `main`.

## Not Frozen Yet

The following details are intentionally deferred to `ISSUE-DOC-09` after
`ISSUE-GW-10`, `ISSUE-GW-11`, and `ISSUE-GW-12` land:

- query-on-gap truth table
- scheduler and shadow-cache interaction
- observe-first freshness profiles
- snapshot skew and notification latency budgets across GraphQL subscriptions,
  Portal SSE, and query reads
- shadow write-order and invalidation-epoch semantics
- breaker-contention limits and feature-flag validity rules
- cold-start observe-first behavior and invalidation semantics

## Current Discovery Rule

Until the runtime lands:

- [`mcp.md`](./mcp.md) documents only implemented MCP tools
- [`graphql.md`](./graphql.md) documents only implemented GraphQL schema
- [`portal.md`](./portal.md) documents only implemented Portal endpoints
- [`../architecture/observability.md`](../architecture/observability.md) and
  [`../deployment/full-stack.md`](../deployment/full-stack.md) remain the
  authoritative docs for current bus observability and passive-capability
  behavior
