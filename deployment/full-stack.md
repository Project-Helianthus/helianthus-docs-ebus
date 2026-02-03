# Full-Stack Deployment

## Current Status

`cmd/gateway` runs the bus stack and serves HTTP endpoints for GraphQL, GraphQL subscriptions, and MCP. It can optionally enable a passive broadcast listener and advertise the GraphQL endpoint over mDNS.

## What Exists

- `helianthus-ebusgo` and `helianthus-ebusreg` build and include unit tests.
- `helianthus-ebusgateway` builds as a Go module and serves:
  - GraphQL queries/mutations: `/graphql`
  - GraphQL subscriptions (SSE/WS): `/graphql/subscriptions`
  - MCP endpoint: `/mcp`
- mDNS advertisement: `_helianthus-graphql._tcp` with TXT `path=/graphql`
- `cmd/gateway` can optionally enable a **passive broadcast listener** (separate connection) for energy broadcasts.

## Build/Verify (Libraries Only)

```bash
# In each repo root:
go test ./...
```
