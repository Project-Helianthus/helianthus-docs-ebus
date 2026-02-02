# GraphQL API

## Current Status

The GraphQL API does not yet include mutations or subscriptions, and there is no HTTP server wiring. However, **read-only queries** and a **dynamic schema builder** are implemented and can be exposed via an HTTP handler.

## Dynamic Schema Builder (Implemented)

The builder assembles a GraphQL-oriented schema model directly from the registry:

- **Registry-driven types**: devices, planes, and methods are enumerated from the registry; each method includes frame primary/secondary bytes and a **response schema** (fields + data types) selected via the schema selector for the device’s address/hardware version.
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
```

### Handler Construction

`NewHandler(builder)` returns an `http.Handler` backed by the query schema. It is ready to mount in an HTTP server but the gateway does not yet expose a server by default.

## Not Yet Implemented

- No mutations.
- No subscriptions.
