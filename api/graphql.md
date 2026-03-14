# GraphQL API

## Current Status

The GraphQL API is implemented and served by `cmd/gateway`. The gateway exposes:

- `/graphql` for queries + mutations
- `/graphql/subscriptions` for subscriptions over WebSocket or SSE

## Observe-First Contract Ownership

This page owns the GraphQL-specific observe-first parity contract that is
currently merged on `main`.

- The merged M3 bus-observability fields `busSummary`, `busMessages`, and
  `busPeriodicity` are frozen below against gateway `main` at merge commit
  `83e9c7b1ba927a282d87599269e91be817ff3582`
  ([Project-Helianthus/helianthus-ebusgateway#379](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/379)).
- The merged M5 watch-summary root field `watchSummary` is frozen below against
  gateway `main` at merge commit `92b3576bf194f8ef6407904db4bc0a5cce6bd385`
  ([Project-Helianthus/helianthus-ebusgateway#393](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/393)).
- `ISSUE-GW-05` / [Project-Helianthus/helianthus-ebusgateway#378](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/378)
  is the runtime-owning lane for this GraphQL parity surface.
- [`watch-summary.md`](./watch-summary.md) owns the shared watch-summary
  contract.
- `ISSUE-DOC-07` freezes the current bus-observability GraphQL contract, and
  `ISSUE-DOC-09` freezes watch-summary GraphQL behavior.

## Dynamic Schema Builder (Implemented)

The builder assembles a GraphQL-oriented schema model directly from the registry:

- **Registry-driven types**: devices, planes, and methods are enumerated from the registry; each method includes frame primary/secondary bytes and a **response schema** (fields + data types) selected via the schema selector for the device’s address/hardware version.
- **Projections in snapshots**: projection graphs are included in each schema snapshot (`Device.projections`) alongside planes and methods.
- **Projection validation**: projections are validated during schema build; invalid projection graphs fail the build and surface a schema error.
- **Rebuild on registry change**: `Start(ctx)` performs an initial build and listens on a `changes` channel; each signal triggers a rebuild. If no channel is provided, callers can trigger rebuilds via `Rebuild()`.
- **Graceful channel close**: if the `changes` channel is closed, the builder stops listening instead of spinning rebuilds.
- **Revisioned snapshots**: each successful rebuild increments a revision counter; `Schema()` returns a deep-copied snapshot to keep callers insulated from concurrent rebuilds.

## Observe-First Query Roots (Implemented)

This excerpt freezes the `ISSUE-DOC-07` + `ISSUE-DOC-09` observe-first subset
of the current merged `Query` surface. It is not a complete `Query`
definition.

```graphql
type Query {
  busSummary: BusSummary
  busMessages(limit: Int): BusMessagesList
  busPeriodicity(limit: Int): BusPeriodicityList
  watchSummary: WatchSummary!
}
```

### Observe-First Bus Queries (`DOC-07`)

This `DOC-07` section freezes only the narrow M3 GraphQL slice shipped by the
merged gateway runtime:

- `busSummary`
- `busMessages(limit: Int)`
- `busPeriodicity(limit: Int)`

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
  `count`/`capacity` stay `0`, `items` is `[]`, and `busSummary.counters`
  remains `"0"` / `"0"`.
- Within one GraphQL operation, all three roots resolve from one shared
  bus-observability snapshot, so `busSummary`, `busMessages`, and
  `busPeriodicity` stay internally consistent for that request.
- GraphQL preserves the same timing-quality semantics as the real
  bus-observability store and MCP adapter. The merged runtime proves
  `estimated` and `unavailable`; these fields must not imply exact wire-time
  precision.

Current value/encoding rules:

- `status.capability.passiveState` and `status.warmup.state` use the bounded
  state set `unavailable | warming_up | available`.
- Current passive-unavailability reasons match the MCP freeze:
  `startup_timeout`, `reconnect_timeout`, `socket_loss`, `flap_dampened`,
  `unsupported_or_misconfigured`, and `capability_withdrawn`.
- `status.degraded.reasons` may include those passive-unavailability reasons and
  `dedup_degraded`.
- `seriesBudgetOverflowTotal` and `periodicityBudgetOverflowTotal` are decimal
  strings, not GraphQL integers.
- `observedAt` and `lastSeen` are UTC RFC3339 strings; the runtime uses
  RFC3339Nano formatting, so fractional seconds appear only when present.
- `lastInterval`, `meanInterval`, `minInterval`, and `maxInterval` are duration
  strings (for example `5s`) and remain omitted until the runtime has a value.

### Watch Summary Query (`DOC-09`)

This `DOC-09` section freezes the merged M5 GraphQL watch-summary root:

- `watchSummary`

Behavioral invariants:

- `watchSummary` is always present as a non-null GraphQL root field.
- If the runtime watch provider is unwired, `watchSummary` resolves to zero
  values and empty lists (not `null`).
- Within one GraphQL operation, multiple `watchSummary` selections resolve from
  one shared snapshot; duplicated aliases do not observe intra-operation skew.
- Portal-specific query cadence/bootstrap behavior is out of scope in this
  file and remains owned by `DOC-10`.

Current value/encoding rules:

- GraphQL names are camelCase (`activationCounts`, `freshnessClasses`,
  `directApplyEligibilityClasses`, `shadowingEnabled`).
- `freshnessClasses`, `directApplyEligibilityClasses`, `inventory.stateClasses`,
  `inventory.pinClasses`, `activationCounts.sourceClasses`, and
  `degraded.reasons` are non-null lists.
- Class labels and semantics are frozen in [`watch-summary.md`](./watch-summary.md).

### Watch Summary Types (`DOC-09`)

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

### Observe-First Bus Types (`DOC-07`)

```graphql
type BusSummary {
  status: BusObservabilityStatus
  messages: BusBoundedListSummary!
  periodicity: BusBoundedListSummary!
  counters: BusObservabilityCounters!
}

type BusObservabilityStatus {
  transportClass: String!
  capability: BusObservabilityCapability!
  warmup: BusObservabilityWarmup!
  timingQuality: BusObservabilityTimingQuality!
  degraded: BusObservabilityDegraded!
}

type BusObservabilityCapability {
  activeSupported: Boolean!
  passiveSupported: Boolean!
  broadcastSupported: Boolean!
  passiveAvailable: Boolean!
  passiveState: String!
  passiveReason: String
  endpointState: String!
  tapConnected: Boolean!
}

type BusObservabilityWarmup {
  state: String!
  blocker: String
  elapsedSeconds: Float
  completedTransactions: Int!
  requiredTransactions: Int!
  completionMode: String
}

type BusObservabilityTimingQuality {
  active: String!
  passive: String!
  busy: String!
  periodicity: String!
}

type BusObservabilityDegraded {
  active: Boolean!
  reasons: [String!]!
}

type BusBoundedListSummary {
  count: Int!
  capacity: Int!
}

type BusObservabilityCounters {
  seriesBudgetOverflowTotal: String!
  periodicityBudgetOverflowTotal: String!
}

type BusMessagesList {
  status: BusObservabilityStatus
  count: Int!
  capacity: Int!
  items: [BusMessage!]!
}

type BusMessage {
  scope: String!
  family: String!
  frameType: String!
  outcome: String!
  observedAt: String
  sourceAddress: Int!
  targetAddress: Int!
  requestLen: Int!
  responseLen: Int!
}

type BusPeriodicityList {
  status: BusObservabilityStatus
  count: Int!
  capacity: Int!
  items: [BusPeriodicityEntry!]!
}

type BusPeriodicityEntry {
  sourceBucket: String!
  targetBucket: String!
  primary: Int!
  secondary: Int!
  family: String!
  state: String!
  lastSeen: String
  sampleCount: Int!
  lastInterval: String
  meanInterval: String
  minInterval: String
  maxInterval: String
}
```

### Types (Current)

```graphql
type Device {
  address: Int!
  addresses: [Int!]!
  manufacturer: String!
  deviceId: String!
  serialNumber: String
  macAddress: String
  softwareVersion: String!
  hardwareVersion: String!
  displayName: String
  productFamily: String
  productModel: String
  partNumber: String
  role: String
  planes: [Plane!]!
  projections: [Projection!]!
}

type Plane {
  name: String!
  methods: [Method!]!
}

type Method {
  name: String!
  readOnly: Boolean!
  primary: Int!
  secondary: Int!
  response: ResponseSchema!
}

type ResponseSchema {
  fields: [Field!]!
}

type Field {
  name: String!
  type: String!
  size: Int!
}

type ServiceStatus {
  status: String!
  firmwareVersion: String
  updatesAvailable: Boolean!
  initiatorAddress: String
}

type Projection {
  plane: String!
  nodes: [ProjectionNode!]!
  edges: [ProjectionEdge!]!
}

type ProjectionNode {
  id: String!
  path: String!
  canonicalPath: String!
}

type ProjectionEdge {
  id: String!
  from: String!
  to: String!
}

type Zone {
  id: String!
  name: String!
  instance: Int!
  state: ZoneState
  config: ZoneConfig
}
type ZoneState {
  operatingMode: String
  currentTemperature: Float
  desiredTemperature: Float
  currentRoomHumidity: Float
}
type ZoneConfig {
  desiredTemperature: Float
  heatingMode: String
  quickVeto: Boolean
  quickVetoSetpoint: Float
  quickVetoExpiry: String
}

type Dhw {
  operatingMode: String
  currentTemperature: Float
  desiredTemperature: Float
  state: String
  config: String
}

type EnergyTotals {
  gas: EnergyCategory
  electric: EnergyCategory
  solar: EnergyCategory
}
type EnergyCategory {
  dhw: EnergyBucket
  climate: EnergyBucket
}
type EnergyBucket {
  today: Float
  yearly: [Float!]!
  monthly: [Float!]!
}

type BoilerStatus {
  state: BoilerState
  config: BoilerConfig
  diagnostics: BoilerDiagnostics
}
type BoilerState {
  flowTemperatureC: Float
  returnTemperatureC: Float
  centralHeatingPumpActive: Boolean
  waterPressureBar: Float
  externalPumpActive: Boolean
  circulationPumpActive: Boolean
  gasValveActive: Boolean
  flameActive: Boolean
  diverterValvePositionPct: Float
  fanSpeedRpm: Int
  targetFanSpeedRpm: Int
  ionisationVoltageUa: Float
  dhwWaterFlowLpm: Float
  dhwDemandActive: Boolean
  heatingSwitchActive: Boolean
  storageLoadPumpPct: Float
  modulationPct: Float
  primaryCircuitFlowLpm: Float
  flowTempDesiredC: Float
  dhwTempDesiredC: Float
  stateNumber: Int
  dhwTemperatureC: Float
  dhwTargetTemperatureC: Float
}
type BoilerConfig {
  dhwOperatingMode: String
  flowsetHcMaxC: Float
  flowsetHwcMaxC: Float
  partloadHcKW: Float
  partloadHwcKW: Float
}
type BoilerDiagnostics {
  heatingStatusRaw: Int
  dhwStatusRaw: Int
  centralHeatingHours: Float
  dhwHours: Float
  centralHeatingStarts: Int
  dhwStarts: Int
  pumpHours: Float
  fanHours: Float
  deactivationsIFC: Int
  deactivationsTemplimiter: Int
}

Boiler field provenance is documented in [`protocols/ebus-vaillant-B509-boiler-register-map.md`](../protocols/ebus-vaillant-B509-boiler-register-map.md). The current contract is hybrid: direct BAI00 B509 is authoritative for most boiler fields, while a small set of controller-mirrored B524 values still feed `dhwTemperatureC`, `dhwTargetTemperatureC`, `dhwOperatingMode`, and `heatingStatusRaw`.

type SystemStatus {
  state: SystemState
  config: SystemConfig
  properties: SystemProperties
}
type SystemState {
  systemOff: Boolean
  systemWaterPressure: Float
  systemFlowTemperature: Float
  outdoorTemperature: Float
  outdoorTemperatureAvg24h: Float
  maintenanceDue: Boolean
  hwcCylinderTemperatureTop: Float
  hwcCylinderTemperatureBottom: Float
}
type SystemConfig {
  adaptiveHeatingCurve: Boolean
  alternativePoint: Float
  heatingCircuitBivalencePoint: Float
  dhwBivalencePoint: Float
  hcEmergencyTemperature: Float
  hwcMaxFlowTempDesired: Float
  maxRoomHumidity: Int
}
type SystemProperties {
  systemScheme: Int
  moduleConfigurationVR71: Int
}

type CircuitStatus {
  index: Int!
  circuitType: String!
  hasMixer: Boolean!
  state: CircuitState!
  config: CircuitConfig!
  managingDevice: CircuitManagingDevice!
}
type CircuitManagingDevice {
  role: ManagingDeviceRole!
  deviceId: String
  address: Int
}
enum ManagingDeviceRole {
  REGULATOR
  FUNCTION_MODULE
  UNKNOWN
}
type CircuitState {
  pumpActive: Boolean
  mixerPositionPct: Float
  flowTemperatureC: Float
  flowSetpointC: Float
  calcFlowTempC: Float
  circuitState: String
  humidity: Float
  dewPoint: Float
  pumpHours: Float
  pumpStarts: Int
}
type CircuitConfig {
  heatingCurve: Float
  flowTempMaxC: Float
  flowTempMinC: Float
  summerLimitC: Float
  frostProtC: Float
  coolingEnabled: Boolean
  roomTempControl: String
}
```

`vr71CircuitStartIndex` is intentionally absent from the canonical GraphQL contract. Circuit ownership is modeled explicitly on each `circuits[]` item via `managingDevice`, not through a global FM5 threshold.

The architectural rationale and the full B524 evidence trail for structure/ownership decisions are documented in:

- [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md)
- [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md)

### `energyTotals` Root Query

`energyTotals` is available directly on `Query` and returns the same canonical energy aggregate exposed to MCP.

Example:

```graphql
query {
  energyTotals {
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

### Service Status Notes

- `daemonStatus.initiatorAddress` reports the configured eBUS initiator source used by gateway reads/scans.
- Value format is `0xNN` when resolved from runtime configuration.
- In auto-leased proxy mode where the initiator is negotiated downstream, the field may return `auto`.

## Semantic Startup Runtime Contract

The semantic runtime distinguishes cache bootstrap from live updates during startup.

- Cache-backed semantic payload may be published first and treated as stale bootstrap data.
- Runtime transitions through startup phases (`BOOT_INIT` → `CACHE_LOADED_STALE` → `LIVE_WARMUP` → `LIVE_READY`, with `DEGRADED` timeout fallback).
- If `-boot-live-timeout` elapses before `LIVE_READY`, runtime enters `DEGRADED` until live epochs recover.
- Successful `ebusd-tcp` fallback hydration from `grab result all` (zones/DHW) is classified as live runtime data.
- Energy broadcast updates do not advance startup live epochs and cannot promote phase readiness by themselves.
- `LIVE_READY` requires live-backed updates for each published semantic stream (zones and/or DHW), not just `live_epoch >= 2`.
- Persistent semantic preload is read from `-semantic-cache-path` and loaded as stale (`CACHE_LOADED_STALE`) when valid.
- Zone visibility is hysteresis-based: `N_miss` consecutive misses before removal and `N_hit` consecutive hits before re-introduction (`-semantic-zone-presence-miss-threshold`, `-semantic-zone-presence-hit-threshold`).
- Transient single-miss/single-hit alternation keeps zones stable and avoids entity flapping.
- Zone/DHW semantic publication uses non-destructive incremental merge: failed attempted fields retain last-known values instead of being wiped by partial snapshots.
- Freshness is tracked per merged field in runtime state; GraphQL currently exposes merged values and startup phase/state contracts.
- DHW retains last-known values during cache-only/transient gaps until `-semantic-dhw-stale-ttl` is exceeded, then `dhw` is explicitly cleared.

Authoritative startup FSM and transition details are documented in [`architecture/startup-semantic-fsm.md`](../architecture/startup-semantic-fsm.md).
Zone lifecycle details are documented in [`architecture/zone-presence-fsm.md`](../architecture/zone-presence-fsm.md).
DHW lifecycle details are documented in [`architecture/dhw-freshness-fsm.md`](../architecture/dhw-freshness-fsm.md).
Structural family/instance discovery rules are documented in [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md) and [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md).

### Projection Notes

- **ProjectionNode.id** derives from the canonical Service path for the node (stable across projections).
- **ProjectionEdge.from/to** refer to node IDs within the same projection.
- **path / canonicalPath format**: `Plane:/segment@value/segment@value/...` where `Plane` is the projection plane name and each segment may include an `@`-qualified locator. `canonicalPath` always uses `Service` as the plane.

### Projections API

Projections are plane-scoped graphs attached to each device. The API exposes:

- **planes**: `Projection.plane` identifies the view (e.g., `Service`, `Observability`, `Debug`).
- **nodes**: `Projection.nodes` is the list of graph nodes; `path` is plane-local for display, while `canonicalPath` anchors identity in the `Service` plane.
- **edges**: `Projection.edges` connects nodes within the same plane; `from` and `to` are node IDs.
- **canonical paths**: `ProjectionNode.id` is derived from the `canonicalPath`, so the same node ID appears across planes when they represent the same canonical entity in a snapshot.

#### Example query

```graphql
query ProjectionBrowserProjections($address: Int!) {
  device(address: $address) {
    address
    addresses
    manufacturer
    deviceId
    projections {
      plane
      nodes {
        id
        path
        canonicalPath
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
      "deviceId": "BASV2",
      "projections": [
        {
          "plane": "Service",
          "nodes": [
            {
              "id": "Service:/ebus/addr@50/device@BASV2",
              "path": "Service:/ebus/addr@50/device@BASV2",
              "canonicalPath": "Service:/ebus/addr@50/device@BASV2"
            },
            {
              "id": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "path": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "canonicalPath": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data"
            }
          ],
          "edges": [
            {
              "id": "Service:Service:/ebus/addr@50/device@BASV2->Service:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "from": "Service:/ebus/addr@50/device@BASV2",
              "to": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data"
            }
          ]
        },
        {
          "plane": "Observability",
          "nodes": [
            {
              "id": "Service:/ebus/addr@50/device@BASV2",
              "path": "Observability:/ebus/addr@50/device@BASV2",
              "canonicalPath": "Service:/ebus/addr@50/device@BASV2"
            },
            {
              "id": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "path": "Observability:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "canonicalPath": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data"
            }
          ],
          "edges": [
            {
              "id": "Observability:Service:/ebus/addr@50/device@BASV2->Service:/ebus/addr@50/device@BASV2/method@get_operational_data",
              "from": "Service:/ebus/addr@50/device@BASV2",
              "to": "Service:/ebus/addr@50/device@BASV2/method@get_operational_data"
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
      "id": "Service:/ebus/addr@16/device@BASV2",
      "path": "Observability:/ebus/addr@16/device@BASV2",
      "canonicalPath": "Service:/ebus/addr@16/device@BASV2"
    },
    {
      "id": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "path": "Observability:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "canonicalPath": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data"
    }
  ],
  "edges": [
    {
      "id": "Observability:Service:/ebus/addr@16/device@BASV2->Service:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "from": "Service:/ebus/addr@16/device@BASV2",
      "to": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data"
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
    deviceId
    projections {
      plane
      nodes { id path canonicalPath }
      edges { id from to }
    }
  }
}
```

**Notes**

- `Projection.plane` is the plane label shown in the projection browser plane picker (ordered with defaults `Service`, `Observability`, `Debug`, `Virtual`, then any device-specific planes).
- `ProjectionNode.id` is the canonical Service path for the node, so it is stable across planes within a snapshot.
- `ProjectionNode.path` is the plane-specific path shown in the projection browser.
- `ProjectionNode.canonicalPath` is the Service-plane path used to correlate nodes across planes.

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
      "id": "Service:/ebus/addr@16/device@BASV2",
      "path": "Observability:/ebus/addr@16/device@BASV2",
      "canonicalPath": "Service:/ebus/addr@16/device@BASV2"
    },
    {
      "id": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "path": "Observability:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "canonicalPath": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data"
    }
  ],
  "edges": [
    {
      "id": "Observability:Service:/ebus/addr@16/device@BASV2->Service:/ebus/addr@16/device@BASV2/method@get_operational_data",
      "from": "Service:/ebus/addr@16/device@BASV2",
      "to": "Service:/ebus/addr@16/device@BASV2/method@get_operational_data"
    }
  ]
}
```

### Handler Construction

`NewHandler(builder)` returns an `http.Handler` backed by the query schema. `cmd/gateway` uses `NewInvokeHandler(builder, registry, invoker)` for `/graphql` and `NewSubscriptionHandler(builder, registry, invoker, hub)` for `/graphql/subscriptions`.

## Mutation Surface (Implemented)

The `invoke` mutation validates parameters against the method signature and routes the request through the Router/Bus stack.

```graphql
type Mutation {
  invoke(address: Int!, plane: String!, method: String!, params: JSON): InvokeResult!
  setBoilerConfig(field: String!, value: String!): BoilerConfigMutationResult!
}

type InvokeResult {
  ok: Boolean!
  error: InvokeError
  result: JSON
}

type InvokeError {
  message: String!
  code: String!
  category: String!
}

type BoilerConfigMutationResult {
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
- **Boiler writes**: `setBoilerConfig` supports `flowsetHcMaxC`, `flowsetHwcMaxC`, `partloadHcKW`, and `partloadHwcKW`. The mutation accepts the value as a string, rejects non-finite input, enforces server-side ranges, and only reports success after B509 ack + read-back confirmation.
- **Boiler write normalization**: `DATA2c` boiler temperature writes publish the normalized wire value, not the raw input string. `UCH` power-limit writes require whole-number kW.

### Handler Construction

`NewInvokeHandler(builder, registry, invoker)` returns an `http.Handler` backed by query + mutation schema.

## Subscription Surface (Implemented)

Subscriptions deliver real-time updates over WebSocket or SSE.

```graphql
type Subscription {
  broadcast(primary: Int!, secondary: Int!): BroadcastEvent!
  zonesUpdate: [Zone!]!
  dhwUpdate: Dhw
  energyTotalsUpdate: EnergyTotals
  boilerStatusUpdate: BoilerStatus
  systemUpdate: SystemStatus
  circuitsUpdate: [CircuitStatus!]!
}

type BroadcastEvent {
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
