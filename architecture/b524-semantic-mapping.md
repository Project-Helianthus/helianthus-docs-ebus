# B524 Semantic Plane Mapping (Helianthus)

> **License:** AGPL-3.0. This file documents Helianthus-specific semantic mapping, not protocol-level specifications.
>
> For the B524 wire protocol, see [`../protocols/vaillant/ebus-vaillant-B524.md`](../protocols/vaillant/ebus-vaillant-B524.md).
> For the register catalog, see [`../protocols/vaillant/ebus-vaillant-B524-register-map.md`](../protocols/vaillant/ebus-vaillant-B524-register-map.md).

This document maps B524 registers to Helianthus MCP semantic plane fields. Only registers actively read by the gateway's semantic poller are listed. The **S** prefix in the register map's Notes column marks these registers.

Related architecture:
- Structural decision catalog: [`./b524-structural-decisions.md`](./b524-structural-decisions.md)
- Discovery flow: [`./semantic-structure-discovery.md`](./semantic-structure-discovery.md)
- Operations-first invariants: [`./b524-namespace-invariants.md`](./b524-namespace-invariants.md)

---

## `ebus.v1.semantic.system.get`

Source: `refreshSystem()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `state.system_off` | GG=0x00, RR=0x0007 | bool |
| `state.energy_manager_state` | GG=0x00, RR=0x0048 | u16 (enum) |
| `state.system_water_pressure` | GG=0x00, RR=0x0039 | f32 |
| `state.system_flow_temperature` | GG=0x00, RR=0x004B | f32 |
| `state.outdoor_temperature` | GG=0x00, RR=0x0073 | f32 |
| `state.outdoor_temperature_avg24h` | GG=0x00, RR=0x0095 | f32 |
| `state.maintenance_due` | GG=0x00, RR=0x0096 | bool |
| `state.hwc_cylinder_temperature_top` | GG=0x00, RR=0x009D | f32 |
| `state.hwc_cylinder_temperature_bottom` | GG=0x00, RR=0x009E | f32 |
| `config.adaptive_heating_curve` | GG=0x00, RR=0x0014 | bool |
| `config.alternative_point` | GG=0x00, RR=0x0022 | f32 |
| `config.heating_circuit_bivalence_point` | GG=0x00, RR=0x0023 | f32 |
| `config.dhw_bivalence_point` | GG=0x00, RR=0x0001 | f32 |
| `config.hc_emergency_temperature` | GG=0x00, RR=0x0026 | f32 |
| `config.hwc_max_flow_temp_desired` | GG=0x00, RR=0x0046 | f32 |
| `config.max_room_humidity` | GG=0x00, RR=0x000E | u16 |
| `properties.system_scheme` | GG=0x00, RR=0x0036 | u16 |
| `properties.module_configuration_vr71` | GG=0x00, RR=0x002F | u16 |

## `ebus.v1.semantic.circuits.get`

Source: `refreshCircuits()` in `semantic_vaillant.go`

Ownership note:
- `circuits[].managing_device` is a semantic contract, not a direct single-register read.
- The gateway now emits explicit ownership only for proven topologies.
- For the currently proven live topology (`system_scheme=1`, `module_configuration_vr71=2`, FM5 interpreted), all discovered circuits are marked as managed by `VR_71` (`FUNCTION_MODULE`, address `0x26`).
- Unproven topologies are emitted as `UNKNOWN`; the gateway does not synthesize a replacement threshold heuristic.
- Broader architectural treatment of FM3/FM5/VR66 as functional-module families is documented in [`./functional-modules.md`](./functional-modules.md).

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].state.heating_circuit_flow_setpoint` | GG=0x02, RR=0x0007 | f32 |
| `[].state.current_circuit_flow_temperature` | GG=0x02, RR=0x0008 | f32 |
| `[].state.circuit_state` | GG=0x02, RR=0x001B | enum (u16): STANDBY/HEATING/COOLING |
| `[].state.pump_status` | GG=0x02, RR=0x001E | bool (u16) |
| `[].state.calculated_flow_temperature` | GG=0x02, RR=0x0020 | f32 |
| `[].state.mixer_position_percentage` | GG=0x02, RR=0x0021 | f32 |
| `[].state.current_humidity_pct` | GG=0x02, RR=0x0022 | f32 |
| `[].state.dew_point_temperature` | GG=0x02, RR=0x0023 | f32 |
| `[].state.pump_operating_hours` | GG=0x02, RR=0x0024 | u32 |
| `[].state.pump_starts_count` | GG=0x02, RR=0x0025 | u32 |
| `[].config.heating_curve` | GG=0x02, RR=0x000F | f32 |
| `[].config.heating_flow_temperature_maximum_setpoint` | GG=0x02, RR=0x0010 | f32 |
| `[].config.heating_flow_temperature_minimum_setpoint` | GG=0x02, RR=0x0012 | f32 |
| `[].config.heat_demand_limited_by_outside_temp` | GG=0x02, RR=0x0014 | f32 |
| `[].config.room_temperature_control_mode` | GG=0x02, RR=0x0015 | u16 |
| `[].managing_device` | derived semantic ownership | object |
| `[].config.cooling_enabled` | GG=0x02, RR=0x0006 | bool (u8) |
| `[].properties.heating_circuit_type` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.mixer_circuit_type_external` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.frost_protection_threshold` | GG=0x02, RR=0x001D | f32 | **Stale path**: FLAGS=0x02 (RW) — should be `config.*`. Pending gateway migration |

