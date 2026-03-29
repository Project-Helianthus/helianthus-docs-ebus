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
  - Projection browser (read-only projection explorer): `/ui`
  - Portal shell + versioned API: `/portal` and `/portal/api/v1`
- mDNS advertisement for the GraphQL endpoint (see mDNS Discovery below).
- `cmd/gateway` can optionally enable a **passive broadcast listener** (separate connection) for energy broadcasts.

## Gateway Transport Backend Selection

`cmd/gateway` selects the eBUS transport backend via CLI flags:

| Flag | Purpose | Notes |
|---|---|---|
| `-transport` | Backend protocol | `enh`, `ens` (alias of `enh`), `udp-plain`, `tcp-plain`, or `ebusd-tcp` |
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

# Raw TCP byte stream (software arbitration required above transport)
go run ./cmd/gateway \
  -transport tcp-plain \
  -network tcp \
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

- `-source-addr auto` (or `-source-addr 0x00`) enables **gentle-join** behavior with proxy-mediated ENS/ENH/UDP-plain/TCP-plain flows.
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
2. In `ebusd-tcp` mode, gateway preloads registry devices directly from that `scan result`
   (address/manufacturer/device ID/HW/SW/SN) before active probing.
3. For non-`ebusd-tcp` transports, it also tries a local fallback ebusd endpoint at `127.0.0.1:8888`.
4. If neither returns targets, gateway falls back to the full default address scan.
5. If direct scan requests time out for all narrowed targets, gateway imports device metadata
   from the same ebusd `scan result` output as a discovery fallback.

Important startup contract:

- `scan result` preload/narrowing is opportunistic bus-load reduction, not proof that
  semantic startup is ready to close.
- Preloaded inventory, product identity, and imported metadata are useful hints, but
  they do not by themselves prove that startup already has a coherent Vaillant/B524
  controller root.
- If narrowed/preloaded inventory does not yield a coherent B524/controller root,
  gateway must perform one bounded full-range discovery retry before concluding startup
  scan.
- If preload already yields a coherent root, no broadened retry is required.

When semantic B524 reads time out in `ebusd-tcp` mode, zone inventory/name/state can be recovered
from ebusd's `grab result all` cache (passive snapshot), so climate entities can still appear without
forcing additional bus traffic.
Successful hydration from this path is classified as **live semantic source** for startup phase accounting
(it is not treated as persistent stale cache preload).

Runtime read/write traffic still uses the configured gateway transport.

### Passive observe-first transport contract

Passive observe-first support is narrower than active startup support.

- `ebusd-tcp` remains `unsupported_or_misconfigured` for passive observe-first.
  See [`protocols/ebusd-tcp.md`](../protocols/ebusd-tcp.md).
- Direct adapter-class `enh` / `ens` endpoints over `tcp/:9999` remain
  `unsupported_or_misconfigured` for passive observe-first, including equivalent
  hostname forms that resolve to the same adapter listener.
  See [`protocols/enh.md`](../protocols/enh.md) and
  [`protocols/ens.md`](../protocols/ens.md).
- Proxy-like `enh` / `ens` endpoints on other ports remain passive-capable for
  observe-first, whether they are reached over local loopback or remote northbound
  addresses.

Operational meaning:

- a coherent B524/controller root still proves active semantic startup readiness;
- it does **not** by itself prove that passive observe-first is supported for the
  chosen transport topology;
- validation cases that use direct adapter-class `enh` / `ens` endpoints should
  expect explicit passive unavailability, not endless `warming_up` / `socket_loss`
  states;
- validation cases that use proxy-like `enh` / `ens` endpoints on non-adapter ports
  should continue to expect passive-capable behavior.

### GW-16 Rollout Decision

The bounded P03 proof contract and the rollout decision remain intentionally
family-scoped. The proof evidence proves the proxy-backed `ENS` topology used by
`P03`, but it does not justify a broad default flip.

- Bounded proof evidence: [`Project-Helianthus/helianthus-ebusgateway#400`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/400)
- Canonical non-promotion decision: [`Project-Helianthus/helianthus-ebusgateway#439`](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/439)

Operational meaning:

- record-only remains the canonical default for any family or deployment
  topology that is not individually proven in the bounded passive proof scope;
- the proven proxy-backed `ENS` P03 topology may continue to serve proof
  artifacts, but that does not widen default promotion to direct adapter-class
  `enh` / `ens` or `ebusd-tcp`;
- any later default-flip claim must be backed by a separate proven deployment
  family.

### Semantic Cache Persistence

- Gateway reads/writes semantic startup cache at `-semantic-cache-path` (default `./semantic_cache.json`).
- Writes are atomic (temp file + rename).
- Runtime semantic cache persistence writes happen for live semantic publications.
- Legacy v1 -> v2 migration can also rewrite the cache during startup load (`semantic_cache_migrated`), before any live publish.
- Cache load failures are fail-safe:
  - missing file → `semantic_cache_miss`
  - malformed/unknown schema/read error → `semantic_cache_invalid`
  - runtime continues with live polling and no crash.
- Legacy v1 cache payloads are migrated to v2 at load time (`semantic_cache_migrated`).

Operator recovery for corrupted cache:

1. Stop gateway/add-on.
2. Move or delete the cache file at `-semantic-cache-path`.
3. Restart gateway; runtime should log `semantic_cache_miss` and rebuild cache from live data.

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
