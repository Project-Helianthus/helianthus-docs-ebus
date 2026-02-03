# Full-Stack Deployment

## Current Status

There is no runnable full-stack server yet. The gateway packages (`graphql`, `mcp`, `mdns`, `matter`) exist, but `cmd/gateway` currently only starts the bus stack and does not serve HTTP endpoints.

## What Exists

- `helianthus-ebusgo` and `helianthus-ebusreg` build and include unit tests.
- `helianthus-ebusgateway` builds as a Go module; `cmd/gateway` can optionally enable a **passive broadcast listener** (separate connection) for energy broadcasts.

## Build/Verify (Libraries Only)

```bash
# In each repo root:
go test ./...
```