Consumer note:
- `[].config.cooling_enabled` remains a gateway-level raw semantic field derived from `GG=0x02 RR=0x0006`.
- It is **not** yet a validated Home Assistant-facing configuration contract.

## `ebus.v1.semantic.zones.get`

Source: `refreshState()` / `refreshDiscovery()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].name` | GG=0x03, RR=0x0016 | string |
| `[].config.operating_mode` | derived from GG=0x03 RR=0x0006 + 0x000E | — |
| `[].state.current_temp_c` | GG=0x03, RR=0x000F | f32 |
| `[].config.target_temp_c` | GG=0x03, RR=0x0022 (primary), 0x0014 (fallback) | f32 |
| `[].state.current_humidity_pct` | GG=0x03, RR=0x0028 | f32 |

### Zone Mode Derivation

The `operating_mode` and `preset` exposed in the zones semantic plane are derived from:
- `heating_operation_mode` (0x0006): opmode enum (0=off, 1=auto, 2=manual)
- `current_special_function` (0x000E): sfmode enum (2=quickveto, 3/4=away)
- Associated circuit's `cooling_enabled` (GG=0x02 RR=0x0006): determines heat vs cool capability for the zone

## `ebus.v1.semantic.dhw.get`

Source: `refreshDHW()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `operating_mode` | GG=0x01, RR=0x0003 | u16 (derived) |
| `current_temp_c` | GG=0x01, RR=0x0005 | f32 |
| `target_temp_c` | GG=0x01, RR=0x0004 | f32 |
| `state` | GG=0x01, RR=0x000D | u16 (special function) |

## `ebus.v1.semantic.boiler_status.get`

Source: `refreshBoilerStatus()` in `semantic_vaillant.go`

The current PASS-profile boiler status plane is no longer a B524-only composite. Helianthus now prefers direct BAI00 B509 reads for the boiler semantic surface and keeps only a small B524 fallback/mirror set in the controller path.

Authoritative direct-boiler mapping:
- see [`../protocols/vaillant/ebus-vaillant-B509-boiler-register-map.md`](../protocols/vaillant/ebus-vaillant-B509-boiler-register-map.md)

The B524 contribution that still feeds the current boiler semantic contract is:

| Semantic Path | B524 | Type | Notes |
|---------------|------|------|-------|
| `state.dhwTemperatureC` | GG=0x01, RR=0x0005 | f32 | Controller mirror from DHW group |
| `state.dhwTargetTemperatureC` | GG=0x01, RR=0x0004 | f32 | Controller mirror from DHW group |
| `config.dhwOperatingMode` | GG=0x01, RR=0x0003 | u16 | Decoded into the public enum string |
| `state.flowTemperatureC` | OP=0x06, GG=0x00, RR=0x0015 | f32 | Controller-side primary heat-source mirror. B509 remains authoritative |
| `diagnostics.activeErrors` | OP=0x06, GG=0x00, RR=0x0012 | u8 (raw) | Controller-side primary heat-source error mirror. `0=no active error`; non-zero semantics remain pending validation |
| `diagnostics.heatingStatusRaw` | GG=0x02, II=0x00, RR=0x001B | u16 | Controller-side raw heating status |

Fields currently present in the schema but not populated from a validated source:
- `state.returnTemperatureC`
- `diagnostics.dhwStatusRaw`

## `ebus.v1.semantic.energy_totals.get`

Source: `refreshEnergy()` in `semantic_vaillant.go`

Semantics:
- After the first valid sample, Helianthus keeps the last known `energyTotals` snapshot across temporary B524 read gaps.
- A refresh cycle with no accepted energy points does **not** clear the semantic snapshot and does **not** reset any series to `0` or `null`.

| Semantic Path | B524 | Type | Period |
|---------------|------|------|--------|
| `gas.climate.yearly[1]` | GG=0x00, RR=0x0056 | u32 (kWh) | all-time |
| `electric.climate.yearly[1]` | GG=0x00, RR=0x0057 | u32 (kWh) | all-time |
| `electric.dhw.yearly[1]` | GG=0x00, RR=0x0058 | u32 (kWh) | all-time |
| `gas.dhw.yearly[1]` | GG=0x00, RR=0x0059 | u32 (kWh) | all-time |
| `gas.climate.monthly[1]` | GG=0x00, RR=0x004E | u32 (kWh) | this month |
| `electric.climate.monthly[1]` | GG=0x00, RR=0x004F | u32 (kWh) | this month |
| `electric.dhw.monthly[1]` | GG=0x00, RR=0x0050 | u32 (kWh) | this month |
| `gas.dhw.monthly[1]` | GG=0x00, RR=0x0051 | u32 (kWh) | this month |
| `gas.climate.monthly[0]` | GG=0x00, RR=0x0052 | u32 (kWh) | last month |
| `electric.climate.monthly[0]` | GG=0x00, RR=0x0053 | u32 (kWh) | last month |
| `electric.dhw.monthly[0]` | GG=0x00, RR=0x0054 | u32 (kWh) | last month |
| `gas.dhw.monthly[0]` | GG=0x00, RR=0x0055 | u32 (kWh) | last month |

## `ebus.v1.semantic.solar.get`

Not implemented. Gated by `fm5_config<=2`. Source registers would come from GG=0x04 (solar circuit).

## `ebus.v1.semantic.cylinders.get`

Source: `readCylinderSnapshots()` / `publishFM5Semantic()` in `semantic_vaillant.go`

Publication gate:
- Entire family is gated by `fm5_config<=2`.
- Individual instances are published only when `GG=0x05 RR=0x0004` (`cylinder_temperature`) is live and decodable for that instance.
- Config-only responses from `GG=0x05 RR=0x0001..0x0003` do not imply a real cylinder and must not create `cylinders[]` entries.

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].index` | GG=0x05, II=* | derived |
| `[].temperatureC` | GG=0x05, RR=0x0004 | f32 |
| `[].maxSetpointC` | GG=0x05, RR=0x0001 | f32 |
| `[].chargeHysteresisC` | GG=0x05, RR=0x0002 | f32 |
| `[].chargeOffsetC` | GG=0x05, RR=0x0003 | f32 |

