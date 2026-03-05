# Vaillant B524 Extended Register Map

> **Status:** Authoritative reference. Single source of truth for B524 register semantics in Helianthus.
>
> **Last updated:** 2026-03-05 | **Device:** BASV2 (VRC720-compatible, HW 1704)

## Protocol Overview

B524 uses primary byte `0xB5`, secondary byte `0x24`. The wire frame for a read request is:

```
QQ ZZ PB SB NN 24 OC OT GG II RR_lo RR_hi
```

- `QQ` = source address (gateway uses `0x71`)
- `ZZ` = destination (`0x15` for BASV2)
- `PB` = `0xB5` (primary), `SB` = `0x24` (secondary)
- `NN` = payload length (6 for a read)
- `OC` = opcode: `0x02` (local) or `0x06` (remote)
- `OT` = operation type: `0x00` (read), `0x01` (write)
- `GG` = group, `II` = instance
- `RR` = register address (16-bit little-endian)

### Response Format

Responses do **not** echo the full request selector. The response payload format:

```
TT GG RR_lo RR_hi [VALUE_BYTES...]
```

- `TT` = reply kind byte (type marker)
- `GG` = group echo
- `RR` = register echo (16-bit LE)
- Value bytes: variable length depending on data type

The instance is **not** echoed in the response — the gateway correlates replies using the original request parameters. When the reply payload is a single `0x00` byte, the register exists but has no data (empty/unsupported).

### Data Type Encoding

| Type | Encoding | Size | Notes |
|------|----------|------|-------|
| `bool` | uint16 LE, `0` = false, `!0` = true | 2 bytes | Decoded from value bytes after header |
| `u8` | Single byte | 1 byte | |
| `u16` | Little-endian uint16 | 1-2 bytes | Single byte treated as u16 |
| `u32` | Little-endian uint32 | 4 bytes | Used for energy counters |
| `f32` | Little-endian IEEE 754 float32 | 4 bytes | Primary numeric type for temps, pressures |
| `string` | Null-terminated C string | Variable | Used for zone names, installer info |
| `date` | BCD-encoded | Variable | System date |
| `time` | HH:MM format | Variable | System time, legionella time |
| `energy4` | Unsigned 32-bit LE (kWh) | 4 bytes | Alias for u32, energy-specific |

### Opcode Routing

| Opcode | Name | Groups | Notes |
|--------|------|--------|-------|
| `0x02` | Local | 0x00-0x05, 0x0A | Controller-local registers |
| `0x06` | Remote | 0x09, 0x0C | Room sensor / remote device registers |

### Selector Subtypes (VRC Explorer Reference)

Beyond read/write, B524 supports additional selector types (documented in `helianthus-vrc-explorer`):

| Opcode | Name | Payload | Purpose |
|--------|------|---------|---------|
| `0x00` | Directory | `[0x00, GG, 0x00]` | Probe group existence (unreliable for GG=0x05) |
| `0x01` | Constraint | `[0x01, GG, RR_lo, RR_hi]` | Query value constraints for a register |
| `0x02` | Local read/write | `[0x02, OT, GG, II, RR_lo, RR_hi]` | Standard local register access |
| `0x03` | Timer (daily) | `[0x03, SEL1, SEL2, SEL3, weekday]` | Timer schedule access |
| `0x04` | Timer (weekly) | `[0x04, SEL1, SEL2, SEL3, weekday]` | Timer schedule access |
| `0x06` | Remote read/write | `[0x06, OT, GG, II, RR_lo, RR_hi]` | Remote register access |

---

## Group Topology

| GG | Name | Instanced | II Range | Opcode | Semantic Planes |
|----|------|-----------|----------|--------|-----------------|
| 0x00 | System/Regulator | No | 0x00 | 0x02 | system, energy_totals, boiler_status (partial) |
| 0x01 | DHW | No | 0x00 | 0x02 | dhw |
| 0x02 | Heating Circuits | Yes | 0x00-0x0A | 0x02 | circuits, boiler_status (partial) |
| 0x03 | Zones | Yes | 0x00-0x0A | 0x02 | zones |
| 0x04 | Solar Circuit | No | 0x00 | 0x02 | solar (gated) |
| 0x05 | Cylinders | Yes | 0x00-0x0A | 0x02 | cylinders (gated) |
| 0x09 | Room Sensors (regulator) | Yes | 0x00-0x0A | 0x06 | - |
| 0x0A | Room Sensors (VR92) | Yes | 0x00-0x0A | 0x06 | - |
| 0x0C | Unknown remote | Yes | 0x00-0x0A | 0x06 | - |

