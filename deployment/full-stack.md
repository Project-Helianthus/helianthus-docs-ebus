# Full-Stack Deployment

## Current Status

`cmd/gateway` is runnable and wires transport, bus, registry, and router. The gateway packages (`graphql`, `mcp`, `mdns`, `matter`) remain stubs, so there is still no API surface.

## What Exists

- `helianthus-ebusgo` and `helianthus-ebusreg` build and include unit tests.
- `helianthus-ebusgateway` includes a `cmd/gateway` runtime that connects to eBUS transport and runs the bus loop.

## Run Gateway (Wired Runtime)

```bash
# From helianthus-ebusgateway
go run ./cmd/gateway --transport enh --network unix --address /var/run/ebusd/ebusd.socket
```

```bash
# TCP example (ENS transport)
go run ./cmd/gateway --transport ens --network tcp --address 127.0.0.1:8888
```

Flags (defaults shown):

- `--transport` (`enh` or `ens`, default `enh`, case-insensitive; unknown value fails on startup)
- `--network` (default `unix`)
- `--address` (default `/var/run/ebusd/ebusd.socket`)
- `--read-timeout` (default `5s`)
- `--write-timeout` (default `5s`)
- `--dial-timeout` (default `5s`)
- `--queue-capacity` (default `0`, uses bus default)

The gateway runs until `SIGINT`/`SIGTERM` and then closes the transport connection.

## Build/Verify

```bash
# In each repo root:
go test ./...
```
