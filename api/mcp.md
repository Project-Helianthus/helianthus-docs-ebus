# MCP Endpoint

## Current Status

The MCP server is implemented and served by `cmd/gateway` at `/mcp`.

## Implemented Surface

- `ebus.devices`: list devices, planes, and methods
- `ebus.invoke`: invoke a plane method with params

## MCP-first Usage in Development

Helianthus uses MCP as the first integration surface for new capabilities.
The development order is:

1. MCP prototype and stabilization (`ebus.v1.*` contract)
2. GraphQL parity after MCP determinism/contract gates are green
3. Consumer rollout (HA and others) after GraphQL parity

The architecture model and gates are documented in:

- [architecture/mcp-first-development.md](../architecture/mcp-first-development.md)