Room sensors use opcode `0x06` with instance `0x09` (regulator) or `0x0A` sub-instances `0x01-0x08` (VR92).

**Discovery:** Directory probe (`opcode=0x00`) is unreliable for GG=0x05 (terminator quirk). Use static topology. Multi-instance groups: scan all instances up to II=0x0A, expose only active ones.

### Discovery Profiles (ebusreg)

Source: `helianthus-ebusreg/vaillant/system/b524_profile.go`

| Group | Opcode | Instance Max | Register Max | Notes |
|-------|--------|-------------|-------------|-------|
| 0x02 | 0x02 (local) | 0x0A | 0x0021 | Heating circuits |
| 0x03 | 0x02 (local) | 0x0A | 0x002F | Zones |
| 0x09 | 0x06 (remote) | 0x0A | 0x002F | Room sensors (regulator) |
| 0x0A | 0x06 (remote) | 0x0A | 0x003F | Room sensors (VR92) |
| 0x0C | 0x06 (remote) | 0x0A | 0x003F | Unknown remote |

---

## Gate Conditions

Several registers are conditionally available based on system configuration:

| Gate Field | Source | Controls |
|-----------|--------|----------|
| `hwc_enabled` | GG=0x01, RR=0x0001 | DHW registers in GG=0x01, HWC-related config in GG=0x00 |
| `fm5_config` | GG=0x00, RR=0x002F | Solar registers (GG=0x04, GG=0x05), solar_flow_rate_quantity |
| `heating_circuit_type` | GG=0x02, RR=0x0002 | Per-circuit config (mixer vs fixed vs return) |
| `cooling_enabled` | GG=0x02, RR=0x0006 | Cooling-related config in circuits and zones |
| `room_temperature_control_mode` | GG=0x02, RR=0x0015 | Dew point monitoring/offset |
| `external_hot_water_cylinder_active` | GG=0x02, RR=0x0018 | External HWC temp/mode |

**Rule:** Gated-off registers are omitted from semantic plane responses. Explicit queries to gated-off registers return an error with gate status explanation.

---

## GG=0x00 — System/Regulator

All registers use opcode `0x02`, instance `0x00`.

### State

| RR | Leaf | Type | Unit | Semantic Field | Source |
|----|------|------|------|----------------|--------|
| 0x0007 | system_off | bool | - | `system.state.system_off` | mypyllant + TSP |
| 0x0034 | system_date | date | BCD | - | mypyllant + TSP |
| 0x0035 | system_time | time | HH:MM:SS | - | mypyllant + TSP |
| 0x0039 | system_water_pressure | f32 | bar | `system.state.system_water_pressure` | mypyllant + TSP |
| 0x004B | system_flow_temperature | f32 | °C | `system.state.system_flow_temperature`, `boiler_status.state.flow_temperature` | mypyllant + TSP |
| 0x0073 | outdoor_temperature | f32 | °C | `system.state.outdoor_temperature` | mypyllant + TSP |
| 0x0095 | outdoor_temperature_average24h | f32 | °C | `system.state.outdoor_temperature_avg24h` | mypyllant + TSP |
| 0x0096 | maintenance_due | bool | - | `system.state.maintenance_due` | TSP only |
| 0x009A | green_iq | bool | - | - | TSP only |
| 0x009D | hwc_cylinder_temperature_top | f32 | °C | `system.state.hwc_cylinder_temperature_top` | TSP only |
| 0x009E | hwc_cylinder_temperature_bottom | f32 | °C | `system.state.hwc_cylinder_temperature_bottom` | TSP only |
| 0x009F | hc_cylinder_temperature_top | f32 | °C | - | TSP only |
| 0x00A0 | hc_cylinder_temperature_bottom | f32 | °C | - | TSP only |

### Config

