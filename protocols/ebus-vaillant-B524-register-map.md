# Vaillant B524 Extended Register Map

> **Status:** Authoritative reference. Single source of truth for B524 register semantics in Helianthus.
>
> **Last updated:** 2026-03-05 (full reconciliation) | **Device:** BASV2 (VRC720-compatible, HW 1704)

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
| 0x08 | Unknown (constraint-only) | Yes | - | 0x02 | - |
| 0x0C | Unknown remote | Yes | 0x00-0x0F | 0x06 | - |

Group 0x08 has 6 constraint entries in `b524_constraints.go` (similar structure to GG=0x05 cylinders) but no responsive registers observed in VRC Explorer scans. Discovery probe returned 0 pages. Possibly a second cylinder bank or buffer tank group on systems with FM5 module.

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
| 0x000A | parallel_tank_loading_allowed | bool | - | - | - | - | ebusd TSP (HwcParallelLoading @ext(0xa,0)) |
| 0x000E | max_room_humidity | u16 | % | - | `system.config.max_room_humidity` | - | mypyllant + TSP |
| 0x0012 | continuous_heating_room_setpoint | u16 | °C | - | - | - | mypyllant (confirmed exact, value=20) |
| 0x0014 | adaptive_heating_curve | bool | - | - | `system.config.adaptive_heating_curve` | - | mypyllant + TSP |
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

### Unknown/Scan-Only (not in CSV or TSP)

Registers that responded to live B524 scans but have no confirmed name from myVaillant CSV or ebusd TSP. The GG=0x00 scan found 81+ responsive registers; most named ones are listed above. These remain unidentified:

| RR | Type | Live Value | Notes |
|----|------|------------|-------|
| 0x000B | u16 | 0 | Near boolean cluster |
| 0x000F | u16 | - | Possibly HybridManager (TSP places it here; see conflicts) |
| 0x0010 | u16 | - | Near config cluster |
| 0x0011 | u16 | 16 | Possible temp threshold |
| 0x0015 | bool | 0 | CSV had this as parallel_tank_loading — ebusd places that at 0x000A instead. Value-matching false positive. |
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

All registers use opcode `0x02`. Instances 0x00-0x0A; active circuits discovered by probing `heating_circuit_type` (0x0002) — values `0xFF`/`0xFFFF` indicate inactive.

> **Reconciliation note (2026-03-05):** Previous version had 8 address mismatches in the Additional Config section (wrong register↔name pairs). This version cross-references three sources: ebusd community TSP (`15.ctlv2.tsp`) confirms 14 of 35 registers independently; the CSV provides value-matched names for the remainder. Registers confirmed only by CSV are marked with `†` — these carry false-positive risk from value-matching.

### Complete Register Map

Source: ebusd community TSP + `helianthus-vrc-explorer/data/myvaillant_register_map.csv`, cross-referenced with gateway production code.

Legend: **S** = actively polled by semantic layer | ebusd name in parentheses.

