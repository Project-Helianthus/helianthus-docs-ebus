# MCP Endpoint

The cross-protocol bounded Modbus V1 surface is specified separately in
[`modbus-v1-mcp.md`](./modbus-v1-mcp.md). It remains raw/profile evidence and
does not publish canonical PV semantics.

The disabled-by-default add-on configuration, protected endpoint-file, and
single direct gateway process lifecycle are specified in
[`modbus-v1-addon-runtime.md`](./modbus-v1-addon-runtime.md). It does not
qualify a live device or extend the MCP schema.

Several Modbus TCP endpoints, each a separately qualified managed driver
instance with its own status, are specified in
[`modbus-multi-endpoint-runtime.md`](./modbus-multi-endpoint-runtime.md). That
page adds one optional `instance` argument to three vendor status tools and to
the existing SunSpec status tool, and defines no other tool or field.

## Current Status

Until the Helianthus 1.0 release, all MCP namespaces, including `ebus_v1_*`,
are pre-stable; the namespace version alone is not a stability promise. A
contract version declared by an individual surface, such as `1.0`, does not
end this period. Schema or behaviour
may change with updated goldens, documentation, and a note in the pull request.
There is no experimental namespace or core-stable graduation before 1.0;
both will be discussed after 1.0. Existing envelope, determinism, golden-test,
and documentation-gate requirements remain in force.

The MCP server is implemented and served by `cmd/gateway` at `/mcp`.

The target additive Vaillant-only
`ebus_v1_runtime_status_get.data.vaillant_regulator_capability` member is
specified in [`vaillant-regulator-capability-v1.md`](./vaillant-regulator-capability-v1.md).
It remains absent from the implemented-surface inventory until open gateway #947
merges after the documentation gate; an older or missing
`vaillant_regulator_capability` member maps to consumer `UNKNOWN`. It does not
imply a gateway-wide or cross-protocol result.

## G5 runtime lifecycle MCP contract (D4)