| RR | Leaf | Type | Unit | Constraints | Semantic Field | Gates | Source |
|----|------|------|------|-------------|----------------|-------|--------|
| 0x0001 | dhw_bivalence_point | f32 | °C | -20..50, step 1 | `system.config.dhw_bivalence_point` | - | mypyllant + TSP |
| 0x0002 | continuous_heating_start_setpoint | f32 | °C | -26..10 | - | - | mypyllant + TSP |
| 0x0003 | frost_override_time | u16 | hours | - | - | - | mypyllant + TSP |
| 0x0004 | maximum_preheating_time | u16 | min | - | - | - | mypyllant only |
| 0x0008 | temporary_allow_backup_heater | u8 | enum | - | - | - | mypyllant dump |
| 0x000E | max_room_humidity | u16 | % | - | `system.config.max_room_humidity` | - | mypyllant + TSP |
| 0x0014 | adaptive_heating_curve | bool | - | - | `system.config.adaptive_heating_curve` | - | mypyllant + TSP |
| 0x0015 | parallel_tank_loading_allowed | bool | - | - | - | - | mypyllant only |
| 0x0017 | dhw_maximum_loading_time | u16 | min | - | - | hwc_enabled | mypyllant + TSP |
| 0x0018 | hwc_lock_time | u16 | min | - | - | hwc_enabled | mypyllant + TSP |
| 0x0019 | solar_flow_rate_quantity | f32 | l/min | min 0 | - | fm5_config<=2 | TSP (see conflicts) |
| 0x001B | pump_additional_time | u16 | min | - | - | - | mypyllant + TSP |
| 0x001C | dhw_maximum_temperature | f32 | °C | - | - | - | mypyllant only |
| 0x0022 | alternative_point | f32 | °C | -21..40 | `system.config.alternative_point` | - | mypyllant + TSP |
| 0x0023 | heating_circuit_bivalence_point | f32 | °C | -20..30 | `system.config.heating_circuit_bivalence_point` | - | TSP (corrected) |
| 0x0024 | backup_heater_mode | u16 | enum | - | - | - | TSP (see conflicts) |
| 0x0026 | hc_emergency_temperature | f32 | °C | 20..80 | `system.config.hc_emergency_temperature` | - | TSP (corrected) |
| 0x0027 | dhw_hysteresis | f32 | K | 3..20, step 0.5 | - | hwc_enabled | mypyllant + TSP |
| 0x0029 | hwc_storage_charge_offset | f32 | K | 0..40 | - | hwc_enabled | TSP (corrected) |
| 0x002A | hwc_legionella_time | time | HH:MM | - | - | hwc_enabled | TSP |
| 0x002B | is_legionella_protection_activated | u16 | day enum | - | - | hwc_enabled | mypyllant + TSP |
| 0x002D | offset_outside_temperature | f32 | K | -3..3, step 0.5 | - | - | TSP |
| 0x0038 | cooling_outside_temperature_threshold | f32 | °C | 10..30 | - | - | TSP |
| 0x003A | dew_point_offset | f32 | K | -10..10 | - | - | TSP |
| 0x0045 | esco_block_function | u16 | enum | - | - | - | TSP |
| 0x0046 | hwc_max_flow_temp_desired | f32 | °C | 15..80 | `system.config.hwc_max_flow_temp_desired` | - | mypyllant + TSP |
| 0x00A2 | buffer_charge_offset | f32 | K | 0..15 | - | - | TSP |

### Energy Registers

| RR | Leaf | Type | Unit | Period | Semantic Field |
|----|------|------|------|--------|----------------|
| 0x004E | fuel_consumption_heating_this_month | energy4 | Wh | This month | - |
| 0x004F | energy_consumption_heating_this_month | energy4 | Wh | This month | - |
| 0x0050 | energy_consumption_dhw_this_month | energy4 | Wh | This month | - |
| 0x0051 | fuel_consumption_dhw_this_month | energy4 | Wh | This month | - |
| 0x0052 | fuel_consumption_heating_last_month | energy4 | Wh | Last month | - |
| 0x0053 | energy_consumption_heating_last_month | energy4 | Wh | Last month | - |
| 0x0054 | energy_consumption_dhw_last_month | energy4 | Wh | Last month | - |
| 0x0055 | fuel_consumption_dhw_last_month | energy4 | Wh | Last month | - |
| 0x0056 | fuel_consumption_heating_total | energy4 | Wh | Total | `energy_totals.gas.climate` |
| 0x0057 | energy_consumption_heating_total | energy4 | Wh | Total | `energy_totals.electric.climate` |
| 0x0058 | energy_consumption_dhw_total | energy4 | Wh | Total | `energy_totals.electric.dhw` |
| 0x0059 | fuel_consumption_dhw_total | energy4 | Wh | Total | `energy_totals.gas.dhw` |
| 0x003D | solar_yield_total | energy4 | Wh | Total (gated fm5_config<=2) | - |
| 0x003E | environmental_yield_total | energy4 | Wh | Total | - |

### Properties