| RR | Leaf | ebusd Name | Type | Category | Semantic Field | Notes |
|----|------|------------|------|----------|----------------|-------|
| 0x0001 | unknown † | - | u16 | - | - | CSV says heating_circuit_type, but gateway uses 0x0002. Catalog constraint 1..2 (Record 0x0100). Purpose unverified. |
| 0x0002 | heating_circuit_type | Hc{hc}CircuitType | u16 | properties | `circuits[].properties.heating_circuit_type`, `mixer_circuit_type_external` | **S** ebusd + gateway confirmed. Discovery probe; 1=mixer, 2=fixed. Catalog constraint 0..4 (Record 0x0200). |
| 0x0003 | room_influence_type † | Hc{hc}RoomInfluenceType | u16 | config | - | CSV only, no ebusd entry |
| 0x0004 | desired_return_temperature_setpoint † | Hc{hc}ReturnTempDesired | f32 | config | - | CSV only; ebusd: "Unknown04, constant 30°C". Catalog constraint 15..80 (Record 0x0400) |
| 0x0005 | dew_point_monitoring_enabled † | Hc{hc}DewPointMonitoring | u16 | config | - | CSV only, no ebusd entry. Gates: cooling_enabled. Catalog constraint 0..1 (Record 0x0500) |
| 0x0006 | cooling_enabled | Hc{hc}CoolingEnabled | u16 | config | `circuits[].config.cooling_enabled` | **S** Gate for cooling registers. Catalog constraint 0..1 (Record 0x0600) |
| 0x0007 | heating_circuit_flow_setpoint | Hc{hc}FlowTempDesired | f32 | state | `circuits[].state.heating_circuit_flow_setpoint` | **S** |
| 0x0008 | current_circuit_flow_temperature | Hc{hc}FlowTemp | f32 | state | `circuits[].state.current_circuit_flow_temperature` | **S** Also `boiler_status.state.return_temperature` (II=0) |
| 0x0009 | ext_hwc_temperature_setpoint † | Hc{hc}ExternalHWCTempDesired | f32 | config | - | CSV only; ebusd: "Unknown09, constant 60°C". Gates: ext_hwc_active |
| 0x000A | dew_point_offset † | Hc{hc}DewPointOffset | f32 | config | - | CSV only, no ebusd entry. Gates: cooling_enabled |
| 0x000B | flow_setpoint_excess_offset | Hc{hc}ExcessTemp | f32 | config | - | Mixer circuit excess. Gates: circuit_type=1 (mixer) |
| 0x000C | fixed_desired_temperature † | Hc{hc}FixedDesiredTemp | f32 | config | - | CSV only; ebusd: "Unknown0c, constant 65°C". Gates: circuit_type=2 (fixed) |
| 0x000D | fixed_setback_temperature † | Hc{hc}SetbackModeTemp | f32 | config | - | CSV only; ebusd: "Unknown0d, constant 65°C". Gates: circuit_type=2 (fixed) |
| 0x000E | set_back_mode_enabled | Hc{hc}SetbackMode | u16 | config | - | Gates: circuit_type=1 (mixer) |
| 0x000F | heating_curve | Hc{hc}HeatCurve | f32 | config | `circuits[].config.heating_curve` | **S** |
| 0x0010 | heating_flow_temp_max_setpoint | Hc{hc}HeatingFlowTempMax | f32 | config | `circuits[].config.heating_flow_temperature_maximum_setpoint` | **S** Constraint 15..80 (ebusd empirical) |
| 0x0011 | cooling_flow_temp_min_setpoint | Hc{hc}CoolingFlowTempMin | f32 | config | - | Gates: cooling_enabled |
| 0x0012 | heating_flow_temp_min_setpoint | Hc{hc}HeatingFlowTempMin | f32 | config | `circuits[].config.heating_flow_temperature_minimum_setpoint` | **S** |
| 0x0013 | ext_hwc_operation_mode | Hc{hc}ExternalHWCOpMode | u16 | config | - | Gates: ext_hwc_active |
| 0x0014 | heat_demand_limited_by_outside_temp | Hc{hc}SummerTempLimit | f32 | config | `circuits[].config.heat_demand_limited_by_outside_temp` | **S** Summer cutoff |
| 0x0015 | room_temperature_control_mode | Hc{hc}RoomTempModulation | u16 | config | `circuits[].config.room_temperature_control_mode` | **S** Gates dew point |
| 0x0016 | screed_drying_day | Hc{hc}ScreedDryingDay | u16 | config | - | Screed drying program |
| 0x0017 | screed_drying_desired_temperature | Hc{hc}ScreedDryingTempDesired | f32 | config | - | Screed drying program |
| 0x0018 | ext_hwc_active | Hc{hc}ExternalHWCActive | u16 | config | - | Gate for ext HWC registers |
| 0x0019 | external_heat_demand | Hc{hc}ExternalHeatDemand | u16 | config | - | External heat source |
| 0x001A | mixer_movement | Hc{hc}MixerMovement | u16 | state | - | Mixer motor activity |
| 0x001B | circuit_state | Hc{hc}Status | u16 | state | `circuits[].state.circuit_state` | **S** Raw state code |
| 0x001C | epsilon | Hc{hc}HeatCurveAdaption | f32 | config | - | Heat curve adaption factor |
| 0x001D | frost_protection_threshold | Hc{hc}FrostProtThreshold | f32 | properties | `circuits[].properties.frost_protection_threshold` | **S** |
| 0x001E | pump_status | Hc{hc}PumpStatus | u16 | state | `circuits[].state.pump_status` | **S** Also `boiler_status.state.pump_running` (II=0) |
| 0x001F | room_temperature_setpoint | Hc{hc}RoomSetpoint | f32 | config | - | |
| 0x0020 | calculated_flow_temperature | Hc{hc}FlowTempCalc | f32 | state | `circuits[].state.calculated_flow_temperature` | **S** |
| 0x0021 | mixer_position_percentage | Hc{hc}MixerPosition | f32 | state | `circuits[].state.mixer_position_percentage` | **S** |
| 0x0022 | current_room_humidity | Hc{hc}Humidity | f32 | state | `circuits[].state.current_room_humidity` | **S** From room sensor |
| 0x0023 | dew_point_temperature | Hc{hc}DewPointTemp | f32 | state | `circuits[].state.dew_point_temperature` | **S** |
| 0x0024 | pump_operating_hours | Hc{hc}PumpHours | u32 | state | `circuits[].state.pump_operating_hours` | **S** |
| 0x0025 | pump_starts_count | Hc{hc}PumpStarts | u32 | state | `circuits[].state.pump_starts_count` | **S** |

