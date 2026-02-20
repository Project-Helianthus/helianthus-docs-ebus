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
| `-source-addr` | Initiator/source address used by scan + semantic reads | Hex (`0xF0`), decimal, `0x00`, or `auto` |
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
  -address 203.0.113.10:9999 \
  -source-addr auto

# Raw UDP byte stream (software arbitration required above transport)
go run ./cmd/gateway \
  -transport udp-plain \
  -network udp \
  -address 203.0.113.10:9999 \
  -source-addr auto

# ebusd command backend over unix socket
go run ./cmd/gateway \
  -transport ebusd-tcp \
  -network unix \
  -address /var/run/ebusd/ebusd.socket
```

For ebusd command syntax and response framing details, see `protocols/ebusd-tcp.md`.

### Source-address behavior

- `-source-addr auto` (or `-source-addr 0x00`) enables **gentle-join** behavior with proxy-mediated ENS/ENH/UDP-plain flows.
- In gentle-join mode, Helianthus asks the proxy to select a free initiator dynamically instead of pinning a fixed address.
- `-source-addr 0x31` should be avoided when `ebusd` is also active, because `0x31` is `ebusd`'s common default initiator.
- With `-transport ebusd-tcp`, source selection only affects ebusd command parameters; the on-wire initiator is still ebusd's own bus identity.

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
- `dump enabled` / `dump disabled` banners are treated as non-semantic noise and ignored.
- If multiple lines are returned, parsers should use the first valid hex payload line and ignore later trailing noise.
- If an `ERR:` line appears before the actual hex payload in the same command response burst, parsers keep a short follow-up window to catch the valid hex line.
- Empty/no non-empty response lines are treated as timeout conditions.
- Runtime transport setup clamps `ebusd-tcp` read/write deadlines to at least `scan-request-timeout` (default floor `400ms`) to reduce cross-command stream desynchronization.

### Startup Scan Target Narrowing (all transports)

Gateway startup scan tries to reduce bus load by using ebusd's known target list when available:

1. If gateway itself runs with `-transport ebusd-tcp` over `tcp`, it asks that endpoint for `scan result`.
2. Otherwise it also tries a local fallback ebusd endpoint at `127.0.0.1:8888`.
3. If neither returns targets, gateway falls back to the full default address scan.
4. If direct scan requests time out for all narrowed targets, gateway imports device metadata
   (address/manufacturer/device ID/HW/SW/SN) from the same ebusd `scan result` output as a discovery fallback.

Runtime read/write traffic still uses the configured gateway transport.

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
