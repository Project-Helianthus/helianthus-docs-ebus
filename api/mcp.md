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
  - `ebus.v1.semantic.boiler_status.get`
  - `ebus.v1.semantic.system.get`
  - `ebus.v1.semantic.circuits.get`
  - `ebus.v1.semantic.radio_devices.get`
  - `ebus.v1.semantic.fm5_mode.get`
  - `ebus.v1.semantic.solar.get`
  - `ebus.v1.semantic.cylinders.get`
  - `ebus.v1.semantic.snapshot.get`
  - `ebus.v1.snapshot.capture`
  - `ebus.v1.snapshot.drop`
  - `ebus.v1.rpc.invoke`
- Legacy aliases
  - `ebus.devices`
  - `ebus.invoke`

## Semantic Payload Notes

- `ebus.v1.semantic.circuits.get` exposes explicit per-circuit ownership as `managing_device`.
- `managing_device.role` is always present and is one of `REGULATOR`, `FUNCTION_MODULE`, or `UNKNOWN`.
- `managing_device.device_id` and `managing_device.address` are populated only when the gateway has proven ownership evidence for the current topology.
- `ebus.v1.semantic.system.get` no longer exposes `vr71_circuit_start_index`; that threshold was a gateway heuristic and is not part of the canonical contract.

## RPC Method Reference — Vaillant System Plane

Methods available via `ebus.v1.rpc.invoke` on the `system` plane for Vaillant/Saunier/AWB controllers.

### `read_timer`

Reads per-day weekly schedule timer programs via B524 opcode 0x03.

**Intent:** `READ_ONLY`

| Param    | Type   | Required | Description |
|----------|--------|----------|-------------|
| source   | byte   | yes      | Initiator address (gateway = 113) |
| sel1     | byte   | yes      | Timer selector 1 (controller-specific) |
| sel2     | byte   | yes      | Timer selector 2 (controller-specific) |
| sel3     | byte   | yes      | Timer selector 3 (controller-specific) |
| weekday  | byte   | yes      | Weekday index: 0x00=Mon .. 0x06=Sun |

**Wire format:** `[0x03, SEL1, SEL2, SEL3, WD]`

**Response fields:** `opcode`, `sel1`, `sel2`, `sel3`, `weekday`, `value` (raw timer bytes), `slot_count` (number of time slots). When the controller returns no data, `value` is invalid.

### `read_raw`

Raw opcode passthrough for investigation. Sends caller-provided payload bytes verbatim on B524.

**Intent:** `MUTATE` (requires `allow_dangerous: true` and `idempotency_key`)

| Param   | Type     | Required | Description |
|---------|----------|----------|-------------|
| source  | byte     | yes      | Initiator address (gateway = 113) |
| payload | `[]byte` | yes      | Raw opcode bytes (1–16 bytes) |

**Response fields:** `request_payload` (echo of sent bytes), `response_payload` (controller response), `value` (alias for response_payload). When no response data, `value` is invalid.

**Safety note:** This method is intentionally `readOnly: false` because it can send arbitrary opcodes including mutating ones (e.g. 0x04 timer write). The gateway enforces `allow_dangerous` and idempotency gates.

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
