# MCP Endpoint

## Current Status

The MCP server is implemented and served by `cmd/gateway` at `/mcp`.

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
- Merge commit: `3daf4beed9d6406f7af52869eea1c53ef14f2f62`
- Gateway workspace proof artifact (outside this docs repo; from a `Project-Helianthus/helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260312T175648Z-pr377-gw04-26ee758-passive-p01-p06-recovery/index.json`
  with `P01..P06 = pass`
- Gateway workspace recovery probe reference (outside this docs repo; from the same `helianthus-ebusgateway` checkout):
  `helianthus-ebusgateway/results-matrix-ha/20260312T175250Z-pr377-gw04-26ee758-recovery/full88-probe-t01-after-adapter-reboot/index.json`
  remained `blocked-infra` with `infra_reason=adapter_no_signal`, and the PR
  merged under explicit owner override after the official addon/runtime restore
  was re-verified cleanly
- Gateway repo code/test proof references (external to this docs repo, at merge commit `3daf4beed9d6406f7af52869eea1c53ef14f2f62`):
  - MCP tool inventory and provider wiring:
    [Project-Helianthus/helianthus-ebusgateway/cmd/gateway/mcp_bus_observability_integration_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/cmd/gateway/mcp_bus_observability_integration_test.go)
  - MCP payload shape and limit/snapshot behavior:
    [Project-Helianthus/helianthus-ebusgateway/mcp/server_test.go](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/3daf4beed9d6406f7af52869eea1c53ef14f2f62/mcp/server_test.go)

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

Note: This inventory reflects the current known tool surface. The gateway may expose additional tools discovered via the MCP `tools/list` endpoint.

- Core stable (`ebus.v1.*`)
  - `ebus.v1.runtime.status.get`
  - `ebus.v1.adapter_info.get`
  - `ebus.v1.registry.devices.list`
  - `ebus.v1.registry.devices.get`
    - JSON response items carry `discovery_source` and
      `verification_state` fields (P3.5). `discovery_source` is one of
      `passive_observed | static_seed | active_confirmed`;
      `verification_state` is one of
      `candidate | corroborated_pending | identity_confirmed`.
      Both are omitted when the registry has no slot record for the
      address. For `devices.list` the labels reflect the entry's
      primary address; for `devices.get(address=X)` the labels
      reflect the queried address X — important for merged entries
      whose aliases may be at different DiscoverySource levels (e.g.
      NETX3's broadcast face `0x04` stays at `static_seed/candidate`
      while the `0xF1` face advances to
      `active_confirmed/identity_confirmed` via active scan).
      Per the
      [`05-static-seed-provenance`](../architecture/atr/05-static-seed-provenance.md)
      ATR, addresses planted by the productids static seed table MUST
      surface as `static_seed/candidate` until corroborated by passive
      observation (→ `corroborated_pending`) or identity-confirmed by
      active scan (→ `active_confirmed/identity_confirmed`).
  - `ebus.v1.registry.planes.list`
  - `ebus.v1.registry.methods.list`
  - `ebus.v1.semantic.zones.get`
  - `ebus.v1.semantic.dhw.get`
  - `ebus.v1.semantic.energy_totals.get`
  - `ebus.v1.semantic.boiler_status.get`
  - `ebus.v1.semantic.system.get`
  - `ebus.v1.semantic.circuits.get`
  - `ebus.v1.semantic.radio_devices.get`
  - `ebus.v1.semantic.fm5_mode.get`
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

## Semantic Payload Notes

- `ebus.v1.semantic.circuits.get` exposes explicit per-circuit ownership as `managing_device`.
- `managing_device.role` is always present and is one of `REGULATOR`, `FUNCTION_MODULE`, or `UNKNOWN`.
- `managing_device.device_id` and `managing_device.address` are populated only when the gateway has ownership evidence for the current topology.
- `ebus.v1.semantic.system.get` no longer exposes `vr71_circuit_start_index`; that threshold was a gateway heuristic and is not part of the canonical contract.

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
