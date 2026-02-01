# Full-Stack Deployment

## Current Status

There is no runnable full-stack server yet. The gateway packages (`graphql`, `mcp`, `mdns`, `matter`) are stubs, and `cmd/gateway` contains an empty `main()`.

## What Exists

- `helianthus-ebusgo` and `helianthus-ebusreg` build and include unit tests.
- `helianthus-ebusgateway` builds as a Go module but does not expose an API surface.

## Build/Verify (Libraries Only)

```bash
# In each repo root:
go test ./...
```