> **Discovery profile discrepancy:** `b524_profile.go` sets RegisterMax=0x0021 for GG=0x02, but registers 0x0022-0x0025 are confirmed active and polled by the gateway. The profile should be updated to RegisterMax=0x0025.

---

## GG=0x03 — Zones (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones discovered by probing `zone_index` (0x001C).

> **Reconciliation note (2026-03-05):** Previous version had wrong names for 0x0001, 0x0002, 0x0005 and was missing 16 registers. This version cross-references ebusd community TSP (all registers confirmed independently) and the myVaillant CSV for leaf names.

### Complete Register Map

Legend: **S** = actively polled by semantic layer | ebusd name in parentheses.

| RR | Leaf | ebusd Name | Type | Category | Semantic Field | Notes |
|----|------|------------|------|----------|----------------|-------|
| 0x0001 | cooling_operation_mode | Zone{z}CoolingOpMode | u16 | config | - | Gates: cooling_enabled. Catalog constraint 0..2 (Record 0x0100) |
| 0x0002 | cooling_set_back_temperature | Zone{z}CoolingSetbackTemp | f32 | config | - | Catalog constraint 15..30, step 0.5 (Record 0x0200). Gates: cooling_enabled |
| 0x0003 | holiday_start_date | Zone{z}HolidayStartPeriod | date | config | - | |
| 0x0004 | holiday_end_date | Zone{z}HolidayEndPeriod | date | config | - | |
| 0x0005 | holiday_setpoint | Zone{z}HolidayTemp | f32 | config | - | Catalog constraint 5..30 (Record 0x0500) |
| 0x0006 | heating_operation_mode | Zone{z}HeatingOpMode | u16 | config | (derived) `zones[].state.operating_mode` | **S** 0=off, 1=manual, 2=auto. Catalog constraint 0..2 (Record 0x0600) |
| 0x0008 | quick_veto_temperature | Zone{z}QuickVetoTemp | f32 | config | - | Veto override target |
| 0x0009 | heating_set_back_temperature | Zone{z}HeatingSetbackTemp | f32 | config | - | Setback/night temp |
| 0x000C | bank_holiday_start | Zone{z}BankHolidayStartDate | date | config | - | ebusd TSP confirmed |
| 0x000D | bank_holiday_end | Zone{z}BankHolidayEndDate | date | config | - | ebusd TSP confirmed |
| 0x000E | current_special_function | Zone{z}SpecialFunction | u16 | state | (derived) `zones[].state.operating_mode` | **S** 0=none, 1=holiday, 2=quick_veto |
| 0x000F | current_room_temperature | Zone{z}RoomTemp | f32 | state | `zones[].state.current_temperature` | **S** From room sensor |
| 0x0012 | valve_status | Zone{z}ValveStatus | u16 | state | - | Used for hvac_action derivation |
| 0x0013 | associated_circuit_index | Zone{z}AssociatedCircuitIndex | u16 | config | - | **S** Internal: look up circuit type |
| 0x0014 | heating_manual_mode_setpoint | Zone{z}HeatingManualSetpoint | f32 | config | `zones[].state.desired_temperature` (fallback) | **S** |
| 0x0015 | cooling_manual_mode_setpoint | Zone{z}CoolingManualSetpoint | f32 | config | - | Gates: cooling_enabled |
| 0x0016 | zone_name | Zone{z}Name | string | config | `zones[].name` | **S** |
| 0x0017 | zone_name_prefix | Zone{z}NamePrefix | string | config | - | Used in name assembly |
| 0x0018 | zone_name_suffix | Zone{z}NameSuffix | string | config | - | Used in name assembly |
| 0x0019 | heating_time_slot_active | Zone{z}HeatingTimeSlotActive | u16 | state | - | Timer schedule flag |
| 0x001A | cooling_time_slot_active | Zone{z}CoolingTimeSlotActive | u16 | state | - | Timer schedule flag. Gates: cooling_enabled |
| 0x001B | zone_status | Zone{z}Status | u16 | state | - | Raw zone status code |
| 0x001C | zone_index | Zone{z}Index | bytes | config | - | **S** Presence marker for discovery |
| 0x001E | quick_veto_end_time | Zone{z}QuickVetoEndTime | time | config | - | When active veto expires |
| 0x0020 | holiday_end_time | Zone{z}HolidayEndTime | time | config | - | |
| 0x0021 | holiday_start_time | Zone{z}HolidayStartTime | time | config | - | |
| 0x0022 | heating_desired_setpoint | Zone{z}RoomTempDesired | f32 | config | `zones[].state.desired_temperature` (primary) | **S** Constraint 15..30, step 0.5 (ebusd empirical) |
| 0x0023 | cooling_desired_setpoint | Zone{z}CoolingDesiredSetpoint | f32 | config | - | Gates: cooling_enabled |
| 0x0024 | quick_veto_end_date | Zone{z}QuickVetoEndDate | date | config | - | |
| 0x0026 | quick_veto_duration | Zone{z}QuickVetoDuration | u16 | config | - | Minutes |
| 0x0028 | current_room_humidity | Zone{z}Humid | f32 | state | `zones[].state.current_room_humidity` | **S** From room sensor |

