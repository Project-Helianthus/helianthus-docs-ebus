# Contributing

## Scope

This repository documents **implemented behavior** only. If a feature is not present in code, it should be described as not implemented rather than speculating.

## Gateway Configuration (Implemented)

The gateway runtime uses a Go config struct and CLI flags (see `deployment/full-stack.md`). There are no environment variables for gateway configuration yet.

### Config Surface

- `Config.Transport`: optional `transport.RawTransport`. If set, transport dialing is skipped and `Close()` calls `Transport.Close()`.
- `Config.TransportConfig`: transport selection and dialing (`Protocol`, `Network`, `Address`, `ReadTimeout`, `WriteTimeout`, `DialTimeout`, optional `Dial` function).
- `Config.BusConfig`: zero value uses `protocol.DefaultBusConfig()`.
- `Config.QueueCapacity`: `0` uses the protocol default queue capacity.
- `Config.Providers`: `registry.PlaneProvider` list used to populate planes on registry registration.

### Transport Selection

- If `Config.Transport` is provided, it is used directly.
- Otherwise the gateway dials using `TransportConfig.Network` + `TransportConfig.Address` (both required).
- `TransportConfig.Protocol` is case-insensitive: `enh` (or empty) selects ENH, `ens` selects ENS; any other value fails at startup.
- Defaults from `DefaultConfig()`: `enh`, `unix`, `/var/run/ebusd/ebusd.socket`, and 5s timeouts.

### Startup/Shutdown

- `New(ctx, cfg)` resolves transport and constructs Bus, DeviceRegistry, and BusEventRouter.
- `Start(ctx)` runs the bus loop; cancellation stops the bus.
- `Close()` closes the underlying transport connection.
- `RefreshRouterPlanes()` updates router subscriptions from planes registered in the registry.

## Dual License Model

This documentation is split across two licenses:

- **CC0-1.0** for `protocols/` and `types/` (public domain, implementation-agnostic).
- **AGPL-3.0** for everything else (Helianthus-specific architecture, APIs, and deployment).

When editing, keep protocol/type content implementation-neutral and avoid Helianthus-specific references.

## Style

- Prefer concise, testable statements.
- Include wire layouts, byte formats, and examples with language-tagged code blocks.
- Keep diagrams in Mermaid for architecture, data flow, and state machines.