| RR | Leaf | Type | Semantic Field | Source |
|----|------|------|----------------|--------|
| 0x0009 | external_energy_management_activation | bool | - | mypyllant |
| 0x002C | maintenance_date | date | - | mypyllant + TSP |
| 0x002F | module_configuration_vr71 | u16 (1..11) | `system.properties.module_configuration_vr71` | mypyllant + TSP |
| 0x0036 | system_scheme | u16 (1..16) | `system.properties.system_scheme` | mypyllant + TSP |
| 0x0081 | smart_photovoltaic_buffer_offset | f32 K | - | mypyllant only |
| 0x006C | installer_name_1 | string | - | TSP only |
| 0x006D | installer_name_2 | string | - | TSP only |
| 0x006F | installer_phone_1 | string | - | TSP only |
| 0x0070 | installer_phone_2 | string | - | TSP only |
| 0x0076 | installer_menu_code | u16 (0..999) | - | TSP only |

### Unknown/PV Cluster (not in TSP or myPyllant)

| RR | Type | Live Value | Notes |
|----|------|------------|-------|
| 0x000B | u16 | 0 | Near boolean cluster |
| 0x0011 | u16 | 16 | Possible temp threshold |
| 0x001E | u8 | 1 | Possible pump/flag |
| 0x0025 | u16 | 0 | Unknown |
| 0x0031 | u16 | 0 | Unknown |
| 0x0048 | u16 | 1 | Unknown |
| 0x0086 | u16 | 60 | PV/smart cluster |
| 0x0089 | u16 | 15 | PV/smart cluster |
| 0x008A | f32 | 1.0 | PV/smart cluster |
| 0x008B | f32 | 90.0 | PV/smart cluster, possible max flow temp |

---

## GG=0x01 — DHW

All registers use opcode `0x02`, instance `0x00`.

All registers except `hwc_status` (0x000F) are gated by `hwc_enabled` (0x0001).

| RR | Leaf | Type | Unit | Category | Semantic Field |
|----|------|------|------|----------|----------------|
| 0x0001 | hwc_enabled | bool | - | config | - (gate) |
| 0x0002 | hwc_circulation_pump_status | bool | - | state | - |
| 0x0003 | operation_mode_dhw | u16 | enum | config | `dhw.operating_mode` |
| 0x0004 | dhw_target_temperature | f32 | °C (35..70) | config | `dhw.desired_temperature` |
| 0x0005 | current_dhw_temperature | f32 | °C | state | `dhw.current_temperature` |
| 0x0006 | hwc_reheating_active | bool | - | state | - |
| 0x0008 | hwc_flow_temperature_desired | f32 | °C | state | - |
| 0x0009 | hwc_holiday_start_date | date | - | config | - |
| 0x000A | hwc_holiday_end_date | date | - | config | - |
| 0x000D | hwc_special_function_mode | u16 | enum | config | `dhw.state` (special function) |
| 0x000F | hwc_status | u16 | enum | state | - (not gated) |
| 0x0010 | hwc_holiday_start_time | time | - | config | - |
| 0x0011 | hwc_holiday_end_time | time | - | config | - |

---

## GG=0x02 — Heating Circuits (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active circuits discovered by probing `circuitRegType` (0x0002) — values `0xFF`/`0xFFFF` indicate inactive.

### State

| RR | Leaf | Type | Unit | Semantic Field | Notes |
|----|------|------|------|----------------|-------|
| 0x0007 | heating_circuit_flow_setpoint | f32 | °C | `circuits[].state.heating_circuit_flow_setpoint` | Target flow temp for this circuit |
| 0x0008 | current_circuit_flow_temperature | f32 | °C | `circuits[].state.current_circuit_flow_temperature`, `boiler_status.state.return_temperature` (II=0) | Per-circuit measured flow temp |
| 0x001B | circuit_state | u16 | enum | `circuits[].state.circuit_state` | Raw state code |
| 0x001E | pump_status | u16 | 0/1 | `circuits[].state.pump_status` (bool), `boiler_status.state.pump_running` (II=0) | 0=off, !0=on |
| 0x0020 | calculated_flow_temperature | f32 | °C | `circuits[].state.calculated_flow_temperature` | Algorithm-computed target |
| 0x0021 | mixer_position_percentage | f32 | % | `circuits[].state.mixer_position_percentage` | Mixer valve position |
| 0x0022 | current_room_humidity | f32 | % | `circuits[].state.current_room_humidity` | From associated room sensor |
| 0x0023 | dew_point_temperature | f32 | °C | `circuits[].state.dew_point_temperature` | Calculated dew point |
| 0x0024 | pump_operating_hours | u32 | hours | `circuits[].state.pump_operating_hours` | Cumulative pump runtime |
| 0x0025 | pump_starts_count | u32 | count | `circuits[].state.pump_starts_count` | Cumulative pump starts |

### Config