### Zone Mode Derivation

The `operating_mode` and `preset` exposed in the zones semantic plane are derived from a combination of:
- `heating_operation_mode` (0x0006): 0=off, 1=manual, 2=auto
- `current_special_function` (0x000E): 0=none, 1=bank_holiday, 2=quick_veto, etc.
- Associated circuit's `heating_circuit_type` (GG=0x02, 0x0002)

---

## GG=0x04 — Solar Circuit

Entire group gated by `fm5_config <= 2`. All registers use opcode `0x02`, instance `0x00`.

> **Reconciliation note (2026-03-05):** Previous version had wrong names for 0x0002, 0x0004, 0x0006 and was missing 4 registers. This version uses the CSV. **No ebusd coverage exists for GG=0x04** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Leaf | ebusd Name | Type | Category | Notes |
|----|------|------------|------|----------|-------|
| 0x0001 | solar_enabled | SolarEnabled | u8 | config | 0/1 |
| 0x0002 | solar_function_mode | SolarFunctionMode | u8 | config | 0/1 (not pump status — pump is at 0x0008) |
| 0x0003 | collector_temperature | SolarCollectorTemp | f32 | state | °C. Constraint -40..155 |
| 0x0004 | delta_t_on_threshold | SolarDeltaTOn | f32 | config | °C. Constraint 0..99 (not storage temp) |
| 0x0005 | max_collector_temperature | SolarMaxCollectorTemp | f32 | config | Constraint 110..150 |
| 0x0006 | max_cylinder_temperature_solar | SolarMaxCylinderTemp | f32 | config | Constraint 75..115 (not collector shutdown) |
| 0x0007 | solar_return_temperature | SolarReturnTemp | f32 | state | °C |
| 0x0008 | solar_pump_active | SolarPumpStatus | u8 | state | 0/1 |
| 0x0009 | solar_yield_current | SolarYieldCurrent | f32 | state | Current yield |
| 0x000B | solar_pump_hours | SolarPumpHours | u32 | state | Cumulative pump runtime |

