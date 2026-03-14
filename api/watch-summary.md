# Watch Summary API Contract

## Current Status

The shared watch-summary surface is implemented on gateway `main` and frozen in
this `DOC-09` lane against merged M5 behavior.

Freeze anchors:

- Scheduler/shadow runtime semantics: mainline commit on `main` `75ee6aa639bb44e8e859835293ae3912dc4d7b48`
  ([Project-Helianthus/helianthus-ebusgateway#391](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/391))
- Watch-summary MCP/GraphQL surfaces: mainline commit on `main` `92b3576c9203bf5a02a45494e935041961044600`
  ([Project-Helianthus/helianthus-ebusgateway#393](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/393))

## Frozen Ownership

| Surface | Name | Runtime lane | Freeze lane | State on `main` |
| --- | --- | --- | --- | --- |
| MCP | `ebus.v1.watch.summary.get` | `ISSUE-GW-11` | `ISSUE-DOC-09` | frozen |
| GraphQL | `watchSummary` | `ISSUE-GW-11` | `ISSUE-DOC-09` | frozen |
| Portal | none in this doc | `ISSUE-GW-14` | `ISSUE-DOC-10` | not frozen here |

## Shared v1 Shape

When the runtime watch provider is wired, both surfaces expose the same logical
watch-summary shape/categories derived from `ShadowCache.WatchSummary()`.
Cross-surface reads are not guaranteed to share one snapshot instance: GraphQL
has request-level snapshot guarantees, while MCP uses its own `LIVE`/`SNAPSHOT`
consistency path. In unwired mode, GraphQL returns zero-value `watchSummary`
data while MCP omits `ebus.v1.watch.summary.get`.

Top-level sections:

- `inventory`
- `activation_counts` / `activationCounts`
- `freshness_classes` / `freshnessClasses`
- `direct_apply_eligibility_classes` / `directApplyEligibilityClasses`
- `degraded`

Class labels are stable v1 strings:

- Activation source classes: `poller`, `write_confirm`, `tooling`, `operator`
- Freshness classes: `state_fast`, `state_slow`, `config`, `discovery`,
  `debug`
- Direct-apply eligibility classes: `state_eligible`, `state_ineligible`,
  `state_master_off`, `config_eligible`, `config_ineligible`,
  `config_master_off`, `not_applicable`
- Entry state classes: `present`, `invalidated`, `tombstone`
- Pin classes: `static`, `write_confirm`, `evictable`
- Degraded reasons: `shadow_pinned_budget_degraded`,
  `shadow_compactor_degraded`

## MCP Contract

Tool:

- `ebus.v1.watch.summary.get`
  - arguments: optional `consistency` (`LIVE` default, or `SNAPSHOT` with
    required `snapshot_id`)

Registration rule:

- The tool appears in `tools/list` only when the MCP server is wired with a
  watch-summary provider (runtime shadow cache path).
- Without that provider, tool calls fail as unknown tool.

MCP field names are snake_case (`activation_counts`, `freshness_classes`,
`shadowing_enabled`, etc.).

## GraphQL Contract

GraphQL query root:

```graphql
type Query {
  watchSummary: WatchSummary!
}
```

GraphQL watch-summary types:

```graphql
type WatchSummary {
  inventory: WatchSummaryInventory!
  activationCounts: WatchSummaryActivationCounts!
  freshnessClasses: [WatchSummaryClassCount!]!
  directApplyEligibilityClasses: [WatchSummaryClassCount!]!
  degraded: WatchSummaryDegraded!
}

type WatchSummaryClassCount {
  class: String!
  count: Int!
}

type WatchSummaryInventory {
  totalEntries: Int!
  pinnedEntries: Int!
  evictableEntries: Int!
  staticPinnedFootprint: Int!
  writeConfirmPinnedActive: Int!
  stateClasses: [WatchSummaryClassCount!]!
  pinClasses: [WatchSummaryClassCount!]!
}

type WatchSummaryActivationCounts {
  catalogDescriptors: Int!
  activeKeys: Int!
  sourceClasses: [WatchSummaryClassCount!]!
}

type WatchSummaryDegraded {
  active: Boolean!
  shadowingEnabled: Boolean!
  pinnedBudgetDegraded: Boolean!
  compactorDegraded: Boolean!
  reasons: [String!]!
}
```

## Freshness Profiles and Effective Max-Age

v1 default profile TTLs:

| Freshness profile | Default TTL |
| --- | --- |
| `state_fast` | `10s` |
| `state_slow` | `30s` |
| `config` | `5m` |
| `discovery` | `1h` |
| `debug` | `0` (ineligible for shadow-hit serving) |

Runtime scheduler semantics use descriptor policy, not legacy hard-coded
`500ms` windows.

Effective shadow-hit limit is:

`min(caller maxAge, descriptor EffectiveFreshnessTTL())`

If the effective limit is `<= 0`, the scheduler does not serve from shadow and
takes the non-shadow decision path (`entry.lastOK` scheduler-cache hit when
valid for max-age+generation, coalesced in-flight read, active fetch, breaker
suppression failure, or active read error).

## Query-on-Gap Truth Table (v1)

Once shadow serving is ineligible, the runtime outcome is branch-dependent and
may include post-wake or post-fetch re-evaluation cycles before a terminal
value/error is returned.

| Outcome | Preconditions | Scheduler action | Result |
| --- | --- | --- | --- |
| `shadow-hit` | Present + eligible shadow entry under effective max-age | Return shadow value immediately | No active fetch |
| `scheduler-cache-hit` | No eligible shadow value; scheduler has `entry.lastOK` that still satisfies caller max-age and generation checks | Return cached active result directly | No active fetch |
| `coalesced-fetch` | No eligible shadow value and no valid `entry.lastOK`; identical read already running | Wait for in-flight read completion, then re-enter scheduler evaluation | Post-wake path is not fixed: it may return a now-eligible value, return a now-valid `entry.lastOK`, start a new active fetch, or fail due to breaker suppression |
| `active-fetch` | No eligible shadow value; no running fetch; breaker allows execution | Run one active read; then apply active-completion validity checks (shadow write/generation revalidation) | Terminal result is branch-dependent: fetched value when completion remains valid, otherwise underlying fetch error or superseded/revalidation failure |
| `breaker-blocked fail-closed` | No eligible shadow value; breaker is open (or half-open probes exhausted) | Suppress fetch and return breaker error | Immediate failure (`semantic read circuit breaker open`) |

## Explicit Scheduler/Shadow Semantics

- Snapshot-skew: GraphQL resolves multiple `watchSummary` fields in one
  operation from one shared snapshot. MCP `SNAPSHOT` mode pins watch-summary to
  the captured snapshot id. Cross-request `LIVE` reads are not guaranteed to be
  synchronized with each other.
- Notification-latency: passive shadow ingestion is asynchronous via
  deduplicator subscription channels; there is no fixed upper-latency SLA in
  this v1 contract.
- Shadow write-order: older timestamps are rejected (`stale_timestamp`); same
  timestamp conflicts are source-precedence-ordered (`active_confirmed` outranks
  `passive`).
- Breaker-bypass: the scheduler checks eligible shadow candidates before breaker
  suppression; a valid shadow hit can be served without active fetch even when
  active path is degraded.
- Invalidation-epoch: key generation is monotonic; invalidation advances
  generation, and stale in-flight `active_confirmed` completions are rejected as
  superseded.
- Feature-flag validity: observe-first flags are normalized before runtime
  usage (`master_off_clamp`, `config_requires_state`,
  `config_requires_invalidation`), and direct-apply classes reflect the
  normalized state.
- Cold-start: GraphQL `watchSummary` remains available and returns zero-value
  data when unwired; MCP omits `ebus.v1.watch.summary.get` until the watch
  provider is wired.

## Explicit Non-Scope (DOC-09)

- Portal-specific watch-summary transport/endpoint/SSE semantics
- UI bootstrap cadence and presentation-specific behavior
- Any Portal-only contract wording (owned by `ISSUE-DOC-10`)

## Evidence

- Runtime scheduler/shadow integration PR: [Project-Helianthus/helianthus-ebusgateway#391](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/391)
- Watch-summary surface PR: [Project-Helianthus/helianthus-ebusgateway#393](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/393)
- Scheduler behavior + breaker/coalescing tests:
  [Project-Helianthus/helianthus-ebusgateway/semantic_read_scheduler.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/semantic_read_scheduler.go),
  [Project-Helianthus/helianthus-ebusgateway/semantic_read_scheduler_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/semantic_read_scheduler_test.go)
- Shadow-cache TTL/order/generation semantics:
  [Project-Helianthus/helianthus-ebusgateway/shadow_cache.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/shadow_cache.go),
  [Project-Helianthus/helianthus-ebusgateway/shadow_cache_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/shadow_cache_test.go)
- Watch-summary computation + classes:
  [Project-Helianthus/helianthus-ebusgateway/watch_summary.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/watch_summary.go),
  [Project-Helianthus/helianthus-ebusgateway/watch_summary_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/watch_summary_test.go)
- GraphQL watch-summary contract and operation snapshot cache:
  [Project-Helianthus/helianthus-ebusgateway/graphql/watch_summary.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/graphql/watch_summary.go),
  [Project-Helianthus/helianthus-ebusgateway/graphql/watch_summary_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/graphql/watch_summary_test.go)
- MCP tool registration/shape/snapshot consistency:
  [Project-Helianthus/helianthus-ebusgateway/mcp/server.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/mcp/server.go),
  [Project-Helianthus/helianthus-ebusgateway/mcp/server_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/92b3576c9203bf5a02a45494e935041961044600/mcp/server_test.go)

## Current Discovery Rule

- [`mcp.md`](./mcp.md) documents only implemented MCP tools
- [`graphql.md`](./graphql.md) documents only implemented GraphQL schema
- [`portal.md`](./portal.md) documents only implemented Portal endpoints
- [`portal.md`](./portal.md) and `ISSUE-DOC-10` continue to own Portal-specific
  watch-summary behavior
