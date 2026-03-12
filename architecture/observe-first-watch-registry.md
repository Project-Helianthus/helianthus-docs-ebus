# Observe-First Watch Registry

This page is the `DOC-01` skeleton for the observe-first architecture lane.
It records the M0 locked decisions from the canonical plan and marks the later
milestone owners that must freeze the detailed runtime contract.

This page does not claim that every section below is already fully implemented.
Current implemented scheduler and runtime behavior remains documented in:

- [`architecture/semantic-read-circuit-breaker.md`](./semantic-read-circuit-breaker.md)
- [`architecture/energy-merge.md`](./energy-merge.md)
- [`deployment/full-stack.md`](../deployment/full-stack.md)

## Status

- canonical doc artifact: `DOC-01`
- canonical issue: `ISSUE-DOC-01`
- current role: M0 skeleton with locked decisions plus milestone-owned placeholders
- later freeze owners:
  - `ISSUE-GW-06` + `ISSUE-DOC-08`: watch catalog, shared keys, runtime activation
  - `ISSUE-GW-07` + `ISSUE-GW-08` + `ISSUE-GW-09` + `ISSUE-DOC-08`: shadow cache, flags, family policy, invalidation rules
  - `ISSUE-GW-10` + `ISSUE-DOC-09`: scheduler integration, query-on-gap semantics

## Scope

This page owns the generic observe-first read-path architecture:

- watch catalog and runtime activation
- shared canonical watch keys
- generic `ShadowCache`
- `ShadowCache` to `SemanticReadScheduler` interaction
- precedence and invalidation rules for generic observe-first state/config reads

This page does not re-document:

- passive transport topology, capability states, or bus-level timing surfaces
- the dedicated B516 energy broadcast merge path
- MCP, GraphQL, or Portal response schemas

Those surfaces are owned elsewhere:

- bus-level observability: [`architecture/bus-observability-v2.md`](./bus-observability-v2.md)
- energy carve-out: [`architecture/energy-merge.md`](./energy-merge.md)
- current transport/runtime caveats: [`deployment/full-stack.md`](../deployment/full-stack.md)

## Locked M0 Decisions

### Watch Catalog And Runtime Activation

- `WatchCatalog` is a bounded static catalog of possible watch descriptors, not
  "all documented selectors always active."
- The static descriptor catalog is immutable after startup for one adapter
  instance.
- Runtime activation is a separate bounded mutable structure.
- Activation is derived from explicit code-owned selector lists, not from docs
  or wildcard discovery.
- Runtime activation source is provenance, not access control. The bounded
  source set is:
  - `poller`
  - `write_confirm`
  - `tooling`
  - `operator`
- Simultaneous activation sources use union semantics: a key stays active while
  at least one source remains.
- `WatchDescriptor` includes, at minimum:
  - family
  - concrete key shape
  - semantic class
  - freshness profile
  - decoder id
  - correlation policy
  - direct-apply policy
  - resolved or resolvable `freshness_ttl`
- Semantic class remains the coarse policy bucket:
  - `state`
  - `config`
  - `discovery`
  - `debug`
- Freshness profile is the finer bounded enum:
  - `state_fast`
  - `state_slow`
  - `config`
  - `discovery`
  - `debug`
- Family-specific keys are typed canonical structs, not ad-hoc string
  formatting. Shared key builders live outside `main` so poller code and
  passive correlation use the same authority.
- `B516WatchKey` exists for freshness/provenance and energy-merge identity, but
  it is not a generic scheduler-facing `ShadowCache` key in v1.
- Passive observations for catalog misses or inactive selectors remain
  observable, but do not allocate shadow entries in v1.

### Shadow Cache

- `ShadowCache` is memory-only in v1.
- Each adapter instance owns its own cache and budget domain.
- Default hard limits are locked:
  - `4096` total shadow entries
  - `2048` pinned-entry sub-budget
  - `256` reserved write-confirm pinned entries
- Semantic and write-confirm keys are pinned; tooling/manual entries are
  evictable and lose first under pressure.
- Budget overflow is fail-closed per adapter instance:
  - gateway process startup still succeeds
  - passive ingest and bus observability remain enabled
  - observe-first shadow satisfaction/direct-apply disables for the affected
    adapter instance until the configuration/watch inventory returns within
    budget
- `ShadowCache` stores observed evidence, including:
  - value or tombstone state
  - source and confidence tier
  - freshness metadata
  - observation timestamp
  - precedence and generation metadata
- Invalidated entries remain diagnostically retained but are ineligible for
  scheduler satisfaction.
- Tombstones compact from payload-retained to metadata-only after the rolling
  `15m` maintenance window and may de-pin after the hard `24h` tombstone
  horizon.
- Compaction is bounded and supervised. It may not hold the cache lock across a
  full sweep and may not silently stop on panic or repeated failure.
- `ShadowCache` does not write directly to `LiveSemanticProvider` in v1.

### Scheduler Integration And Query-On-Gap

- `ShadowCache` does not replace `SemanticReadScheduler`.
- The generic order is locked:
  1. scheduler receives `Get(key, maxAge, fetch)`
  2. shadow eligibility is consulted first
  3. eligible shadow hits seed scheduler freshness
  4. active fetch runs only on gap, invalidation, or ineligibility
  5. successful active fetch updates both scheduler state and `ShadowCache`
- `query-on-gap` means active reads happen only when no eligible scheduler or
  shadow evidence satisfies the bounded freshness policy, or when invalidation
  rules have explicitly disqualified the cached evidence.
- Shadow consultation happens outside the scheduler mutex.
- Once the scheduler mutex is acquired, the candidate shadow hit must be
  revalidated against an atomic per-key shadow eligibility snapshot. The
  scheduler may not reacquire the full `ShadowCache` mutex while holding its own
  mutex.
