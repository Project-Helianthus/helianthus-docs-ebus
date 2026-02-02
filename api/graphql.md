# GraphQL API

## Current Status

The GraphQL API surface is still **not** exposed (no server, queries, mutations, or subscriptions). However, a **dynamic schema builder** is now implemented and produces registry-driven schema snapshots.

## Dynamic Schema Builder (Implemented)

The builder assembles a GraphQL-oriented schema model directly from the registry:

- **Registry-driven types**: devices, planes, and methods are enumerated from the registry; each method includes frame primary/secondary bytes and a **response schema** (fields + data types) selected via the schema selector for the device’s address/hardware version.
- **Rebuild on registry change**: `Start(ctx)` performs an initial build and listens on a `changes` channel; each signal triggers a rebuild. If no channel is provided, callers can trigger rebuilds via `Rebuild()`.
- **Revisioned snapshots**: each successful rebuild increments a revision counter; `Schema()` returns a deep-copied snapshot to keep callers insulated from concurrent rebuilds.

## Not Yet Implemented

- No GraphQL server or resolvers.
- No queries, mutations, or subscriptions exposed.
