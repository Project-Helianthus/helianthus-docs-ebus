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
  manufacturer: String!
  deviceId: String!
  softwareVersion: String!
  hardwareVersion: String!
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

### Projection Notes

- **ProjectionNode.id** derives from the canonical Service path for the node (stable across projections).
- **ProjectionEdge.from/to** refer to node IDs within the same projection.
- **path / canonicalPath format**: `Plane:/segment@value/segment@value/...` where `Plane` is the projection plane name and each path segment may include an `@`-qualified locator.

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

- **Parameter validation**: params are checked against either the template schema (`ParamSchema`) or a template builder (`Build`). Values are coerced from GraphQL floats to ints when safe.
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
