# Portal API

## Status

Portal API is exposed by `helianthus-ebusgateway` as an additive HTTP surface.

- UI shell: `/portal`
- Versioned API base: `/portal/api/v1`
- Current UX is capability-driven (status cards + enabled sections) and does not expose milestone placeholder labels.

## Contribution-Driven Portal Contract V1 (INT-10 Target)

This section freezes the public browser contract required for the Vaillant B503
part of Gateway [#552](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/552).
It is a **target contract**. Gateway #552 is open; this document does not claim
that its B503 rendering, generated assets, or production browser tests have
been implemented or validated on a device.

`helianthus-ebusgateway` is the platform owner of the Portal host, the
immutable `helianthus.gateway.portal-catalog/v1` read model, catalog/action
admission, provider lifecycle, rendering, navigation cleanup, and the fixed
browser transport. Portal consumes accepted driver contributions and SemReg
records. It neither creates an upstream semantic record nor interprets native
eBUS evidence.

The historical `/portal/api/v1/*` endpoints documented below remain their own
endpoint contracts. They are not a transport or semantic fallback for this
INT-10 B503 presentation.

### Fixed catalog and rendering boundary

The browser obtains the catalog read model only through `POST /graphql/portal/v1`
and the fixed `PortalCatalogV1` operation. The only action operation on that
route is `PortalActionInvokeV1`; it is governed by the action-admission rules
below. No B503 operation is admitted on this route.
For this B503 UX there is no REST compatibility shim, no alternate Portal API
route, no dual semantic publication, and no direct MCP/native fallback.
The host does not use a central vendor switch or an arbitrary-English parser to
recover a contribution, field state, or action meaning.

The catalog is a Gateway-composed, immutable snapshot. Its five domain entries
are exactly `Thermal/HVAC`, `PV`, `Storage/BMS`, `EVSE`, and
`Infrastructure`. A domain without an admitted contribution is truthfully
absent or unavailable; a missing field is never displayed as zero. A valid new
fixture contribution must render through the same generic catalog path. It
must not require a vendor switch, a product branch, or compatibility logic in
central bootstrap or rendering code.

One accepted contribution identity is the full tuple
`(driver_id, manifest_id, manifest_version)`. The browser joins a contribution
to its resource and capability using that exact identity; a manifest ID alone
is insufficient. The host canonicalizes accepted descriptors and rejects a
conflicting digest for the same identity/version into quarantine. Rejection or
withdrawal of one contribution cannot make a different admitted contribution
disappear.

The gateway catalog carries a `catalog_revision`, `catalog_digest`,
`evaluation_instant`, and caller `authorization_scope`. It binds each accepted
contribution to its descriptor digest, lifecycle/source generation, installation
and resource context, capability, SemReg snapshot and semantic revision. These
are presentation inputs, not proof that the browser qualified a device or read
a native frame.

### Records, truth, and action admission

Every rendered field is identified by its contribution identity, resource ID,
field ID, exact SemReg field `DefinitionRef`, service `DefinitionRef`,
capability `DefinitionRef`, and canonical-unit `DefinitionRef`. A B503 card
can display only a field admitted through this chain. It must show the
Gateway-supplied lifecycle, freshness, projection-loss, quality, and provenance
state; it cannot reconstruct any of them from a label, a historical aggregate,
or a raw MCP response.

Accepted source records and accepted semantic records remain distinct from the
browser presentation state. The browser may render their admitted outcome, but
it cannot promote a source, qualification, topology, field value, or native
evidence from its own state.

The UI preserves `unavailable`, `stale`, `conflict`, `partial`, `unknown`,
`unsupported`, `withdrawn`, `withheld`, and `invalid-contribution` as distinct
states. `partial` retains valid sibling fields. A retained value remains
explicitly non-current when its freshness or quality says so. Native B503
identity, qualification, evidence, dispatch, acknowledgement, readback, retry
fencing, and installation safety remain with their owning protocol and Gateway
components.

An action is identified by the same contribution/resource/capability chain,
its action ID, operation `DefinitionRef`, service/capability/argument/effect
`DefinitionRef`s, and the catalog revision/digest that presented it. Discovery
permission controls visibility: without it, no action node, identifier, label,
count, tooltip, or explanatory text is present. Invoke permission alone does
not enable an action.

Before invocation, Gateway revalidates the request-bound caller,
catalog revision/digest claim, contribution identity/digest, resource and
capability, semantic snapshot/revision, binding, source epoch/generation,
typed preconditions, route, deadline, and idempotency key. A previously visible
or enabled action does not grant authority. The browser has no authority to
turn a B503 banner, a cached catalog, or a translated label into an action.

### Vaillant B503 target contract

The `Vaillant B503` card is a contribution-driven section-projection card. It
appears only for an admitted selected resource whose B503 capability state is
`AVAILABLE`; it identifies the selected target and enters the B503 perspective
without creating another B503 data model. Target selection is resource-scoped.
Every target-bearing B503 read or session request uses only the main public
`POST /graphql` endpoint. That endpoint is protected by the stable eBUS MCP
graduation/parity contract. These operations are not `PortalCatalogV1` or
`PortalActionInvokeV1` operations, and they do not call `/graphql/portal/v1`:

- `vaillantCapabilities(targetAddress:)`
- `vaillantErrors(targetAddress:)`
- `vaillantServiceCurrent(targetAddress:)`
- `vaillantErrorHistory(targetAddress:index:)`
- `vaillantErrorsHistory(targetAddress:limit:)`
- `vaillantServiceHistory(targetAddress:index:)`
- `vaillantLiveMonitor(action:issuerToken:targetAddress:)`
- `vaillantLiveMonitorSession(targetAddress:)`

The catalog/action route and the B503 route are an exclusive operation-to-route
split, not a fallback or compatibility shim. The B503 route does not expand the
accepted #974 catalog/action endpoint. If either fixed route is unavailable,
the UI renders the Gateway-supplied unavailable state and does not try the
other route, REST, MCP, or native I/O.

Changing target atomically invalidates the active target-bound presentation:
capability, current errors/service, history, live-monitor strip, and pending
completion must not bleed into the new target. On every target switch, before
admitting the new target presentation, the browser begins targeted cleanup for
each prior target that it locally owns and whose session is `ENABLING` or
`ACTIVE` or `REFRESHING`. An `ACTIVE` prior target receives an immediate target-specific
disable using its locally held issuer token. For an `ENABLING` prior target,
the browser registers that same target-specific disable at switch time and
dispatches it immediately when the locally initiated enable completes with its
issuer token. For a `REFRESHING` prior target, the browser queues that
same token-bound disable without invoking an operation while Refreshing is busy;
after refresh succeeds to `Active`, it dispatches the queued disable, and after
refresh failure returns `Idle`, it clears the queued pair without a disable.
This is switch-time cleanup, never passive timeout cleanup.

Any late enable completion after a switch follows the same prior-target cleanup
and cannot mutate the new target. Gateway's session view exposes only `state`
and opaque `owned`: `owned` means that the Gateway session gate is held, not
which client holds it. The browser never derives a foreign owner from `owned`
or from an absent local token. It never disables a gate-held session without a
locally held issuer token. The B503 target tests are named `M8-TGT-01`,
`M8-TGT-02`, `M8-TGT-03`, and `M8-TGT-04`.

`B503Availability` has exactly these five public reasons. `EXPIRED` is
internal-only and is never a sixth browser state.

| Reason | Stable selector | Required presentation truth |
|---|---|---|
| `AVAILABLE` | `data-testid="b503-state-available"` | Render admitted B503 tabs and the session strip for the selected target. |
| `NOT_SUPPORTED` | `data-testid="b503-state-not-supported"` | State that the selected target does not support the B503 surface; do not infer a value. |
| `TRANSPORT_DOWN` | `data-testid="b503-state-transport-down"` | State that transport is unavailable and offer only a retry/reconnect hint. |
| `SESSION_BUSY` | `data-testid="b503-state-session-busy"` | State neutrally that bounded ownership-or-lifecycle contention makes the session busy; do not infer a foreign owner. |
| `UNKNOWN` | `data-testid="b503-state-unknown"` | State that capability is undetermined; do not equate it with unsupported. |

The selectors above are stable browser-test identifiers, never locale-dependent
parsers or authorization inputs. Tests must also retain
`data-testid="b503-session-strip"`,
`data-testid="b503-session-state-label"` for the Gateway-owned live-monitor
session strip. The strip states are `Idle`, `Enabling`, `Active`, and
`Refreshing`, and `Disabled`. `Refreshing` means an epoch refresh holds the
ownership gate and all live-monitor operations are busy. Refresh success returns
`Active`; refresh failure releases the gate and returns `Idle`. `Disabled` is
never reported with `owned:true`. `Disabled` with `owned:false` maps only an
explicit operator or configuration disable; enable failure, the 30-second idle
timeout, transport disconnect, and gateway restart map to `Idle` with
`owned:false` after cleanup. The base `SESSION_BUSY` presentation is neutral.
The strip may show that the Gateway session gate is held, but must not identify
another client. Leaving the B503 perspective uses the same locally-token-bound cleanup
rule as target switching.

Refresh success revalidates only a surviving authenticated current-owner
token/target/epoch handle and returns it to `Active`; it is continuation, not
reconstruction or auto-resume. After restart, a lost owner handle, or an
absent/invalid current issuer token, Gateway does not reconstruct the session
and the client must issue a new explicit Enable.
A terminal transport disconnect releases ownership to `Idle`; a later reconnect
therefore has no owner, does not enter `Refreshing`, and also requires explicit
client Enable.

When a selected target has Gateway session state `Refreshing` with `owned:true`,
the session strip remains observable alongside temporarily `UNKNOWN` capability.
It is status-only: the section-projection card, B503 tabs, and every B503
operation remain unavailable until capability is `AVAILABLE` again.

The selected-target B503 tabs expose a `role="tablist"` with one named
`role="tab"` and matching `role="tabpanel"` for Errors, Service, History, and
Live-Monitor. Each tab exposes `aria-selected`; ArrowLeft, ArrowRight, Home,
and End move tab focus, while Enter and Space select the focused tab. The
session strip is a named `role="status"` for the selected target.

On a Gateway capability transition or transport reconnect, the browser renders
only the Gateway-supplied availability state. It neither preserves
`AVAILABLE`, replays a session enable/disable action, nor changes route; it
may re-query only the selected target after Gateway publishes a new state.

On a selected-target context cancellation before bus turnaround, the browser
renders the Gateway-supplied structured `UPSTREAM_TIMEOUT` alongside the
unchanged last-known B503 availability. On a selected-target bus/arbitration
timeout, NAK, or CRC failure, it renders structured `UPSTREAM_RPC_FAILED`
alongside that same availability. Neither field-operation error becomes
`TRANSPORT_DOWN` or invalidates capability.

Each target-bound asynchronous request captures a frontend presentation epoch
at dispatch. Target switch, B503 navigation-away, and reconnect advance that
epoch; a completion may mutate presentation only when both its target address
and captured epoch still match, otherwise it is discarded.

The available state includes Errors, Service, History, and Live-Monitor tabs.
The History tab uses the typed B503 history GraphQL records for the selected
target and has `data-role="vaillant-b503-tab-history"`; it does not infer
history from labels or retained aggregate data. The section-projection card
uses `data-role="projection-b503-card"` only for `AVAILABLE` B503 capability.

The B503 section permanently displays the generic AD02 installation-write warning with
`data-testid="b503-install-writes-banner"` and tooltip anchor
`id="b503-ad02-tooltip-anchor"`. It exposes no device command name, selector
name, or control. The banner neither creates an action nor changes
authorization. Any real installation/device write still needs action-time
operator confirmation.

### Required implementation checks

Gateway #552 must mechanically check the five rows above, target invalidation,
projection card admission, session ownership/nav-away cleanup, typed history,
AD02 banner, keyboard/accessibility, reconnect/error, and frontend epoch
rollover. The stable B503 selectors and contract wording are checked in this
repository by `scripts/check_portal_ux_contract.py` and
`tests/test_portal_ux_contract_checker.py`. Those checks reject missing states
or selectors, B503 command vocabulary, compatibility/fallback wording, absent
source/authorization boundaries, and a claim that #552 is implemented.

This documentation gate is based on Gateway contribution contract
[#972](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/972)
and production catalog/action admission
[#974](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/974).
The five-state session wording follows Gateway
[#975](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/975)
source contract commit `9985f7d73dfabb44d645335a08065e9397907fb3` and current open
evidence head `9985f7d73dfabb44d645335a08065e9397907fb3`; #975 remains open,
intermediate, and unmerged, and this documentation does not claim it is
merged.
It does not close Gateway #552, the wider INT-10 parent, SemReg cutover, or
physical validation.

## Observe-First Contract Ownership

This page owns the frozen Portal-specific observe-first contract after merged
`ISSUE-GW-14`.

- GraphQL owns domain aggregate contracts (`zones`, `dhw`, `energyTotals`,
  `watchSummary`, `busSummary`, `busMessages`, `busPeriodicity`) and
  cross-surface schema semantics.
- Portal API/SSE own Portal-specific transport/bootstrap/presentation behavior:
  endpoint names under `/portal/api/v1/*`, capability flags, stream/timeline/
  provenance/snapshots/session flows, and bus-panel state mapping.
- [`watch-summary.md`](./watch-summary.md) remains the shared watch-summary
  schema/semantics authority. This page freezes only the Portal-facing behavior.

## Design Constraints

- Gateway-first: semantic logic stays in gateway runtime.
- Read-only by default for portal API.
- Versioned endpoint paths (`/api/v1`) for forward evolution.
- Runtime is Go-only; frontend assets are embedded in the gateway binary.

## Driver Runtime Control Target

The generic runtime-control target is frozen in
[`driver-runtime-v1.md`](./driver-runtime-v1.md). Portal is a consumer, not
lifecycle authority: it renders gateway-owned `DriverSnapshotV1` records and
invokes the gateway-owned start, stop, and restart operations only after their
MCP contract is stable and GraphQL parity has merged. It does not create an
independent driver FSM, edit add-on options, retain endpoints or credentials,
or call a protocol adapter directly.

This is a post-MCP target and does not claim that driver-control Portal routes
or controls are implemented in the current endpoint inventory below. When the
consumer rollout occurs, capability discovery must hide unsupported controls
without hiding the stable driver snapshot or its categorical unavailable
state.

## eeBUS Owner Workbench

The post-M9 shared consumer isolation, FM5 degraded interpretation, and single
release-version authority are frozen in
[`eebus-operator-admin.md`](./eebus-operator-admin.md). Protocol-specific
operator routes and browser semantics remain exclusively in the linked
`helianthus-docs-eebus` canonical documents. Portal uses the gateway boundary
and never reads the eeBUS trust store or owner-only operator socket directly.
Home Assistant uses the same gateway-owned pairing boundary. Portal and Home
Assistant pairing remain functional without an eeBUS-specific authentication
layer; neither consumer receives direct store, socket, or transport ownership.

## Core Endpoints

### `GET /portal/api/v1/health`

Returns lightweight health metadata used by the portal shell.

Example response:

```json
{
  "status": "ok",
  "gateway_version": "dev",
  "build_id": "unknown",
  "time_utc": "2026-02-24T00:00:00Z"
}
```

### `GET /portal/api/v1/bootstrap`

Returns portal boot configuration and capability flags.

Example response:

```json
{
  "capabilities": {
    "registry": true,
    "semantic": true,
    "bus_observability": true,
    "projection": true,
    "search": true,
    "stream": true,
    "timeline": true,
    "provenance": true,
    "snapshots": true,
    "snapshot_diff": true,
    "sessions": true,
    "issue_builder": true
  },
  "endpoints": {
    "graphql": "/graphql",
    "snapshot": "/snapshot",
    "subscriptions": "/graphql/subscriptions",
    "mcp": "/mcp",
    "bus_observability": "/portal/api/v1/bus/observability",
    "search": "/portal/api/v1/search",
    "stream": "/portal/api/v1/stream",
    "timeline": "/portal/api/v1/timeline/events",
    "provenance": "/portal/api/v1/provenance/events",
    "snapshots": "/portal/api/v1/snapshots",
    "capture": "/portal/api/v1/snapshots/capture",
    "retention": "/portal/api/v1/snapshots/retention",
    "snapshot_diff": "/portal/api/v1/snapshots/diff",
    "sessions": "/portal/api/v1/sessions",
    "session_save": "/portal/api/v1/sessions/save",
    "session_load": "/portal/api/v1/sessions/load",
    "issue_draft": "/portal/api/v1/issues/draft",
    "issue_export": "/portal/api/v1/issues/export"
  },
  "limits": {
    "max_events_per_second": 200,
    "snapshot_retention": "disabled_in_m0"
  },
  "ui_version": "m0"
}
```

## Data Endpoints

### `GET /portal/api/v1/registry/devices`

Returns a read-only snapshot list of discovered registry devices.

Query parameters:

- `q` (optional): case-insensitive filter across manufacturer, device id, serial, plane names, method names
- `limit` (optional): max returned items (`default=200`, `max=1000`)

Example response:

```json
{
  "count": 2,
  "items": [
    {
      "address": 8,
      "addresses": [8],
      "manufacturer": "Vaillant",
      "device_id": "BAI",
      "software_version": "08.06",
      "hardware_version": "01.00",
      "planes": [
        {
          "name": "heating",
          "methods": ["get_operational_data"]
        }
      ]
    },
    {
      "address": 16,
      "addresses": [16],
      "manufacturer": "Vaillant",
      "device_id": "VRC720",
      "software_version": "08.05",
      "hardware_version": "01.00",
      "planes": [
        {
          "name": "system",
          "methods": ["get_status"]
        }
      ]
    }
  ]
}
```

### `GET /portal/api/v1/semantic/snapshot`

Returns a read-only semantic snapshot for portal list views.
Portal overview renders all zones from this payload (not only the first zone), plus DHW and energy summary.

Response fields:

- `zones`: semantic zone list
- `dhw`: optional DHW semantic object
- `energy_totals`: optional aggregated energy object (numeric values + freshness/provenance metadata)
- `boiler_status`: optional boiler semantic object (`state`, `config`, `diagnostics`)
- `system`: optional system status (state, config, properties)
- `circuits`: optional circuit list (`index`, `circuit_type`, `has_mixer`, `state`, `config`, `managing_device`)
- `radio_devices`: optional radio-device list (per-slot semantic RF data)
- `fm5_semantic_mode`: optional FM5 semantic mode string
- `fm5_semantic_degraded_reason`: **post-M9 target field, pending gateway
  implementation**; explicit closed acquisition-health reason supplied by the
  shared semantic provider and never inferred by Portal; a transient reason
  does not rewrite the last coherent structural mode
- `fm5_semantic_evidence_revision`: **post-M9 target field, pending gateway
  implementation**; opaque revision binding structural mode, acquisition
  reason, and evidence to one result
- `solar`: optional solar semantic object
- `cylinders`: optional cylinder list
- `captured_utc`: RFC3339 UTC timestamp

The example below shows the target response after the post-M9 gateway
implementation; the two target FM5 fields are not claims about current runtime
availability.

Before the first coherent structural classification, the semantic snapshot
omits all three FM5 verdict fields until the first coherent structural
classification. Portal presents acquisition as unavailable and does not infer
`GPIO_ONLY` or `ABSENT` from missing fields.

Energy freshness/provenance metadata (`GW-13` freeze):

- Each series (`gas/electric/solar` × `dhw/climate`) includes `today_meta` and
  may include `yearly_meta[]` / `monthly_meta[]`.
- Metadata fields are: `freshness_state`, `provenance`, `last_observed_utc`,
  `age_seconds`, `stale`.
- `freshness_state` values are `never_seen`, `fresh`, `warming_up`, `stale`,
  `unavailable`.
- `provenance` values are `none`, `register`, `broadcast`.
- Values are non-destructive: stale/unavailable points may keep last numeric
  value; consumers must use metadata for freshness/availability truth.

Example response:

```json
{
  "zones": [
    {
      "id": "zone_1",
      "name": "Living",
      "state": {
        "current_temp_c": 21.3,
        "hvac_action": "HEATING"
      },
      "config": {
        "operating_mode": "auto",
        "target_temp_c": 22.0,
        "allowed_modes": ["auto", "day", "night"]
      }
    }
  ],
  "dhw": {
    "state": {
      "current_temp_c": 47.2
    },
    "config": {
      "operating_mode": "auto",
      "target_temp_c": 49.0
    }
  },
  "energy_totals": {
    "gas": {
      "dhw": { "today": 1.2, "yearly": [1.0, 1.1, 1.2], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } },
      "climate": { "today": 4.8, "yearly": [4.2, 4.5, 4.8], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } }
    },
    "electric": {
      "dhw": { "today": 0.1, "yearly": [0.0, 0.1, 0.1], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } },
      "climate": { "today": 0.7, "yearly": [0.5, 0.6, 0.7], "today_meta": { "freshness_state": "fresh", "provenance": "register", "last_observed_utc": "2026-02-23T22:44:55Z", "age_seconds": 5, "stale": false } }
    },
    "solar": {
      "dhw": { "today": 0.0, "yearly": [0.0, 0.0, 0.0], "today_meta": { "freshness_state": "never_seen", "provenance": "none", "stale": false } },
      "climate": { "today": 0.0, "yearly": [0.0, 0.0, 0.0], "today_meta": { "freshness_state": "never_seen", "provenance": "none", "stale": false } }
    }
  },
  "boiler_status": {
    "state": {
      "flow_temperature_c": 54.2,
      "water_pressure_bar": 1.5,
      "flame_active": true
    },
    "config": {
      "dhw_operating_mode": "auto",
      "flowset_hc_max_c": 75.0
    },
    "diagnostics": {
      "heating_status_raw": 3,
      "central_heating_hours": 1042.0
    }
  },
  "system": {
    "state": {
      "system_off": false,
      "system_water_pressure": 1.5,
      "system_flow_temperature": 31.4,
      "outdoor_temperature": 5.0,
      "outdoor_temperature_avg24h": 4.8,
      "maintenance_due": false,
      "hwc_cylinder_temperature_top": 58.0,
      "hwc_cylinder_temperature_bottom": 42.5
    },
    "config": {
      "adaptive_heating_curve": true,
      "heating_circuit_bivalence_point": -3.0,
      "dhw_bivalence_point": -7.0,
      "hc_emergency_temperature": 30.0,
      "hwc_max_flow_temp_desired": 60.0,
      "max_room_humidity": 70
    },
    "properties": {
      "system_scheme": 1,
      "module_configuration_vr71": 2
    }
  },
  "circuits": [
    {
      "index": 0,
      "circuit_type": "HC",
      "has_mixer": false,
      "state": {
        "flow_setpoint_c": 35.0,
        "flow_temperature_c": 31.2,
        "circuit_state": "active",
        "pump_active": true,
        "calc_flow_temp_c": 35.0
      },
      "config": {
        "heating_curve": 0.8,
        "flow_temp_max_c": 75.0,
        "flow_temp_min_c": 20.0,
        "room_temp_control": "modulating",
        "cooling_enabled": false
      },
      "managing_device": {
        "role": "FUNCTION_MODULE",
        "device_id": "VR_71",
        "address": 38
      }
    }
  ],
  "radio_devices": [
    {
      "group": 0,
      "instance": 1,
      "slot_mode": "THERMOSTAT",
      "device_connected": true,
      "device_model": "VR92",
      "firmware_version": "09.03",
      "zone_assignment": 2,
      "room_temperature_c": 22.5,
      "room_humidity_pct": 44.0
    }
  ],
  "fm5_semantic_mode": "INTERPRETED",
  "fm5_semantic_degraded_reason": null,
  "fm5_semantic_evidence_revision": "opaque-acquisition-revision",
  "solar": {
    "collector_temperature_c": 62.5,
    "return_temperature_c": 45.1,
    "pump_active": true,
    "current_yield": 3.4,
    "pump_hours": 104.0,
    "solar_enabled": true,
    "function_mode": false
  },
  "cylinders": [
    {
      "index": 1,
      "temperature_c": 49.5,
      "max_setpoint_c": 59.0,
      "charge_hysteresis_c": 5.0,
      "charge_offset_c": 2.0
    }
  ],
  "captured_utc": "2026-02-23T22:45:00Z"
}
```

### `GET /portal/api/v1/bus/observability`

Returns Portal bus-observability summary (bus panel + bootstrap capability
surface).

Behavior:

- Returns `200` with JSON when bus observability provider is wired.
- Returns `503` with `bus observability unavailable` when provider is absent or
  nil.

Response fields:

- `status.transport_class`: runtime transport class (`enh`, `ens`, `udp-plain`,
  `tcp-plain`, `ebusd-tcp`).
- `status.capability`: capability booleans plus passive state:
  `passive_state` uses `unavailable | warming_up | available`.
- `status.capability.passive_reason`: when unavailable, one of
  `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`,
  `unsupported_or_misconfigured`, `capability_withdrawn`.
- `status.capability.endpoint_state`: passive endpoint state
  (`unknown`, `connected`, `temporarily_disconnected`,
  `unsupported_or_misconfigured`, `closed`).
- `status.warmup`: warmup counters and blocker/completion fields.
- `status.degraded`: `active` + `reasons`; reasons may include passive
  unavailability reason and/or `dedup_degraded`.
- `status.startup`: machine-readable semantic startup readiness surface:
  `phase` plus monotonic `cache_epoch` / `live_epoch`.
- `status.feature_flags`: observe-first feature-flag state and normalizations.
  Current rollout wording remains conservative: until a later family-specific
  proof lane plus docs freeze says otherwise, the canonical default state is the
  non-promotion path with `external_write_policy=record_only`.
- `messages`, `periodicity`, `counters`: bounded summary counters used by Portal
  observability views.

Portal-facing bus state mapping (frozen):

1. `warming_up` when `status.warmup.state` is `warming_up` (fallback:
   `status.capability.passive_state`).
2. `degraded` when not warming-up and `status.degraded.active == true`.
3. `unavailable` when neither above matches and (`passive_state == unavailable`
   or `passive_supported == false`).
4. `available` otherwise.

For `transport_class == ebusd-tcp`, when Portal view-state is `degraded` or
`unavailable`, the banner appends:
`ebusd-tcp transport limits passive observe-first coverage.`

Example response:

```json
{
  "status": {
    "transport_class": "ebusd-tcp",
    "capability": {
      "active_supported": true,
      "passive_supported": false,
      "broadcast_supported": false,
      "passive_available": false,
      "passive_state": "unavailable",
      "passive_reason": "unsupported_or_misconfigured",
      "endpoint_state": "unsupported_or_misconfigured",
      "tap_connected": false
    },
    "warmup": {
      "state": "unavailable",
      "completed_transactions": 0,
      "required_transactions": 20
    },
    "timing_quality": {
      "active": "unavailable",
      "passive": "unavailable",
      "busy": "unavailable",
      "periodicity": "unavailable"
    },
    "degraded": {
      "active": true,
      "reasons": ["unsupported_or_misconfigured"]
    },
    "startup": {
      "phase": "BOOT_INIT",
      "cache_epoch": 0,
      "live_epoch": 0
    },
    "feature_flags": {
      "observe_first_enabled": false,
      "passive_state_direct_apply": false,
      "passive_config_direct_apply": false,
      "external_write_policy": "record_only",
      "normalizations": []
    }
  },
  "messages": {
    "count": 0,
    "capacity": 384
  },
  "periodicity": {
    "count": 0,
    "capacity": 256
  },
  "counters": {
    "series_budget_overflow_total": 0,
    "periodicity_budget_overflow_total": 0
  }
}
```

Current rollout note:

- this example intentionally shows the canonical non-promotion default state:
  `observe_first_enabled=false`,
  `passive_state_direct_apply=false`,
  `passive_config_direct_apply=false`,
  `external_write_policy=record_only`;
- that wording is frozen by gateway issue
  [`Project-Helianthus/helianthus-ebusgateway#439`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/439); and
- the merged proof artifacts behind the decision prove only the bounded
  `proxy-single-client / passive_mode=required / ens / no-ebusd` family, not a
  broader automatic default flip.

### `GET /portal/api/v1/projection/devices`

Returns projection summary per discovered device.
Portal overview uses this endpoint to populate projection device/plane selectors.

Query parameters:

- `q` (optional): case-insensitive filter over manufacturer/device/display name/plane
- `limit` (optional): max returned items (`default=200`, `max=1000`)

Example response:

```json
{
  "count": 1,
  "items": [
    {
      "address": 16,
      "manufacturer": "Vaillant",
      "device_id": "VRC720",
      "display_name": "sensoCOMFORT",
      "projections": [
        {
          "plane": "Service",
          "node_count": 18,
          "edge_count": 20
        },
        {
          "plane": "Observability",
          "node_count": 18,
          "edge_count": 20
        }
      ]
    }
  ]
}
```

### `GET /portal/api/v1/projection/graph`

Returns one projection graph for a selected device and plane.
Portal overview uses this endpoint for the live projection graph canvas.

Query parameters:

- `address` (required): device address (decimal or hex, e.g. `16` or `0x10`)
- `plane` (required): projection plane name (e.g. `Service`)

Example response:

```json
{
  "address": 16,
  "plane": "Service",
  "nodes": [
    {
      "id": "Service:/ebus/addr@16/device@BASV2",
      "path": "Service:/ebus/addr@16/device@BASV2",
      "canonical_path": "Service:/ebus/addr@16/device@BASV2"
    }
  ],
  "edges": [
    {
      "id": "Service:Service:/ebus/addr@16/device@BASV2->Service:/ebus/addr@16/device@BASV2/method@get_status",
      "from": "Service:/ebus/addr@16/device@BASV2",
      "to": "Service:/ebus/addr@16/device@BASV2/method@get_status"
    }
  ]
}
```

### `GET /portal/api/v1/search`

Returns unified, read-only search matches across currently available portal layers
(registry, semantic snapshot, projection summary).

Query parameters:

- `q` (required): search string (case-insensitive)
- `limit` (optional): max returned items (`default=25`, `max=1000`)

Example response:

```json
{
  "query": "service",
  "count": 2,
  "items": [
    {
      "layer": "registry",
      "kind": "method",
      "id": "reg:10:system:get_status",
      "title": "get_status",
      "subtitle": "system plane addr=0x10",
      "address": 16
    },
    {
      "layer": "projection",
      "kind": "plane",
      "id": "proj:10:service",
      "title": "Service",
      "subtitle": "addr=0x10 nodes=18 edges=20",
      "address": 16
    }
  ]
}
```

### `GET /portal/api/v1/stream`

Server-Sent Events (SSE) stream for lightweight live updates with server-side throttling and coalescing.

Query parameters:

- `layers` (optional): comma-separated layer filter (`registry`, `semantic`, `projection`)
- `interval_ms` (optional): producer interval (`default=1000`, bounded `200..5000`)
- `max_events_per_second` (optional): flush limit (`default=3`, bounded `1..30`)
- `max_events` (optional): stop stream after N emitted events (useful for tests)

SSE event format:

```text
event: update
data: {"at":"2026-02-24T01:00:00.123456Z","type":"snapshot","layer":"registry","correlation_id":"reg-...","payload":{"device_count":2},"provenance":{"source":"poll:registry","dropped":0,"interval_ms":1000}}
```

Notes:

- The server coalesces pending updates and reports dropped intermediate updates in
  `provenance.dropped`.
- Keep-alive comments (`: keep-alive`) are emitted periodically to keep the connection open.
- If no readable data providers are available, the endpoint returns `503`.

### `GET /portal/api/v1/timeline/events`

Returns recent stream events from the in-memory timeline store (newest first).

Query parameters:

- `limit` (optional): max returned events (`default=100`, `max=1000`)
- `layer` (optional): filter by layer (`registry`, `semantic`, `projection`)
- `correlation_id` (optional): substring match on correlation id
- `since` (optional): RFC3339/RFC3339Nano lower-bound timestamp (UTC recommended)

Example response:

```json
{
  "count": 2,
  "items": [
    {
      "at": "2026-02-24T01:23:45.123456Z",
      "type": "snapshot",
      "layer": "registry",
      "correlation_id": "reg-1740356625123456000",
      "payload": {
        "device_count": 2
      },
      "provenance": {
        "source": "poll:registry",
        "dropped": 0,
        "interval_ms": 1000
      }
    }
  ]
}
```

### `GET /portal/api/v1/provenance/events`

Returns provenance projections derived from timeline events (newest first).

Query parameters:

- `limit` (optional): max returned records (`default=50`, `max=1000`)
- `layer` (optional): filter by layer (`registry`, `semantic`, `projection`)
- `correlation_id` (optional): substring match on correlation id

Example response:

```json
{
  "count": 1,
  "items": [
    {
      "correlation_id": "reg-1740356625123456000",
      "layer": "registry",
      "at": "2026-02-24T01:23:45.123456Z",
      "source": "poll:registry",
      "dropped": 0,
      "interval_ms": 1000,
      "decode_path": [
        "source:poll:registry",
        "layer:registry",
        "gateway.portal.stream",
        "gateway.portal.timeline"
      ],
      "payload_keys": ["device_count"],
      "confidence": 0.7
    }
  ]
}
```

### `GET /portal/api/v1/snapshots`

Lists retained snapshots from the in-memory snapshot store (newest first).

Query parameters:

- `limit` (optional): max returned snapshots (`default=20`, `max=1000`)

Example response:

```json
{
  "count": 2,
  "stored_count": 2,
  "max_snapshots": 50,
  "items": [
    {
      "id": "snap-3",
      "label": "after-system-change",
      "captured_at": "2026-02-24T02:12:00.123456Z",
      "payload": {
        "captured_at": "2026-02-24T02:12:00.123456Z",
        "registry": { "count": 2 },
        "timeline": { "count": 6 }
      }
    }
  ]
}
```

### `GET /portal/api/v1/snapshots/capture`

Captures a new snapshot from current portal read models and returns capture metadata.

Query parameters:

- `label` (optional): free text label stored with the snapshot

If no readable providers are available, returns `503`.

### `GET /portal/api/v1/snapshots/retention`

Reads or updates snapshot retention limits.

Query parameters:

- `max_snapshots` (optional): set retention bound (`1..500`)

Example response:

```json
{
  "max_snapshots": 50,
  "stored_count": 3
}
```

### `GET /portal/api/v1/snapshots/diff`

Computes a structural diff between two snapshots.

Query parameters:

- `from_id` (optional): source snapshot id
- `to_id` (optional): target snapshot id
- `limit` (optional): max returned diff entries (`default=200`, `max=1000`)

Behavior:

- If both ids are omitted, the endpoint compares the latest two snapshots.
- If only one id is provided, the endpoint returns `400`.
- If referenced snapshots are missing, the endpoint returns `404`.

Example response:

```json
{
  "from_snapshot": {
    "id": "snap-4",
    "label": "before-change",
    "captured_at": "2026-02-24T02:15:00.123456Z"
  },
  "to_snapshot": {
    "id": "snap-5",
    "label": "after-change",
    "captured_at": "2026-02-24T02:16:00.123456Z"
  },
  "change_count": 2,
  "count": 2,
  "items": [
    {
      "path": "$.registry.items[0].device_id",
      "change": "changed",
      "from": "\"VRC720\"",
      "to": "\"VRC720B\""
    }
  ]
}
```

### `GET /portal/api/v1/sessions`

Lists saved investigation sessions (newest first).

Query parameters:

- `limit` (optional): max returned sessions (`default=30`, `max=1000`)

### `GET /portal/api/v1/sessions/save`

Saves an investigation session/bookmark in the in-memory session store.

Query parameters (all optional):

- `name`
- `search_query`
- `timeline_correlation`
- `provenance_correlation`
- `snapshot_from_id`
- `snapshot_to_id`
- `selected_layer`

### `GET /portal/api/v1/sessions/load`

Loads one saved session by id.

Query parameters:

- `id` (required): session id (e.g. `sess-3`)

Returns `400` when id is missing and `404` when not found.

### `GET /portal/api/v1/issues/draft`

Generates a Markdown issue draft using live portal evidence.

Query parameters (optional):

- `title`
- `observation`
- `reproduction_steps`
- `hypothesis`
- `impact`
- `proposal`
- `acceptance_criteria`
- `controller`
- `device`

Response includes:

- `title`
- `markdown` (full issue body)
- `evidence` (snapshot/timeline/provenance context)

### `GET /portal/api/v1/issues/export`

Builds an export bundle for issue filing workflows.

Response includes:

- `format_version` (`helianthus-issue-bundle/v1`)
- `generated_at`
- `title`
- `markdown`
- `evidence`
- `filename_hint`

### Gateway Explorer Endpoints (`/portal/api/v1/explorer/...`)

Portal's gateway-native explorer is served under this API namespace. It is
distinct from the standalone `helianthus-vrc-explorer` project. The current
scan contract is:

- `POST /portal/api/v1/explorer/scans` starts one B524 or B509 scan from a JSON
  request containing `kind`, `target`, and the applicable client-selected range
  fields; success returns HTTP 202 with `{"status":"started"}`. The current
  server does not impose a smaller scan-range maximum beyond each field's wire
  type, so callers must keep ranges proportionate to the intended read workload.
- `GET /portal/api/v1/explorer/scans/current` returns the current
  `ExplorerScanState`; `DELETE` on the same route cancels an active scan.
- `GET /portal/api/v1/explorer/scans/current/results?offset=0&limit=100`
  returns the requested page. A positive `limit` is currently client-selected
  and has no separate server-side cap. Each register result preserves `raw_hex`
  and `raw_len` beside the convenience `default_float`; raw data remains the
  authoritative exploration evidence.
- `GET /portal/api/v1/explorer/scans/current/stream` returns
  `text/event-stream`. The server always emits the complete current scan state
  as the initial `data:` event. It closes immediately when that initial state is
  `idle`, `done`, `cancelled`, or `error`; an active stream closes when a later
  event reaches `done`, `cancelled`, or `error`.
- `GET /portal/api/v1/explorer/read/b524`, `/read/b509`, and `/read/scanid`
  provide focused read-only operations.

The implementation and executable HTTP contract tests are public in
[`portal/explorer.go`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/portal/explorer.go)
and
[`portal/explorer_test.go`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/portal/explorer_test.go).

## FMV3-M5-06 PV And Modbus Portal Boundary

The two routes in this section are the pre-implementation target for the
FMV3-M5-06 gateway companion. They are unavailable until that companion is
merged and are disabled independently by default.

Portal does not receive a second PV semantic model. The browser calls
`GET /portal/api/v1/semantic/pv/current` with no query parameters or request
body. A gateway-owned backend-for-frontend then sends the exact fixed
`M2MCurrentSnapshot` POST to the dedicated `/graphql/m2m/v1` listener over
TLS 1.3 with verified server identity and a distinct client certificate. The
asset reference is deployment configuration, not browser input. The route
forwards the closed GraphQL success or error envelope without falling back to
the generic GraphQL route, a direct canonical provider, MCP, or Modbus.

The browser never receives a private key, certificate bytes, CA bytes, M2M
listener address, asset allowlist, or arbitrary GraphQL input. The semantic PV
panel polls no faster than once every five seconds and renders canonical
quality, availability, freshness, exact decimal values, dimensions,
continuity, and projection losses without inferring missing values.

Raw diagnostics use the separate
`POST /portal/api/v1/explorer/modbus/raw-read` route. Its JSON body is limited
to 4 KiB and contains exactly:

```json
{"unit_id":1,"function":3,"offset":40069,"quantity":2}
```

The route accepts no endpoint, tool name, profile, asset, credential, or write
function. It invokes the same `modbus.v1.raw.read` core used by MCP, preserving
the FC03/FC04, unit, range, deadline, reconnect, resource, redaction, envelope,
and shared four-reads-per-second limits. Portal cannot create a second quota or
call the Modbus adapter directly. Raw words and wire bytes remain only in this
diagnostic response and never enter semantic GraphQL, semantic Portal state,
snapshots, sessions, search, timeline, or browser persistence.

Browser-to-Portal authentication remains the generic deployment boundary, for
example Home Assistant ingress. FMV3-M5-06 adds no Modbus-specific login,
bearer token, cookie, certificate, or browser secret. A deployment without a
generic authenticated Portal boundary must keep the raw route disabled.

Every admitted, rejected, exhausted, or failed raw request emits one bounded
audit event with request ID, surface, fixed MCP tool ID, numeric unit/function/
range, outcome, static error code, duration, and endpoint reference when one is
available. Audit output excludes returned words, wire bytes, request bodies,
network endpoints, credentials, certificate material, and private paths.

The bootstrap advertises separate `semantic_pv` and `modbus_raw_diagnostic`
capabilities. Disabling semantic PV hides its panel and returns `404` without
stopping `/graphql/m2m/v1`. Disabling raw diagnostics hides its panel and
returns `404` without removing `/mcp`. All four enablement combinations are
valid, and neither route changes transport, device configuration, or write
authority.

## Portal Quick Probes

Use these commands against a local gateway instance (`:8080`) to verify portal API behavior:

```bash
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/health'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/bootstrap'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/registry/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/semantic/snapshot'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/bus/observability'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/devices?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/projection/graph?address=0x10&plane=Service'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/search?q=service&limit=10'
curl -N -fsS 'http://127.0.0.1:8080/portal/api/v1/stream?layers=registry&max_events=3'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/timeline/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/provenance/events?layer=registry&limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/capture?label=manual'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/retention?max_snapshots=25'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/snapshots/diff'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions?limit=5'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions/save?name=investigation-a&search_query=service'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/sessions/load?id=sess-1'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/issues/draft?title=Mapping+Candidate'
curl -fsS 'http://127.0.0.1:8080/portal/api/v1/issues/export?title=Mapping+Candidate'
```

## Portal Asset Build and Drift Check

Portal static assets are generated from `portal/web/src` and embedded into the gateway binary under
`portal/static/assets`.

Use the gateway helper scripts:

```bash
./scripts/build_portal_assets.sh
./scripts/check_portal_assets.sh
```

Production runtime does not require Node.js. Node is only required when regenerating embedded assets.

## Security Defaults

- Portal API accepts `GET` except for explicitly documented closed operator
  routes. FMV3-M5-06 adds only the bounded raw-read POST above; it cannot write
  device state.
- CORS remains same-origin by default.
- No mutating/invoke actions are exposed by portal routes.
- Snapshot capture/retention mutate only internal portal memory, not bus/device state.
- Session save/load mutate only internal portal memory, not bus/device state.
- Issue draft/export endpoints are read-only generators over in-memory evidence.

## Observability and Performance

- Target latency:
  - portal list/read endpoints p95 < 200ms
- Static assets should include caching headers where possible.
- Portal-specific request metrics and logs should be tagged by route.

Baseline portal observability in gateway runtime:
- Request log fields: `method`, `path`, `route`, `status`, `duration_ms`
- `expvar` counters/maps: `portal_requests_total`, `portal_route_duration_ms_total`
- Stream counters/maps: `portal_stream_events_total`, `portal_stream_dropped_total`
