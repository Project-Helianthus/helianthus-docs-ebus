# Full-Stack Deployment

## Current Status

`cmd/gateway` runs the bus stack and serves HTTP endpoints for GraphQL, GraphQL subscriptions, and MCP. It can optionally enable a passive broadcast listener and advertise the GraphQL endpoint over mDNS.

## What Exists

- `helianthus-ebusgo` and `helianthus-ebusreg` build and include unit tests.
- `helianthus-ebusgateway` builds as a Go module and serves:
  - GraphQL queries/mutations: `/graphql`
  - GraphQL subscriptions (SSE/WS): `/graphql/subscriptions`
  - Projection snapshot endpoint: `/snapshot`
  - MCP endpoint: `/mcp`
  - Portal UI (read-only projection explorer): `/ui`
- mDNS advertisement for the GraphQL endpoint (see mDNS Discovery below).
- `cmd/gateway` can optionally enable a **passive broadcast listener** (separate connection) for energy broadcasts.

## Gateway Transport Backend Selection

`cmd/gateway` selects the eBUS transport backend via CLI flags:

| Flag | Purpose | Notes |
|---|---|---|
| `-transport` | Backend protocol | `enh`, `ens`, or `ebusd-tcp` |
| `-network` | Dial network | `unix` or `tcp` |
| `-address` | Socket path or host:port | Example: `/var/run/ebusd/ebusd.socket` or `127.0.0.1:8888` |
| `-read-timeout` | Read timeout | Default `5s` |
| `-write-timeout` | Write timeout | Default `5s` |
| `-dial-timeout` | Connect timeout | Default `5s` |

### Example Transport Configurations

```bash
# ENH over unix socket (default-style setup)
go run ./cmd/gateway \
  -transport enh \
  -network unix \
  -address /var/run/ebusd/ebusd.socket

# ENS over TCP adapter
go run ./cmd/gateway \
  -transport ens \
  -network tcp \
  -address 127.0.0.1:9999

# ebusd command backend over TCP
go run ./cmd/gateway \
  -transport ebusd-tcp \
  -network tcp \
  -address 127.0.0.1:8888
```

For ebusd command syntax and response framing details, see `protocols/ebusd-tcp.md`.

## ebusd-tcp Backend Notes (Gateway)

When `-transport ebusd-tcp` is selected, the gateway uses ebusd's text command channel (typically port `8888`) and executes request/response traffic via `hex` commands.

### Limitations

- The ebusd command backend is request/response oriented; it is not a continuous bus sniff stream.
- Broadcast sends (`DST=0xFE`) may return textual completion (for example `done ...`) with no hex payload.
- The optional passive broadcast listener (`-broadcast`) expects stream-style frame input; this is generally not useful with ebusd command-mode connections.

### Error Behavior

- `ERR:` lines with timeout/no-answer wording are treated as timeouts.
- Other `ERR:` lines (or malformed hex/usage responses) are treated as invalid payload errors.
- If multiple lines are returned, parsers should use the first valid hex payload line and ignore later trailing noise.
- Empty/no non-empty response lines are treated as timeout conditions.

## mDNS Discovery

When `-mdns` is enabled (default), the gateway advertises its GraphQL endpoint via DNS-SD:

- **Service type:** `_helianthus-graphql._tcp` (domain `local.`)
- **Instance name:** `-mdns-instance` (default `helianthus`)
- **Port:** the HTTP listener port
- **TXT records:**
  - `path`: HTTP path for GraphQL (default `-mdns-path` or `-graphql-path`, e.g. `/graphql`)
  - `version`: discovery schema version (default `1`)
  - `transport`: endpoint transport (default `http`)

## Build/Verify (Libraries Only)

```bash
# In each repo root:
go test ./...
```
