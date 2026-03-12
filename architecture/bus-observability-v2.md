# Bus Observability V2

This page is the `DOC-02` skeleton for the observe-first architecture lane.
It records the locked bus-observability decisions and the milestone owners that
must later freeze the detailed runtime and API contracts.

This page is intentionally narrow. It documents the bus-level observability
model, not the generic shadow/scheduler read path. Current implemented runtime
notes that already exist elsewhere remain authoritative for their own scope:

- [`architecture/observability.md`](./observability.md)
- [`deployment/full-stack.md`](../deployment/full-stack.md)
- [`architecture/energy-merge.md`](./energy-merge.md)

## Status

- canonical doc artifact: `DOC-02`
- canonical issue: `ISSUE-DOC-01`
- current role: M0 skeleton with locked decisions plus milestone-owned placeholders
- later freeze owners:
  - `ISSUE-GW-01` + `ISSUE-GW-01B` + `ISSUE-GW-01C` + `ISSUE-GW-02` + `ISSUE-GW-03` + `ISSUE-DOC-05`: passive pipeline, dedup boundary, store, metrics
  - `ISSUE-GW-04` + `ISSUE-DOC-06`: MCP query surfaces
  - `ISSUE-GW-05` + `ISSUE-DOC-07`: GraphQL parity surfaces

## Scope

This page owns the bus-level observability contract for:

- passive source model and passive pipeline split
- busy-time and timing-quality rules
- error and degraded-state taxonomy
- periodicity tracking
- transport capability matrix
- Prometheus and `expvar` coexistence

This page does not own:

- generic watch catalog or shadow-cache behavior
- semantic publish rules for generic state/config values
- Portal-specific bootstrap or stream APIs

## Locked M0 Decisions

### Source Model And Pipeline Split

- `active` means traffic initiated by Helianthus on the primary connection.
- `passive` means traffic observed from a separate passive feed.
- `ebusd-tcp` is `active-only`.
- No synthetic passive estimates are allowed.
- In passive-capable mode there are exactly two gateway bus connections:
  - one primary active connection
  - one passive tap connection
- There is no third standalone broadcast-only connection.
- `PassiveBusTap` owns the passive connection and emits logical bus symbols plus
  lifecycle and discontinuity signals.
- `PassiveTransactionReconstructor` is the single raw passive-stream consumer
  and emits classified passive events.
- `BroadcastListener` and `BusObservabilityStore` consume pre-dedup classified
  passive events. Dedup only owns the downstream adjudicated stream used for
  shadow correlation and watch-efficiency accounting.

### Busy-Time Model

- Busy-time and periodicity are based on passive timing markers, not on active
  request scheduling.
- Passive timing markers are receive-time estimates unless the transport
  supplies true wire timestamps.
- ENH/ENS buffering over TCP means busy-time and periodicity are estimated, not
  ground-truth wire timing.
- Whole-bus observability keeps Helianthus-originated traffic:
  - busy ratio still counts it
  - frame totals still count it
  - source/destination distribution still counts it
- A passive event that is later dedup-matched for shadow or watch-efficiency
  purposes still remains authoritative input for bus-level busy-time and
  periodicity.
- When passive capability is unavailable, busy-time is unavailable, not zero.

### Error Taxonomy And Degraded-State Taxonomy

- Classified passive outputs are bounded to:
  - `PassiveMasterFrame`
  - `PassiveBroadcastFrame`
  - `PassiveTransaction`
  - `PassiveAbandonedTransaction`
- Only successful classified terminal events are eligible for periodicity
  interval formation.
- Reconstructor, subscriber-overflow, and dedup-degraded conditions are explicit
  faults. Correctness-critical loss may not remain silent.
- Passive capability unavailability uses explicit bounded reasons:
  - `startup_timeout`
  - `reconnect_timeout`
  - `socket_loss`
  - `flap_dampened`
  - `unsupported_or_misconfigured`
  - `capability_withdrawn`
- Relay transports that cannot prove passive timing or passive coverage must
  report those surfaces as unavailable or estimated instead of inventing active
  approximations.

### Periodicity Model

- `busMessages` is a bounded recent-message ring, not unbounded event history.
- `busPeriodicity` is a bounded summary tracker keyed by normalized
  `(source, target, PB, SB)` tuple identity.
- `family` is a derived tag carried with a tuple summary; it is not part of
  tuple identity.
- Default store bounds are locked:
  - recent-message ring: `1024`
  - periodicity tuple budget: `256`
  - stale eviction: `1h`
- Per-tuple periodicity warmup requires at least `3` observed intervals, which
  means `4` qualifying successful transactions for that tuple.
- Abandoned, ambiguous, or decode-failed transactions do not contribute
  periodicity samples.
- A tuple can remain `warming_up` even if global passive capability is already
  `available`.

### Capability Matrix By Transport