---

## Circuit Type Layer B — Derived Projections

Higher-level semantic projections combine the raw circuit type (GG=0x02 RR=0x0002) with other registers:

- **Cooling capability**: derived from `cooling_enabled` (GG=0x02 RR=0x0006), NOT from circuit type. A heating circuit (type=1) with `cooling_enabled=1` supports both heating and cooling modes.
- **Pool heating**: an APPLICATION of `fixed_value` (type=2) when the system topology includes pool hydraulics (sensor, circulation pump). NOT a separate raw enum value on VRC720/BASV2.
- **Cylinder charging**: `type=3` (DHW) combined with GG=0x05 group presence indicates a cylinder-charging circuit.

These projections are Helianthus runtime logic and are NOT part of the B524 wire protocol. For the raw Layer A register definition, see the register map's circuit type enum.

---

## Discovery & Scan Strategy

### Phase A: group discovery

- probe `0x00` directory sequentially
- stop on first `NaN`
- record unknown groups and unknown descriptor classes for follow-up

### Phase B: constraint dictionary sampling (`0x01`)

- probe `0x01 GG RR` over bounded per-group RR windows
- decode and persist `min/max/step` domains (`u8`, `u16le`, `f32le`, `date`)
- persist decoded entries under artifact metadata (`meta.constraint_dictionary`)
- current implementation keeps constraints advisory (they do not resize planner ranges yet)

