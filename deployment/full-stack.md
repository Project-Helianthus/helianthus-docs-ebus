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
| `-transport` | Backend protocol | `enh`, `ens` (alias of `enh`), `udp-plain`, or `ebusd-tcp` |
| `-network` | Dial network | `unix`, `tcp`, or `udp` |
| `-address` | Socket path or host:port | Example: `/var/run/ebusd/ebusd.socket` or `127.0.0.1:8888` |
| `-read-timeout` | Read timeout | Default `5s` |
| `-write-timeout` | Write timeout | Default `5s` |
| `-dial-timeout` | Connect timeout | Default `5s` |

### Example Transport Configurations

```bash
# ENH over TCP adapter (enhanced adapter protocol, ebusd-style port 9999)
go run ./cmd/gateway \
  -transport enh \
  -network tcp \
  -address 203.0.113.10:9999

# ENS alias over TCP (same framing as ENH for network endpoints)
go run ./cmd/gateway \
  -transport ens \
  -network tcp \
  -address 203.0.113.10:9999

# Raw UDP byte stream (software arbitration required above transport)
go run ./cmd/gateway \
  -transport udp-plain \
  -network udp \
  -address 203.0.113.10:9999

# ebusd command backend over unix socket
go run ./cmd/gateway \
  -transport ebusd-tcp \
  -network unix \
  -address /var/run/ebusd/ebusd.socket
```

For ebusd command syntax and response framing details, see `protocols/ebusd-tcp.md`.

Terminology note:

- `protocols/enh.md` / `protocols/ens.md` describe ebusd’s enhanced adapter protocol and the meaning of the `enh:`/`ens:` prefixes.
- In Helianthus gateway CLI, `-transport ens` is accepted as a compatibility alias for `-transport enh`.
- Raw ESC/SYN wire symbols (`0xA9`/`0xAA`) are decoded in the bus/protocol layer.

### UDP-PLAIN operational guidance

For UDP-PLAIN adapters, run Helianthus behind a proxy with a **single southbound owner**. Do not connect multiple independent clients directly to the adapter endpoint.

Recommended topology:

```text
adapter (udp-plain) <-single southbound-> helianthus-ebus-adapter-proxy <-northbound-> gateway / ebusd / tools
```

Rationale:

- prevents cross-client request/response mismatch on raw byte streams,
- centralizes bounded retry/backoff and collision signaling,
- keeps a consistent bus view for all northbound consumers.

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