| RR | Leaf | Type | Unit | Constraints | Semantic Field | Gates |
|----|------|------|------|-------------|----------------|-------|
| 0x0002 | heating_circuit_type | u16 | enum | 1..2 | `circuits[].properties.heating_circuit_type` | Controls per-circuit behavior |
| 0x0006 | cooling_enabled | u16 | 0/1 | 0..1 | `circuits[].config.cooling_enabled` (bool) | Gates cooling registers |
| 0x000F | heating_curve | f32 | - | - | `circuits[].config.heating_curve` | Heating curve slope |
| 0x0010 | heating_flow_temperature_maximum_setpoint | f32 | °C | 15..80 | `circuits[].config.heating_flow_temperature_maximum_setpoint` | |
| 0x0012 | heating_flow_temperature_minimum_setpoint | f32 | °C | - | `circuits[].config.heating_flow_temperature_minimum_setpoint` | |
| 0x0014 | heat_demand_limited_by_outside_temp | f32 | °C | - | `circuits[].config.heat_demand_limited_by_outside_temp` | Summer cutoff threshold |
| 0x0015 | room_temperature_control_mode | u16 | enum | - | `circuits[].config.room_temperature_control_mode` | Gates dew point registers |
| 0x001D | frost_protection_threshold | f32 | °C | - | `circuits[].properties.frost_protection_threshold` | |

### Additional Config (gate-dependent)

| RR | Leaf | Type | Gates | Notes |
|----|------|------|-------|-------|
| 0x0003 | set_back_mode_enabled | u16 | circuit_type=1 (mixer) | |
| 0x0004 | desired_temperature (fixed) | f32 | circuit_type=2 (fixed) | |
| 0x0005 | fixed_setback_temperature | f32 | circuit_type=2 (fixed) | |
| 0x0009 | excess_offset | f32 | circuit_type=1 (mixer) | |
| 0x0011 | desired_return_temperature_setpoint | f32 | circuit_type=4 (return) | |
| 0x0016 | dew_point_monitoring | u16 | cooling_enabled=1 | |
| 0x0017 | dew_point_offset | f32 | cooling_enabled=1 | |
| 0x0018 | external_hot_water_cylinder_active | u16 | - | Gates ext HWC registers |
| 0x0019 | cooling_flow_desired | f32 | cooling_enabled=1 | |
| 0x001A | cooling_flow_min | f32 | cooling_enabled=1 | |

### Properties

| RR | Leaf | Type | Semantic Field |
|----|------|------|----------------|
| 0x0002 | heating_circuit_type | u16 | `circuits[].properties.heating_circuit_type` |
| 0x0002 | mixer_circuit_type_external | u16 | `circuits[].properties.mixer_circuit_type_external` (same register, re-read) |

---

## GG=0x03 — Zones (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones discovered by probing `zone_index` (0x001C).

### State

| RR | Leaf | Type | Unit | Semantic Field | Notes |
|----|------|------|------|----------------|-------|
| 0x000E | current_special_function | u16 | enum | `zones[].state.operating_mode` (derived) | Quick veto / holiday / etc. |
| 0x000F | current_room_temperature | f32 | °C | `zones[].state.current_temperature` | From room sensor |
| 0x0012 | valve_status | u16 | enum | - (used for hvac_action derivation) | |
| 0x0028 | current_room_humidity | f32 | % | `zones[].state.current_room_humidity` | From room sensor |

### Config

| RR | Leaf | Type | Unit | Constraints | Semantic Field |
|----|------|------|------|-------------|----------------|
| 0x0006 | heating_operation_mode | u16 | enum | 0..2 | `zones[].state.operating_mode` (derived) |
| 0x0013 | associated_circuit_index | u16 | index | - | - (internal, used to look up circuit type) |
| 0x0014 | manual_mode_setpoint | f32 | °C | - | `zones[].state.desired_temperature` (fallback) |
| 0x0016 | zone_name | string | - | - | `zones[].name` |
| 0x0017 | zone_name_prefix | string | - | - | - (used in name assembly) |
| 0x0018 | zone_name_suffix | string | - | - | - (used in name assembly) |
| 0x001C | zone_index | bytes | - | - | - (presence marker for discovery) |
| 0x0022 | desired_setpoint | f32 | °C | 15..30, step 0.5 | `zones[].state.desired_temperature` (primary) |

### Zone Mode Derivation

The `operating_mode` and `preset` exposed in the zones semantic plane are derived from a combination of:
- `heating_operation_mode` (0x0006): 0=off, 1=manual, 2=auto
- `current_special_function` (0x000E): 0=none, 1=bank_holiday, 2=quick_veto, etc.
- Associated circuit's `heating_circuit_type` (GG=0x02, 0x0002)