This is the first external control contract for
[docs issue #717](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/717),
a partial slice of [gateway #1032](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1032).
The five runtime tools are **implemented** and included in the implemented
inventory below. The gateway always lists them while it runs and they answer
`UNAVAILABLE` when no service is composed. Registration is owned by
[gateway runtime control](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/runtime_control.go)
and composed by the
[HTTP server](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/gateway_http_server.go). A5's internal service for
`ebus.primary` is implemented by the merged
[gateway PR #1241](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1241).
That software status establishes neither hardware validation nor a universal
provider SPI. The [lifecycle contract](../architecture/runtime-driver-lifecycle.md)
owns durable decisions, refusal order and CTL/LIFE semantics.

### Ordinary discovery and dispatch

The exact tool family is `helianthus_runtime_{list,get,start,stop,restart}`.
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
Every namespace, including `ebus_v1_*`, remains pre-stable until 1.0. Intentional
changes require documentation, deterministic envelopes, schema/output goldens
and PR explanation; neither a compatibility veto nor promotion to a new major
or experimental namespace applies before 1.0.

### Closed inputs and exact service delegation

The MCP adapter is a thin `ControlService` delegate. The companion's conceptual
`ListDrivers`/`GetDriver`/`StartDriver`/`StopDriver`/`RestartDriver` operations map
to the landed internal `Service` methods as follows:

| Wire tool | Complete arguments object | Internal service call |
|---|---|---|
| `helianthus_runtime_list` | `{}` | `List()` |
| `helianthus_runtime_get` | `{"DriverID":"ebus.primary"}` | `Get(DriverID)` |
| `helianthus_runtime_start` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodStart, request)` |
| `helianthus_runtime_stop` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodStop, request)` |
| `helianthus_runtime_restart` | `{"DriverID":"ebus.primary","ExpectedRevision":"7"}` | `Decide(ctx, MethodRestart, request)` |

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
`DriverStatus` with exactly these fields; every member except the optional
`recovery` is always present:

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
| `recovery` | Optional recovery schedule, present only while `observed_state` is `BACKOFF`; defined below |

The driver object stays closed except for that one optional member. `recovery`
is present only while `observed_state` is `BACKOFF`. In `DISABLED`, `STOPPED`,
`STARTING`, `RUNNING`, `DEGRADED`, `STOPPING` and `FAILED` it is absent: never
`null`, never an empty object. `RETRY_SCHEDULED` is a `reason` value that
`BACKOFF` reports, not an observed state, so a reason alone never admits the
member. A driver in `BACKOFF` may omit it; absence there means only that no
schedule is published. Reads still perform no endpoint I/O: the member reports
the cached schedule.

When present, `recovery` is a closed object with exactly these four members, all
required:

| `recovery` member | Type and meaning |
|---|---|
| `attempt` | Integer of at least 1: the one-based number of the recovery attempt scheduled for `next_attempt_at` |
| `next_attempt_at` | String: when that attempt is due, an RFC 3339 UTC timestamp written with the `Z` designator, whole seconds or up to nine fractional digits, never a numeric offset |
| `last_failure_class` | String: one of `DIAL_FAILED`, `TIMEOUT`, `TRANSPORT_CLOSED` or `OTHER` |
| `last_failure_cause` | String: display text of the last failure, 0 to 160 characters, printable ASCII (U+0020 to U+007E), with every address stripped by the gateway |

This contract names no failure class for a driver attempt: its closed reason
codes describe the driver state, not the attempt that failed. `last_failure_class`
therefore has the following closed set, and adding a value is a contract change:

| `last_failure_class` | Meaning |
|---|---|
| `DIAL_FAILED` | The transport connection could not be established |
| `TIMEOUT` | The attempt, or an established transport, exceeded its time limit |
| `TRANSPORT_CLOSED` | An established transport was closed or lost |
| `OTHER` | Any other retryable failure |

`next_attempt_at` is a scheduled time, not a promise that the attempt starts at
that instant. The gateway removes every address from `last_failure_cause` before
publishing it: no IP address, host name, port, URL, device path or hardware
address remains. Consumers display the text and do not parse it; the
machine-readable member is `last_failure_class`. Accepted-mutation data and
`REVISION_CONFLICT` data are unchanged and never carry `recovery`; the member
adds no tool, argument, error code or GraphQL field.

Compatibility: `recovery` is an additive, optional member, a change of the kind a
minor revision would admit. Responses for drivers outside `BACKOFF` are
unchanged, so a consumer written against the closed driver object without
`recovery` keeps working for them. A consumer that rejects unknown driver members
must accept `recovery` before it reads from a gateway that publishes it. The
pre-1.0 rule above governs: this change is recorded by this documentation, the
updated examples and the pull request, and `meta.contract` stays `major: 1`,
`minor: 0`.

The examples below show one `BACKOFF` driver with `recovery` and one `RUNNING`
driver without it. The committed checker rejects `recovery` in every other
observed state, any other driver member, and a `recovery` object with a missing,
extra, out-of-range or malformed member. Gateway output goldens must cover the
same cases.

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

The list/get data shapes above describe successful reads with validated durable
revision bounds. If either the issued-revision high-water mark or durable catalog
revision is missing with existing control material, malformed, unreadable,
unsupported or overflowing, both `helianthus_runtime_list` and
`helianthus_runtime_get` refuse with `UNAVAILABLE` and `data: null`. Return no
driver snapshot, success catalog or usable revision; never substitute zero,
a sentinel, stale cached state or corrupt values, even if the other bound is
valid. With both counters valid and coherent cached records, one or all drivers
may be `FAILED` while reads retain the ordinary sorted, coherent projection.

A zero-valued catalog revision always refuses, including for an empty registry.
With existing control material that includes a registered driver, a zero-valued
issued mark also refuses. Both use the same non-retriable read envelope with
the categorical message `Durable control state unavailable; offline repair required`.
These zero values cannot supply revision authority even when the other counter
is valid. An empty registry in which nothing was ever decided may retain issued
mark 0, but its catalog revision must still start at 1. Preserve the record under
the load rules; no bootstrap seed follows.

The issued mark must also bound every desired revision in the verified retained
D5 recovery stream. If any such revision exceeds the mark, or the retained D5
stream cannot be verified, the shared issued bound is unvalidated even when
all current records are at or below it. After the existing get identity checks,
every registered get and the entire list return non-retriable `UNAVAILABLE`
with `data: null` and no usable revision. Preserve the mark, records and D5
material; do not advance the mark, discard recovery evidence or bootstrap to
make reads succeed.

For get, the existing driver-ID input checks and registry-membership refusal are decided first, because they need no durable state: a noncanonical or unregistered `DriverID` returns `NOT_FOUND`, without construction or endpoint access; only a canonical, registered driver ID proceeds to the durable-bounds check and its `UNAVAILABLE` refusal; list has no driver ID.

With both shared counters valid, a registered driver whose existing durable
record has a missing or malformed `desired_revision` has no authoritative read
revision. After the existing get identity checks, get of that driver and the
entire list refuse with `UNAVAILABLE` and `data: null`, using the same
non-retriable read envelope as invalid shared bounds. Do not omit the driver,
substitute the current mark, or use stale cached fields. Get of an independent
driver with a validated coherent record remains usable. The current-mark
fallback applies only when the driver's record is absent, never when an
existing record is malformed; preserve that record under the load rules.

The same refusal applies when both shared counters and `desired_revision`
are valid but the existing registered record has a missing or invalid
`desired_state` (a present value other than exactly `RUNNING` or `STOPPED`).
After the existing get identity checks, the affected get and the entire list
return `UNAVAILABLE` with `data: null` and no usable revision in the same
non-retriable read envelope. An independent valid get remains usable. Preserve
the record under the load rules; no current-mark fallback, invented intent or
omission of the driver is allowed.

With both shared counters individually valid, an existing registered record
must satisfy `0 < desired_revision <= issued mark`. A canonical zero revision
or a revision above the issued mark is incoherent and receives the same refusal:
after the existing get identity checks, the affected get and the entire list
return non-retriable `UNAVAILABLE` with `data: null` and no usable revision.
An independent get with a coherent record remains usable. Preserve the record;
never substitute the mark, omit the driver, clamp the revision or advance the
mark to make the read succeed. For example, with issued mark `7`, record
revisions `0` and `8` refuse; distinct revisions `6` and `7` satisfy this bound.
The catalog revision is a separate view counter, never a desired-revision bound.

Existing registered records must also have distinct desired revisions across
drivers. If two records share a revision, both affected gets and the entire
list return non-retriable `UNAVAILABLE` with `data: null` and no usable revision
after the existing get identity checks; an independent get with a coherent,
noncolliding record remains usable. For example, two registered records at
revision `6` under issued mark `7` both refuse. Preserve both records; do not
choose a winner, renumber either record or use the absent-record mark fallback.
This uniqueness check applies to stored record revisions, not the current-mark
projection for an absent record.

For invalid shared bounds, unverified retained D5 material, or missing, malformed
or incoherent durable record fields (including revision collisions), use
the categorical message `Durable control state unavailable; offline repair required`.

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
      "revision": "29",
      "recovery": {
        "attempt": 3,
        "next_attempt_at": "2000-01-01T00:00:08Z",
        "last_failure_class": "DIAL_FAILED",
        "last_failure_cause": "dial: connection refused"
      }
    }
  ]
}
```

Synthetic get `data` example for the same driver after it recovered (not a live
observation):

```json
{
  "catalog_revision": "30",
  "driver": {
    "driver_id": "ebus.primary",
    "enabled": true,
    "desired_state": "RUNNING",
    "desired_revision": "7",
    "observed_state": "RUNNING",
    "reason": "NONE",
    "safety_quarantined": false,
    "revision": "30"
  }
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

For list/get, the `UNAVAILABLE` row also covers invalid or unvalidatable durable
revision bounds (including the retained D5 cross-check) and incoherent or colliding record revisions: set `isError: true`, `data: null` and `retriable: false`, using
the existing categorical error members and envelope. Hash JSON null as usual;
metadata must not imply a validated lifecycle revision. Explicit GUID-preserving
offline repair is required; retry, restart, provider recovery and configuration
reload cannot repair the bounds. Keep the shell and tools available. The ordered
refusal table still governs mutations, where unusable control remains
`FAILED_PRECONDITION`; the read error grants no online repair or bypass of the
offline reset's own requirement for validated bounds.

Synthetic failure envelopes below use a deterministic synthetic clock and hash the JSON text `null`; neither metadata value is revision authority. Missing, malformed, unreadable, unsupported and overflowing bounds, retained D5 verification failures or revisions above the mark, and incoherent or colliding record revisions, use the same categorical envelope without exposing the invalid value. The get label identifies the manager registry read, not a new tool. The outer MCP tool result must set `isError: true`; the payload envelopes below contain exactly `meta`, `data`, and `error`.

The `data_hash` values are publication placeholders, not wire values. Validation requires `<computed-data-hash>` and replaces it in memory with the lowercase SHA-256 digest of the JSON text `null`; no concrete digest is published.

Synthetic list failure with an invalid issued bound:

```json
{
  "meta": {
    "contract": {
      "name": "helianthus-ebus-mcp",
      "major": 1,
      "minor": 0
    },
    "consistency": {
      "mode": "LIVE"
    },
    "data_timestamp": "2000-01-01T00:00:00Z",
    "data_hash": "<computed-data-hash>"
  },
  "data": null,
  "error": {
    "code": "UNAVAILABLE",
    "message": "Durable control state unavailable; offline repair required",
    "retriable": false,
    "source_layer": "gateway"
  }
}
```

Synthetic get of `ebus.primary` failure with an invalid catalog revision:

```json
{
  "meta": {
    "contract": {
      "name": "helianthus-ebus-mcp",
      "major": 1,
      "minor": 0
    },
    "consistency": {
      "mode": "LIVE"
    },
    "data_timestamp": "2000-01-01T00:00:00Z",
    "data_hash": "<computed-data-hash>"
  },
  "data": null,
  "error": {
    "code": "UNAVAILABLE",
    "message": "Durable control state unavailable; offline repair required",
    "retriable": false,
    "source_layer": "gateway"
  }
}
```

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

- `ebus_v1_bus_summary_get`
- `ebus_v1_bus_messages_list`
- `ebus_v1_bus_periodicity_list`

This `DOC-06` freeze covers the M2 `ebus_v1_bus_*` tools only. Shared
watch-summary MCP behavior is frozen separately in `DOC-09`.

### Invariants

- `ebus_v1_bus_*` stays separate from semantic MCP tools because it exposes
  bus-observability and transport-capability data rather than protocol-agnostic
  semantic state.
- The `ebus_v1_bus_*` tools are bounded summary/list surfaces. They do not
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

- `ebus_v1_bus_summary_get`
  - arguments: optional `consistency`
- `ebus_v1_bus_messages_list`
  - arguments: optional positive integer `limit`, optional `consistency`
- `ebus_v1_bus_periodicity_list`
  - arguments: optional positive integer `limit`, optional `consistency`

### `ebus_v1_bus_summary_get`

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

### `ebus_v1_bus_messages_list`

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

### `ebus_v1_bus_periodicity_list`

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

- `ebus_v1_watch_summary_get`
  - arguments: optional `consistency`

MCP-specific invariants:

- Tool registration is provider-gated: the tool appears in `tools/list` only
  when the runtime wires a watch-summary provider (shadow cache lane).
- Without provider wiring, tool calls fail as unknown tool.
- `consistency.mode` follows the standard MCP rules (`LIVE` by default;
  `SNAPSHOT` with required `snapshot_id`).
- Payload fields use snake_case and mirror the shared watch-summary schema.

### Unsupported or Unproven Cases

- No GraphQL `bus_summary`, `bus_messages`, or `bus_periodicity` freeze exists in
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

- `ebus_v1_bus_*` appears in `tools/list` without a real bus observability
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

The machine-readable tables below are the complete scoped registration inventory.
The subsequent bullets retain selected payload notes; they are not a second
registration inventory. In particular, the adapter information tool is
`ebus_v1_semantic_adapter_info_get`.

- Core stable (`ebus_v1_*`)
  - `ebus_v1_runtime_status_get`
  - `ebus_v1_registry_devices_list`
  - `ebus_v1_registry_devices_get`
    - **Conclusion: Proven.**
    - JSON response items carry `discovery_source` and
      `verification_state` fields (P3.5). `discovery_source` is one of
      `passive_observed | static_seed | active_confirmed`;
      `verification_state` is one of
      `candidate | corroborated_pending | identity_confirmed`.
      <!-- publication-audit: machine-checked-record start -->
      This current MCP provenance contract is implemented at reviewed gateway
      HEAD `77b898633672e123a05d39a3cf46398cce2d72ab`. The reviewed and merge
      tree is identical at `bb8f59fed4be68104d8ab206f55f7f32ea33e031`; the
      accepted squash merge on gateway `main` is
      `f5cd9c51c60bdf422e8fc1b5690fbde52a393be3`; and the accepted registry
      dependency is `e24532a50caa00c113751b98b88239e045d731e8`.
      <!-- publication-audit: machine-checked-record end -->
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
  - `ebus_v1_registry_planes_list`
  - `ebus_v1_registry_methods_list`
  - `ebus_v1_semantic_zones_get`
  - `ebus_v1_semantic_dhw_get`
  - `ebus_v1_semantic_energy_totals_get`
  - `ebus_v1_semantic_boiler_status_get`
  - `ebus_v1_semantic_system_get`
  - `ebus_v1_semantic_system_set_config`
    - Required arguments: `field` and `value`, both strings; `field` accepts emitted provisional keys such as `dhwBivalencePointC`; its selector-qualified value name remains unresolved.
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
  - `ebus_v1_semantic_circuits_get`
  - `ebus_v1_semantic_radio_devices_get`
    - `data: []` means the startup radio inventory probe completed without
      publishable radio slots. `data: null` means the plane has not been
      published yet.
  - `ebus_v1_semantic_fm5_mode_get`
    - stable scalar mode retained for existing consumers
  - `ebus_v1_semantic_solar_get`
  - `ebus_v1_semantic_cylinders_get`
  - `ebus_v1_semantic_schedules_get`
  - `ebus_v1_semantic_schedules_set_zone_time_program`
  - `ebus_v1_semantic_schedules_set_dhw_time_program`
  - `ebus_v1_semantic_snapshot_get`
  - `ebus_v1_snapshot_capture`
  - `ebus_v1_snapshot_drop`
  - `ebus_v1_rpc_invoke`
- Observe-first bus surface (registered only when the runtime wires bus
  observability)
  - `ebus_v1_bus_summary_get`
  - `ebus_v1_bus_messages_list`
  - `ebus_v1_bus_periodicity_list`
- Observe-first watch-summary surface (registered only when the runtime wires
  watch-summary provider)
  - `ebus_v1_watch_summary_get`
- Legacy aliases


### Checked registration inventory

**Conclusion: Proven** registration coverage in synthetic discovery profiles.
This is implementation evidence, not native protocol evidence or physical
qualification. Deployment configuration and physical state remain Unknown.
`implemented` means registration in the named production-composition profiles;
`target` means structural helper coverage only, with no production enablement
claim. Target profiles can also enumerate constructor tools. The lifecycle
provider SPI and uncomposed helpers are not promoted by this inventory. Native
evidence, partial last-known-good state, fail-closed admission, eBUS MCP
compatibility and GraphQL parity retain their existing contracts.

The checker expands each comma-separated profile into a distinct entry and
compares name, surface, profile, condition and implementation source. The
profile table is closed; additions require documentation review. Availability
is a registration condition, not a guarantee that a listed service can answer.
Only these marked tables are parsed; unrelated prose remains editable.

mcp-profiles:start

| Profile | Surface | Classification |
|---|---|---|
| b503_disabled | ordinary | implemented |
| b503_enabled | ordinary | implemented |
| bus_enabled | ordinary | implemented |
| constructor | ordinary | implemented |
| eebus_enabled | ordinary | implemented |
| identification_enabled | ordinary | implemented |
| modbus_production_0 | ordinary | implemented |
| modbus_production_1 | ordinary | implemented |
| modbus_production_2 | ordinary | implemented |
| modbus_production_3 | ordinary | implemented |
| modbus_production_4 | ordinary | implemented |
| modbus_production_5 | ordinary | implemented |
| modbus_production_6 | ordinary | implemented |
| modbus_production_7 | ordinary | implemented |
| operator_capture_only | operator | implemented |
| operator_commands_only | operator | implemented |
| operator_composed | operator | implemented |
| operator_disabled | operator | implemented |
| operator_eebus_only | operator | implemented |
| operator_enabled | operator | implemented |
| operator_promotion_only | operator | implemented |
| operator_source_disabled | operator_source | implemented |
| operator_source_enabled | operator_source | implemented |
| ordinary_composed | ordinary | implemented |
| runtime_disabled | ordinary | implemented |
| runtime_enabled | ordinary | implemented |
| semantic_disabled | ordinary | implemented |
| semantic_enabled | ordinary | implemented |
| target_fronius | ordinary | target |
| target_growatt_protocol | ordinary | target |
| target_huawei_dongle | ordinary | target |
| target_huawei_emma | ordinary | target |
| target_huawei_instances | ordinary | target |
| target_huawei_instances_coreless | ordinary | target |
| target_huawei_logger | ordinary | target |
| target_modbus_core | ordinary | target |
| target_outback | ordinary | target |
| target_tesla_hsc | ordinary | target |
| target_tesla_summary | ordinary | target |
| target_tesla_vitals | ordinary | target |
| watch_enabled | ordinary | implemented |

mcp-profiles:end

End of the profile table.

The registration inventory follows.

mcp-inventory:start

| Tool | Surface | Profiles | Availability condition | Implementation source | Classification |
|---|---|---|---|---|---|
| ebus_v1_bus_identification_evidence_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/identification_evidence.go | implemented |
| ebus_v1_bus_identification_evidence_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/identification_evidence.go | implemented |
| ebus_v1_bus_identification_evidence_list | ordinary | identification_enabled | bus provider retains identification evidence | mcp/identification_evidence.go | implemented |
| ebus_v1_bus_messages_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/server.go | implemented |
| ebus_v1_bus_messages_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/server.go | implemented |
| ebus_v1_bus_messages_list | ordinary | bus_enabled | bus observability provider present | mcp/server.go | implemented |
| ebus_v1_bus_messages_list | ordinary | identification_enabled | bus provider retains identification evidence | mcp/server.go | implemented |
| ebus_v1_bus_periodicity_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/server.go | implemented |
| ebus_v1_bus_periodicity_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/server.go | implemented |
| ebus_v1_bus_periodicity_list | ordinary | bus_enabled | bus observability provider present | mcp/server.go | implemented |
| ebus_v1_bus_periodicity_list | ordinary | identification_enabled | bus provider retains identification evidence | mcp/server.go | implemented |
| ebus_v1_bus_protocol_specimens_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/server.go | implemented |
| ebus_v1_bus_protocol_specimens_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/server.go | implemented |
| ebus_v1_bus_protocol_specimens_list | ordinary | bus_enabled | bus observability provider present | mcp/server.go | implemented |
| ebus_v1_bus_protocol_specimens_list | ordinary | identification_enabled | bus provider retains identification evidence | mcp/server.go | implemented |
| ebus_v1_bus_summary_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/server.go | implemented |
| ebus_v1_bus_summary_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/server.go | implemented |
| ebus_v1_bus_summary_get | ordinary | bus_enabled | bus observability provider present | mcp/server.go | implemented |
| ebus_v1_bus_summary_get | ordinary | identification_enabled | bus provider retains identification evidence | mcp/server.go | implemented |
| ebus_v1_ebus_standard_command_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_command_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_command_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/ebus_standard_wiring.go | target |
| ebus_v1_ebus_standard_commands_list | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_commands_list | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_commands_list | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/ebus_standard_wiring.go | target |
| ebus_v1_ebus_standard_decode | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_decode | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_decode | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/ebus_standard_wiring.go | target |
| ebus_v1_ebus_standard_services_list | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_services_list | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/ebus_standard_wiring.go | implemented |
| ebus_v1_ebus_standard_services_list | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/ebus_standard_wiring.go | target |
| ebus_v1_registry_devices_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_devices_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_devices_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_registry_devices_list | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_devices_list | operator_source | operator_source_disabled, operator_source_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_devices_list | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_devices_list | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_registry_methods_list | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_methods_list | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_methods_list | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_registry_planes_list | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_planes_list | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_registry_planes_list | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_rpc_invoke | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_rpc_invoke | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_rpc_invoke | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_runtime_status_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_runtime_status_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_runtime_status_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_adapter_info_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_adapter_info_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_adapter_info_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_boiler_status_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_boiler_status_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_boiler_status_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_boiler_status_set_config | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_boiler_status_set_config | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_boiler_status_set_config | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_circuits_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_circuits_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_circuits_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_cylinders_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_cylinders_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_cylinders_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_dhw_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_dhw_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_dhw_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_energy_totals_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_energy_totals_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_energy_totals_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_fm5_interpretation_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_fm5_interpretation_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_fm5_interpretation_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_fm5_mode_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_fm5_mode_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_fm5_mode_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_radio_devices_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_radio_devices_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_radio_devices_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_schedules_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_schedules_set_dhw_time_program | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_set_dhw_time_program | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_set_dhw_time_program | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_schedules_set_zone_time_program | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_set_zone_time_program | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_schedules_set_zone_time_program | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_snapshot_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_snapshot_get | operator_source | operator_source_disabled, operator_source_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_snapshot_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_snapshot_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_solar_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_solar_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_solar_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_system_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_system_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_system_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_system_set_config | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_system_set_config | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_system_set_config | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_semantic_zones_get | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_zones_get | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_semantic_zones_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_snapshot_capture | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_snapshot_capture | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_snapshot_capture | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_snapshot_drop | operator | operator_capture_only, operator_commands_only, operator_composed, operator_disabled, operator_eebus_only, operator_enabled, operator_promotion_only | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_snapshot_drop | ordinary | b503_disabled, b503_enabled, bus_enabled, constructor, eebus_enabled, identification_enabled, modbus_production_0, modbus_production_1, modbus_production_2, modbus_production_3, modbus_production_4, modbus_production_5, modbus_production_6, modbus_production_7, ordinary_composed, runtime_disabled, runtime_enabled, semantic_disabled, semantic_enabled, watch_enabled | always: NewServer | mcp/server_tools.go | implemented |
| ebus_v1_snapshot_drop | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger, target_modbus_core, target_outback, target_tesla_hsc, target_tesla_summary, target_tesla_vitals | always: NewServer | mcp/server_tools.go | target |
| ebus_v1_vaillant_errors_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_list | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_errors_history_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_session_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_session_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_live_monitor_session_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_current_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_current_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_current_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_history_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_history_get | ordinary | b503_enabled | B503 dispatcher and session manager present | mcp/vaillant_b503.go | implemented |
| ebus_v1_vaillant_service_history_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/vaillant_b503.go | implemented |
| ebus_v1_watch_summary_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/server.go | implemented |
| ebus_v1_watch_summary_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/server.go | implemented |
| ebus_v1_watch_summary_get | ordinary | watch_enabled | watch summary provider present | mcp/server.go | implemented |
| eebus_v1_features_data_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_data_get | operator | operator_commands_only | command router present; eeBUS provider absent | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_data_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_data_set | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_data_set | operator | operator_commands_only | command router present; eeBUS provider absent | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_data_set | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_get | operator | operator_commands_only | command router present; eeBUS provider absent | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_features_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_get | operator | operator_commands_only | command router present; eeBUS provider absent | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_rollback | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_rollback | operator | operator_commands_only | command router present; eeBUS provider absent | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_mutations_rollback | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1_commands.go | implemented |
| eebus_v1_pairing_status_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_pairing_status_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_pairing_status_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_pairing_status_get | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_pairing_status_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_pairing_status_get | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_runtime_status_get | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_get | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_services_list | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_get | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_sessions_list | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_capture | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_snapshot_drop | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | operator_source | operator_source_enabled | operator source scope; eeBUS provider present | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/eebus_v1.go | implemented |
| eebus_v1_topology_get | ordinary | eebus_enabled | eeBUS provider present | mcp/eebus_v1.go | implemented |
| helianthus_experimental_leaf_promotion_capture | operator | operator_composed | all composed ordinary and operator providers present | mcp/leaf_promotion_capture.go | implemented |
| helianthus_experimental_leaf_promotion_capture | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/leaf_promotion_capture.go | implemented |
| helianthus_experimental_leaf_promotion_capture | operator | operator_promotion_only | leaf promotion capture provider present; eeBUS provider absent | mcp/leaf_promotion_capture.go | implemented |
| helianthus_experimental_m8_source_state_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/m8_source_state.go | implemented |
| helianthus_experimental_m8_source_state_get | operator | operator_eebus_only | eeBUS provider present; command and capture providers absent | mcp/m8_source_state.go | implemented |
| helianthus_experimental_m8_source_state_get | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/m8_source_state.go | implemented |
| helianthus_runtime_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_get | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_get | ordinary | runtime_enabled | runtime service present; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_list | operator | operator_composed | all composed ordinary and operator providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_list | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_list | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_list | ordinary | runtime_enabled | runtime service present; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_restart | operator | operator_composed | all composed ordinary and operator providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_restart | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_restart | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_restart | ordinary | runtime_enabled | runtime service present; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_start | operator | operator_composed | all composed ordinary and operator providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_start | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_start | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_start | ordinary | runtime_enabled | runtime service present; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_stop | operator | operator_composed | all composed ordinary and operator providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_stop | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/runtime_control.go | implemented |
| helianthus_runtime_stop | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_runtime_stop | ordinary | runtime_enabled | runtime service present; eeBUS absent | mcp/runtime_control.go | implemented |
| helianthus_v1_synchronized_evidence_capture | operator | operator_composed | all composed ordinary and operator providers present | mcp/synchronized_evidence.go | implemented |
| helianthus_v1_synchronized_evidence_capture | operator | operator_enabled | eeBUS provider, command router and capture providers present | mcp/synchronized_evidence.go | implemented |
| helianthus_v1_synchronized_evidence_capture | operator | operator_capture_only | synchronized capture provider present; eeBUS provider absent | mcp/synchronized_evidence.go | implemented |
| modbus_v1_fronius_sunspec_status_get | ordinary | target_fronius | target/uncomposed structural provider; not a production enablement claim | mcp/fronius_sunspec_v1.go | target |
| modbus_v1_growatt_bms_rs485_status_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_bms_rs485_status_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_bms_rs485_status_get | ordinary | modbus_production_2 | owner mask 2: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_bms_rs485_status_get | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_bms_rs485_status_get | ordinary | modbus_production_6 | owner mask 6: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_bms_rs485_status_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_bms_rs485_v202.go | implemented |
| modbus_v1_growatt_protocol_ii_identity_get | ordinary | target_growatt_protocol | target/uncomposed structural provider; not a production enablement claim | mcp/growatt_protocol_ii_v1.go | target |
| modbus_v1_huawei_emma_identity_get | ordinary | target_huawei_emma | target/uncomposed structural provider; not a production enablement claim | mcp/huawei_emma_v1.go | target |
| modbus_v1_huawei_emma_status_get | ordinary | target_huawei_instances, target_huawei_instances_coreless | target/uncomposed structural provider; not a production enablement claim | mcp/huawei_smartlogger_v1.go | target |
| modbus_v1_huawei_sdongle_status_get | ordinary | target_huawei_dongle | target/uncomposed structural provider; not a production enablement claim | mcp/huawei_sdongle_v1.go | target |
| modbus_v1_huawei_sdongle_status_get | ordinary | target_huawei_instances, target_huawei_instances_coreless | target/uncomposed structural provider; not a production enablement claim | mcp/huawei_smartlogger_v1.go | target |
| modbus_v1_huawei_smartlogger_status_get | ordinary | target_huawei_instances, target_huawei_instances_coreless, target_huawei_logger | target/uncomposed structural provider; not a production enablement claim | mcp/huawei_smartlogger_v1.go | target |
| modbus_v1_outback_axs_status_get | ordinary | target_outback | target/uncomposed structural provider; not a production enablement claim | mcp/outback_axs_v1.go | target |
| modbus_v1_profile_observation_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | modbus_production_1 | owner mask 1: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_profile_observation_get | ordinary | target_modbus_core, target_tesla_hsc | structural helper profile; production owner availability checked separately | mcp/modbus_v1.go | target |
| modbus_v1_profile_observation_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_logger, target_outback, target_tesla_summary, target_tesla_vitals | target/uncomposed structural provider; not a production enablement claim | mcp/modbus_v1.go | target |
| modbus_v1_raw_read | operator | operator_composed | all composed ordinary and operator providers present | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | modbus_production_1 | owner mask 1: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| modbus_v1_raw_read | ordinary | target_modbus_core, target_tesla_hsc | structural helper profile; production owner availability checked separately | mcp/modbus_v1.go | target |
| modbus_v1_raw_read | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_logger, target_outback, target_tesla_summary, target_tesla_vitals | target/uncomposed structural provider; not a production enablement claim | mcp/modbus_v1.go | target |
| modbus_v1_tesla_fc100_summary_get | ordinary | target_tesla_summary | target/uncomposed structural provider; not a production enablement claim | mcp/tesla_fc100_summary_v1.go | target |
| modbus_v1_tesla_gen3_evse_current_limit_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_gen3_evse_current_limit_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_gen3_evse_current_limit_get | ordinary | modbus_production_4 | owner mask 4: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_gen3_evse_current_limit_get | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_gen3_evse_current_limit_get | ordinary | modbus_production_6 | owner mask 6: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_gen3_evse_current_limit_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_current_limit_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | modbus_production_1 | owner mask 1: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_hsc_v1.go | implemented |
| modbus_v1_tesla_hsc_status_get | ordinary | target_tesla_hsc | structural helper profile; production owner availability checked separately | mcp/tesla_hsc_v1.go | target |
| modbus_v1_tesla_wcapi_get_vitals_replay_get | ordinary | target_tesla_vitals | target/uncomposed structural provider; not a production enablement claim | mcp/tesla_wcapi_get_vitals_v1.go | target |
| semantic_v1_evse_current_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_evse_current_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_evse_current_get | ordinary | modbus_production_4 | owner mask 4: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_evse_current_get | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_evse_current_get | ordinary | modbus_production_6 | owner mask 6: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_evse_current_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/tesla_gen3_evse_semantic.go | implemented |
| semantic_v1_pv_current_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | modbus_production_1 | owner mask 1: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | modbus_production_5 | owner mask 5: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/modbus_v1.go | implemented |
| semantic_v1_pv_current_get | ordinary | target_modbus_core, target_tesla_hsc | structural helper profile; production owner availability checked separately | mcp/modbus_v1.go | target |
| semantic_v1_pv_current_get | ordinary | target_fronius, target_growatt_protocol, target_huawei_dongle, target_huawei_emma, target_huawei_instances, target_huawei_logger, target_outback, target_tesla_summary, target_tesla_vitals | target/uncomposed structural provider; not a production enablement claim | mcp/modbus_v1.go | target |
| semantic_v1_snapshot_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/semantic_snapshot.go | implemented |
| semantic_v1_snapshot_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/semantic_snapshot.go | implemented |
| semantic_v1_snapshot_get | ordinary | semantic_disabled | shared semantic provider absent; discovery remains configured | mcp/semantic_snapshot.go | implemented |
| semantic_v1_snapshot_get | ordinary | semantic_enabled | shared semantic provider present | mcp/semantic_snapshot.go | implemented |
| semantic_v1_storage_growatt_current_get | operator | operator_composed | all composed ordinary and operator providers present | mcp/growatt_storage_semantic.go | implemented |
| semantic_v1_storage_growatt_current_get | ordinary | ordinary_composed | all composed ordinary optional providers present | mcp/growatt_storage_semantic.go | implemented |
| semantic_v1_storage_growatt_current_get | ordinary | modbus_production_2 | owner mask 2: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_storage_semantic.go | implemented |
| semantic_v1_storage_growatt_current_get | ordinary | modbus_production_3 | owner mask 3: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_storage_semantic.go | implemented |
| semantic_v1_storage_growatt_current_get | ordinary | modbus_production_6 | owner mask 6: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_storage_semantic.go | implemented |
| semantic_v1_storage_growatt_current_get | ordinary | modbus_production_7 | owner mask 7: SunSpec=1, Growatt storage=2, Tesla retained=4 | mcp/growatt_storage_semantic.go | implemented |

mcp-inventory:end

End of the registration inventory.

## System Bound Payload Contract

This contract is implemented by the gateway's GraphQL system-bounds resolver
(`graphql/system_bounds.go`), the `set_system_config` mutation path
(`graphql/mutations.go`), and the MCP tool `ebus_v1_semantic_system_set_config`
handler in companion gateway [pull request #1033](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1033),
which is merged after this page per the documentation gate; this page describes
the behaviour of that change, the reviewed source artifact.
The contract test [`tests/test_system_config_bound_contract.py`](../tests/test_system_config_bound_contract.py)
in this repository pins the documented members and examples.

`ebus_v1_semantic_system_get` publishes `config.dhw_bivalence_point_bound`.
Its `source` is `controller_profile` with `profile`, or `unmatched_policy`
with `reason`. The reason values are `unknown_profile`, `unknown_register`,
`unqualified_bound` and `invalid_bound`. Empty optional `reason` and `profile`
strings are omitted in MCP and `null` in GraphQL. The required boolean
`narrowed_only` is true for every `controller_profile` bound and false for
`unmatched_policy` (GraphQL: `narrowed_only: Boolean!`). A profile identifies
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
entirely. GraphQL returns `null` for `dhw_bivalence_point_bound`.

## Semantic Payload Notes

### Post-M9 FM5 Contract

`ebus_v1_semantic_fm5_interpretation_get` is the MCP-first post-M9
behavioral remediation. Its availability is stated only by the checked
registration inventory above; this section freezes its response contract. The method returns `null` until the
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
the single `ebus_v1_*` namespace; no v2 tool or legacy alias is introduced.
The older `ebus_v1_semantic_fm5_mode_get` scalar retains its frozen response
shape and is not a substitute for the degradation verdict.

- `ebus_v1_semantic_circuits_get` exposes explicit per-circuit ownership as `managing_device`.
- `managing_device.role` is always present and is one of `REGULATOR`, `FUNCTION_MODULE`, or `UNKNOWN`.
- `managing_device.device_id` and `managing_device.address` are populated only when the gateway has ownership evidence for the current topology.
- `ebus_v1_semantic_system_get` exposes `config.dhw_bivalence_point_bound`
  (`min_c`, `max_c`, `source`, optional `reason` and `profile`): the range
  `ebus_v1_semantic_system_set_config` accepts for `dhwBivalencePointC`.
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
  `ebus_v1_rpc_invoke` have no API qualifier and always apply the unmatched
  policy. Every numeric configuration write rejects `NaN` and positive or
  negative infinity before encoding, with `success: false` and no bus request.
  See [`graphql.md`](./graphql.md) "System Config Write Bounds" for the
  profile and unmatched-policy rules.
- `ebus_v1_semantic_system_get` no longer exposes `vr71_circuit_start_index`; that threshold was a gateway heuristic and is not part of the canonical contract.

[gateway-bound-discovery]:
  https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1034

## RPC Method Reference - Vaillant System Plane

Methods available via `ebus_v1_rpc_invoke` on the `system` plane for
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

1. MCP prototype and stabilization (`ebus_v1_*` contract)
2. GraphQL parity after MCP determinism/contract gates are green
3. Consumer rollout (HA and others) after GraphQL parity

The architecture model and gates are documented in:

- [architecture/mcp-first-development.md](../architecture/mcp-first-development.md)
- [architecture/bus-observability-v2.md](../architecture/bus-observability-v2.md)
- [api/watch-summary.md](./watch-summary.md)

## Naming and writable boundary

Only the registered underscore namespace spelling is accepted. The removed `ebus.devices` and `ebus.invoke` names have no replacement aliases. The versioned invoke capability retains its safety, permission, idempotency and replay checks. Pairing status remains registered as `eebus_v1_pairing_status_get`; the dangling-name removal count is zero.

The circuit configuration setter accepts these selector-qualified fields under group `0x02`; existing routes, types and bounds are unchanged.

| Field | Register | Type and bound |
| --- | --- | --- |
| `circuit_heating_curve_factor` | `0x000F` | float32, 0.1–4.0 |
| `heating_circuit_flow_temperature_setpoint_maximum` | `0x0010` | float32, 15–80 |
| `circuit_flow_temperature_setpoint_minimum` | `0x0012` | float32, 5–30 |
| `heating_circuit_outdoor_temperature_limit_maximum` | `0x0014` | float32, 15–30 |
| `circuit_room_temperature_influence_mode` | `0x0015` | enum_u16, unchanged accepted values |
| `circuit_cooling_enabled` | `0x0006` | bool_u8 |

F56b is a partial control-withdrawal and width-evidence boundary: `frostProtC` and `frost_prot_c` are rejected without dispatch. No enum writer is defined. The raw provisional read representation and width evidence remain unchanged.

### Provisional system and zone setter names

These accepted keys remain unchanged and provisional rather than receiving invented canonical value names. Their open question is which selector-qualified quantity and value role each key should express; syntax-only alternatives are not accepted. Native meaning remains governed by [the B524 register identities](../protocols/vaillant/ebus-vaillant-b524.md).

| Family | Accepted key | Opcode / group / instance / register |
| --- | --- | --- |
| system | `dhwBivalencePointC` | `0x02 / 0x00 / 0x00 / 0x0001` |
| system | `maxRoomHumidityPct` | `0x02 / 0x00 / 0x00 / 0x000E` |
| system | `adaptiveHeatingCurve` | `0x02 / 0x00 / 0x00 / 0x0014` |
| system | `hcBivalencePointC` | `0x02 / 0x00 / 0x00 / 0x0023` |
| system | `hcEmergencyTempC` | `0x02 / 0x00 / 0x00 / 0x0026` |
| system | `hwcMaxFlowTempC` | `0x02 / 0x00 / 0x00 / 0x0046` |
| system | `maintenanceDate` | `0x02 / 0x00 / 0x00 / 0x002C` |
| system | `installerName` | `0x02 / 0x00 / 0x00 / 0x006C` |
| system | `installerPhone` | `0x02 / 0x00 / 0x00 / 0x006F` |
| system | `installerMenuCode` | `0x02 / 0x00 / 0x00 / 0x0076` |
| zone | `operatingMode` | `0x02 / 0x03 / selected zone / 0x0006` |
| zone | `quickVetoTemperature` | `0x02 / 0x03 / selected zone / 0x0008` |
| zone | `quickVetoDuration` | `0x02 / 0x03 / selected zone / 0x0026` |
| zone | `desiredSetpoint` | `0x02 / 0x03 / selected zone / 0x0022` |
| zone | `holidaySetpoint` | `0x02 / 0x03 / selected zone / 0x0005` |

Runtime input keys `DriverID` and `ExpectedRevision` remain emitted provisional exceptions: which structural spellings can express their existing identity and optimistic revision without changing the closed request shape?

### Provisional boiler setter names

The boiler setter accepts `field` and `value` strings. Its accepted value keys remain provisional; the open questions are the selector-qualified value roles, the partial-load unit and the meaning of the access-code candidate. No syntax-only alternatives are accepted. These routes are implementation behavior; the [native B509 correspondence](../protocols/vaillant/fixtures/b509-register-name-correspondence.csv) governs interpretation.

| Accepted key | B509 register selector | Existing encoding and bound |
| --- | --- | --- |
| `flowsetHcMaxC` | `0x0E04`; existing alternate `0xA500` | DATA2c, 20–80 |
| `flowsetHwcMaxC` | `0x0F04` | DATA2c, 30–65 |
| `partloadHcKW` | `0x0704` | UCH, whole number 0–40 |
| `partloadHwcKW` | `0x0804` | UCH, whole number 0–40 |
| `phoneNumber` | `0x8104` | Existing BCD validation |
| `installerMenuCode` | `0x4904` | Existing integer validation; native meaning unresolved |

The selector columns identify registers, not new writable native semantics; no value or unit conversion follows from naming.
