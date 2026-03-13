# Bus Observability v2

## Status

- State: frozen through the M4 observe-first watch architecture closure on
  docs `main`
- Frozen owners:
  - `ISSUE-DOC-06` for MCP
  - `ISSUE-DOC-07` for GraphQL parity wording
  - `ISSUE-DOC-08` for M4 watch-layer architecture wording
- Later owner:
  - `ISSUE-DOC-09` for M5 watch-summary and scheduler/shadow public-surface
    freeze

## Scope

This document is the architecture anchor for whole-bus observability in the
observe-first rollout.

This document now freezes:

- M2 MCP wording needed by merged `ISSUE-GW-04`
- M3 GraphQL parity wording needed by merged `ISSUE-GW-05`
- M4 observe-first watch-layer architecture wording needed by merged
  `ISSUE-GW-06` through `ISSUE-GW-09`, including:
  - `WatchCatalog`/watch-observation evidence model
  - bounded `ShadowCache` architecture baseline and feature-flag normalization
  - family-policy routing and runtime outcomes
  - retained-active fallback wording constrained to policy/watch evidence

This document still does not freeze Portal/watch-summary, scheduler/shadow
behavior, or docs-stage1 cleanup work. The detailed GraphQL schema and
nullability contract live in [`../api/graphql.md`](../api/graphql.md).

## Invariants

- `ebus.v1.bus.*` remains a bus-observability namespace, not a semantic
  namespace.
- M2 MCP and M3 GraphQL both expose bounded summaries and bounded retained lists
  only.
- Busy-time and periodicity timing quality must remain explicit whenever the
  runtime lacks true wire timestamps.
- Whole-bus passive capability state remains explicit even when bounded
  retained history still exists.
- B524 `state_default` behavior remains descriptor-backed/policy-backed; this
  document does not permit request-shape-only promotion semantics.
- Retained-active fallback is architectural evidence reuse, not a standalone
  selector heuristic.

## M4 Observe-First Watch Baseline

Merged `ISSUE-GW-06` through `ISSUE-GW-09` establish the M4 architecture
baseline for observe-first watch behavior:

- `WatchCatalog` provides descriptor-backed key semantics (`state`, `config`,
  correlation policy, direct-apply policy) for canonical watch keys.
- `ShadowCache` is bounded and policy-gated; it is not an unbounded write
  journal.
- Observe-first feature flags are normalized into a coherent runtime
  configuration before policy evaluation.
- Family-policy routing is evaluated per transaction and carried into runtime
  adjudication paths.

### Runtime Outcome Classes

At architecture level, passive adjudication outcomes are distinct:

- direct-apply-eligible paths (`state_default`, `config_opt_in`,
  `energy_merge_only`) are runtime third-party eligible under the family-policy
  verdict
- `record/invalidate` paths are runtime third-party eligible without implying
  direct state application
- observability-only paths are retained for evidence and diagnostics but do not
  imply runtime application

### B524 Descriptor-Backed Rule

For B524, `state_default` eligibility is descriptor-backed and policy-backed.
`catalog_miss`, inactive keys, config keys, write/timer forms, or mismatched
policy evidence do not become `state_default` eligible.

Retained-active fallback wording in this document is bounded to retained active
fingerprints that already carry compatible policy evidence; it is not a
request-shape override.

## Degraded Behavior

- When passive support is unavailable or still warming up, MCP surfaces keep
  publishing explicit capability, warmup, degraded, and timing-quality state.
- The same explicit-state rule applies to GraphQL `busSummary`, `busMessages`,
  and `busPeriodicity`; retained list items do not imply current passive
  availability.
- Busy-time and periodicity are unavailable, not synthetic zeroes, when passive
  timing is unavailable.
- Retained recent-message and periodicity history may still be visible during
  passive outage or reset recovery, but the top-level status remains the source
  of truth for current capability and timing state.

## MCP Public Surface

The observe-first MCP public surface is intentionally split from the semantic
MCP surface:

- `ebus.v1.bus.summary.get`
- `ebus.v1.bus.messages.list`
- `ebus.v1.bus.periodicity.list`

Reasons for the split:

- these tools expose bus evidence, transport capability, bounded traffic
  history, and timing-quality metadata
- semantic MCP tools expose protocol-agnostic projected state such as zones,
  DHW, and energy totals
- keeping the namespaces separate prevents raw bus-observability contracts from
  being mistaken for stable semantic payloads

Current registration rule:

- the bus tools are advertised only when the runtime wires a real bus
  observability provider into the MCP server
- a semantic-only MCP server does not list `ebus.v1.bus.*`

