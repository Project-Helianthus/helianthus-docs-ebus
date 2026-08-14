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
  - `instance_guid` (required stable installation identity)
- TXT key matching is case-insensitive.

Discovery is only a hint. The integration must verify the discovered endpoint over GraphQL before it creates or rebinds a config entry.

### 2. Manual configuration

The config flow supports manual fields:

- `host`
- `port`
- `path` (GraphQL endpoint path)
- `transport` (`http` or `https`)
- `version` (optional metadata)

Before creating the config entry, the integration validates connectivity and stable identity by querying:

```graphql
query GatewayIdentity {
  gatewayIdentity {
    instanceGuid
  }
}
```

The config entry `unique_id` is the verified `instanceGuid`, not `host:port`.
`host`, `port`, `path`, and `transport` are mutable transport coordinates and may be rewritten after verified rediscovery.

## GraphQL Capability Matrix

| Capability | Query/Field | Required | Behavior if Missing |
|---|---|---|---|
| Config-flow identity probe | `gatewayIdentity.instanceGuid` | Yes | Setup blocked (`invalid_response` / `cannot_connect` / `requires_gateway_upgrade`) |
| Device inventory (base) | `devices { address manufacturer deviceId softwareVersion hardwareVersion }` | Yes | Setup cannot build device tree |
| Device identity enrichment | `devices { serialNumber macAddress }` | Optional | Integration falls back to base query and fallback ID scheme |
| Service status | `daemonStatus`, `adapterStatus` | Yes (current implementation) | Setup refresh fails |
| Semantic climate/DHW | `zones`, `dhw` | Optional | Coordinator returns empty/default semantic payload |
| Energy totals | `energyTotals` | Optional | Coordinator returns `energyTotals: null` |
| Realtime subscriptions | GraphQL WS (`graphql-transport-ws`) | Optional | Polling remains available via coordinator intervals |

## Semantic entity contract

### Zone climate

The integration reads semantic zone data from GraphQL and exposes:

- `current_temperature` from `zones[].state.currentTempC`
- `target_temperature` from `zones[].config.targetTempC`
- `current_humidity` from `zones[].state.currentHumidityPct` (when available)
- `hvac_mode` from `zones[].config.operatingMode`
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

## eeBUS And FM5 Diagnostics

Home Assistant consumes the gateway-owned eeBUS operator projection from the
boundary defined in
[`../api/eebus-operator-admin.md`](../api/eebus-operator-admin.md). It provides
a native pairing flow without an eeBUS-specific credential or reauthentication
step and submits only the closed typed actions owned by the gateway. It never
changes the generic Home Assistant authentication or lifecycle, which remain
outside the eeBUS contract. Home Assistant may receive bounded raw SPINE and
complete comparison identity through the gateway boundary only. It uses that
data only in active view/request memory, does not persist it beyond the active
view, does not promote it into semantic state, and never includes it in public
or shareable output. It never receives trust-store access, operator-socket
access, or transport ownership, and it does not own a second pairing state
machine. Protocol-specific action and identity semantics remain in the canonical
`helianthus-docs-eebus` documents linked by that boundary.

After the pending GraphQL contract and the corresponding HA PR are implemented,
FM5 diagnostics read `fm5Interpretation { mode degradedReason
evidenceRevision }`. This is a target contract, not current integration
availability. The diagnostic entity exposes the gateway-supplied mode and
sanitized reason and uses the revision only to keep one coherent update; it does
not derive a reason from missing solar/cylinder values or from the legacy mode
scalar. `GPIO_ONLY` with any reason other than
`CONFIGURATION_NOT_INTERPRETABLE` is an invalid response and enters integration
repair/degraded state rather than being shown as a healthy configuration. A
transient acquisition reason retains the last coherent structural mode and is
shown only as current acquisition health.

Until the first coherent structural classification, GraphQL returns a null
verdict. Home Assistant treats a null verdict as acquisition unavailable and
does not create, retain, or infer a structural FM5 mode from other semantic
objects.

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

- Another config entry already uses the same verified `instanceGuid`.

### `requires_gateway_upgrade`

- The gateway does not yet expose `gatewayIdentity.instanceGuid`.
- New GUID-native setup is blocked until the gateway is upgraded.

### `identity_mismatch`

- Zeroconf TXT `instance_guid` did not match the GraphQL-verified `gatewayIdentity.instanceGuid`.
- Automatic rebind is refused.

### Coordinator response structure

The coordinator now uses a nested response structure from the GraphQL semantic snapshot.
Zone, DHW, circuit, and system data are returned as sub-objects (`zones`, `dhw`, `circuits`, `system`, `boiler_status`, etc.) rather than flat top-level fields.
Entity platforms consume these nested sub-objects directly from the coordinator data dict.

### Missing optional data

- If `zones` are absent, zone climate entities remain empty.
- DHW entity is created even when `dhw` is initially absent; it stays unavailable until semantic DHW payload appears.
- If `energyTotals` is absent, energy entities remain unavailable.
- In `ebusd-tcp` deployments, zone entities can appear after the first semantic refresh cycle
  (default up to ~1 minute), because fallback discovery may hydrate zones from ebusd `grab result all`.
- This fallback hydration is treated as live runtime semantic data (not stale cache preload), so startup
  phase progression can continue when direct B524 reads are unavailable.
- In `ebusd-tcp` fallback parsing, both B524 selector opcode families (`0x02` and `0x06`) are accepted from `grab result all` lines.
- If `allowedModes` is absent, zone climate falls back to `off/auto/heat`.
