# MCP Endpoint

## Current Status

The MCP server is implemented and served by `cmd/gateway` at `/mcp`.

## Implemented Surface

- Core stable (`ebus.v1.*`)
  - `ebus.v1.runtime.status.get`
  - `ebus.v1.registry.devices.list`
  - `ebus.v1.registry.devices.get`
  - `ebus.v1.registry.planes.list`
  - `ebus.v1.registry.methods.list`
  - `ebus.v1.semantic.zones.get`
  - `ebus.v1.semantic.dhw.get`
  - `ebus.v1.semantic.energy_totals.get`
  - `ebus.v1.semantic.snapshot.get`
  - `ebus.v1.snapshot.capture`
  - `ebus.v1.snapshot.drop`
  - `ebus.v1.rpc.invoke`
- Legacy aliases
  - `ebus.devices`
  - `ebus.invoke`

## Plane Boundary Note

- `scan` is treated as a cross-device discovery layer and is not modeled as a heat-source class plane.
- Heat-source planes (for class-specific modeling) are documented under architecture decisions and class design docs.

## MCP-first Usage in Development

Helianthus uses MCP as the first integration surface for new capabilities.
The development order is:

1. MCP prototype and stabilization (`ebus.v1.*` contract)
2. GraphQL parity after MCP determinism/contract gates are green
3. Consumer rollout (HA and others) after GraphQL parity

The architecture model and gates are documented in:

- [architecture/mcp-first-development.md](../architecture/mcp-first-development.md)