## GraphQL Public Surface

The merged M3 GraphQL parity surface mirrors the same bounded store model
through:

- `busSummary`
- `busMessages(limit: Int)`
- `busPeriodicity(limit: Int)`

GraphQL-specific invariants:

- the list roots preserve the same bounded-store semantics as MCP: `count` and
  `capacity` describe the retained store, while `limit` truncates only the
  returned newest suffix
- top-level `status` remains the source of truth for availability, warmup,
  degraded, and timing-quality state even when retained items remain visible
- the current unwired runtime returns zero-value wrappers with `status: null`
  rather than treating these roots as missing semantic fields
- detailed schema shape, field nullability, and encoding rules are frozen in
  [`../api/graphql.md`](../api/graphql.md)

## Busy-Time and Timing Model

### Current M2 Freeze

- `bus.summary.get` is the M2 MCP owner for busy-time/timing capability
  exposure.
- M2 does not publish a dedicated numeric busy-ratio MCP payload. The frozen
  public contract is the summary status plus explicit timing-quality markers.
- `status.timing_quality.busy` and `status.timing_quality.periodicity` track the
  passive timing-quality class used by current whole-bus observe-first
  accounting.

### Timing-Quality Semantics

- The merged `GW-04` runtime currently proves two timing-quality values on the
  MCP surface: `estimated` and `unavailable`.
- `estimated` means the runtime is using gateway-side observation timestamps on
  buffered transports rather than true wire timestamps.
- `unavailable` means the runtime cannot make a timing claim for that channel
  at all.
- M2 may not imply wire-time precision on active, passive, busy-time, or
  periodicity fields unless a later runtime milestone and paired doc update add
  that proof.

### Capability and Warmup State

- `status.capability.passive_state` and `status.warmup.state` use the bounded
  state set `unavailable | warming_up | available`.
- Current passive unavailability reasons exposed by MCP are bounded to:
  `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`,
  `unsupported_or_misconfigured`, and `capability_withdrawn`.
- `status.degraded.reasons` may include those passive unavailability reasons and
  `dedup_degraded`.

## Periodicity Model

### Current M2 Freeze

- `bus.periodicity.list` exposes a bounded retained list of periodicity tuple
  summaries, not an unbounded tuple history.
- The list response always carries top-level `status`, `count`, and `capacity`
  so consumers can distinguish retained history from current passive health.
- Per-tuple identity is carried by `source_bucket`, `target_bucket`, `primary`,
  `secondary`, and `family`.

### Per-Tuple State

- The merged `GW-04` runtime currently emits per-tuple periodicity states
  `warming_up` and `available`.
- Per-tuple state is not a substitute for overall passive capability state.
  Overall availability still comes from the top-level summary/list `status`.
- Optional interval fields (`last_interval`, `mean_interval`, `min_interval`,
  `max_interval`) remain omitted until the runtime has a value to publish.

### Retention and Bounds

- The recent-message ring and periodicity tuple store are both bounded.
- `count` reports current retained occupancy; `capacity` reports configured
  store capacity.
- Supplying `limit` truncates the returned slice to the newest retained items.
  Omitting `limit` returns all retained items and nothing more.

## Unsupported or Unproven Cases

- This file does not own the detailed GraphQL schema; it owns only the shared
  architecture invariants behind the MCP + GraphQL parity surfaces.
- No Portal/watch-summary naming or behavior is frozen in this file.
- No M5 watch-summary contract or scheduler/shadow/query-on-gap public contract
  is frozen in this file.
- No exact wire-timestamp guarantee is frozen for current transports.
- No dedicated numeric busy-time MCP payload is frozen in M2.

## Evidence