### Additional Zone Registers (gate-dependent)

| RR | Leaf | Type | Gates | Notes |
|----|------|------|-------|-------|
| 0x0001 | operation_mode_zone | u16 | - | Raw operation mode (0..2) |
| 0x0002 | room_desired_temp | f32 | - | Target temp (constraint 15..30, step 0.5) |
| 0x0005 | active_special_function | u16 | - | Special function target temp (5..30) |
| 0x000D | quick_veto_setpoint | f32 | - | Veto override temp |
| 0x0010 | quick_veto_remaining | u16 | - | Minutes remaining |

---

## GG=0x04 — Solar Circuit

Entire group gated by `fm5_config <= 2`. All registers use opcode `0x02`, instance `0x00`.

| RR | Leaf | Type | Gates | Notes |
|----|------|------|-------|-------|
| 0x0001 | solar_enabled | u8 | - | 0/1 |
| 0x0002 | solar_pump_status | u8 | - | 0/1 |
| 0x0003 | collector_temperature | f32 | - | °C |
| 0x0004 | solar_storage_temperature | f32 | - | °C |
| 0x0005 | max_collector_temperature | f32 | - | Constraint 110..150 |
| 0x0006 | collector_shutdown_temperature | f32 | - | Constraint 75..115 |

---

## GG=0x05 — Cylinders (multi-instance)

Entire group gated by `fm5_config <= 2`. These are solar charging parameters per cylinder (TSP: "Solar Cylinder"). General cylinder config (max temp, charge hysteresis) is in GG=0x00 system config.

| RR | Leaf | Type | Gates | Notes |
|----|------|------|-------|-------|
| 0x0001 | cylinder_temperature | f32 | - | °C |
| 0x0002 | charge_hysteresis | f32 | - | Constraint 2..25 |
| 0x0003 | charge_duration_max | f32 | - | Constraint 1..20 |
| 0x0004 | charge_setpoint | f32 | - | Constraint -10..110 |

---

## Semantic Plane Mapping

This section maps B524 registers to Helianthus MCP semantic plane fields. Only registers actively read by the gateway's semantic poller are listed.

### `ebus.v1.semantic.system.get`

Source: `refreshSystem()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `state.system_off` | GG=0x00, RR=0x0007 | bool |
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

### `ebus.v1.semantic.circuits.get`

Source: `refreshCircuits()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].state.heating_circuit_flow_setpoint` | GG=0x02, RR=0x0007 | f32 |
| `[].state.current_circuit_flow_temperature` | GG=0x02, RR=0x0008 | f32 |
| `[].state.circuit_state` | GG=0x02, RR=0x001B | u16 |
| `[].state.pump_status` | GG=0x02, RR=0x001E | bool (u16) |
| `[].state.calculated_flow_temperature` | GG=0x02, RR=0x0020 | f32 |
| `[].state.mixer_position_percentage` | GG=0x02, RR=0x0021 | f32 |
| `[].state.current_room_humidity` | GG=0x02, RR=0x0022 | f32 |
| `[].state.dew_point_temperature` | GG=0x02, RR=0x0023 | f32 |
| `[].state.pump_operating_hours` | GG=0x02, RR=0x0024 | u32 |
| `[].state.pump_starts_count` | GG=0x02, RR=0x0025 | u32 |
| `[].config.heating_curve` | GG=0x02, RR=0x000F | f32 |
| `[].config.heating_flow_temperature_maximum_setpoint` | GG=0x02, RR=0x0010 | f32 |
| `[].config.heating_flow_temperature_minimum_setpoint` | GG=0x02, RR=0x0012 | f32 |
| `[].config.heat_demand_limited_by_outside_temp` | GG=0x02, RR=0x0014 | f32 |
| `[].config.room_temperature_control_mode` | GG=0x02, RR=0x0015 | u16 |
| `[].config.cooling_enabled` | GG=0x02, RR=0x0006 | bool (u16) |
| `[].properties.heating_circuit_type` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.mixer_circuit_type_external` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.frost_protection_threshold` | GG=0x02, RR=0x001D | f32 |

### `ebus.v1.semantic.zones.get`

Source: `refreshState()` / `refreshDiscovery()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].name` | GG=0x03, RR=0x0016 | string |
| `[].state.operating_mode` | derived from GG=0x03 RR=0x0006 + 0x000E | - |
| `[].state.current_temperature` | GG=0x03, RR=0x000F | f32 |
| `[].state.desired_temperature` | GG=0x03, RR=0x0022 (primary), 0x0014 (fallback) | f32 |
| `[].state.current_room_humidity` | GG=0x03, RR=0x0028 | f32 |

### `ebus.v1.semantic.dhw.get`

Source: `refreshDHW()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `operating_mode` | GG=0x01, RR=0x0003 | u16 (derived) |
| `current_temperature` | GG=0x01, RR=0x0005 | f32 |
| `desired_temperature` | GG=0x01, RR=0x0004 | f32 |
| `state` | GG=0x01, RR=0x000D | u16 (special function) |

