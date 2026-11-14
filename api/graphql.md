# GraphQL API

## Current Status

The GraphQL API is implemented and served by `cmd/gateway`. The gateway exposes:

- `/graphql` for queries + mutations
- `/graphql/subscriptions` for subscriptions over WebSocket or SSE

**Current gateway status: Proven.** The gateway implements `/graphql/m2m/v1`
on a dedicated TLS 1.3 listener. Its current SemReg queries are
`semanticPVCurrent`, `semanticStorageCurrent`, and `semanticEVSECurrent`.
The separate canonical-PV `m2mCurrentSnapshot` schema is an unimplemented target;
the implemented route does not establish that target contract.

The listener is off by default. Gateway configuration is disabled exactly when
all five settings are empty: `m2m-graphql-listen`, `m2m-graphql-server-name`,
`m2m-graphql-server-cert`, `m2m-graphql-server-key`, and
`m2m-graphql-allowed-assets`. Any partial non-disabled configuration fails
validation; all five are required, and empty or duplicate asset entries fail.
The add-on's `m2m_graphql_enabled` option is separate from these gateway
settings; its default is Unknown here (candidate, not part of the Proven status). The listener provides server-authenticated TLS;
no client principal is derived, and retired client-certificate flags are ignored.

| Surface | Status |
| --- | --- |
| `/graphql/m2m/v1` | Implemented, default off |
| `semanticPVCurrent`, `semanticStorageCurrent`, `semanticEVSECurrent` | Current SemReg queries |
| `m2mCurrentSnapshot` | Unimplemented target |
| Complete gateway settings | Required for a listener |
| Partial gateway settings | Rejected |

Sources: [handler](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/m2mgraphql/handler.go),
[configuration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/config.go),
[flag bindings](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/m2m_graphql_config.go),
[listener](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/cmd/gateway/m2m_graphql_runtime.go).

The separate target is described in
[`docs/platform/public-graphql-m2m-v1.md`](../docs/platform/public-graphql-m2m-v1.md).

The additive Vaillant-only regulator capability root is specified in
[`vaillant-regulator-capability-v1.md`](./vaillant-regulator-capability-v1.md).
It is a target contract for open gateway #947, not evidence that this root is
already deployed or a gateway-wide/cross-protocol regulator aggregate. The interface shape is retained as a separate contract.

## Observe-First Contract Ownership

This page owns the GraphQL-specific observe-first parity contract that is
currently merged on `main`.

