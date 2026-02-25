# GraphQL API

## Current Status

The GraphQL API is implemented and served by `cmd/gateway`. The gateway exposes:

- `/graphql` for queries + mutations
- `/graphql/subscriptions` for subscriptions over WebSocket or SSE

## Dynamic Schema Builder (Implemented)

The builder assembles a GraphQL-oriented schema model directly from the registry:

- **Registry-driven types**: devices, planes, and methods are enumerated from the registry; each method includes frame primary/secondary bytes and a **response schema** (fields + data types) selected via the schema selector for the device’s address/hardware version.
- **Projections in snapshots**: projection graphs are included in each schema snapshot (`Device.projections`) alongside planes and methods.
- **Projection validation**: projections are validated during schema build; invalid projection graphs fail the build and surface a schema error.
- **Rebuild on registry change**: `Start(ctx)` performs an initial build and listens on a `changes` channel; each signal triggers a rebuild. If no channel is provided, callers can trigger rebuilds via `Rebuild()`.
- **Graceful channel close**: if the `changes` channel is closed, the builder stops listening instead of spinning rebuilds.
- **Revisioned snapshots**: each successful rebuild increments a revision counter; `Schema()` returns a deep-copied snapshot to keep callers insulated from concurrent rebuilds.

## Query Surface (Implemented)

The following query entry points are available:

```graphql
type Query {
  daemonStatus: ServiceStatus!
  adapterStatus: ServiceStatus!
  zones: [Zone!]!
  dhw: Dhw
  energyTotals: EnergyTotals
  devices: [Device!]!
  device(address: Int!): Device
  planes(address: Int!): [Plane!]!
  methods(address: Int!, plane: String!): [Method!]!
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

Authoritative startup FSM and transition details are documented in [`architecture/startup-semantic-fsm.md`](../architecture/startup-semantic-fsm.md).
Zone lifecycle details are documented in [`architecture/zone-presence-fsm.md`](../architecture/zone-presence-fsm.md).

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
query PortalProjections($address: Int!) {
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

## Portal UI (Projection Explorer)

The portal UI is a read-only projection explorer (default path: `/ui`). It uses a single GraphQL query to fetch projections for all devices, then renders the device list, plane picker, projection graph, and node details. The UI auto-refreshes on an interval (default 5s) and exposes manual refresh + pause/resume controls.

### GraphQL projection query

```graphql
query PortalProjections {
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

- `Projection.plane` is the plane label shown in the portal plane picker (ordered with defaults `Service`, `Observability`, `Debug`, `Virtual`, then any device-specific planes).
- `ProjectionNode.id` is the canonical Service path for the node, so it is stable across planes within a snapshot.
- `ProjectionNode.path` is the plane-specific path shown in the UI.
- `ProjectionNode.canonicalPath` is the Service-plane path used to correlate nodes across planes.

### Projection snapshot endpoint

The gateway exposes a lightweight HTTP endpoint to fetch a single projection graph from the latest schema snapshot (outside GraphQL). The portal UI uses GraphQL; the snapshot endpoint is intended for lightweight or plane-specific clients. The default path is `/snapshot` and can be configured via `-snapshot-path`.

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
```

### Behavior

- **Parameter validation**: params are checked against either the template schema (`ParamSchema`) or a template builder (`Build`).
  - Whole-number JSON numerics are accepted for integer fields (for example GraphQL-decoded `float64(2.0)` and `json.Number("2")`).
  - Fractional values for integer fields are rejected (`INVALID_PAYLOAD`).
- **Error mapping**: typed errors are mapped to `code`/`category` (e.g., `TIMEOUT` → `TRANSIENT`, `NO_SUCH_DEVICE` → `DEFINITIVE`).
- **Result normalization**: `types.Value{Valid:false}` fields are returned as `null` in the JSON result map.

### Handler Construction

`NewInvokeHandler(builder, registry, invoker)` returns an `http.Handler` backed by query + mutation schema.

## Subscription Surface (Implemented)

Broadcast subscriptions deliver raw eBUS broadcast frames filtered by primary/secondary bytes.

```graphql
type Subscription {
  broadcast(primary: Int!, secondary: Int!): BroadcastEvent!
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

## Not Yet Implemented

- No additional subscription fields beyond `broadcast`.