### `ebus.v1.semantic.boiler_status.get`

Source: `refreshBoilerStatus()` in `semantic_vaillant.go`

The boiler status plane is a **cross-group composite** — it reads from both GG=0x00 (regulator) and GG=0x02 (heating circuit 0). The BAI boiler does not respond to direct B504 reads from third-party sources — only from its paired controller. The controller mirrors boiler data in its own B524 register space.

| Semantic Path | B524 | Type | Notes |
|---------------|------|------|-------|
| `state.flow_temperature` | GG=0x00, RR=0x004B | f32 | System flow temp from regulator |
| `state.return_temperature` | GG=0x02, II=0x00, RR=0x0008 | f32 | Circuit 0 flow temp as return proxy |
| `state.pump_running` | GG=0x02, II=0x00, RR=0x001E | bool | Circuit 0 pump status |
| `state.circuit_state` (raw) | GG=0x02, II=0x00, RR=0x001B | u16 | Circuit 0 state |

Note: `dhw_storage_temperature`, `dhw_outlet_temperature`, `flame_on`, `current_power_percent`, `starts_count`, `operating_hours`, `dhw_operating_hours` are not populated from B524 — these would require direct BAI access (B504) which is not available from third-party sources.

### `ebus.v1.semantic.energy_totals.get`

