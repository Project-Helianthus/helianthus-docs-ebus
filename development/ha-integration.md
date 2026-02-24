# Home Assistant Integration

## Scope

This guide documents how `helianthus-ha-integration` discovers a Helianthus gateway and what GraphQL capabilities are required versus optional.

## Setup

### 1. Automatic discovery (mDNS)

- The integration listens for `_helianthus-graphql._tcp.local.`.
- TXT keys used by the integration:
  - `path` (default: `/graphql`)
  - `transport` (`http` or `https`, default: `http`)
  - `version` (optional, informational)
- TXT key matching is case-insensitive.

### 2. Manual configuration

The config flow supports manual fields:

- `host`
- `port`
- `path` (GraphQL endpoint path)
- `transport` (`http` or `https`)
- `version` (optional metadata)

Before creating the config entry, the integration validates connectivity by running a schema probe query:

```graphql
query HelianthusSchema {
  __schema {
    queryType { name }
  }
}
```

Duplicate endpoint detection (`host:port`) is checked before network validation.

## GraphQL Capability Matrix

| Capability | Query/Field | Required | Behavior if Missing |
|---|---|---|---|
| Config-flow probe | `__schema.queryType.name` | Yes | Setup blocked (`invalid_response` / `cannot_connect`) |
| Device inventory (base) | `devices { address manufacturer deviceId softwareVersion hardwareVersion }` | Yes | Setup cannot build device tree |
| Device identity enrichment | `devices { serialNumber macAddress }` | Optional | Integration falls back to base query and fallback ID scheme |
| Service status | `daemonStatus`, `adapterStatus` | Yes (current implementation) | Setup refresh fails |
| Semantic climate/DHW | `zones`, `dhw` | Optional | Coordinator returns empty/default semantic payload |
| Energy totals | `energyTotals` | Optional | Coordinator returns `energyTotals: null` |
| Realtime subscriptions | GraphQL WS (`graphql-transport-ws`) | Optional | Polling remains available via coordinator intervals |

## Semantic entity contract

### Zone climate

The integration reads semantic zone data from GraphQL and exposes:

- `current_temperature` from `zones[].currentTempC`
- `target_temperature` from `zones[].targetTempC`
- `current_humidity` from `zones[].currentHumidityPct` (when available)
- `hvac_mode` from `zones[].operatingMode`
- `preset_mode` normalized to canonical tokens:
  - `schedule`
  - `manual`
  - `quickveto`
  - `away`
- `hvac_modes` from `zones[].allowedModes` (fallback: `off`, `auto`, `heat`)

Raw semantic fields are also kept as extra attributes for diagnostics:

- `zoneOperationModeRaw`
- `zoneSpecialFunctionRaw`
- `zoneValveStatusRaw`
- `zoneCircuitIndexRaw`
- `circuitTypeRaw`

### DHW climate

The DHW entity reads semantic data from `dhw` and exposes:

- `current_temperature` from `dhw.currentTempC`
- `target_temperature` from `dhw.targetTempC`
- `operation_mode` from `dhw.operatingMode` (`off` / `auto` / `manual`)
- canonical preset in attributes (`schedule` / `manual` / `quickveto` / `away`)

Raw DHW fields are also exposed as attributes:

- `dhwOperationModeRaw`
- `dhwSpecialFunctionRaw`

## Write policy (config-only registers)

The integration enforces config-only writes. State registers are blocked at entity level.

### Zone writes (group `0x03`)

- `set_temperature` writes:
  - `0x0022` (`configuration.heating.desired_setpoint`)
  - `0x0014` (`configuration.heating.manual_mode_setpoint`)
- `set_hvac_mode` writes:
  - `0x0006` (`configuration.heating.operation_mode`)
- `set_preset_mode`:
  - `schedule` -> write `0x0006=auto`
  - `manual` -> write `0x0006=manual`
  - `quickveto` / `away` -> blocked (non-config path required)

### DHW writes (group `0x01`, instance `0x00`)

- `set_temperature` writes:
  - `0x0004` (`configuration.domestic_hot_water.tapping_setpoint`)
- `set_operation_mode` writes:
  - `0x0003` (`configuration.domestic_hot_water.operation_mode`)

## Schedule mirror entities and helper bindings

The integration adds read-only schedule mirror binary sensors:

- per zone:
  - `Daily Schedule Active`
  - `Quick Veto Active`
  - `Away Schedule Active`
- for DHW:
  - same three sensors

Optional HA helper bindings can drive schedule mode:

- `zone_schedule_helpers`
  - CSV format: `zone-1=schedule.zone1,zone-2=schedule.zone2`
  - When helper turns `on`, integration sets zone op-mode to `auto`
- `dhw_schedule_helper`
  - format: `schedule.dhw_name`
  - When helper turns `on`, integration sets DHW op-mode to `auto`

## Device Tree

The integration materializes this hierarchy in HA device registry:

1. `Helianthus Daemon` (root)
2. `eBUS Adapter` (via daemon)
3. Physical eBUS devices (via adapter)
4. Virtual semantic devices (derived) attached to their semantic parent (for example zones/DHW via the regulator)

Device IDs are generated with deterministic fallback:

1. Prefer stable, addressable identity: `deviceId + address + hw + sw`
2. If present, include `serialNumber` and/or `macAddress` as *additional* identifiers (enrichment), but do not create a new device when those fields are temporarily missing.

### Canonical naming/model mapping

For known Vaillant devices, integration-level names/models are normalized to stable marketing values:

- `deviceId=BASV*`
  - Name: `sensoCOMFORT RF`
  - Model: `VRC 720f/2 (eBUS: BASV)` (when product model is available)
- `deviceId=VR_71`
  - Name: `FM5 Control Centre`
  - Model: `VR 71 (eBUS: VR_71)` (when product model is available)

Other devices keep gateway-provided display/model fields, with `model` augmented as `(<eBUS id>)` for stable troubleshooting context.

### Stale Helianthus artifacts cleanup

At setup, integration performs best-effort cleanup of stale `helianthus/*` registry artifacts that are not tied to any active Helianthus config entry.

- Scope: **only** Helianthus-owned identifiers.
- Non-scope: devices from `ebusd_http` / MQTT / other integrations are untouched.

## Troubleshooting

### `cannot_connect`

- Host/port/path/transport mismatch.
- Endpoint unreachable from HA.
- TLS mismatch (for example `http` configured for an `https` endpoint).

### `invalid_response`

- Endpoint is reachable but does not return GraphQL schema data.
- Reverse proxy or non-GraphQL endpoint is mapped to the configured path.

### `already_configured`

- Another config entry already uses the same `host:port`.

### Missing optional data

- If `zones` are absent, zone climate entities remain empty.
- DHW entity is created even when `dhw` is initially absent; it stays unavailable until semantic DHW payload appears.
- If `energyTotals` is absent, energy entities remain unavailable.
- In `ebusd-tcp` deployments, zone entities can appear after the first semantic refresh cycle
  (default up to ~1 minute), because fallback discovery may hydrate zones from ebusd `grab result all`.
- In `ebusd-tcp` fallback parsing, both B524 selector opcode families (`0x02` and `0x06`) are accepted from `grab result all` lines.
- If `allowedModes` is absent, zone climate falls back to `off/auto/heat`.