### Phase C: instance detection (instanced groups)

- evaluate all `II=0x00..II_max` (no early stop on holes)
- `II_max` comes from planner/static profile and observed valid instances, not from `0x01`.
- mark present slots based on group-specific heuristics

### Phase D: register scan

- scan selected groups/instances/ranges from planner
- for unknown groups, scanners may probe both `0x02` and `0x06` and keep best response

### Static fallback profile (when dynamic evidence is missing)

```text
GG   Opcode  InstanceMax  RegisterMax
0x02 0x02    0x0A         0x0025
0x03 0x02    0x0A         0x002F
0x09 0x06    0x0A         0x0030
0x0A 0x06    0x0A         0x003F
0x0C 0x06    0x0A         0x003F
```

---

## Sources & FLAGS Verification

- **BASV2 constraint catalog** (`b524_constraints.go`) — Downloaded from hardware via constraint probe. Authoritative for value ranges.
- **ebusd community TSP** (`15.ctlv2.tsp`) — Community register definitions. Highest authority for name mapping.
- **myVaillant register map CSV** (`myvaillant_register_map.csv`) — Helianthus-curated mapping by value-matching live B524 reads against myPyllant API fields. NOT a Vaillant-published source.
- **Gateway production code** (`semantic_vaillant.go`) — Authoritative for which registers are actively polled.
- **Live B524 scan** (2026-03-04) — MCP RPC reads from BASV2 via Helianthus gateway.
- **VRC Explorer full group scan** — Raw register data, FLAGS byte verification.

### FLAGS Corrections

Category corrections applied from VRC Explorer FLAGS analysis and MCP validation:

| Group | RR | Name | Old Cat | New Cat | FLAGS | Rationale |
|-------|-----|------|---------|---------|-------|-----------|
| 0x02 | 0x0017 | screed_drying_desired_temperature | C | S | 0x01 | Computed setpoint, read-only |
| 0x02 | 0x0018 | ext_hwc_active | C | S | 0x00 | Status register, not config |
| 0x02 | 0x0019 | external_heat_demand | C | S | 0x00 | External demand status |
| 0x02 | 0x001D | frost_protection_threshold | P | C | 0x02 | Technical config, writable |
| 0x03 | 0x000E | current_special_function | S | C | 0x03 | User-writable (set quickveto/away) |
| 0x03 | 0x0014 | heating_manual_mode_setpoint | C | S | 0x01 | Computed output, read-only |
| 0x03 | 0x0015 | cooling_manual_mode_setpoint | C | S | 0x01 | Computed output, read-only |
| 0x03 | 0x001E | quick_veto_end_time | S | C | 0x03 | Writable (extend/set veto) |
| 0x03 | 0x0024 | quick_veto_end_date | S | C | 0x03 | Writable (extend/set veto) |
| 0x00 | 0x0007 | system_off | S | C | 0x03 | User-writable on/off switch |

Wire type corrections from MCP validation (2026-03-05):

| Group | RR | Name | Old Wire | New Wire | Evidence |
|-------|-----|------|----------|----------|----------|
| 0x00 | 0x0007 | system_off | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x00 | 0x0014 | adaptive_heating_curve | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x00 | 0x0096 | maintenance_due | u16 | u8 | 1-byte response, FLAGS=0x01 |
| 0x01 | 0x000D | hwc_special_function_mode | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x03 | 0x000E | current_special_function | u16 | u8 | 1-byte response, FLAGS=0x03 |

### Related Files

- `_work_register_mapping/mypyllant_b524_system_mapping.json` — Original mapping analysis (historical)
- `_work_register_mapping/B524/` — Raw VRC Explorer scan data per group
- `helianthus-ebusreg/vaillant/system/b524_profile.go` — Discovery profiles
- `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/15.ctlv2.tsp` — ebusd TSP source
