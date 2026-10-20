# MCP Endpoint

The cross-protocol bounded Modbus V1 surface is specified separately in
[`modbus-v1-mcp.md`](./modbus-v1-mcp.md). It remains raw/profile evidence and
does not publish canonical PV semantics.

The disabled-by-default add-on configuration, protected endpoint-file, and
single direct gateway process lifecycle are specified in
[`modbus-v1-addon-runtime.md`](./modbus-v1-addon-runtime.md). It does not
qualify a live device or extend the MCP schema.

## Current Status

Until the Helianthus 1.0 release, all MCP namespaces, including `ebus.v1.*`,
are pre-stable; the namespace version alone is not a stability promise. A
contract version declared by an individual surface, such as `1.0`, does not
end this period. Schema or behaviour
may change with updated goldens, documentation, and a note in the pull request.
There is no experimental namespace or core-stable graduation before 1.0;
both will be discussed after 1.0. Existing envelope, determinism, golden-test,
and documentation-gate requirements remain in force.

The MCP server is implemented and served by `cmd/gateway` at `/mcp`.

The target additive Vaillant-only
`ebus.v1.runtime.status.get.data.vaillant_regulator_capability` member is
specified in [`vaillant-regulator-capability-v1.md`](./vaillant-regulator-capability-v1.md).
It remains absent from the implemented-surface inventory until open gateway #947
merges after the documentation gate; an older or missing
`vaillant_regulator_capability` member maps to consumer `UNKNOWN`. It does not
imply a gateway-wide or cross-protocol result.

## G5 runtime lifecycle MCP contract (D4)