Source: `refreshEnergy()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `gas.climate` | GG=0x00, RR=0x0056 | energy4 (u32 LE, kWh) |
| `electric.climate` | GG=0x00, RR=0x0057 | energy4 |
| `electric.dhw` | GG=0x00, RR=0x0058 | energy4 |
| `gas.dhw` | GG=0x00, RR=0x0059 | energy4 |

---

## Constraint Catalog (ebusreg)

Source: `helianthus-ebusreg/vaillant/system/b524_constraints.go`

The constraint catalog uses a `(Group, Record)` selector where `Record` is a **TSP-style** register address (byte-swapped from RR). These are used for constraint-probe responses, not standard read addressing.

| Group | Record | Type | Min | Max | Step |
|-------|--------|------|-----|-----|------|
| 0x00 | 0x0100 | f32_range | -20 | 50 | 1 |
| 0x00 | 0x0200 | f32_range | -26 | 10 | 1 |
| 0x00 | 0x0300 | u16_range | 0 | 12 | 1 |
| 0x00 | 0x0400 | u16_range | 0 | 300 | 10 |
| 0x00 | 0x8000 | f32_range | -10 | 10 | 1 |
| 0x01 | 0x0100 | u16_range | 0 | 1 | 1 |
| 0x01 | 0x0200 | u8_range | 0 | 1 | 1 |
| 0x01 | 0x0300 | u16_range | 0 | 2 | 1 |
| 0x01 | 0x0400 | f32_range | 35 | 70 | 1 |
| 0x01 | 0x0500 | f32_range | 0 | 99 | 1 |
| 0x01 | 0x0600 | u8_range | 0 | 1 | 1 |
| 0x02 | 0x0100 | u16_range | 1 | 2 | 1 |
| 0x02 | 0x0200 | u16_range | 0 | 4 | 1 |
| 0x02 | 0x0400 | f32_range | 15 | 80 | 1 |
| 0x02 | 0x0500 | u8_range | 0 | 1 | 1 |
| 0x02 | 0x0600 | u8_range | 0 | 1 | 1 |
| 0x03 | 0x0100 | u16_range | 0 | 2 | 1 |
| 0x03 | 0x0200 | f32_range | 15 | 30 | 0.5 |
| 0x03 | 0x0500 | f32_range | 5 | 30 | 1 |
| 0x03 | 0x0600 | u16_range | 0 | 2 | 1 |
| 0x04 | 0x0100 | u8_range | 0 | 1 | 1 |
| 0x04 | 0x0200 | u8_range | 0 | 1 | 1 |
| 0x04 | 0x0300 | f32_range | -40 | 155 | 1 |
| 0x04 | 0x0400 | f32_range | 0 | 99 | 1 |
| 0x04 | 0x0500 | f32_range | 110 | 150 | 1 |
| 0x04 | 0x0600 | f32_range | 75 | 115 | 1 |
| 0x05 | 0x0100 | f32_range | 0 | 99 | 1 |
| 0x05 | 0x0200 | f32_range | 2 | 25 | 1 |
| 0x05 | 0x0300 | f32_range | 1 | 20 | 1 |
| 0x05 | 0x0400 | f32_range | -10 | 110 | 1 |
| 0x08 | 0x0100 | f32_range | 0 | 99 | 1 |
| 0x08 | 0x0200 | f32_range | 0 | 99 | 1 |
| 0x08 | 0x0300 | f32_range | 2 | 25 | 1 |
| 0x08 | 0x0400 | f32_range | 1 | 20 | 1 |
| 0x08 | 0x0500 | f32_range | -10 | 110 | 1 |
| 0x08 | 0x0600 | f32_range | -10 | 110 | 1 |
| 0x09 | 0x0100 | u16_range | 0 | 255 | 1 |
| 0x09 | 0x0200 | u16_range | 1 | 3 | 1 |
| 0x09 | 0x0300 | u8_range | 0 | 1 | 1 |
| 0x09 | 0x0400 | u16_range | 0 | 10 | 1 |
| 0x09 | 0x0500 | u16_range | 0 | 32768 | 1 |
| 0x09 | 0x0600 | u16_range | 0 | 32768 | 1 |
| 0x0A | 0x0100 | u8_range | 0 | 3 | 1 |
| 0x0A | 0x0200 | u8_range | 1 | 2 | 1 |
| 0x0A | 0x0300 | u8_range | 1 | 2 | 1 |
| 0x0A | 0x0500 | u8_range | 0 | 3 | 1 |
| 0x0A | 0x0600 | u8_range | 0 | 1 | 1 |

**Note:** TSP-style registers (`0x0100+`) are listed in the constraint catalog but are NOT accessible via standard B524 read operations — only standard registers (`0x0001-0x00FF`) work through gateway RPC.

---

## Mapping Conflicts

Three register mappings from the original myPyllant value-matching had errors, resolved using TSP:

| RR | myPyllant CSV leaf | TSP name | Resolution |
|----|-------------------|----------|------------|
| 0x0019 | heating_circuit_bivalence_point | SolarFlowRateQuantity | Coincidental 0.0 match (solar disabled). Real HcBivalencePoint at 0x0023. |
| 0x0026 | dhw_flow_setpoint_offset | HcEmergencyTemperature | 25.0 fits both semantics, TSP authoritative. |
| 0x0029 | max_flow_setpoint_hp_error | HwcStorageChargeOffset | 25.0 fits range, TSP authoritative. |

One conflict is still pending:

| RR | myPyllant CSV leaf | TSP name | Status |
|----|-------------------|----------|--------|
| 0x0024 | hybrid_control_strategy (BIVALENCE_POINT) | BackupBoiler | Pending. TSP puts HybridManager at 0x000F. |

---

## Sources

- **myVaillant register map CSV** (`helianthus-vrc-explorer/data/myvaillant_register_map.csv`) — Vaillant's official register-to-leaf mapping from cloud API analysis
- **burmistrzak ebusd TSP** (`15.720.tsp`) — Community ebusd TypeSpec definitions with gate conditions and constraints
- **Live B524 scan** (2026-03-04) — MCP RPC reads from BASV2 via Helianthus gateway, 81 registers in GG=0x00
- **myPyllant system dump** (2026-03-04T17:43Z) — Cloud API snapshot for value cross-reference
- **Gateway production code** (`helianthus-ebusgateway/cmd/gateway/semantic_vaillant.go`) — Authoritative for which registers are actively polled and how they map to semantic planes
- **Registry constraint catalog** (`helianthus-ebusreg/vaillant/system/b524_constraints.go`) — Static constraint ranges per (group, register)
- **Discovery profiles** (`helianthus-ebusreg/vaillant/system/b524_profile.go`) — Instance/register ranges for group scanning
- **VRC Explorer protocol** (`helianthus-vrc-explorer/src/helianthus_vrc_explorer/protocol/b524.py`) — Selector types, payload builders, value parsers

## Related Files

- `_work_register_mapping/b524_register_catalog.json` — Complete machine-readable catalog
- `_work_register_mapping/b524_semantic_planes.json` — Semantic plane design for MCP API
- `_work_register_mapping/mypyllant_b524_system_mapping.json` — Original mapping analysis (historical)
- `_work_register_mapping/15.720.tsp` — Downloaded TSP source