---

## GG=0x05 — Cylinders (multi-instance)

Entire group gated by `fm5_config <= 2`. These are solar charging parameters per cylinder (TSP: "Solar Cylinder"). General cylinder config (max temp, charge hysteresis) is in GG=0x00 system config.

> **Reconciliation note (2026-03-05):** Previous version had wrong name↔address assignments for 3 of 4 registers. This version uses the CSV. **No ebusd coverage exists for GG=0x05** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Leaf | ebusd Name | Type | Category | Notes |
|----|------|------------|------|----------|-------|
| 0x0001 | cylinder_max_setpoint | Cyl{cyl}MaxSetpoint | f32 | config | Constraint 0..99 |
| 0x0002 | cylinder_charge_hysteresis | Cyl{cyl}ChargeHyst | f32 | config | Constraint 2..25 |
| 0x0003 | cylinder_charge_offset | Cyl{cyl}ChargeOffset | f32 | config | Constraint 1..20 |
| 0x0004 | cylinder_temperature | Cyl{cyl}Temp | f32 | state | °C. Constraint -10..110 |

---

## GG=0x09 — Room Sensors, Regulator (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0A (discovery scan found up to 31 instances). Register range 0x0001-0x000F observed in VRC Explorer scans. No myVaillant CSV mapping exists for this group.

Known constraints from `b524_constraints.go`:

| Record (TSP) | RR (std) | Type | Range | Possible Purpose |
|-------------|----------|------|-------|------------------|
| 0x0100 | 0x0001 | u16 | 0..255 | Sensor ID / address |
| 0x0200 | 0x0002 | u16 | 1..3 | Sensor type / protocol |
| 0x0300 | 0x0003 | u8 | 0..1 | Enable flag |
| 0x0400 | 0x0004 | u16 | 0..10 | Zone association |
| 0x0500 | 0x0005 | u16 | 0..32768 | Timer/counter |
| 0x0600 | 0x0006 | u16 | 0..32768 | Timer/counter |

Scan data contains mostly schedule/time entries. Further register identification requires controlled testing with paired room sensors.

---

## GG=0x0A — Room Sensors, VR92 (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0A (discovery scan found up to 31 instances). Instance 0 has 78+ responsive registers in VRC Explorer scan, including serial numbers (ASCII strings) and what appears to be temperature profile schedules.

Known constraints from `b524_constraints.go`:

| Record (TSP) | RR (std) | Type | Range | Possible Purpose |
|-------------|----------|------|-------|------------------|
| 0x0100 | 0x0001 | u8 | 0..3 | Sensor mode |
| 0x0200 | 0x0002 | u8 | 1..2 | Protocol type |
| 0x0300 | 0x0003 | u8 | 1..2 | Communication mode |
| 0x0500 | 0x0005 | u8 | 0..3 | Status flags |
| 0x0600 | 0x0006 | u8 | 0..1 | Enable flag |

Notable scan observations:
- RR=0x001D: ASCII string "212134" (possibly serial/version)
- RR=0x001E: ASCII string "002026" (possibly date component)
- RR=0x0022-0x0039: Incrementing/decrementing byte sequences (25→45→45→25→10→30) — likely a temperature profile or weekly schedule