This is the first external control contract for
[docs issue #717](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/717),
a partial slice of [gateway #1032](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1032).
It is the prerequisite for gateway PR 2; the tools are **pending implementation**
and are not part of the implemented inventory below. A5's internal service for
`ebus.primary` is implemented by the merged
[gateway PR #1241](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1241).
That software status establishes neither hardware validation nor a universal
provider SPI. The [lifecycle contract](../architecture/runtime-driver-lifecycle.md)
owns durable decisions, refusal order and CTL/LIFE semantics.

### Ordinary discovery and dispatch

The exact tool family is `helianthus.runtime.{list,get,start,stop,restart}`.
All five tools must appear in ordinary `tools/list` and dispatch through
every ordinary MCP transport the gateway offers (HTTP today), including with
eeBUS disabled or absent.
Registration lasts for the shell's lifetime, independently of driver startup,
STOPPED/FAILED state and eeBUS provider availability. A disabled driver remains
visible; tool disappearance is not an unavailable-state signal.

Final D4 requires no lifecycle principal checks, authority adapter or
authorization before 0.9. No owner-only kernel socket, separate listener,
operator-boundary-only registration or eeBUS dependency is introduced. Existing
native-write checks and unrelated eeBUS security boundaries keep their current
owners. Driver contribution hooks remain unimplemented; these are host tools.
Every namespace, including `ebus.v1.*`, remains pre-stable until 1.0. Intentional
changes require documentation, deterministic envelopes, schema/output goldens
and PR explanation; neither a compatibility veto nor promotion to a new major
or experimental namespace applies before 1.0.

### Closed inputs and exact service delegation

The MCP adapter is a thin `ControlService` delegate. The companion's conceptual
`ListDrivers`/`GetDriver`/`StartDriver`/`StopDriver`/`RestartDriver` operations map
to the landed internal `Service` methods as follows:

| Wire tool | Complete arguments object | Internal service call |
|---|---|---|
| `helianthus.runtime.list` | `{}` | `List()` |
| `helianthus.runtime.get` | `{"DriverID":"ebus.primary"}` | `Get(DriverID)` |
| `helianthus.runtime.start` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodStart, request)` |
| `helianthus.runtime.stop` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodStop, request)` |
| `helianthus.runtime.restart` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodRestart, request)` |

These are closed, case-sensitive objects: reject missing, additional or duplicate
members, non-object inputs and non-string values with
`INVALID_ARGUMENT`. Detect duplicates before decoding can discard them. List
has no members; get has exactly `DriverID`; each mutation has exactly the two
shown members. No idempotency key, request digest, receipt, principal, authority,
operation handle or caller-selected deadline member is accepted or returned.
This removes lifecycle command tracking entirely; `meta.data_hash` and internal
semantic replay digests retain their separate purposes.
A request body with trailing data is rejected at the transport as an invalid
request before any tool runs; `arguments` cannot carry trailing data.

`DriverID` matches `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`, at most 128 bytes,
and must identify a registered driver. A noncanonical or unregistered ID is
`NOT_FOUND`, without construction or endpoint access. `ExpectedRevision` echoes
the read-back `desired_revision`, never the catalog/view revision: a canonical
nonzero unsigned 64-bit decimal JSON string. Reject `"0"`, `"01"`, signs,
whitespace, numbers and overflow. Response revisions are canonical unsigned
64-bit decimal strings and may be `"0"` only for a withheld/unissued view.

Every call uses a finite context deadline. The transport adapter supplies a
bounded deadline when the transport has none and preserves an earlier caller
deadline; this adds no argument field. Mutations retain the service's fixed
refusal order, bounded namespace-wide serialization wait, deadline recheck
after acquiring it and pre-commit recheck. Neither same-desired requests nor
retries renew operation budgets. The adapter must not call DriverManager,
construct a provider, open an endpoint, reconcile or poll in place of the service.

### Read and mutation data

List `data` has exactly `catalog_revision` and `drivers`. Get `data` has exactly
`catalog_revision` and `driver`. Each driver object projects the landed cached
`DriverStatus` with exactly these fields:

| Wire field | Internal field / meaning |
|---|---|
| `driver_id` | `DriverID`, canonical configured identity |
| `enabled` | `Enabled`, configuration eligibility |
| `desired_state` | `DesiredState`, `RUNNING` or `STOPPED` |
| `desired_revision` | `DesiredRevision`, durable optimistic revision string |
| `observed_state` | `ObservedState`, `DISABLED`, `STOPPED`, `STARTING`, `RUNNING`, `DEGRADED`, `BACKOFF`, `STOPPING` or `FAILED` |
| `reason` | `Reason`, categorical manager reason string, never a raw error |
| `safety_quarantined` | `SafetyQuarantined`, unproven native close |
| `revision` | `Revision`, catalog/view revision string |

List includes every registered driver, sorted bytewise by `driver_id`, with
`drivers: []` for an empty catalog. Entries and `catalog_revision` come from
one coherent cached service read; every entry's `revision` equals that catalog
revision. Get uses its one cached entry's revision as `catalog_revision`.
Do not assemble a list with repeated get calls. Reads perform no endpoint I/O
and remain responsive while another driver is starting, stopping or blocked in
persistence. Internal event cursors and typed work slots are not public fields.
These G5 shapes supersede the older proposed `drivers.v1.*` inventory and richer
`DriverSnapshotV1` projection in [driver-runtime-v1.md](./driver-runtime-v1.md)
for this first external slice; that older proposal must not create extra tools,
fixed placeholder drivers or invented observations in PR 2.

Synthetic list `data` example (not a live observation):

```json
{
  "catalog_revision": "29",
  "drivers": [
    {
      "driver_id": "ebus.primary",
      "enabled": true,
      "desired_state": "RUNNING",
      "desired_revision": "7",
      "observed_state": "BACKOFF",
      "reason": "RETRY_SCHEDULED",
      "safety_quarantined": false,
      "revision": "29"
    }
  ]
}
```

Accepted mutations and same-desired no-ops return only this `data` shape:

```json
{"desired_state":"RUNNING","desired_revision":"8"}
```

Acceptance acknowledges durable intent, not native completion. Observe progress
and failure through list/get. START while desired RUNNING and STOP while desired
STOPPED are no-ops only after the revision comparison: they change no revision,
retry budget, observation or quarantine. RESTART requires desired RUNNING,
keeps it RUNNING and accepts a new replacement/revision each time. After a lost
RESTART response, read back before retrying: an old-revision retry conflicts;
a fresh-revision retry after settlement performs **another restart**. Readback
does not attribute completion to a particular call. No completed-call lookup
or replay result exists.

### Envelope, lifecycle errors and acceptance vectors

All five tools use the existing `meta`, `data`, `error` envelope, including
`meta.contract` (`name: helianthus-ebus-mcp`, `major: 1`, `minor: 0`),
`meta.consistency` (`mode: LIVE`), `meta.data_timestamp` and `meta.data_hash`.
Lifecycle tools accept no snapshot/consistency argument and do not read an eBUS
snapshot. `data_timestamp` is UTC RFC3339Nano response metadata, not a native
capture time. `data_hash` is the existing lowercase SHA-256 of the JSON-marshaled
`data` alone: stable member encoding and sorted lists produce the same hash for
the same data even when response metadata changes. Compute hashes in goldens;
do not make a literal digest a contract field. Success has `error: null`.

Refusals set MCP `isError: true` and use the existing error object members
`code`, `message`, `retriable`, `source_layer` (`gateway`). Messages are bounded,
categorical and sanitized. Normally `data` is null; `REVISION_CONFLICT` carries
only the current cached `{desired_state, desired_revision}` view, matching the
landed service refusal, without an observed completion claim. Preserve these
lifecycle codes rather than collapsing them into generic transport errors:

| Code | Meaning / retry |
|---|---|
| `INVALID_ARGUMENT` | Closed-shape/revision error or no finite service deadline; correct the call |
| `NOT_FOUND` | Noncanonical or unregistered ID; no effects |
| `FAILED_PRECONDITION` | Disabled configuration, unusable control, RESTART while STOPPED, quarantine or unresolved recovery; resolve the precondition |
| `UNAVAILABLE` | Persistence failure or pending ambiguous readback; retry only after resolution/readback |
| `DEADLINE_EXCEEDED` | Deadline expired before decision; use a new deadline and read back if delivery was uncertain |
| `REVISION_CONFLICT` | Stale desired revision; read back before deciding again |
| `TRANSITION_BUSY` | Typed slot full or namespace decision wait exceeded; bounded retry, no revision-comparison outcome implied |
| `RESOURCE_EXHAUSTED` | Bounded storage/reservation cannot fit; retry after capacity is available |
| `COUNTER_EXHAUSTED` | Required unsigned counter cannot advance; no wrap or retry loop |

The [ordered lifecycle refusal table](../architecture/runtime-driver-lifecycle.md#validate-decide-and-commit)
is authoritative when several checks fail. `CLOSE_UNCONFIRMED` is an observed
reason, not a request error. Semantic `ErrorID` values remain unchanged in their
own domain. No lifecycle GraphQL field, resolver, mutation or subscription is
introduced; existing eBUS MCP/GraphQL status parity remains required.

PR 2 must supply deterministic schema/output goldens and synthetic
discovery/dispatch over every ordinary MCP transport the gateway offers (HTTP
today) with eeBUS disabled; verify exact closed fields, duplicate member refusal,
transport-level rejection of trailing data, sorted coherent reads and every
error mapping.
Apply amended CTL-01/02 (reads), CTL-03/05/14/15/19 (validation, refusal order and
deadlines), CTL-04/06/10/11 (no-op and lost responses), CTL-07/08/09 (serialized
replacement/recovery), CTL-12/13/16 (revision/durability) and CTL-17/18
(bootstrap/disabled configuration). Preserve A2 LIFE close-before-replacement
and late-result fences. This page supplies documentation acceptance only;
transport execution, smoke tests and hardware qualification remain unverified.

## Observe-First Bus MCP Contract (`DOC-06`)

### Scope

This `DOC-06` section freezes only the narrow M2 MCP slice shipped by
`ISSUE-GW-04`:

- `ebus.v1.bus.summary.get`
- `ebus.v1.bus.messages.list`
- `ebus.v1.bus.periodicity.list`

This `DOC-06` freeze covers the M2 `ebus.v1.bus.*` tools only. Shared
watch-summary MCP behavior is frozen separately in `DOC-09`.

### Invariants

- `ebus.v1.bus.*` stays separate from semantic MCP tools because it exposes
  bus-observability and transport-capability data rather than protocol-agnostic
  semantic state.
- The `ebus.v1.bus.*` tools are bounded summary/list surfaces. They do not
  construct or expose unbounded traffic history on demand.
- All three tools accept the standard optional `consistency` argument. The two
  list tools also accept an optional positive integer `limit`.
- Omitting `limit` returns all currently retained records; it does not upgrade
  the surface into an unbounded dump.
- These tools appear in `tools/list` only when the runtime wires a real bus
  observability provider into the MCP server.

### Degraded Behavior

- Top-level `status` remains part of the public contract for all three tools so
  passive capability, warmup, degraded, and timing-quality state stay explicit
  even when retained history still exists.
- When passive support is unavailable or still warming up, the surface reports
  that state explicitly through `status.capability`, `status.warmup`, and
  `status.timing_quality`; it does not silently degrade those conditions into
  empty lists or fake zero-valued timing claims.
- Busy-time and periodicity timing quality may be `estimated` or `unavailable`
  on the current transport stack. The MCP surface may not imply exact wire
  timestamps when the runtime does not have them.

### Shared Request and Envelope Rules

All three tools return the standard Helianthus MCP envelope:

- `meta.contract`
- `meta.consistency`
- `meta.data_timestamp`
- `meta.data_hash`
- `data`
- `error`

`consistency.mode` supports:

- `LIVE` (default when omitted)
- `SNAPSHOT` with required `snapshot_id`

### Tool Inventory

- `ebus.v1.bus.summary.get`
  - arguments: optional `consistency`
- `ebus.v1.bus.messages.list`
  - arguments: optional positive integer `limit`, optional `consistency`
- `ebus.v1.bus.periodicity.list`
  - arguments: optional positive integer `limit`, optional `consistency`

### `ebus.v1.bus.summary.get`

Returns the current bus-observability summary snapshot.

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | object | Current transport class, capability, warmup, timing-quality, and degraded state. |
| `messages` | object | Bounded recent-message summary: `count`, `capacity`. |
| `periodicity` | object | Bounded periodicity summary: `count`, `capacity`. |
| `counters` | object | Overflow counters: `series_budget_overflow_total`, `periodicity_budget_overflow_total`. |

`status.capability` fields:

| Field | Meaning |
| --- | --- |
| `active_supported` | The runtime can observe its own active traffic on this transport. |
| `passive_supported` | The runtime/transport topology supports the passive observe-first path. |
| `broadcast_supported` | The passive path is able to serve broadcast-derived observe-first behavior. |
| `passive_available` | `true` only when passive capability has reached `available`. |
| `passive_state` | One of `unavailable`, `warming_up`, `available`. |
| `passive_reason` | Present when the passive path is unavailable. Current runtime reasons are `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`, `unsupported_or_misconfigured`, and `capability_withdrawn`. |
| `endpoint_state` | Passive tap endpoint lifecycle state from the runtime. |
| `tap_connected` | Current passive tap connection flag. |

`status.warmup` fields:

| Field | Meaning |
| --- | --- |
| `state` | Matches the bounded state set `unavailable`, `warming_up`, `available`. |
| `blocker` | Current dominant warmup blocker when the path is not fully ready. |
| `elapsed_seconds` | Current warmup-session elapsed time when the runtime has one. |
| `completed_transactions` | Number of passive completed transactions counted for the current session. |
| `required_transactions` | Threshold required for normal warmup completion. |
| `completion_mode` | Current/last completion mode when known. |

`status.timing_quality` fields:

| Field | Meaning |
| --- | --- |
| `active` | Current timing quality for active-path observations. |
| `passive` | Current timing quality for passive-path observations. |
| `busy` | Current timing quality for busy-time accounting. |
| `periodicity` | Current timing quality for periodicity accounting. |

Current timing-quality values evidenced on the merged `GW-04` runtime are
`estimated` and `unavailable`.

`status.degraded` fields:

| Field | Meaning |
| --- | --- |
| `active` | `true` when degraded reasons are present. |
| `reasons` | Bounded degraded-reason list. Current MCP output includes passive unavailability reasons and `dedup_degraded`. |

### `ebus.v1.bus.messages.list`

Returns a bounded slice of recent bus-message records from the observe-first
store.

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | object | Same status model as `bus.summary.get`. |
| `count` | integer | Number of retained recent-message records in the bounded store. |
| `capacity` | integer | Store capacity for recent-message retention. |
| `items` | array | The most recent retained records, optionally truncated by `limit`. |

`items[]` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `scope` | string | Runtime traffic scope classification such as active or passive. |
| `family` | string | Family classifier such as `B509`, `B524`, or `other`. |
| `frame_type` | string | Frame-shape classifier from the observability store. |
| `outcome` | string | Runtime outcome classifier such as success or timeout. |
| `observed_at` | RFC3339 timestamp | Gateway observation timestamp. |
| `source_address` | integer | Source device address. |
| `target_address` | integer | Target device address. |
| `request_len` | integer | Request frame length in bytes. |
| `response_len` | integer | Response frame length in bytes. |

Ordering and bounds:

- `count` and `capacity` describe the whole bounded store, not just the
  returned slice.
- If `limit` is present, the gateway returns the newest retained `limit`
  records.
- Returned records preserve retained order within that newest suffix.

### `ebus.v1.bus.periodicity.list`

Returns a bounded slice of periodicity summaries from the observe-first store.

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | object | Same status model as `bus.summary.get`. |
| `count` | integer | Number of retained periodicity tuples in the bounded store. |
| `capacity` | integer | Configured periodicity-tuple capacity. |
| `items` | array | The most recent retained periodicity tuples, optionally truncated by `limit`. |

`items[]` fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `source_bucket` | string | Normalized source bucket key used by the store. |
| `target_bucket` | string | Normalized target bucket key used by the store. |
| `primary` | integer | Primary opcode byte. |
| `secondary` | integer | Secondary opcode byte. |
| `family` | string | Family classifier such as `B509` or `B524`. |
| `state` | string | Per-tuple periodicity state. The merged `GW-04` runtime currently emits `warming_up` and `available`. |
| `last_seen` | RFC3339 timestamp | Most recent observation for this tuple. |
| `sample_count` | integer | Number of samples accepted into the tuple summary. |
| `last_interval` | string | Last observed interval, when available. |
| `mean_interval` | string | Mean interval, when available. |
| `min_interval` | string | Minimum interval, when available. |
| `max_interval` | string | Maximum interval, when available. |

Periodicity semantics:

- Per-tuple `state` stays local to that tuple. Overall passive availability and
  timing-quality state still come from the top-level `status`.
- Retained periodicity entries may still be returned while overall passive
  capability is unavailable. Consumers must not treat a non-empty `items` list
  as proof that the passive path is currently healthy.
- Interval fields are optional. The surface omits them when the runtime does
  not yet have a value to publish.

## Watch Summary MCP Contract (`DOC-09`)

Shared watch-summary details are frozen in [`watch-summary.md`](./watch-summary.md).
This section captures the MCP-specific surface only.

Tool inventory:

- `ebus.v1.watch.summary.get`
  - arguments: optional `consistency`

MCP-specific invariants:

- Tool registration is provider-gated: the tool appears in `tools/list` only
  when the runtime wires a watch-summary provider (shadow cache lane).
- Without provider wiring, tool calls fail as unknown tool.
- `consistency.mode` follows the standard MCP rules (`LIVE` by default;
  `SNAPSHOT` with required `snapshot_id`).
- Payload fields use snake_case and mirror the shared watch-summary schema.

### Unsupported or Unproven Cases

- No GraphQL `busSummary`, `busMessages`, or `busPeriodicity` freeze exists in
  this lane.
- No Portal-specific watch-summary surface is frozen here.
- No unbounded traffic dump or timeline stream is part of this M2 bus contract.
- No exact wire-timestamp guarantee is frozen for current transports.
- No numeric busy-ratio MCP payload is frozen here; in M2 the MCP surface
  freezes summary/list semantics and explicit timing-quality state only.

### Evidence

- Runtime lane: [Project-Helianthus/helianthus-ebusgateway#376](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/376)
- Merged implementation PR: [Project-Helianthus/helianthus-ebusgateway#377](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/377)
- Unknown: recovery validation. The historical recovery probe remained
  `blocked-infra` with `infra_reason=adapter_no_signal`; the implementation PR
  merged under explicit owner override after the official add-on/runtime restore
  was re-verified cleanly. The probe artifact is identified in that PR by the
  path suffix `full88-probe-t01-after-adapter-reboot/index.json`; its full workspace
  path is omitted under publication policy. This is not hardware evidence for
  the G5 lifecycle tools.
- Gateway code/test references (branch links, not immutable evidence coordinates):
  - MCP tool inventory and provider wiring:
    [Project-Helianthus/helianthus-ebusgateway/cmd/gateway/mcp_bus_observability_integration_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/mcp_bus_observability_integration_test.go)
  - MCP payload shape and limit/snapshot behavior:
    [Project-Helianthus/helianthus-ebusgateway/mcp/server_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/server_test.go)

### Falsification Cases

This contract is wrong if later review proves any of the following:

- `ebus.v1.bus.*` appears in `tools/list` without a real bus observability
  provider being wired
- either list tool fabricates unbounded history when `limit` is omitted
- passive unavailability or warmup becomes implicit instead of remaining visible
  in top-level `status`
- busy-time or periodicity timing precision is implied without explicit
  `timing_quality`

### Concrete Examples

Summary response fragment:

```json
{
  "data": {
    "status": {
      "capability": {
        "passive_state": "unavailable",
        "passive_reason": "unsupported_or_misconfigured"
      },
      "timing_quality": {
        "passive": "unavailable",
        "busy": "unavailable",
        "periodicity": "unavailable"
      }
    },
    "messages": {
      "count": 1,
      "capacity": 1024
    }
  }
}
```

Messages response fragment:

```json
{
  "data": {
    "count": 3,
    "capacity": 16,
    "items": [
      {
        "scope": "passive",
        "family": "B524",
        "frame_type": "broadcast",
        "outcome": "success"
      }
    ]
  }
}
```

Periodicity response fragment:

```json
{
  "data": {
    "count": 2,
    "capacity": 8,
    "items": [
      {
        "family": "B524",
        "state": "available",
        "last_interval": "30s",
        "mean_interval": "29s"
      }
    ]
  }
}
```

## Implemented Surface

The legacy "Core stable" inventory label below does not confer stability
before 1.0; all listed namespaces remain pre-stable.

Note: This inventory reflects the current known tool surface. The gateway may expose additional tools discovered via the MCP `tools/list` endpoint.

- Core stable (`ebus.v1.*`)
  - `ebus.v1.runtime.status.get`
  - `ebus.v1.adapter_info.get`
  - `ebus.v1.registry.devices.list`
  - `ebus.v1.registry.devices.get`
    - **Conclusion: Proven.**
    - JSON response items carry `discovery_source` and
      `verification_state` fields (P3.5). `discovery_source` is one of
      `passive_observed | static_seed | active_confirmed`;
      `verification_state` is one of
      `candidate | corroborated_pending | identity_confirmed`.
      The implementation and historical review records are owned by the
      [gateway registry source](https://github.com/Project-Helianthus/helianthus-ebusgateway/tree/main/internal).
      Both are omitted when the registry has no slot record for the
      address. For `devices.list` the labels reflect the entry's
      canonical primary address; for `devices.get(address=X)` the labels
      reflect the queried address X. Each face retains its original
      discovery source when verification advances: a static-seeded face
      remains `static_seed`, a passively discovered face remains
      `passive_observed`, and `active_confirmed` applies only when active
      discovery created that face. Passive corroboration may advance the
      independent verification state to `corroborated_pending`; identity
      confirmation may advance it to `identity_confirmed`. Neither event
      rewrites `discovery_source`.
      Per the
      [`05-static-seed-provenance`](../architecture/atr/05-static-seed-provenance.md)
      ATR, addresses planted by the productids static seed table MUST
      initially surface as `static_seed/candidate`. Passive or active
      verification changes only `verification_state`; it MUST NOT rewrite
      the face's `static_seed` discovery source.
  - `ebus.v1.registry.planes.list`
  - `ebus.v1.registry.methods.list`
  - `ebus.v1.semantic.zones.get`
  - `ebus.v1.semantic.dhw.get`
  - `ebus.v1.semantic.energy_totals.get`
  - `ebus.v1.semantic.boiler_status.get`
  - `ebus.v1.semantic.system.get`
  - `ebus.v1.semantic.system.set_config`
    - Required arguments: `field` and `value`, both strings; `field` uses
      camelCase names such as `dhwBivalencePointC`.
    - Returns the standard `meta`, `data`, `error` envelope, with
      `meta.contract`, `meta.consistency`, `meta.data_timestamp` and
      `meta.data_hash`. The setter uses `LIVE` consistency.
    - Success returns `data.success: true`, omits `data.error`, and leaves
      top-level `error: null`. A bound rejection returns `data.success: false`
      and `data.error` naming the active bound, with top-level `error: null`
      and MCP `isError: true`, before any bus write. Error text includes
      `controller profile <identity> allows [min, max]` or
      `controller identity unmatched (<reason>): conservative policy bound
      [-20, 50] applies`.
  - `ebus.v1.semantic.circuits.get`
  - `ebus.v1.semantic.radio_devices.get`
    - `data: []` means the startup radio inventory probe completed without
      publishable radio slots. `data: null` means the plane has not been
      published yet.
  - `ebus.v1.semantic.fm5_mode.get`
    - stable scalar mode retained for existing consumers
  - `ebus.v1.semantic.solar.get`
  - `ebus.v1.semantic.cylinders.get`
  - `ebus.v1.semantic.schedules.get`
  - `ebus.v1.semantic.schedules.set_zone_time_program`
  - `ebus.v1.semantic.schedules.set_dhw_time_program`
  - `ebus.v1.semantic.snapshot.get`
  - `ebus.v1.snapshot.capture`
  - `ebus.v1.snapshot.drop`
  - `ebus.v1.rpc.invoke`
- Observe-first bus surface (registered only when the runtime wires bus
  observability)
  - `ebus.v1.bus.summary.get`
  - `ebus.v1.bus.messages.list`
  - `ebus.v1.bus.periodicity.list`
- Observe-first watch-summary surface (registered only when the runtime wires
  watch-summary provider)
  - `ebus.v1.watch.summary.get`
- Legacy aliases
  - `ebus.devices`
  - `ebus.invoke`

## System Bound Payload Contract

This contract is implemented by the gateway's GraphQL system-bounds resolver
(`graphql/system_bounds.go`), the `setSystemConfig` mutation path
(`graphql/mutations.go`), and the MCP tool `ebus.v1.semantic.system.set_config`
handler in companion gateway [pull request #1033](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1033),
which is merged after this page per the documentation gate; this page describes
the behaviour of that change, the reviewed source artifact.
The contract test [`tests/test_system_config_bound_contract.py`](../tests/test_system_config_bound_contract.py)
in this repository pins the documented members and examples.

`ebus.v1.semantic.system.get` publishes `config.dhw_bivalence_point_bound`.
Its `source` is `controller_profile` with `profile`, or `unmatched_policy`
with `reason`. The reason values are `unknown_profile`, `unknown_register`,
`unqualified_bound` and `invalid_bound`. Empty optional `reason` and `profile`
strings are omitted in MCP and `null` in GraphQL. The required boolean
`narrowed_only` is true for every `controller_profile` bound and false for
`unmatched_policy` (GraphQL: `narrowedOnly: Boolean!`). A profile identifies
an observation context, not an installation. Its bound is a **Hypothesis**
for the target installation and can only narrow the policy window `-20..50`:
`min = max(profile min, -20)`, `max = min(profile max, 50)`. An empty
intersection uses `unmatched_policy` with reason `invalid_bound`; otherwise
the source and profile identity remain `controller_profile`.
The empty-intersection fallback bound is the policy window `-20..50`.
Widening needs installation-qualified evidence, which no seeded profile
provides. The BASV0 profile bound `-20..20` narrows the window on a qualified
match.

The policy window equals the range the gateway accepted before profiles existed,
so v1 clients see no change, and narrowing applies only on a qualified profile
match (none is reachable until identities are acquired at discovery, gateway
[#1034][gateway-bound-discovery]).
Unmatched controllers (unknown identity, unseeded family, missing API qualifier,
profile without this selector, or an unqualified or invalid profile bound) use
`min_c: -20`, `max_c: 50` and `source: unmatched_policy` with the reason codes
above.

The following response `data` fragments pin the two resolved shapes. The
profile fragment illustrates a matched observation context; current discovery
still uses the unmatched policy as described below.

```json
{
  "config": {
    "dhw_bivalence_point_bound": {
      "min_c": -20,
      "max_c": 20,
      "narrowed_only": true,
      "source": "controller_profile",
      "profile": "BASV0/SW0217/HW8803/API1.1"
    }
  }
}
```

```json
{
  "config": {
    "dhw_bivalence_point_bound": {
      "min_c": -20,
      "max_c": 50,
      "narrowed_only": false,
      "source": "unmatched_policy",
      "reason": "unknown_profile"
    }
  }
}
```

Before the first resolution, MCP omits `config.dhw_bivalence_point_bound`
entirely. GraphQL returns `null` for `dhwBivalencePointBound`.

## Semantic Payload Notes

### Post-M9 Pending FM5 Contract

`ebus.v1.semantic.fm5_interpretation.get` is the target MCP-first post-M9
behavioral remediation and is not part of the implemented surface above until
the gateway implementation PR merges. The method returns `null` until the
first coherent structural classification; it never fabricates `GPIO_ONLY` or
`ABSENT` during bootstrap. Once available, its target object contains exactly
`mode`, `degraded_reason`, and `evidence_revision`. Structural `mode` is the
last coherent classification and does not change on a transient acquisition
failure. A healthy current `INTERPRETED` result and a fresh coherent `ABSENT`
result have no reason; `GPIO_ONLY` carries only
`CONFIGURATION_NOT_INTERPRETABLE`; a transient provider-owned reason may
accompany the unchanged retained structural mode. `evidence_revision` binds
the tuple to one acquisition result. Consumers must not infer the reason from empty
solar/cylinder payloads. The closed mode/reason semantics are frozen in
[`eebus-operator-admin.md`](./eebus-operator-admin.md). It is additive within
the single `ebus.v1.*` namespace; no v2 tool or legacy alias is introduced.
The older `ebus.v1.semantic.fm5_mode.get` scalar retains its frozen response
shape and is not a substitute for the degradation verdict.

- `ebus.v1.semantic.circuits.get` exposes explicit per-circuit ownership as `managing_device`.
- `managing_device.role` is always present and is one of `REGULATOR`, `FUNCTION_MODULE`, or `UNKNOWN`.
- `managing_device.device_id` and `managing_device.address` are populated only when the gateway has ownership evidence for the current topology.
- `ebus.v1.semantic.system.get` exposes `config.dhw_bivalence_point_bound`
  (`min_c`, `max_c`, `source`, optional `reason` and `profile`): the range
  `ebus.v1.semantic.system.set_config` accepts for `dhwBivalencePointC`.
  A value outside it is rejected before any bus write. Before the first
  resolution, MCP omits the bound entirely; GraphQL returns `null`.
  Empty optional `reason` and `profile` strings are omitted in MCP and
  `null` in GraphQL. Resolution uses only registry discovery/import metadata,
  with no bus I/O or on-demand system-information identifier reads. Existing
  polling does not acquire `0006h` `interface_version` or `0007h`
  `interface_revision` (the registry identity's API version and revision).
  Today even the seeded BASV0 identity resolves to `unknown_profile`, so every
  bound is the policy window `-20..50` with `source: unmatched_policy`.
  `controller_profile` can appear only after gateway issue
  [#1034][gateway-bound-discovery]
  acquires both identifiers in discovery. The bound is resolved from current
  registry metadata at validation and at publication, and published bounds
  update on the next system publication. A controller swap at the same
  address retains the registry identity until that metadata changes, so the
  identity can be stale. Registry/invoker writes through
  `ebus.v1.rpc.invoke` have no API qualifier and always apply the unmatched
  policy. Every numeric configuration write rejects `NaN` and positive or
  negative infinity before encoding, with `success: false` and no bus request.
  See [`graphql.md`](./graphql.md) "System Config Write Bounds" for the
  profile and unmatched-policy rules.
- `ebus.v1.semantic.system.get` no longer exposes `vr71_circuit_start_index`; that threshold was a gateway heuristic and is not part of the canonical contract.

[gateway-bound-discovery]:
  https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1034

## RPC Method Reference - Vaillant System Plane

Methods available via `ebus.v1.rpc.invoke` on the `system` plane for
Vaillant/Saunier/AWB controllers.

### `read_timer`

Reads per-day weekly schedule timer programs via B524 opcode `0x03`.

**Intent:** `READ_ONLY`

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `source` | byte | yes | Initiator address (gateway = 113) |
| `sel1` | byte | yes | Timer selector 1 (controller-specific) |
| `sel2` | byte | yes | Timer selector 2 (controller-specific) |
| `sel3` | byte | yes | Timer selector 3 (controller-specific) |
| `weekday` | byte | yes | Weekday index: `0x00=Mon .. 0x06=Sun` |

**Wire format:** `[0x03, SEL1, SEL2, SEL3, WD]`

**Response fields:** `opcode`, `sel1`, `sel2`, `sel3`, `weekday`, `value` (raw
timer bytes), `slot_count` (number of time slots). When the controller returns
no data, `value` is invalid.

### `read_raw`

Raw opcode passthrough for investigation. Sends caller-provided payload bytes
verbatim on B524.

**Intent:** `MUTATE` (requires `allow_dangerous: true` and `idempotency_key`)

| Param | Type | Required | Description |
| --- | --- | --- | --- |
| `source` | byte | yes | Initiator address (gateway = 113) |
| `payload` | `[]byte` | yes | Raw opcode bytes (1-16 bytes) |

**Response fields:** `request_payload` (echo of sent bytes), `response_payload`
(controller response), `value` (alias for response_payload). When no response
data, `value` is invalid.

**Safety note:** This method is intentionally `readOnly: false` because it can
send arbitrary opcodes including mutating ones (for example `0x04` timer
write). The gateway enforces `allow_dangerous` and idempotency gates.

## Plane Boundary Note

- `scan` is treated as a cross-device discovery layer and is not modeled as a
  heat-source class plane.
- Heat-source planes (for class-specific modeling) are documented under
  architecture decisions and class design docs.

## MCP-first Usage in Development

Helianthus uses MCP as the first integration surface for new capabilities. The
development order is:

1. MCP prototype and stabilization (`ebus.v1.*` contract)
2. GraphQL parity after MCP determinism/contract gates are green
3. Consumer rollout (HA and others) after GraphQL parity

The architecture model and gates are documented in:

- [architecture/mcp-first-development.md](../architecture/mcp-first-development.md)
- [architecture/bus-observability-v2.md](../architecture/bus-observability-v2.md)
- [api/watch-summary.md](./watch-summary.md)
