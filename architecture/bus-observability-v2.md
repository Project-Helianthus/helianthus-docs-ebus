# Bus Observability v2

## Status

- State: partially frozen for the M2 MCP slice on docs `main`
- Active freeze owner: `ISSUE-DOC-06`
- Later owners:
  - `ISSUE-DOC-07` for GraphQL parity wording
  - `ISSUE-DOC-08` for family-policy, freshness, and later observe-first
    architecture updates

## Scope

This document is the architecture anchor for whole-bus observability in the
observe-first rollout.

This lane freezes only the MCP-owned sections:

- busy-time and timing model wording needed by the M2 MCP surface
- periodicity model wording needed by the M2 MCP surface
- public-surface wording for the `ebus.v1.bus.*` MCP namespace

This lane does not freeze GraphQL, Portal/watch-summary, scheduler/shadow
behavior, or docs-stage1 cleanup work.

## Invariants

- `ebus.v1.bus.*` remains a bus-observability namespace, not a semantic
  namespace.
- M2 exposes bounded summaries and bounded retained lists only.
- Busy-time and periodicity timing quality must remain explicit whenever the
  runtime lacks true wire timestamps.
- Whole-bus passive capability state remains explicit even when bounded
  retained history still exists.

## Degraded Behavior

- When passive support is unavailable or still warming up, MCP surfaces keep
  publishing explicit capability, warmup, degraded, and timing-quality state.
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

## Busy-Time and Timing Model

### Current M2 Freeze

- `bus.summary.get` is the M2 MCP owner for busy-time/timing capability
  exposure.
- M2 does not publish a dedicated numeric busy-ratio MCP payload. The frozen
  public contract is the summary status plus explicit timing-quality markers.
- `status.timing_quality.bus` and `status.timing_quality.periodicity` track the
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

- No GraphQL contract is frozen in this file.
- No Portal/watch-summary naming or behavior is frozen in this file.
- No scheduler/shadow/query-on-gap behavior is frozen in this file.
- No exact wire-timestamp guarantee is frozen for current transports.
- No dedicated numeric busy-time MCP payload is frozen in M2.

## Evidence

- Runtime implementation: [Project-Helianthus/helianthus-ebusgateway#376](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/376)
- Merged PR: [Project-Helianthus/helianthus-ebusgateway#377](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/377)
- Merge commit: `3daf4beed9d6406f7af52869eea1c53ef14f2f62`
- Fresh passive proof artifact:
  `results-matrix-ha/20260312T175648Z-pr377-gw04-26ee758-passive-p01-p06-recovery/index.json`
  with `P01..P06 = pass`
- Fresh standard recovery probe reference:
  `results-matrix-ha/20260312T175250Z-pr377-gw04-26ee758-recovery/full88-probe-t01-after-adapter-reboot/index.json`
  with `blocked-infra` / `infra_reason=adapter_no_signal`
- Runtime code/tests used for this freeze:
  - `mcp/bus.go`
  - `mcp/server.go`
  - `mcp/server_test.go`
  - `cmd/gateway/mcp_bus_observability_integration_test.go`
- Current-state docs references:
  - [api/mcp.md](../api/mcp.md)
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
`status.timing_quality.bus`, and `status.timing_quality.periodicity` remain
`unavailable`.

### Example: retained periodicity history does not prove current health

After a passive reset or unavailable transition, `bus.periodicity.list` may
still return retained items from the bounded store. Consumers still need the
top-level `status` to determine whether passive capability is currently
`warming_up`, `available`, or `unavailable`.