- The scheduler remains the owner of:
  - coalescing
  - active-read freshness cache
  - circuit-breaker state
- Eligible shadow hits may bypass the active-read breaker guard.
- Shadow hits do not heal breaker failure counters; only successful active
  fetches affect breaker recovery.
- In-flight active fetches carry a generation token. If invalidation or a newer
  generation appears before completion, stale fetch results fail closed instead
  of reseeding scheduler freshness.
- Generic observe-first does not create a second passive-to-provider publish
  path. The existing semantic poller remains the publish owner.

### Precedence And Invalidation

- `CRC valid` is necessary but never sufficient for passive application.
- Confidence is categorical:
  - `high_confidence`
  - `limited_confidence`
  - `no_confidence`
- Response-class policy is explicit and bounded:
  - `value_bearing`
  - `ack_only`
  - `header_only`
  - `error_or_ambiguous`
- Passive direct-apply requires all of:
  - valid reconstruction
  - accepted family correlation rule
  - successful family decoder selection
  - accepted response class
  - accepted semantic/direct-apply policy
- Observation timestamp ordering is authoritative. Older evidence may not
  overwrite newer evidence merely because it arrived later in process time.
- `active_confirmed` outranks passive evidence only when timestamps are equal or
  the active evidence is not older.
- External passive writes do not become eligible replacements by default.
  `external_write_policy` governs whether they are:
  - `invalidate_only`
  - `record_only`
  - `record_and_invalidate`
- Helianthus-originated writes remain `write + read-back confirm`; passive
  observe-first does not replace targeted confirm reads.

## Invariants

- The watch catalog is immutable per adapter instance after startup.
- Runtime activation is bounded and separate from the immutable catalog.
- Shared canonical keys are typed and reused across poller, shadow, and passive
  correlation paths.
- `ShadowCache` stays upstream of the scheduler; it is not the scheduler.
- Generic observe-first never publishes directly into semantic providers.
- Invalidation advances the shared per-key generation domain before later reads
  can commit a shadow or active-confirmed hit.

## Degraded Behavior

- On cold start, scheduler freshness and shadow state are empty. Observe-first
  therefore begins in an active-only effective mode until passive warmup and
  eligible shadow accumulation occur.
- If pinned-budget validation fails, observe-first shadowing disables for that
  adapter instance while passive ingest and bus observability continue.
- If invalidation wins a race against an in-flight fetch, the read path fails
  closed to the non-shadow path instead of serving stale data.
- When `observe_first_enabled=false`, runtime behavior clamps back to the
  conservative non-observe-first path and shadow satisfaction stops.

## Unsupported Or Unproven Cases

- No wildcard or doc-driven watch activation.
- No cross-adapter shared shadow cache or scheduler cache.
- No persistent on-disk shadow cache in v1.
- No generic direct passive publish path into semantic providers in v1.
- No default debug-profile shadow allocation or debug-profile pinned budget in
  v1.
- Exact descriptor inventory, family-specific activation tables, and final flag
  normalization behavior are not frozen by this M0 skeleton. Later milestone
  owners must add implementation-backed evidence before those sections can be
  treated as final.

## Milestone-Owned Placeholders

| Surface | Locked in M0 | Freeze owner |
| --- | --- | --- |
| Watch descriptor schema and shared keys | Catalog/activation split, typed canonical keys, bounded enums, no wildcard activation | `ISSUE-GW-06` + `ISSUE-DOC-08` |
| Shadow budgets and lifecycle | Memory-only cache, pinned budgets, tombstone compaction, fail-closed overflow | `ISSUE-GW-07` + `ISSUE-DOC-08` |
| Feature flags and external-write policy | Conservative defaults, explicit bounded values, invalidation semantics | `ISSUE-GW-08` + `ISSUE-GW-09` + `ISSUE-DOC-08` |
| Query-on-gap read path | Shadow-before-fetch ordering, post-lock revalidation, generation-token stale rejection | `ISSUE-GW-10` + `ISSUE-DOC-09` |
| Watch-summary and efficiency surfaces | Out of scope for this skeleton page | `ISSUE-GW-11` + `ISSUE-GW-12` + `ISSUE-DOC-09` |

## Evidence

- Canonical locked-decision source:
  `helianthus-execution-plans/observe-first-bus-observability.implementing/00-canonical.md`
  sections `5` through `10` and `14`
- Canonical milestone map:
  `helianthus-execution-plans/observe-first-bus-observability.implementing/90-issue-map.md`
- No section on this page should be read as `PROVEN` unless a later milestone
  adds implementation-backed evidence in the owning docs update.

## Falsification Cases

- If runtime activation is inferred from docs or wildcard selector discovery,
  this page is wrong.
- If the scheduler must take the full `ShadowCache` mutex while holding its own
  mutex, this page is wrong.
- If passive generic shadow writes bypass generation/invalidation checks and
  directly publish semantic state, this page is wrong.
- If an older `active_confirmed` result can overwrite newer passive evidence
  purely because its request completed later, this page is wrong.

## Concrete Examples

### Example: Canonical B524 Watch Key

One observe-first state key uses the typed dimensions:

```text
B524WatchKey{
  target=0x15,
  opcode=0x06,
  group=0x08,
  instance=0x01,
  register_address=0x1234,
}
```

The typed key is the authority for scheduler lookup, runtime activation, and
passive correlation. Any string form is derived from that typed authority only
for logs and metrics.

### Example: External Write Invalidation

If a third-party passive write is observed for an already cached config key
while `external_write_policy=invalidate_only`:

1. the old cached entry stays available for diagnostics only
2. the shadow entry becomes invalidated/tombstoned for scheduler purposes
3. matching scheduler freshness is cleared or aged out
4. the next read must use fresh active or eligible passive evidence