---

## GG=0x0C — Unknown Remote (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0F. VRC Explorer scan returned `0x00` (empty) for all registers across all instances on the test system. No active data.

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

**Notes:**
- TSP-style registers (`0x0100+`) are listed in the constraint catalog but are NOT accessible via standard B524 read operations — only standard registers (`0x0001-0x00FF`) work through gateway RPC.
- GG=0x00 Record 0x8000 (f32_range -10..10) is orphaned — its standard-address equivalent would be 0x0080 which is not a known register. Possibly a constraint for `smart_photovoltaic_buffer_offset` (0x0081) with an off-by-one, or a high-address register not yet identified.

---

## Mapping Conflicts

Three register mappings from the original myPyllant value-matching had errors, resolved using TSP:

| RR | myPyllant CSV leaf | TSP name | Resolution |
|----|-------------------|----------|------------|
| 0x0019 | heating_circuit_bivalence_point | SolarFlowRateQuantity | Coincidental 0.0 match (solar disabled). Real HcBivalencePoint at 0x0023. |
| 0x0026 | dhw_flow_setpoint_offset | HcEmergencyTemperature | 25.0 fits both semantics, TSP authoritative. |
| 0x0029 | max_flow_setpoint_hp_error | HwcStorageChargeOffset | 25.0 fits range, TSP authoritative. |

One resolved by ebusd verification:

| RR | CSV leaf | ebusd TSP | Resolution |
|----|----------|-----------|------------|
| 0x0015 | paralell_tank_loading_allowed | (not at this address) | CSV value-matching false positive. ebusd places HwcParallelLoading at 0x000A (`@ext(0xa,0)`). 0x0015 purpose unknown. |

One conflict is still pending:

| RR | myPyllant CSV leaf | TSP name | Status |
|----|-------------------|----------|--------|
| 0x0024 | hybrid_control_strategy (BIVALENCE_POINT) | BackupBoiler | Pending. TSP puts HybridManager at 0x000F. |

---

## Sources

- **ebusd community TSP** (`15.ctlv2.tsp` in `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/`) — Community-maintained register definitions using `@ext(RR, 0)` addressing (same as B524 RR). **Highest authority** for register↔name mapping where coverage exists. Covers GG=0x00, 0x01, 0x02 (partial), 0x03. No coverage for GG=0x04, 0x05.
- **myVaillant register map CSV** (`helianthus-vrc-explorer/data/myvaillant_register_map.csv`) — Helianthus-curated mapping built by value-matching live B524 reads against myPyllant cloud API field values. 115 entries across groups 0x00-0x05. **NOT a Vaillant-published source** — carries false-positive risk where multiple registers share the same value (see Mapping Conflicts). Leaf names come from myPyllant API; ebusd_name column from ebusd community definitions.
- **Live B524 scan** (2026-03-04) — MCP RPC reads from BASV2 via Helianthus gateway, 81 registers in GG=0x00
- **VRC Explorer full group scan** — Raw register data for GG=0x02-0x0C across all instances (`_work_register_mapping/B524/` directory), used for cross-verification
- **myPyllant system dump** (2026-03-04T17:43Z) — Cloud API snapshot for value cross-reference
- **Gateway production code** (`helianthus-ebusgateway/cmd/gateway/semantic_vaillant.go`) — Authoritative for which registers are actively polled and how they map to semantic planes
- **Registry constraint catalog** (`helianthus-ebusreg/vaillant/system/b524_constraints.go`) — Static constraint ranges per (group, register)
- **Discovery profiles** (`helianthus-ebusreg/vaillant/system/b524_profile.go`) — Instance/register ranges for group scanning

## Related Files

- `_work_register_mapping/mypyllant_b524_system_mapping.json` — Original mapping analysis with confidence ratings (historical)
- `_work_register_mapping/B524/` — Raw VRC Explorer scan data per group (op0200_0600_g*.json)
- `_work_register_mapping/b524_groups_scan_schema_decoded.json` — Decoded register values with type annotations