- The merged M3 bus-observability fields `bus_summary`, `bus_messages`, and
  `bus_periodicity` use the published interface below
  ([Project-Helianthus/helianthus-ebusgateway#379](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/379)).
- The merged M5 watch-summary root field `watch_summary` is frozen below against
  the published interface
  ([Project-Helianthus/helianthus-ebusgateway#393](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/393)).
- `ISSUE-GW-05` / [Project-Helianthus/helianthus-ebusgateway#378](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/378)
  is the runtime-owning lane for the M3 bus-observability GraphQL parity
  surface (`bus_summary`, `bus_messages`, `bus_periodicity`).
- `ISSUE-GW-11` is the runtime-owning lane for the M5 watch-summary GraphQL
  parity surface (`watch_summary`).
- [`watch-summary.md`](./watch-summary.md) owns the shared watch-summary
  contract.
- `ISSUE-DOC-07` freezes the current bus-observability GraphQL contract, and
  `ISSUE-DOC-09` freezes watch-summary GraphQL behavior.

## Dynamic Schema Builder (Implemented)

The builder assembles a GraphQL-oriented schema model directly from the registry:

- **Registry-driven types**: devices, planes, and methods are enumerated from the registry; each method includes frame primary/secondary bytes and a **response schema** (fields + data types) selected via the schema selector for the device’s address/hardware version.
- **Projections in snapshots**: projection graphs are included in each schema snapshot (`device.projections`) alongside planes and methods.
- **Projection validation**: projections are validated during schema build; invalid projection graphs fail the build and surface a schema error.
- **Rebuild on registry change**: `Start(ctx)` performs an initial build and listens on a `changes` channel; each signal triggers a rebuild. If no channel is provided, callers can trigger rebuilds via `Rebuild()`.
- **Graceful channel close**: if the `changes` channel is closed, the builder stops listening instead of spinning rebuilds.
- **Revisioned snapshots**: each successful rebuild increments a revision counter; `Schema()` returns a deep-copied snapshot to keep callers insulated from concurrent rebuilds.

## Observe-First Query Roots (Implemented)

This excerpt freezes the `ISSUE-DOC-07` + `ISSUE-DOC-09` observe-first subset
of the current merged `query` surface. It is not a complete `query`
definition.

```graphql
type query {
  bus_summary: bus_summary
  bus_messages(limit: Int): bus_messages_list
  bus_periodicity(limit: Int): bus_periodicity_list
  watch_summary: watch_summary!
}
```

### Observe-First Bus Queries (`DOC-07`)

This `DOC-07` section freezes only the narrow M3 GraphQL slice shipped by the
merged gateway runtime:

- `bus_summary`
- `bus_messages(limit: Int)`
- `bus_periodicity(limit: Int)`

Behavioral invariants:

- The two list roots keep bounded-list parity with MCP. `count` and `capacity`
  describe the whole retained store, not just the returned slice.
- When `limit` is present it must be a positive integer; the gateway returns the
  newest retained `limit` items in retained order. Omitting `limit` returns all
  currently retained items and nothing more.
- Current passive capability, warmup, degraded, and timing-quality state stay
  explicit through the top-level `status` object on all three roots. Retained
  message/periodicity history does not imply current passive health.
- When no real bus-observability provider is wired, the current runtime still
  returns zero-value wrapper objects for all three roots; `status` is `null`,
  `count`/`capacity` stay `0`, `items` is `[]`, and `bus_summary.counters`
  remains `"0"` / `"0"`.
- Within one GraphQL operation, all three roots resolve from one shared
  bus-observability snapshot, so `bus_summary`, `bus_messages`, and
  `bus_periodicity` stay internally consistent for that request.
- GraphQL preserves the same timing-quality semantics as the real
  bus-observability store and MCP adapter. The merged runtime proves
  `estimated` and `unavailable`; these fields must not imply exact wire-time
  precision.

Current value/encoding rules:

- `status.capability.passive_state` and `status.warmup.state` use the bounded
  state set `unavailable | warming_up | available`.
- Current passive-unavailability reasons match the MCP freeze:
  `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`,
  `unsupported_or_misconfigured`, and `capability_withdrawn`.
- `status.degraded.reasons` may include those passive-unavailability reasons and
  `dedup_degraded`.
- `series_budget_overflow_total` and `periodicity_budget_overflow_total` are decimal
  strings, not GraphQL integers.
- `observed_at` and `last_seen` are UTC RFC3339 strings; the runtime uses
  RFC3339Nano formatting, so fractional seconds appear only when present.
- `last_interval`, `mean_interval`, `min_interval`, and `max_interval` are duration
  strings (for example `5s`) and remain omitted until the runtime has a value.

### Watch Summary Query (`DOC-09`)

This `DOC-09` section freezes the merged M5 GraphQL watch-summary root:

- `watch_summary`

Behavioral invariants:

- `watch_summary` is always present as a non-null GraphQL root field.
- If the runtime watch provider is unwired, `watch_summary` resolves to zero
  values and empty lists (not `null`).
- Within one GraphQL operation, multiple `watch_summary` selections resolve from
  one shared snapshot; duplicated aliases do not observe intra-operation skew.
- Portal-specific query cadence/bootstrap behavior is out of scope in this
  file and remains owned by `DOC-10`.

Current value/encoding rules:

- GraphQL names are snake_case (`activation_counts`, `freshness_classes`,
  `direct_apply_eligibility_classes`, `shadowing_enabled`).
- Source-selection admission status follows the naming contract in
  the gateway schema: consumers query `bus_summary.status.bus_admission` and
  `bus_admission.source_selection`. The removed `busAdmission` compatibility alias
  is intentionally absent.
- `freshness_classes`, `direct_apply_eligibility_classes`, `inventory.state_classes`,
  `inventory.pin_classes`, `activation_counts.source_classes`, and
  `degraded.reasons` are non-null lists.
- Class labels and semantics are frozen in [`watch-summary.md`](./watch-summary.md).

### Watch Summary Types (`DOC-09`)

```graphql
type watch_summary {
  inventory: watch_summary_inventory!
  activation_counts: watch_summary_activation_counts!
  freshness_classes: [watch_summary_class_count!]!
  direct_apply_eligibility_classes: [watch_summary_class_count!]!
  degraded: watch_summary_degraded!
}

type watch_summary_class_count {
  class: String!
  count: Int!
}

type watch_summary_inventory {
  total_entries: Int!
  pinned_entries: Int!
  evictable_entries: Int!
  static_pinned_footprint: Int!
  write_confirm_pinned_active: Int!
  state_classes: [watch_summary_class_count!]!
  pin_classes: [watch_summary_class_count!]!
}

type watch_summary_activation_counts {
  catalog_descriptors: Int!
  active_keys: Int!
  source_classes: [watch_summary_class_count!]!
}

type watch_summary_degraded {
  active: Boolean!
  shadowing_enabled: Boolean!
  pinned_budget_degraded: Boolean!
  compactor_degraded: Boolean!
  reasons: [String!]!
}
```

### Observe-First Bus Types (`DOC-07`)

```graphql
type bus_summary {
  status: bus_observability_status
  messages: bus_bounded_list_summary!
  periodicity: bus_bounded_list_summary!
  counters: bus_observability_counters!
}

type bus_observability_status {
  transport_class: String!
  capability: bus_observability_capability!
  bus_admission: bus_admission
  warmup: bus_observability_warmup!
  timing_quality: bus_observability_timing_quality!
  degraded: bus_observability_degraded!
}

type bus_admission {
  source_selection: bus_admission_source_selection
}

type bus_admission_source_selection {
  state: String!
  outcome: String!
  selected_source: Int
  companion_target: Int
  reason: String
  active_probe: bus_admission_active_probe
  retryable: Boolean!
  automatic_retry_scheduled: Boolean!
  next_action: String
  last_successful_source: Int
  rejected_candidates: [bus_admission_rejected_candidate!]!
}

type bus_admission_active_probe {
  target: Int
  status: String!
}

type bus_admission_rejected_candidate {
  source: Int!
  companion_target: Int
  reason: String!
  retryable: Boolean!
}

type bus_observability_capability {
  active_supported: Boolean!
  passive_supported: Boolean!
  broadcast_supported: Boolean!
  passive_available: Boolean!
  passive_state: String!
  passive_reason: String
  endpoint_state: String!
  tap_connected: Boolean!
}

type bus_observability_warmup {
  state: String!
  blocker: String
  elapsed_seconds: Float
  completed_transactions: Int!
  required_transactions: Int!
  completion_mode: String
}

type bus_observability_timing_quality {
  active: String!
  passive: String!
  busy: String!
  periodicity: String!
}

type bus_observability_degraded {
  active: Boolean!
  reasons: [String!]!
}

type bus_bounded_list_summary {
  count: Int!
  capacity: Int!
}

type bus_observability_counters {
  series_budget_overflow_total: String!
  periodicity_budget_overflow_total: String!
}

type bus_messages_list {
  status: bus_observability_status
  count: Int!
  capacity: Int!
  items: [bus_message!]!
}

type bus_message {
  scope: String!
  family: String!
  frame_type: String!
  outcome: String!
  observed_at: String
  source_address: Int!
  target_address: Int!
  request_len: Int!
  response_len: Int!
}

type bus_periodicity_list {
  status: bus_observability_status
  count: Int!
  capacity: Int!
  items: [bus_periodicity_entry!]!
}

type bus_periodicity_entry {
  source_bucket: String!
  target_bucket: String!
  primary: Int!
  secondary: Int!
  family: String!
  state: String!
  last_seen: String
  sample_count: Int!
  last_interval: String
  mean_interval: String
  min_interval: String
  max_interval: String
}
```

### Types (Current)

```graphql
type device {
  address: Int!
  addresses: [Int!]!
  discovery_source: String
  verification_state: String
  manufacturer: String!
  device_id: String!
  serial_number: String
  mac_address: String
  software_version: String!
  hardware_version: String!
  display_name: String
  product_family: String
  product_model: String
  part_number: String
  role: String
  planes: [plane!]!
  projections: [projection!]!
}

type plane {
  name: String!
  methods: [method!]!
}

type method {
  name: String!
  read_only: Boolean!
  primary: Int!
  secondary: Int!
  response: response_schema!
}

type response_schema {
  fields: [field!]!
}

type field {
  name: String!
  type: String!
  size: Int!
}

type service_status {
  status: String!
  firmware_version: String
  updates_available: Boolean!
  initiator_address: String
}

type projection {
  plane: String!
  nodes: [projection_node!]!
  edges: [projection_edge!]!
}

type projection_node {
  id: String!
  path: String!
  canonical_path: String!
}

type projection_edge {
  id: String!
  from: String!
  to: String!
}

type zone {
  id: String!
  name: String!
  instance: Int!
  state: zone_state
  config: zone_config
}
type zone_state {
  zone_room_temperature: Float
  zone_room_humidity: Float
}
type zone_config {
  operating_mode: String
  target_temp_c: Float
  heating_mode: String
  quick_veto: Boolean
  quick_veto_setpoint: Float
  quick_veto_expiry: String
}

type dhw {
  operating_mode: String
  current_temp_c: Float
  target_temp_c: Float
  state: String
  config: String
}

type energy_totals {
  gas: energy_category
  electric: energy_category
  solar: energy_category
}
type energy_category {
  dhw: energy_bucket
  climate: energy_bucket
}
type energy_bucket {
  today: Float
  yearly: [Float!]!
  monthly: [Float!]!
}

type boiler_status {
  state: boiler_state
  config: boiler_config
  diagnostics: boiler_diagnostics
}
type boiler_state {
  flow_temperature_c: Float
  return_temperature_c: Float
  central_heating_pump_active: Boolean
  water_pressure_bar: Float
  external_pump_active: Boolean
  circulation_pump_active: Boolean
  gas_valve_active: Boolean
  flame_active: Boolean
  diverter_valve_position_pct: Float
  fan_speed_rpm: Int
  target_fan_speed_rpm: Int
  ionisation_voltage_ua: Float
  dhw_water_flow_lpm: Float
  dhw_demand_active: Boolean
  heating_switch_active: Boolean
  storage_load_pump_pct: Float
  modulation_pct: Float
  primary_circuit_flow_lpm: Float
  flow_temp_desired_c: Float
  dhw_temp_desired_c: Float
  state_number: Int
  dhw_temperature_c: Float
  dhw_target_temperature_c: Float
}
type boiler_config {
  dhw_operating_mode: String
  flowset_hc_max_c: Float
  flowset_hwc_max_c: Float
  partload_hc_kw: Float
  partload_hwc_kw: Float
}
type boiler_diagnostics {
  heating_status_raw: Int
  dhw_status_raw: Int
  central_heating_hours: Float
  dhw_hours: Float
  central_heating_starts: Int
  dhw_starts: Int
  pump_hours: Float
  fan_hours: Float
  deactivations_ifc: Int
  deactivations_templimiter: Int
}
```

Boiler field provenance is documented in [`protocols/vaillant/ebus-vaillant-b509-boiler-register-map.md`](../protocols/vaillant/ebus-vaillant-b509-boiler-register-map.md). The current contract is hybrid: direct BAI00 B509 is authoritative for most boiler fields, while a small set of controller-mirrored B524 values still feed `dhw_temperature_c`, `dhw_target_temperature_c`, `dhw_operating_mode`, and `heating_status_raw`.

```graphql
type system_status {
  state: system_state
  config: system_config
  properties: system_properties
}
type system_state {
  system_off: Boolean
  water_pressure: Float
  flow_temperature: Float
  outdoor_temperature: Float
  outdoor_temperature_avg24h: Float
  maintenance_due: Boolean
  hwc_cylinder_temperature_top: Float
  hwc_cylinder_temperature_bottom: Float
}
type system_config {
  adaptive_heating_curve_enabled: Boolean
  alternative_point: Float
  heating_outdoor_bivalence_temperature_limit: Float
  dhw_bivalence_point: Float
  dhw_bivalence_point_bound: system_config_bound
  hc_emergency_temperature: Float
  hwc_max_flow_temp_desired: Float
  room_humidity_limit_maximum: Int
}
# active write bound of the dhw_outdoor_bivalence_temperature_limit setter key (see "System Config Write Bounds").
type system_config_bound {
  min_c: Float!
  max_c: Float!
  narrowed_only: Boolean!
  source: String!   # "controller_profile" | "unmatched_policy"
  reason: String    # set only for "unmatched_policy"
  profile: String   # set only for "controller_profile"
}
type system_properties {
  hydraulic_scheme_code: Int
  functional_module_configuration_code: Int
}

type circuit_status {
  index: Int!
  circuit_type: String!
  has_mixer: Boolean!
  state: circuit_state!
  config: circuit_config!
  managing_device: circuit_managing_device!
}
type circuit_managing_device {
  role: managing_device_role!
  device_id: String
  address: Int
}
enum managing_device_role {
  REGULATOR
  FUNCTION_MODULE
  UNKNOWN
}
type circuit_state {
  pump_active: Boolean
  mixer_position_pct: Float
  flow_temperature_c: Float
  flow_setpoint_c: Float
  calc_flow_temp_c: Float
  circuit_state: String
  humidity: Float
  dew_point: Float
  pump_hours: Float
  pump_starts: Int
}
type circuit_config {
  heating_curve: Float
  flow_temp_max_c: Float
  flow_temp_min_c: Float
  summer_limit_c: Float
  frost_prot_c: Float
  cooling_enabled: Boolean
  room_temp_control: String
}
```

### Current Device Face Discovery Provenance

**Conclusion: Proven.**

The current gateway schema exposes the nullable snake_case fields
`device.discovery_source` and `device.verification_state`. They are independent
label dimensions. Valid non-null values are the Cartesian product of the
separately allowed source and state sets; no source label determines or
restricts the state label.

This current contract is implemented at reviewed gateway HEAD
`77b898633672e123a05d39a3cf46398cce2d72ab`. The reviewed and merge tree is
identical at `bb8f59fed4be68104d8ab206f55f7f32ea33e031`; the accepted squash
merge on gateway `main` is `f5cd9c51c60bdf422e8fc1b5690fbde52a393be3`; and the
accepted registry dependency is `e24532a50caa00c113751b98b88239e045d731e8`.

Allowed `discovery_source` labels:

| label |
|---|
| `static_seed` |
| `passive_observed` |
| `active_confirmed` |

Allowed `verification_state` labels:

| label |
|---|
| `candidate` |
| `corroborated_pending` |
| `identity_confirmed` |

When a registry device has no address-slot record for the selected face, both
fields resolve to GraphQL `null`. `null` is the absence representation, not a
fourth source or verification label. A slotless entry remains visible through
`devices` and `device(address:)`; the absence of provenance does not invalidate
its canonical identity or address fields. This matches MCP, which omits both
snake-case provenance members for the same slotless condition.

Typical initial combinations are examples, not an exhaustive pairing rule:

| `discovery_source` | `verification_state` |
|---|---|
| `static_seed` | `candidate` |
| `passive_observed` | `corroborated_pending` |
| `active_confirmed` | `identity_confirmed` |

The accepted registry rule requires `discovery_source` to preserve the original
native discovery source. Verification advancement MUST NOT rewrite
`static_seed` or `passive_observed` to `active_confirmed`. Retained
`static_seed` / `identity_confirmed` and `passive_observed` / `identity_confirmed`
forms are valid. Invalid labels remain rejected.

`devices` selects the face at each device's canonical primary `address`.
`device(address:)`
accepts a canonical address or an alias address and projects that queried
canonical or alias face's discovery provenance. In either selection, the
returned device identity remains canonical and `address` remains the canonical
primary address. `device(address:)` returns `null` for an unknown address.

```graphql
type query {
  devices: [device!]!
  device(address: Int!): device
}
```

Topology alias grouping, qualified cross-address identity, native observation,
and per-face discovery provenance are distinct records. Topology grouping does
not prove identity; only the documented qualified identity rule may establish a
cross-address identity. A discovery source or verification state does not prove
a supported device, current qualification, stable cross-address identity, or
live behavior.

`vr71CircuitStartIndex` is intentionally absent from the canonical GraphQL contract. Circuit ownership is modeled explicitly on each `circuits[]` item via `managing_device`, not through a global FM5 threshold.

### FM5 Interpretation Verdict

**Status:** Pending gateway implementation.

After the additive MCP `ebus_v1_semantic_fm5_interpretation_get` contract is
implemented, GraphQL exposes the same provider-owned result without
recalculation:

```graphql
type query {
  fm5_interpretation: fm5_interpretation
}

type fm5_interpretation {
  mode: fm5_semantic_mode!
  degraded_reason: fm5_semantic_degraded_reason
  evidence_revision: String!
}

enum fm5_semantic_mode {
  INTERPRETED
  GPIO_ONLY
  ABSENT
}

enum fm5_semantic_degraded_reason {
  CONTROLLER_UNREACHABLE
  CONFIGURATION_UNAVAILABLE
  CONFIGURATION_NOT_INTERPRETABLE
  SOLAR_ACQUISITION_FAILED
  CYLINDER_ACQUISITION_FAILED
  EVIDENCE_STALE
  INCOHERENT_ACQUISITION
}
```

`fm5_interpretation` is nullable until the first coherent structural
classification. A null value is the only bootstrap/unavailable
representation and must not synthesize `GPIO_ONLY` or `ABSENT`. Once a verdict
exists, only `mode` and `evidence_revision` are non-null. `degraded_reason`
remains nullable and is null for healthy `INTERPRETED` and fresh coherent
`ABSENT`. A degraded verdict carries one closed reason; `GPIO_ONLY` requires
fresh coherent structural evidence and carries only
`CONFIGURATION_NOT_INTERPRETABLE`.

`mode` is the last coherent structural classification and does not change on a
transient acquisition failure. A healthy current `INTERPRETED` result and a
fresh coherent `ABSENT` result have null `degraded_reason`; a transient reason
may accompany the unchanged retained mode and marks retained values non-current.
`evidence_revision` binds all fields to one acquisition result. Existing
`fm5_semantic_mode` remains stable for current consumers but does not authorize a
client to infer degradation. The canonical shared behavior and reason
precedence are defined in
[`eebus-operator-admin.md`](./eebus-operator-admin.md).

The architectural rationale and the full B524 evidence trail for structure/ownership decisions are documented in:

- [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md)
- [`../architecture/b524-structural-decisions.md`](../architecture/b524-structural-decisions.md)

### `energy_totals` Root Query

`energy_totals` is available directly on `query` and returns the same canonical energy aggregate exposed to MCP.

Example:

```graphql
query {
  energy_totals {
    gas {
      dhw { today yearly monthly }
      climate { today yearly monthly }
    }
    electric {
      dhw { today yearly monthly }
      climate { today yearly monthly }
    }
    solar {
      dhw { today yearly monthly }
      climate { today yearly monthly }
    }
  }
}
```

Address semantics:

- `address` is the canonical primary eBUS address for the physical device node.
- `addresses` contains canonical + alias faces observed for that same device.
- `device(address:)`, `planes(address:)`, and `methods(address:, plane:)` accept either the canonical address or any alias address from `addresses`.
- Explicit topology alias evidence (source/target or canonical-companion) MAY group
  faces, but it does not create or prove a cross-address stable identity.
  A cross-address identity merge is permitted only when the exact normalized
  `(manufacturer, device_id, serial_number)` triple matches. A shared manufacturer
  + serial number or manufacturer + MAC address MUST NOT merge independent faces,
  and a differing `device_id` cannot satisfy that exact triple. `device_id` remains
  exported as model/provider metadata for the canonical entry. Before that exact
  comparison, fixed-width native `device_id` decoding removes only terminal NUL
  (`0x00`) and ASCII-space (`0x20`) padding; the registry separately trims outer
  Unicode whitespace and folds case for all three members while preserving
  internal punctuation. `VR_71` and `VR71` therefore remain distinct; a GraphQL
  selector, display label, or product code does not create identity equivalence.
  The canonical machine-readable companion is the public
  schema-v2 [qualified-identity policy](../architecture/regulator-qualified-identity-policy.json);
  this API page retains its explanatory consumer contract.

### Service Status Notes

- `daemon_status.initiator_address` reports the configured eBUS initiator source used by gateway reads/scans.
- Value format is `0xNN` when resolved from runtime configuration.
- In auto-leased proxy mode where the initiator is negotiated downstream, the field may return `auto`.

## Semantic Startup Runtime Contract

The semantic runtime distinguishes cache bootstrap from live updates during startup.

- `bus_summary.status.startup { phase cache_epoch live_epoch }` exposes the
  machine-readable startup readiness surface used by proof-mode orchestration
  and Portal parity.
- Cache-backed semantic payload may be published first and treated as stale bootstrap data.
- Runtime transitions through startup phases (`BOOT_INIT` → `CACHE_LOADED_STALE` → `LIVE_WARMUP` → `LIVE_READY`, with `DEGRADED` timeout fallback).
- If `-boot-live-timeout` elapses before `LIVE_READY`, runtime enters `DEGRADED` until live epochs recover.
- Successful `ebusd-tcp` fallback hydration from `grab result all` (zones/DHW) is classified as live runtime data.
- Energy broadcast updates do not advance startup live epochs and cannot promote phase readiness by themselves.
- **Hypothesis — candidate readiness contract.** Provenance is not published.
  `LIVE_READY` requires `live_epoch >= 2`, a live observation for every published
  domain (zones, DHW, boiler status, circuits, and radio devices), and at least
  one live observation across those five domains, regardless of publication.
  System and energy are outside the predicate; energy-only updates do not
  satisfy it. The first live update returns `LIVE_WARMUP`; subsequent live
  updates evaluate the predicate. Actual device readiness remains **Unknown**
  without qualification. See [Live readiness](../architecture/startup-semantic-fsm.md#live-readiness).
- Persistent semantic preload is read from `-semantic-cache-path` and loaded as stale (`CACHE_LOADED_STALE`) when valid.
- Zone visibility is hysteresis-based: `N_miss` consecutive misses before removal and `N_hit` consecutive hits before re-introduction (`-semantic-zone-presence-miss-threshold`, `-semantic-zone-presence-hit-threshold`).
- Transient single-miss/single-hit alternation keeps zones stable and avoids entity flapping.
- Zone/DHW semantic publication uses non-destructive incremental merge: failed attempted fields retain last-known values instead of being wiped by partial snapshots.
- Freshness is tracked per merged field in runtime state; GraphQL currently exposes merged values and startup phase/state contracts.
- DHW retains last-known values during cache-only/transient gaps until `-semantic-dhw-stale-ttl` is exceeded, then `dhw` is explicitly cleared.

Example startup-readiness query:

```graphql
query {
  bus_summary {
    status {
      startup {
        phase
        cache_epoch
        live_epoch
      }
    }
  }
}
```

Authoritative startup FSM and transition details are documented in [`architecture/startup-semantic-fsm.md`](../architecture/startup-semantic-fsm.md).
Zone lifecycle details are documented in [`architecture/zone-presence-fsm.md`](../architecture/zone-presence-fsm.md).
DHW lifecycle details are documented in [`architecture/dhw-freshness-fsm.md`](../architecture/dhw-freshness-fsm.md).
Structural family/instance discovery rules are documented in [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md) and [`../architecture/b524-structural-decisions.md`](../architecture/b524-structural-decisions.md).

### Projection Notes

- **projection_node.id** derives from the canonical Service path for the node (stable across projections).
- **projection_edge.from/to** refer to node IDs within the same projection.
- **path / canonical_path format**: `Plane:/segment@value/segment@value/...` where `plane` is the projection plane name and each segment may include an `@`-qualified locator. `canonical_path` always uses `Service` as the plane.

### Projections API

Projections are plane-scoped graphs attached to each device. The API exposes:

- **planes**: `projection.plane` identifies the view (e.g., `Service`, `Observability`, `Debug`).
- **nodes**: `projection.nodes` is the list of graph nodes; `path` is plane-local for display, while `canonical_path` anchors identity in the `Service` plane.
- **edges**: `projection.edges` connects nodes within the same plane; `from` and `to` are node IDs.
- **canonical paths**: `projection_node.id` is derived from the `canonical_path`, so the same node ID appears across planes when they represent the same canonical entity in a snapshot.

#### Example query

```graphql
query ProjectionBrowserProjections($address: Int!) {
  device(address: $address) {
    address
    addresses
    manufacturer
    device_id
    projections {
      plane
      nodes {
        id
        path
        canonical_path
      }
      edges {
        id
        from
        to
      }
    }
  }
}
```

#### Example response

```json
{
  "data": {
    "device": {
      "address": 50,
      "addresses": [50, 236],
      "manufacturer": "Vaillant",
      "device_id": "synthetic-family",
      "projections": [
        {
          "plane": "Service",
          "nodes": [
            {
              "id": "Service:/ebus/addr@50/device@synthetic-family",
              "path": "Service:/ebus/addr@50/device@synthetic-family",
              "canonical_path": "Service:/ebus/addr@50/device@synthetic-family"
            },
            {
              "id": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "path": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "canonical_path": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data"
            }
          ],
          "edges": [
            {
              "id": "Service:Service:/ebus/addr@50/device@synthetic-family->Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "from": "Service:/ebus/addr@50/device@synthetic-family",
              "to": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data"
            }
          ]
        },
        {
          "plane": "Observability",
          "nodes": [
            {
              "id": "Service:/ebus/addr@50/device@synthetic-family",
              "path": "Observability:/ebus/addr@50/device@synthetic-family",
              "canonical_path": "Service:/ebus/addr@50/device@synthetic-family"
            },
            {
              "id": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "path": "Observability:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "canonical_path": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data"
            }
          ],
          "edges": [
            {
              "id": "Observability:Service:/ebus/addr@50/device@synthetic-family->Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data",
              "from": "Service:/ebus/addr@50/device@synthetic-family",
              "to": "Service:/ebus/addr@50/device@synthetic-family/method@get_operational_data"
            }
          ]
        }
      ]
    }
  }
}
```

### Projection Snapshot Endpoint

The gateway exposes a lightweight HTTP endpoint to fetch a single projection graph from the latest schema snapshot (outside GraphQL). The default path is `/snapshot` and can be configured via `-snapshot-path`.

**Request**

- Method: `GET`
- Query params:
  - `address` (required): device address as decimal or hex (e.g., `16` or `0x10`)
  - `plane` (required): projection plane name (e.g., `Service`, `Observability`, `Debug`)

#### Example request

```
GET /snapshot?address=0x10&plane=Observability
Accept: application/json
```

#### Example response

```json
{
  "address": 16,
  "plane": "Observability",
  "nodes": [
    {
      "id": "Service:/ebus/addr@16/device@synthetic-family",
      "path": "Observability:/ebus/addr@16/device@synthetic-family",
      "canonical_path": "Service:/ebus/addr@16/device@synthetic-family"
    },
    {
      "id": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "path": "Observability:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "canonical_path": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data"
    }
  ],
  "edges": [
    {
      "id": "Observability:Service:/ebus/addr@16/device@synthetic-family->Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "from": "Service:/ebus/addr@16/device@synthetic-family",
      "to": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data"
    }
  ]
}
```

## Projection Browser (`/ui`)

The projection browser is a read-only projection explorer served at `/ui` by default. It uses a single GraphQL query to fetch projections for all devices, then renders the device list, plane picker, projection graph, and node details. The browser auto-refreshes on an interval (default 5s) and exposes manual refresh + pause/resume controls. This surface is separate from the Portal shell/API served under `/portal` and `/portal/api/v1`.

### GraphQL projection query

```graphql
query ProjectionBrowserProjections {
  devices {
    address
    addresses
    manufacturer
    device_id
    projections {
      plane
      nodes { id path canonical_path }
      edges { id from to }
    }
  }
}
```

**Notes**

- `projection.plane` is the plane label shown in the projection browser plane picker (ordered with defaults `Service`, `Observability`, `Debug`, `Virtual`, then any device-specific planes).
- `projection_node.id` is the canonical Service path for the node, so it is stable across planes within a snapshot.
- `projection_node.path` is the plane-specific path shown in the projection browser.
- `projection_node.canonical_path` is the Service-plane path used to correlate nodes across planes.

### Projection snapshot endpoint

The gateway exposes a lightweight HTTP endpoint to fetch a single projection graph from the latest schema snapshot (outside GraphQL). The projection browser uses GraphQL; the snapshot endpoint is intended for lightweight or plane-specific clients. The default path is `/snapshot` and can be configured via `-snapshot-path`.

**Request**

- Method: `GET`
- Query params:
  - `address` (required): device address as decimal or hex (e.g., `16` or `0x10`)
  - `plane` (required): projection plane name (e.g., `Service`, `Observability`, `Debug`)

#### Example request

```
GET /snapshot?address=0x10&plane=Observability
Accept: application/json
```

#### Example response

```json
{
  "address": 16,
  "plane": "Observability",
  "nodes": [
    {
      "id": "Service:/ebus/addr@16/device@synthetic-family",
      "path": "Observability:/ebus/addr@16/device@synthetic-family",
      "canonical_path": "Service:/ebus/addr@16/device@synthetic-family"
    },
    {
      "id": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "path": "Observability:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "canonical_path": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data"
    }
  ],
  "edges": [
    {
      "id": "Observability:Service:/ebus/addr@16/device@synthetic-family->Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data",
      "from": "Service:/ebus/addr@16/device@synthetic-family",
      "to": "Service:/ebus/addr@16/device@synthetic-family/method@get_operational_data"
    }
  ]
}
```

[basv0-profile]:
  ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md

[gateway-bound-discovery]:
  https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1034

### Handler Construction

`NewHandler(builder)` returns an `http.Handler` backed by the query schema. `cmd/gateway` uses `NewInvokeHandler(builder, registry, invoker)` for `/graphql` and `NewSubscriptionHandler(builder, registry, invoker, hub)` for `/graphql/subscriptions`.

## Mutation Surface (Implemented)

The `invoke` mutation validates parameters against the method signature and routes the request through the Router/Bus stack.

```graphql
type mutation {
  invoke(address: Int!, plane: String!, method: String!, params: json): invoke_result!
  set_boiler_config(field: String!, value: String!): boiler_config_mutation_result!
  set_system_config(field: String!, value: String!): config_mutation_result
}

type invoke_result {
  ok: Boolean!
  error: invoke_error
  result: json
}

type invoke_error {
  message: String!
  code: String!
  category: String!
}

type boiler_config_mutation_result {
  success: Boolean!
  error: String
}

type config_mutation_result {
  success: Boolean!
  error: String
}
```

### Behavior

- **Parameter validation**: params are checked against either the template schema (`ParamSchema`) or a template builder (`Build`).
  - Whole-number JSON numerics are accepted for integer fields (for example GraphQL-decoded `float64(2.0)` and `json.Number("2")`).
  - Fractional values for integer fields are rejected (`INVALID_PAYLOAD`).
- **Error mapping**: typed errors are mapped to `code`/`category` (e.g., `TIMEOUT` → `TRANSIENT`, `NO_SUCH_DEVICE` → `DEFINITIVE`).
- **Result normalization**: `types.Value{Valid:false}` fields are returned as `null` in the JSON result map.
- **Boiler writes**: `set_boiler_config` accepts exactly the keys `maximum_heating_flow_temperature_setpoint`, `maximum_dhw_flow_temperature_setpoint`, `heating_partial_load_power`, `dhw_partial_load_power`, `installer_phone_number` and the provisional `installerMenuCode`, whose register meaning is open; [the MCP setter tables](./mcp.md#boiler-setter-keys) list their selectors and bounds. The mutation accepts the value as a string, rejects non-finite input, enforces server-side ranges, and only reports success after B509 ack + read-back confirmation.
- **Boiler write normalization**: `DATA2c` boiler temperature writes publish the normalized wire value, not the raw input string. `UCH` power-limit writes require whole-number kW.

### System Config Write Bounds

This contract is implemented by the gateway's GraphQL system-bounds resolver
(`graphql/system_bounds.go`), the `set_system_config` mutation path
(`graphql/mutations.go`), and the MCP tool `ebus_v1_semantic_system_set_config`
handler in companion gateway [pull request #1033](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1033),
which defines the system-bounds behaviour described here.
The contract test [`tests/test_system_config_bound_contract.py`](../tests/test_system_config_bound_contract.py)
in this repository pins the documented members and examples.

The `set_system_config(field, value)` mutation, the MCP tool
`ebus_v1_semantic_system_set_config`, and the registry/invoker mutation path
share one validation rule for the `dhw_outdoor_bivalence_temperature_limit` key (register
`GG=0x00`, `RR=0x0001`): the accepted range is not fixed, it is resolved per
controller.

The policy window equals the range the gateway accepted before profiles existed,
so v1 clients see no change, and narrowing applies only on a qualified profile
match (none is reachable until identities are acquired at discovery, gateway
[#1034][gateway-bound-discovery]).

- **Profile bound.** The range comes from the controller-profile lookup of the
  register library, keyed by the complete selector (opcode, group, instance
  byte, register) under one controller identity. A profile matches only when
  the whole identity matches exactly: device identifier, raw software value,
  raw hardware value, API version and API revision. The API version and
  revision correspond to the OP=00h system-information identifiers
  `0006h` `interface_version` and `0007h` `interface_revision`
  ([B524 system information](../protocols/vaillant/ebus-vaillant-b524.md)).
  The lookup uses only registry discovery/import metadata, including the
  device identifier (EID), raw software and raw hardware. Bound resolution
  performs no bus I/O or on-demand system-information identifier reads.
  Existing polling does not acquire these two identifiers. An identity
  missing any of the five values never matches a profile that recorded it.
  The register is `dhw_outdoor_bivalence_temperature_limit`
  (`OP=02h`, `GG=00h`, `II=00h`, `RR=0001h`); a profile seeded for `II=00h`
  answers no bound for any other instance. The only seeded profile is the
  `BASV0` controller family with software `0217`, hardware `8803`,
  API `1.1`, range `-20..20`
  ([profile page][basv0-profile]).
  Only the retained description bytes are **Proven**; the decoded `-20..20`
  range rests on the EXP decoding and is a **Hypothesis**. A matching
  identity identifies an observation context, not the target installation.
  Its bound remains a **Hypothesis** for that installation and may narrow
  but never widen the policy window `-20..50`. The effective
  bound is the intersection: `min = max(profile min, -20)` and
  `max = min(profile max, 50)`. An empty intersection falls back to
  `unmatched_policy` with reason `invalid_bound`. A nonempty intersection
  retains `source: controller_profile` and the matched profile identity.
  The empty-intersection fallback bound is the policy window `-20..50`.
  Widening beyond the window requires installation-qualified evidence, such
  as a description of the target installation's own selector;
  no seeded profile provides it. The BASV0 profile bound `-20..20` narrows
  the window on a qualified match. The register map's
  `-20..50` is an unqualified historical observation that names no controller
  identity, so it is not used as a profile bound. Today even the seeded
  BASV0 identity resolves to `unknown_profile`: every bound is the policy window `-20..50` with
  `source: unmatched_policy`. The `controller_profile` source can appear
  when gateway issue
  [#1034][gateway-bound-discovery]
  acquires both identifiers in the discovery path.
- **Unmatched policy.** When no profile matches (unknown identity, a controller
  without a seeded profile, an API qualifier missing from metadata, or a
  profile without a bound for this selector, or an unqualified or invalid
  profile bound), the range `-20..50` applies. A controller family whose
  profile is not seeded therefore falls under this policy until a profile is added, even when other documentation
  lists a wider catalog range for it. The registry/invoker write path
  (`ebus_v1_rpc_invoke`-style writes through the registry) has no API qualifier
  and therefore always applies the unmatched policy.
- **Before any bus write.** A value outside the active bound is rejected
  before the first bus frame of the write is sent, with `success: false`. The
  error text names the active bound: `controller profile <identity> allows
  [min, max]` or `controller identity unmatched (<reason>): conservative policy
  bound [-20, 50] applies`. A value inside the bound is written and still
  reported as success only after the read-back matches the written value.
- **Non-finite input.** Every numeric configuration write rejects `NaN` and
  positive or negative infinity before encoding, with `success: false` and
  no bus request.
- **Other system numbers.** `room_humidity_limit_maximum`,
  `heating_outdoor_bivalence_temperature_limit`,
  `heating_flow_temperature_setpoint_maximum_at_heat_pump_fault`,
  `dhw_flow_temperature_setpoint_maximum` and `installer_access_code` keep
  their fixed ranges and carry no bound.

`system_config_bound` publishes `min_c`, `max_c`, and `narrowed_only`.

`system_config.dhw_bivalence_point_bound` publishes the resolved bound so a consumer can
limit its input control to it. The bound is resolved from current registry
metadata at validation and at publication; published bounds update on the
next system publication. A controller swap at the same address keeps the
registry identity until the registry metadata changes, so that identity can
be stale. `source` is `controller_profile`
(with `profile` naming the matched identity as
`<EID>/SW<sw>/HW<hw>/API<v>.<r>`) or `unmatched_policy`
(with `reason` one of `unknown_profile`, `unknown_register`,
`unqualified_bound`, `invalid_bound`). `narrowed_only: Boolean!` is true for
every profile-sourced bound and false for `unmatched_policy`; it describes
the restriction even when the numeric bound equals the policy window. The
MCP tool
`ebus_v1_semantic_system_get` returns the same value as
`config.dhw_bivalence_point_bound` with `min_c`, `max_c`, `source`, `reason`,
`profile` and boolean `narrowed_only` .
Before the first resolution, GraphQL returns `null` for
`dhw_bivalence_point_bound` and MCP omits `config.dhw_bivalence_point_bound`
entirely. Empty optional `reason` and `profile` strings are `null` in GraphQL
and omitted in MCP.

### Handler Construction

`NewInvokeHandler(builder, registry, invoker)` returns an `http.Handler` backed by query + mutation schema.

## Subscription Surface (Implemented)

Subscriptions deliver real-time updates over WebSocket or SSE.

```graphql
type subscription {
  broadcast(primary: Int!, secondary: Int!): broadcast_event!
  zones_update: [zone!]!
  dhw_update: dhw
  energy_totals_update: energy_totals
  boiler_status_update: boiler_status
  system_update: system_status
  circuits_update: [circuit_status!]!
}

type broadcast_event {
  source: Int!
  target: Int!
  primary: Int!
  secondary: Int!
  data: [Int!]!
}
```

### Transports

- **WebSocket**: supports `graphql-transport-ws` and legacy `graphql-ws` subprotocols.
- **SSE fallback**: request with `Accept: text/event-stream` or `?sse=1`. Supports GET query params or POST JSON body.

### Handler Construction

`NewSubscriptionHandler(builder, registry, invoker, hub)` returns an `http.Handler` that serves both WebSocket and SSE.

## Naming limitations

The six M2M contract artifacts are excluded because their shape differs from the emitted interface; docs-ebus#1166 tracks that unit.

Zone `target_temp_c` is provisional: which manual, effective heating or cooling selection determines its value?

DHW `dhw_state.current_temp_c` and `dhw_config.target_temp_c` are provisional: which selector-qualified meanings should their value names express?

Owned GraphQL object, input, enum and type names use snake_case; built-in scalars and protocol introspection names retain their protocol spelling. Enum tokens follow the owned schema; native string values retain their identity.

The subscription excerpt retains members whose shape differs from the emitted interface; those members are outside this bounded spelling update.