The transport-level direction is locked even where later milestones still need
to freeze exact API field names:

| Transport shape | Active reads | Passive observe-first | Broadcast coverage | Timing quality |
| --- | --- | --- | --- | --- |
| `ebusd-tcp` | yes | no | no | unavailable |
| Direct adapter-class `enh` / `ens` over adapter listener (`tcp/:9999`) | yes | no | no passive proof surface in v1 | unavailable |
| Proxy-like `enh` / `ens` on non-adapter ports | yes | yes | yes | estimated unless the adapter exports true wire timestamps |

This table is intentionally about capability state, not rollout proof. Later
milestones must attach implementation evidence before these rows can be treated
as proven across every supported topology.

### Prometheus And `expvar` Coexistence

- Existing `expvar` remains in place.
- This feature does not migrate the existing runtime wholesale away from
  `expvar`.
- New bus/watch metrics are exposed through a dedicated Prometheus text
  exporter.
- Gateway metric series must stay within bounded-cardinality rules.
- Tinyebus alignment matters, so the feature does not rely on blind
  auto-registration from `prometheus/client_golang`.

## Invariants

- Whole-bus observability is pre-dedup and passive-grounded.
- No surface may silently claim exact wire-time precision when the transport
  only provides buffered receive times.
- Unavailable bus timing is omitted or explicitly unavailable, not encoded as a
  misleading zero value.
- Bus-level observability and shadow/write-efficiency are separate correctness
  domains and do not share the same suppression rules.

## Degraded Behavior

- Before the first successful passive connect, passive capability remains
  `unavailable`.
- After passive reconnect or passive reset, busy-time and periodicity re-enter
  explicit warmup before returning to normal reporting.
- On passive outage, monotonic counters remain monotonic while timing-sensitive
  surfaces become `unavailable` or `warming_up`.
- `ebusd-tcp` remains an explicit degraded transport for passive observability:
  active runtime may continue, but passive and broadcast surfaces do not.

## Unsupported Or Unproven Cases

- No synthetic passive traffic model for `ebusd-tcp`.
- No active-only fallback that pretends to be whole-bus busy-time.
- No unbounded recent-message history or per-tuple raw sample retention.
- Exact MCP and GraphQL field-level response shapes are not frozen by this M0
  skeleton. Later milestone owners must add real-output evidence before those
  surfaces are treated as final.

## Milestone-Owned Placeholders

| Surface | Locked in M0 | Freeze owner |
| --- | --- | --- |
| Passive pipeline and classified event model | Two-connection design, tap/reconstructor split, pre-dedup observability boundary | `ISSUE-GW-01` through `ISSUE-GW-03` + `ISSUE-DOC-05` |
| Metrics and bounded stores | Busy/error/family/length/busy/periodicity model, bounded message/tuple stores, warmup/degraded states | `ISSUE-GW-03` + `ISSUE-DOC-05` |
| MCP observability responses | `busSummary`, `busMessages`, `busPeriodicity` surface split | `ISSUE-GW-04` + `ISSUE-DOC-06` |
| GraphQL observability responses | GraphQL parity for the same bounded domain data | `ISSUE-GW-05` + `ISSUE-DOC-07` |
| Portal-native timeline/bootstrap surfaces | Explicitly out of scope for this page | Later Portal docs lane |

## Evidence

- Canonical locked-decision source:
  `helianthus-execution-plans/observe-first-bus-observability.implementing/00-canonical.md`
  sections `1` through `4` and `11` through `12`
- Canonical milestone map:
  `helianthus-execution-plans/observe-first-bus-observability.implementing/90-issue-map.md`
- No section on this page should be read as `PROVEN` unless a later milestone
  adds implementation-backed evidence in the owning docs update.

## Falsification Cases

- If whole-bus busy-time drops Helianthus-originated traffic after dedup, this
  page is wrong.
- If a passive-capable topology introduces a third broadcast-only connection,
  this page is wrong.
- If relay transports emit passive busy-time as ordinary numeric zero instead of
  an explicit unavailable state, this page is wrong.
- If bounded tuple tracking is replaced by unbounded message-history inference at
  query time, this page is wrong.

## Concrete Examples

### Example: Periodicity Tuple Identity

One periodicity entry tracks the normalized tuple:

```text
(source=0x15, target=0x08, PB=0xB5, SB=0x24)
```

The tuple summary records bounded interval statistics such as sample count, last
interval, rolling mean, min interval, and max interval. The family tag
(`B524` here) is derived metadata, not part of the tuple identity.

### Example: Passive Capability On `ebusd-tcp`

For `ebusd-tcp`:

- active reads may still work
- passive observe-first is unavailable
- broadcast-derived timing and freshness surfaces are unavailable
- operator-facing surfaces must report the degraded capability explicitly rather
  than silently presenting active-only approximations as bus observability