- Runtime implementation: [Project-Helianthus/helianthus-ebusgateway#376](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/376)
- Merged PR: [Project-Helianthus/helianthus-ebusgateway#377](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/377)
- Merge commit: `3daf4beed9d6406f7af52869eea1c53ef14f2f62`
- GraphQL runtime implementation: [Project-Helianthus/helianthus-ebusgateway#378](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/378)
- Merged GraphQL PR: [Project-Helianthus/helianthus-ebusgateway#379](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/379)
- GraphQL merge commit: `83e9c7b1ba927a282d87599269e91be817ff3582`
- Watch-catalog architecture implementation: [Project-Helianthus/helianthus-ebusgateway#380](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/380)
- Merged watch-catalog PR: [Project-Helianthus/helianthus-ebusgateway#381](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/381)
- Watch-catalog merge commit: `873c970459d1933ba50638df5e6fb349a6a9a3a2`
- Shadow-cache architecture implementation: [Project-Helianthus/helianthus-ebusgateway#382](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/382)
- Merged shadow-cache PR: [Project-Helianthus/helianthus-ebusgateway#385](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/385)
- Shadow-cache merge commit: `9e9e6904e0337812ffa87591a83ad6f4a5c0ea44`
- Feature-flag architecture implementation: [Project-Helianthus/helianthus-ebusgateway#386](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/386)
- Merged feature-flag PR: [Project-Helianthus/helianthus-ebusgateway#387](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/387)
- Feature-flag merge commit: `23e46011f3c57d08148cf3cdd51acd6958303f90`
- Family-policy architecture implementation: [Project-Helianthus/helianthus-ebusgateway#388](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/388)
- Merged family-policy PR: [Project-Helianthus/helianthus-ebusgateway#389](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/389)
- Family-policy merge commit: `db09bbae687912a16fbc9f0a2f3a5616b84931e8`
- Gateway workspace proof artifact (outside this docs repo; from a `Project-Helianthus/helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260312T175648Z-pr377-gw04-26ee758-passive-p01-p06-recovery/index.json`
  with `P01..P06 = pass`
- Gateway workspace recovery probe reference (outside this docs repo; from the same `helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260312T175250Z-pr377-gw04-26ee758-recovery/full88-probe-t01-after-adapter-reboot/index.json`
  with `blocked-infra` / `infra_reason=adapter_no_signal`
- Gateway repo code/test proof references (external to this docs repo, at merge commit `3daf4beed9d6406f7af52869eea1c53ef14f2f62`):
  - [Project-Helianthus/helianthus-ebusgateway/mcp/bus.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/mcp/bus.go)
  - [Project-Helianthus/helianthus-ebusgateway/mcp/server.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/mcp/server.go)
  - [Project-Helianthus/helianthus-ebusgateway/mcp/server_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/mcp/server_test.go)
  - [Project-Helianthus/helianthus-ebusgateway/cmd/gateway/mcp_bus_observability_integration_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/cmd/gateway/mcp_bus_observability_integration_test.go)
- Gateway repo GraphQL proof references (external to this docs repo, at merge commit `83e9c7b1ba927a282d87599269e91be817ff3582`):
  - [Project-Helianthus/helianthus-ebusgateway/graphql/bus_observability.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/83e9c7b1ba927a282d87599269e91be817ff3582/graphql/bus_observability.go)
  - [Project-Helianthus/helianthus-ebusgateway/graphql/queries.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/83e9c7b1ba927a282d87599269e91be817ff3582/graphql/queries.go)
  - [Project-Helianthus/helianthus-ebusgateway/graphql/queries_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/83e9c7b1ba927a282d87599269e91be817ff3582/graphql/queries_test.go)
  - [Project-Helianthus/helianthus-ebusgateway/cmd/gateway/bus_observability_provider.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/83e9c7b1ba927a282d87599269e91be817ff3582/cmd/gateway/bus_observability_provider.go)
  - [Project-Helianthus/helianthus-ebusgateway/cmd/gateway/graphql_bus_observability_integration_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/83e9c7b1ba927a282d87599269e91be817ff3582/cmd/gateway/graphql_bus_observability_integration_test.go)
- Current-state docs references:
  - [api/mcp.md](../api/mcp.md)
  - [api/graphql.md](../api/graphql.md)
  - [architecture/observability.md](./observability.md)
  - [development/smoke-matrix.md](../development/smoke-matrix.md)

## Falsification Cases

This architecture freeze is wrong if later review proves any of the following:

- the MCP bus namespace collapses back into semantic tools
- M2 starts implying exact wire timing without an explicit timing-quality
  upgrade and supporting proof
- retained periodicity/message history is used as implicit proof that passive
  capability is currently healthy
- passive-unavailable busy-time is exposed as zero instead of unavailable

## Concrete Examples

### Example: `ebusd-tcp` degrades timing and passive capability explicitly

On `ebusd-tcp`, the MCP summary may still expose active-path bounded data, but
`status.capability.passive_state` is `unavailable` with reason
`unsupported_or_misconfigured`, while `status.timing_quality.passive`,
`status.timing_quality.busy`, and `status.timing_quality.periodicity` remain
`unavailable`.

### Example: retained periodicity history does not prove current health

After a passive reset or unavailable transition, `bus.periodicity.list` may
still return retained items from the bounded store. Consumers still need the
top-level `status` to determine whether passive capability is currently
`warming_up`, `available`, or `unavailable`.
