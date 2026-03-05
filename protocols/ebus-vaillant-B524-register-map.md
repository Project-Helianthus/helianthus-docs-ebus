# Vaillant B524 Extended Register Map

> **Status:** Authoritative reference. Single source of truth for B524 register semantics in Helianthus.
>
> **Last updated:** 2026-03-05 (v3 — FLAGS verification from VRC Explorer scans, category corrections)
>
> **Device:** BASV2 (VRC720-compatible, HW 1704)

## Protocol Overview

B524 uses primary byte `0xB5`, secondary byte `0x24`. The wire frame for a read request is:

```
QQ ZZ PB SB NN OC OT GG II RR_lo RR_hi
```

- `QQ` = source address (gateway uses `0x71`)
- `ZZ` = destination (`0x15` for BASV2)
- `PB` = `0xB5` (primary), `SB` = `0x24` (secondary)
- `NN` = payload length (6 for a read: OC + OT + GG + II + RR_lo + RR_hi)
- `OC` = opcode: `0x02` (local) or `0x06` (remote)
- `OT` = operation type: `0x00` (read), `0x01` (write)
- `GG` = group, `II` = instance
- `RR` = register address (16-bit little-endian)

### Response Format

Responses do **not** echo the full request selector. The slave response payload (after eBUS NN byte):

```
FLAGS GG RR_lo RR_hi [VALUE_BYTES...]
```

- `FLAGS` = access/writability byte (see below)
- `GG` = group echo
- `RR` = register echo (16-bit LE)
- Value bytes: variable length depending on data type

The instance is **not** echoed in the response — the gateway correlates replies using the original request parameters. When the reply payload is a single `0x00` byte, the register exists but has no data (empty/unsupported).

### FLAGS Byte (Response Header)

The FLAGS byte in the response header encodes register access mode. Discovered via VRC Explorer full-group B524 scans (`_work_register_mapping/B524/`), verified against ebusd TSP r/rw annotations (89% agreement, 48/54 match).

| FLAGS | Bit 1 (writable) | Bit 0 (sub-cat) | Access | Category | Description |
|-------|-------------------|------------------|--------|----------|-------------|
| `0x00` | 0 | 0 | RO | State (volatile) | Changes frequently — external pushes, counters |
| `0x01` | 0 | 1 | RO | State (stable) | Computed outputs, sensor readings, properties |
| `0x02` | 1 | 0 | RW | Config (technical) | Offsets, thresholds, numeric ranges |
| `0x03` | 1 | 1 | RW | Config (user-facing) | Modes, schedules, names, setpoints |

**Opcode-specific behavior:** Opcode `0x0600` (remote) is heavily RO — across all groups, 0x0600 exposes far fewer writable registers. When it does allow writes, they are always FLAGS=0x02 (technical), never 0x03 (user-facing). All user-configurable settings are exclusively on the 0x0200 (local) path.

**Coverage:** FLAGS data available for GG=0x02, 0x03, 0x09, 0x0A, 0x0C (from VRC Explorer scans). **No FLAGS data for GG=0x00 and GG=0x01** — these groups were not scanned with `b524_grab_op.py`; a future scan is needed.

### Data Type Encoding

| Type | Encoding | Size | Notes |
|------|----------|------|-------|
| `bool` | `0` = false, `!0` = true | 1 or 2 bytes | Wire width varies: some registers use u8 (1 byte), others u16 LE (2 bytes). See per-register Type column and constraint catalog for actual width |
| `u8` | Single byte | 1 byte | |
| `u16` | Little-endian uint16 | 2 bytes | Some constraint entries use u8 (1-byte) for boolean-range u16 registers; wire always returns 2 bytes |
| `u32` | Little-endian uint32 | 4 bytes | |
| `f32` | Little-endian IEEE 754 float32 | 4 bytes | Primary numeric type for temps, pressures |
| `string` | Null-terminated C string | Variable | Used for zone names, installer info |
| `bytes` | Raw byte sequence | Variable | Opaque payload, not decoded as numeric |
| `date` | BCD-encoded `DD MM YY` | 3 bytes | Year = 2000 + YY. See constraint type `0x0C` in GetExtendedRegisters |
| `time` | BCD-encoded `HH MM [SS]` | 2-3 bytes | 2 bytes (HH:MM) for timers, 3 bytes (HH:MM:SS) for system clock |
| `energy4` | Unsigned 32-bit LE (kWh) | 4 bytes | Alias for u32, energy counters only |

### Opcode Routing

| Opcode | Name | Groups | Notes |
|--------|------|--------|-------|
| `0x02` | Local | 0x00-0x05 | Controller-local registers |
| `0x06` | Remote | 0x09, 0x0A, 0x0C | Room sensor / remote device registers |

### Selector Subtypes (VRC Explorer Reference)

Beyond read/write, B524 supports additional selector types (documented in `helianthus-vrc-explorer`):

| Opcode | Name | Payload | Purpose |
|--------|------|---------|---------|
| `0x00` | Directory | `[0x00, GG, 0x00]` | Probe group existence (unreliable for GG=0x05) |
| `0x01` | Constraint | `[0x01, GG, RR]` | Query value constraints (3 bytes). **Note:** RR is u8 here (low byte only), unlike register read where RR is u16 LE |
| `0x02` | Local read/write | `[0x02, OT, GG, II, RR_lo, RR_hi]` | Standard local register access |
| `0x03` | Timer read | `[0x03, SEL1, SEL2, SEL3, weekday]` | Read timer schedule |
| `0x04` | Timer write | `[0x04, SEL1, SEL2, SEL3, weekday, ...]` | Write timer schedule (data bytes follow weekday) |
| `0x06` | Remote read/write | `[0x06, OT, GG, II, RR_lo, RR_hi]` | Remote register access |

---

## Table Legend

| Column | Meaning |
|--------|---------|
| **RR** | Register address (hex) |
| **Name** | Our leaf name (from myVaillant/myPyllant API path) |
| **Cat** | **S**=state (RO), **C**=config (RW), **P**=property (RO, stable), **E**=energy (RO, counter). Verified against observed FLAGS where scan data exists |
| **Type** | Wire type (`bool`, `u16`, `f32`, `string`, `date`, `time`, `energy4`) |
| **ebusd** | ebusd community TSP name. `—` = not in TSP. `(commented)` = present but commented out |
| **Constraint** | From BASV2 constraint catalog (authoritative, downloaded from hardware). `—` = no catalog entry |
| **Values** | Enum mapping. Inline for ≤3 values, otherwise `→enum_name` referencing [Enum Reference](#enum-reference) |
| **Gates** | Condition for register to be present/meaningful. `—` = always available |
| **Semantic** | MCP semantic field path. **S** prefix = actively polled by gateway |

**Source annotations** (in Notes):
- No annotation = confirmed by multiple independent sources (ebusd + gateway + scan)
- `†` = CSV value-matched only, not independently confirmed (false-positive risk)
- `ebusd: "..."` = ebusd has this as unknown/commented-out with the quoted observation

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
| 0x08 | Unknown (constraint-only) | Yes | — | 0x02 | — |
| 0x09 | Room Sensors (regulator) | Yes | 0x00-0x0A | 0x06 | — |
| 0x0A | Room Sensors (VR92) | Yes | 0x00-0x0A | 0x06 | — |
| 0x06 | Programs/Timetables | — | — | 0x0B | — |
| 0x07 | Programs/Timetables | — | — | 0x0B | — |
| 0x0C | Unknown remote | Yes | 0x00-0x0A | 0x06 | — |

Group 0x08 has 6 constraint entries in `b524_constraints.go` (similar structure to GG=0x05 cylinders) but no responsive registers observed in VRC Explorer scans. Discovery probe returned 0 pages. Possibly a second cylinder bank or buffer tank group on systems with FM5 module.

Room sensors use groups GG=0x09 (regulator-side) and GG=0x0A (VR92-side), both via opcode `0x06` (remote). The instance II selects which sensor within that group (II=0x00 for the first, up to 0x0A).

**Discovery:** Directory probe (`opcode=0x00`) is unreliable for GG=0x05 (terminator quirk). Use static topology. Multi-instance groups: scan all instances up to II=0x0A, expose only active ones.

### Discovery Profiles (ebusreg)

Source: `helianthus-ebusreg/vaillant/system/b524_profile.go`

| Group | Opcode | Instance Max | Register Max | Notes |
|-------|--------|-------------|-------------|-------|
| 0x02 | 0x02 (local) | 0x0A | 0x0025 | Heating circuits. Profile says 0x0021 — stale, should be 0x0025 |
| 0x03 | 0x02 (local) | 0x0A | 0x002F | Zones |
| 0x09 | 0x06 (remote) | 0x0A | 0x002F | Room sensors (regulator) |
| 0x0A | 0x06 (remote) | 0x0A | 0x003F | Room sensors (VR92) |
| 0x0C | 0x06 (remote) | 0x0A | 0x003F | Unknown remote |

---

## Gate Conditions (Quick Reference)

Several registers are conditionally available based on system configuration. Gates are also annotated per-register in the group tables below.

| Gate | Source Register | Controls |
|------|----------------|----------|
| `hwc_enabled` | GG=0x01 RR=0x0001 | DHW registers in GG=0x01, HWC-related config in GG=0x00 |
| `fm5_config` | GG=0x00 RR=0x002F | Solar registers (GG=0x04, GG=0x05), `solar_flow_rate_quantity` |
| `circuit_type` | GG=0x02 RR=0x0002 | Per-circuit: heating regs (type=1), fixed_value regs (type=2), return_increase regs (type=4) |
| `cooling_enabled` | GG=0x02 RR=0x0006 | Cooling-related config in circuits and zones |
| `room_temp_control_mode` | GG=0x02 RR=0x0015 | Dew point monitoring/offset |
| `ext_hwc_active` | GG=0x02 RR=0x0018 | External HWC temp/mode |

**Rule:** Gated-off registers are omitted from semantic plane responses. Explicit queries to gated-off registers return an error with gate status explanation.

---

## GG=0x00 — System/Regulator

All registers use opcode `0x02`, instance `0x00`.

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | dhw_bivalence_point | C | f32 | — | -20..50 step 1 | — | — | **S** `system.config.dhw_bivalence_point` | |
| 0x0002 | continuous_heating_start_setpoint | C | f32 | ContinuousHeating | -26..10 step 1 | — | — | | ebusd: `-26=off` disables function |
| 0x0003 | frost_override_time | C | u16 | FrostOverRideTime | 0..12 step 1 | — | — | | Hours |
| 0x0004 | maximum_preheating_time | C | u16 | — | 0..300 step 10 | — | — | | Minutes. † |
| 0x0007 | system_off | S | bool | — | — | `0=false 1=true` | — | **S** `system.state.system_off` | |
| 0x0008 | temporary_allow_backup_heater | C | u8 | — | — | — | — | | † |
| 0x0009 | external_energy_management_activation | P | bool | — | — | `0=false 1=true` | — | | † |
| 0x000A | parallel_tank_loading_allowed | C | bool | HwcParallelLoading | — | →onoff | — | | ebusd confirmed at `@ext(0xa,0)` |
| 0x000B | (unknown) | — | u16 | — | — | — | — | | Scan value: 0. Near boolean cluster |
| 0x000E | max_room_humidity | C | u16 | MaxRoomHumidity | — | — | — | **S** `system.config.max_room_humidity` | Percent |
| 0x000F | (unknown) | — | u16 | — | — | — | — | | Possibly HybridManager per TSP |
| 0x0010 | (unknown) | — | u16 | — | — | — | — | | Near config cluster |
| 0x0011 | (unknown) | — | u16 | — | — | — | — | | Scan value: 16. Possible temp threshold |
| 0x0012 | continuous_heating_room_setpoint | C | u16 | — | — | — | — | | Confirmed exact, value=20. °C |
| 0x0014 | adaptive_heating_curve | C | bool | AdaptHeatCurve | — | →yesno | — | **S** `system.config.adaptive_heating_curve` | |
| 0x0015 | (unknown) | — | bool | — | — | — | — | | False positive in CSV (was `parallel_tank_loading`; actual is at 0x000A) |
| 0x0017 | dhw_maximum_loading_time | C | u16 | MaxCylinderChargeTime | — | — | hwc_enabled | | Minutes |
| 0x0018 | hwc_lock_time | C | u16 | HwcLockTime | — | — | hwc_enabled | | Minutes |
| 0x0019 | solar_flow_rate_quantity | C | f32 | — | — | — | fm5_config≤2 | | See [Mapping Conflicts](#mapping-conflicts) |
| 0x001B | pump_additional_time | C | u16 | PumpAdditionalTime | — | — | — | | Minutes |
| 0x001C | dhw_maximum_temperature | C | f32 | — | — | — | — | | °C. † |
| 0x001E | (unknown) | — | u8 | — | — | — | — | | Scan value: 1. Possible pump/flag |
| 0x0022 | alternative_point | C | f32 | — | — | — | — | **S** `system.config.alternative_point` | °C. -21..40 per TSP |
| 0x0023 | heating_circuit_bivalence_point | C | f32 | — | — | — | — | **S** `system.config.heating_circuit_bivalence_point` | °C. -20..30 per TSP |
| 0x0024 | backup_heater_mode | C | u16 | — | — | — | — | | See [Mapping Conflicts](#mapping-conflicts) |
| 0x0025 | (unknown) | — | u16 | — | — | — | — | | Scan value: 0 |
| 0x0026 | hc_emergency_temperature | C | f32 | — | — | — | — | **S** `system.config.hc_emergency_temperature` | °C. 20..80 per TSP |
| 0x0027 | dhw_hysteresis | C | f32 | CylinderChargeHyst | — | — | hwc_enabled | | K. 3..20 step 0.5 per TSP |
| 0x0029 | hwc_storage_charge_offset | C | f32 | CylinderChargeOffset | — | — | hwc_enabled | | K. 0..40 per TSP |
| 0x002A | hwc_legionella_time | C | time | — | — | — | hwc_enabled | | HH:MM |
| 0x002B | is_legionella_protection_activated | C | u16 | — | — | `0=off 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun` | hwc_enabled | | Day-of-week selector. 0=disabled |
| 0x002C | maintenance_date | P | date | MaintenanceDate | — | — | — | | |
| 0x002D | offset_outside_temperature | C | f32 | — | — | — | — | | K. -3..3 step 0.5 per TSP |
| 0x002F | module_configuration_vr71 | P | u16 | — | — | — | — | **S** `system.properties.module_configuration_vr71` | 1..11 |
| 0x0031 | (unknown) | — | u16 | — | — | — | — | | Scan value: 0 |
| 0x0034 | system_date | S | date | Date | — | — | — | | BCD |
| 0x0035 | system_time | S | time | Time | — | — | — | | HH:MM:SS |
| 0x0036 | system_scheme | P | u16 | HydraulicScheme | — | — | — | **S** `system.properties.system_scheme` | 1..16 |
| 0x0038 | cooling_outside_temperature_threshold | C | f32 | — | — | — | — | | °C. 10..30 per TSP. ebusd: `(commented) Unknown38 constant 21` |
| 0x0039 | system_water_pressure | S | f32 | WaterPressure | — | — | — | **S** `system.state.system_water_pressure` | bar. Read-only |
| 0x003A | dew_point_offset | C | f32 | — | — | — | — | | K. -10..10 per TSP |
| 0x003D | solar_yield_total | E | energy4 | SolarYieldTotal | — | — | fm5_config≤2 | | kWh |
| 0x003E | environmental_yield_total | E | energy4 | YieldTotal | — | — | — | | kWh |
| 0x0045 | esco_block_function | C | u16 | — | — | — | — | | Enum |
| 0x0046 | hwc_max_flow_temp_desired | C | f32 | HwcMaxFlowTempDesired | — | — | — | **S** `system.config.hwc_max_flow_temp_desired` | °C. 15..80 per TSP |
| 0x0048 | (unknown) | — | u16 | — | — | — | — | | Scan value: 1 |
| 0x004B | system_flow_temperature | S | f32 | SystemFlowTemp | — | — | — | **S** `system.state.system_flow_temperature`, `boiler_status.state.flow_temperature` | °C. Read-only |
| 0x004D | multi_relay_setting | C | u16 | MultiRelaySetting | — | →mamode | — | | |
| 0x004E | fuel_consumption_heating_this_month | E | energy4 | PrFuelSumHcThisMonth | — | — | — | | kWh |
| 0x004F | energy_consumption_heating_this_month | E | energy4 | PrEnergySumHcThisMonth | — | — | — | | kWh |
| 0x0050 | energy_consumption_dhw_this_month | E | energy4 | PrEnergySumHwcThisMonth | — | — | — | | kWh |
| 0x0051 | fuel_consumption_dhw_this_month | E | energy4 | PrFuelSumHwcThisMonth | — | — | — | | kWh |
| 0x0052 | fuel_consumption_heating_last_month | E | energy4 | PrFuelSumHcLastMonth | — | — | — | | kWh |
| 0x0053 | energy_consumption_heating_last_month | E | energy4 | PrEnergySumHcLastMonth | — | — | — | | kWh |
| 0x0054 | energy_consumption_dhw_last_month | E | energy4 | PrEnergySumHwcLastMonth | — | — | — | | kWh |
| 0x0055 | fuel_consumption_dhw_last_month | E | energy4 | PrFuelSumHwcLastMonth | — | — | — | | kWh |
| 0x0056 | fuel_consumption_heating_total | E | energy4 | PrFuelSumHc | — | — | — | **S** `energy_totals.gas.climate` | kWh |
| 0x0057 | energy_consumption_heating_total | E | energy4 | PrEnergySumHc | — | — | — | **S** `energy_totals.electric.climate` | kWh |
| 0x0058 | energy_consumption_dhw_total | E | energy4 | PrEnergySumHwc | — | — | — | **S** `energy_totals.electric.dhw` | kWh |
| 0x0059 | fuel_consumption_dhw_total | E | energy4 | PrFuelSumHwc | — | — | — | **S** `energy_totals.gas.dhw` | kWh |
| 0x005C | energy_consumption_total | E | energy4 | PrEnergySum | — | — | — | | kWh |
| 0x005D | fuel_consumption_total | E | energy4 | PrFuelSum | — | — | — | | kWh |
| 0x006C | installer_name_1 | P | string | Installer1 | — | — | — | | maxLength 6 |
| 0x006D | installer_name_2 | P | string | Installer2 | — | — | — | | maxLength 6 |
| 0x006F | installer_phone_1 | P | string | PhoneNumber1 | — | — | — | | maxLength 6 |
| 0x0070 | installer_phone_2 | P | string | PhoneNumber2 | — | — | — | | maxLength 6 |
| 0x0073 | outdoor_temperature | S | f32 | DisplayedOutsideTemp | — | — | — | **S** `system.state.outdoor_temperature` | °C. Read-only |
| 0x0076 | installer_menu_code | P | u16 | KeyCodeforConfigMenu | — | — | — | | 0..999 |
| 0x0081 | smart_photovoltaic_buffer_offset | P | f32 | — | — | — | — | | K. † |
| 0x0086 | (unknown) | — | u16 | — | — | — | — | | Scan value: 60. PV/smart cluster |
| 0x0089 | (unknown) | — | u16 | — | — | — | — | | Scan value: 15. PV/smart cluster |
| 0x008A | (unknown) | — | f32 | — | — | — | — | | Scan value: 1.0. PV/smart cluster |
| 0x008B | (unknown) | — | f32 | — | — | — | — | | Scan value: 90.0. PV/smart cluster, possible max flow temp |
| 0x0095 | outdoor_temperature_average24h | S | f32 | OutsideTempAvg | — | — | — | **S** `system.state.outdoor_temperature_avg24h` | °C. Rounded avg updated every 3h |
| 0x0096 | maintenance_due | S | bool | MaintenanceDue | — | →yesno | — | **S** `system.state.maintenance_due` | Read-only |
| 0x009A | green_iq | S | bool | — | — | — | — | | |
| 0x009D | hwc_cylinder_temperature_top | S | f32 | HwcStorageTempTop | — | — | — | **S** `system.state.hwc_cylinder_temperature_top` | °C. Read-only |
| 0x009E | hwc_cylinder_temperature_bottom | S | f32 | HwcStorageTempBottom | — | — | — | **S** `system.state.hwc_cylinder_temperature_bottom` | °C. Read-only |
| 0x009F | hc_cylinder_temperature_top | S | f32 | HcStorageTempTop | — | — | — | | °C. Read-only |
| 0x00A0 | hc_cylinder_temperature_bottom | S | f32 | HcStorageTempBottom | — | — | — | | °C. Read-only |
| 0x00A2 | buffer_charge_offset | C | f32 | — | — | — | — | | K. 0..15 per TSP |

---

## GG=0x01 — DHW

All registers use opcode `0x02`, instance `0x00`. All registers except `hwc_status` (0x000F) are gated by `hwc_enabled` (0x0001).

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | hwc_enabled | C | bool | — | 0..1 | `0=off 1=on` | — | | Gate register for GG=0x01 |
| 0x0002 | hwc_circulation_pump_status | S | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | | |
| 0x0003 | operation_mode_dhw | C | u16 | HwcOpMode | 0..2 | →opmode | hwc_enabled | **S** `dhw.operating_mode` | |
| 0x0004 | dhw_target_temperature | C | f32 | HwcTempDesired | 35..70 | — | hwc_enabled | **S** `dhw.desired_temperature` | °C |
| 0x0005 | current_dhw_temperature | S | f32 | HwcStorageTemp | 0..99 | — | hwc_enabled | **S** `dhw.current_temperature` | °C. Read-only |
| 0x0006 | hwc_reheating_active | S | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | | |
| 0x0008 | hwc_flow_temperature_desired | S | f32 | HwcFlowTemp | — | — | hwc_enabled | | °C. Read-only |
| 0x0009 | hwc_holiday_start_date | C | date | HwcHolidayStartPeriod | — | — | hwc_enabled | | |
| 0x000A | hwc_holiday_end_date | C | date | HwcHolidayEndPeriod | — | — | hwc_enabled | | |
| 0x000B | hwc_bank_holiday_start | C | date | HwcBankHolidayStartPeriod | — | — | hwc_enabled | | ebusd confirmed |
| 0x000C | hwc_bank_holiday_end | C | date | HwcBankHolidayEndPeriod | — | — | hwc_enabled | | ebusd confirmed |
| 0x000D | hwc_special_function_mode | C | u16 | HwcSFMode | — | →sfmode | hwc_enabled | **S** `dhw.state` | Special function |
| 0x000F | hwc_status | S | u16 | — | — | — | — | | Not gated. ebusd: `(commented) UnknownValue0f HEX:6` |
| 0x0010 | hwc_holiday_start_time | C | time | — | — | — | hwc_enabled | | |
| 0x0011 | hwc_holiday_end_time | C | time | — | — | — | hwc_enabled | | |

---

## GG=0x02 — Heating Circuits (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active circuits discovered by probing `heating_circuit_type` (RR=0x0002) — value `0` (`mctype=inactive`) indicates unused circuit slot. Absent instances (beyond the highest configured slot) return empty/null response (no valid payload from bus). Verified via MCP: II=0,1 return mctype=1 (heating), II=2-9 return mctype=0 (inactive), II=10 returns null (absent).

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | (unknown) | — | u16 | — | 1..2 | — | — | | CSV says `heating_circuit_type` but gateway uses 0x0002. Purpose unverified. † |
| 0x0002 | heating_circuit_type | P | u16 | Hc{hc}CircuitType | 0..4 | →mctype | — | **S** `circuits[].properties.heating_circuit_type` | Discovery probe. Also `mixer_circuit_type_external` |
| 0x0003 | room_influence_type | C | u8 | Hc{hc}RoomInfluenceType | — | `0=inactive 1=active 2=extended` | — | | Controls room sensor influence on heating curve. Not responsive on II=0x00 in VRC Explorer scan. See GetExtendedRegisters §4.2.5 for behavioral semantics |
| 0x0004 | target_return_temperature | C | f32 | Hc{hc}ReturnTempDesired | 15..80 | — | circuit_type=4 (return_increase) | | Factory setting 30°C. jonesPD CTLV2 confirmed. Only meaningful for "Increase in return" circuits |
| 0x0005 | dew_point_monitoring_enabled | C | u16 | — | 0..1 | `0=off 1=on` | cooling_enabled | | † |
| 0x0006 | cooling_enabled | C | u16 | Hc{hc}CoolingEnabled | 0..1 | `0=off 1=on` | — | **S** `circuits[].config.cooling_enabled` | Gate register |
| 0x0007 | heating_circuit_flow_setpoint | S | f32 | Hc{hc}FlowTempDesired | — | — | — | **S** `circuits[].state.heating_circuit_flow_setpoint` | °C. Read-only |
| 0x0008 | current_circuit_flow_temperature | S | f32 | Hc{hc}FlowTemp | — | — | — | **S** `circuits[].state.current_circuit_flow_temperature` | °C. Read-only. Also `boiler_status.state.return_temperature` (II=0) |
| 0x0009 | ext_hwc_temperature_setpoint | C | f32 | — | — | — | ext_hwc_active | | ebusd: `(commented) Unknown09, constant 60°C`. † |
| 0x000A | dew_point_offset | C | f32 | — | — | — | cooling_enabled | | † |
| 0x000B | flow_setpoint_excess_offset | C | f32 | Hc{hc}ExcessTemp | — | — | circuit_type=1 (heating) | | K. Flow temp increased by this value to keep mixing valve in control range |
| 0x000C | fixed_desired_temperature | C | f32 | — | — | — | circuit_type=2 (fixed_value) | | ebusd: `(commented) Unknown0c, constant 65°C`. Fixed-value circuit target flow temp. † |
| 0x000D | fixed_setback_temperature | C | f32 | — | — | — | circuit_type=2 (fixed_value) | | ebusd: `(commented) Unknown0d, constant 65°C`. Fixed-value circuit setback temp. † |
| 0x000E | set_back_mode_enabled | C | u16 | Hc{hc}SetbackMode | — | →offmode | circuit_type=1 (heating) | | |
| 0x000F | heating_curve | C | f32 | Hc{hc}HeatCurve | — | — | — | **S** `circuits[].config.heating_curve` | |
| 0x0010 | heating_flow_temp_max_setpoint | C | f32 | Hc{hc}MaxFlowTempDesired | — | — | — | **S** `circuits[].config.heating_flow_temperature_maximum_setpoint` | °C. 15..80 per ebusd |
| 0x0011 | cooling_flow_temp_min_setpoint | C | f32 | Hc{hc}MinCoolingTempDesired | — | — | cooling_enabled | | °C |
| 0x0012 | heating_flow_temp_min_setpoint | C | f32 | Hc{hc}MinFlowTempDesired | — | — | — | **S** `circuits[].config.heating_flow_temperature_minimum_setpoint` | °C |
| 0x0013 | ext_hwc_operation_mode | C | u16 | — | — | — | ext_hwc_active | | |
| 0x0014 | heat_demand_limited_by_outside_temp | C | f32 | Hc{hc}SummerTempLimit | — | — | — | **S** `circuits[].config.heat_demand_limited_by_outside_temp` | °C. Summer cutoff |
| 0x0015 | room_temperature_control_mode | C | u16 | Hc{hc}RoomTempSwitchOn | — | →rcmode | — | **S** `circuits[].config.room_temperature_control_mode` | Gate for dew point |
| 0x0016 | screed_drying_day | C | u16 | Hc{hc}ScreedDryingDay | — | — | — | | Screed drying program |
| 0x0017 | screed_drying_desired_temperature | S | f32 | Hc{hc}ScreedDryingTempDesired | — | — | — | | °C. Screed drying program. FLAGS=0x01 (stable RO) — computed setpoint, not user-configurable |
| 0x0018 | ext_hwc_active | S | u16 | Hc{hc}ExternalHWCActive | — | — | — | | Gate register for ext HWC. FLAGS=0x00 (volatile RO) — status, not config |
| 0x0019 | external_heat_demand | S | u16 | Hc{hc}ExternalHeatDemand | — | — | — | | External heat source. FLAGS=0x00 (volatile RO) — status, not config |
| 0x001A | mixer_movement | S | f32 | Hc{hc}MixerMovement | — | — | — | | Signed float: `<0`=closing, `>0`=opening. MCP verified: -100.0 when fully closing. Read-only |
| 0x001B | circuit_state | S | u16 | Hc{hc}Status | — | — | — | **S** `circuits[].state.circuit_state` | Raw state code |
| 0x001C | epsilon | S | f32 | Hc{hc}HeatCurveAdaption | — | — | — | | Heat curve adaption factor. Read-only |
| 0x001D | frost_protection_threshold | C | f32 | Hc{hc}FrostProtThreshold | — | — | — | **S** `circuits[].properties.frost_protection_threshold` | °C. FLAGS=0x02 (technical RW) — writable config, not property. Semantic path needs migration to `config.*` |
| 0x001E | pump_status | S | u16 | Hc{hc}PumpStatus | — | — | — | **S** `circuits[].state.pump_status` | Also `boiler_status.state.pump_running` (II=0) |
| 0x001F | room_temperature_setpoint | C | f32 | Hc{hc}RoomSetpoint | — | — | — | | °C |
| 0x0020 | calculated_flow_temperature | S | f32 | Hc{hc}FlowTempCalc | — | — | — | **S** `circuits[].state.calculated_flow_temperature` | °C |
| 0x0021 | mixer_position_percentage | S | f32 | Hc{hc}MixerPosition | — | — | — | **S** `circuits[].state.mixer_position_percentage` | % |
| 0x0022 | current_room_humidity | S | f32 | Hc{hc}Humidity | — | — | — | **S** `circuits[].state.current_room_humidity` | %. From room sensor |
| 0x0023 | dew_point_temperature | S | f32 | Hc{hc}DewPointTemp | — | — | — | **S** `circuits[].state.dew_point_temperature` | °C |
| 0x0024 | pump_operating_hours | S | u32 | Hc{hc}PumpHours | — | — | — | **S** `circuits[].state.pump_operating_hours` | |
| 0x0025 | pump_starts_count | S | u32 | Hc{hc}PumpStarts | — | — | — | **S** `circuits[].state.pump_starts_count` | |

---

## GG=0x03 — Zones (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones discovered by probing `zone_index` (RR=0x001C).

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | cooling_operation_mode | C | u16 | — | 0..2 | →opmode | cooling_enabled | | Same enum as heating_operation_mode |
| 0x0002 | cooling_set_back_temperature | C | f32 | Zone{z}CoolingTemp | 15..30 step 0.5 | — | cooling_enabled | | °C |
| 0x0003 | holiday_start_date | C | date | Zone{z}HolidayStartPeriod | — | — | — | | |
| 0x0004 | holiday_end_date | C | date | Zone{z}HolidayEndPeriod | — | — | — | | |
| 0x0005 | holiday_setpoint | C | f32 | Zone{z}HolidayTemp | 5..30 | — | — | | °C |
| 0x0006 | heating_operation_mode | C | u16 | Zone{z}OpMode | 0..2 | →opmode | — | **S** (derived) `zones[].state.operating_mode` | |
| 0x0008 | quick_veto_temperature | C | f32 | Zone{z}QuickVetoTemp | — | — | — | | °C. Veto override target |
| 0x0009 | heating_set_back_temperature | C | f32 | Zone{z}NightTemp | — | — | — | | °C. Night setpoint |
| 0x000C | bank_holiday_start | C | date | Zone{z}BankHolidayStartPeriod | — | — | — | | ebusd confirmed |
| 0x000D | bank_holiday_end | C | date | Zone{z}BankHolidayEndPeriod | — | — | — | | ebusd confirmed |
| 0x000E | current_special_function | C | u16 | Zone{z}SFMode | — | →sfmode | — | **S** (derived) `zones[].state.operating_mode` | FLAGS=0x03 (user RW) — writable to set quickveto/away |
| 0x000F | current_room_temperature | S | f32 | Zone{z}RoomTemp | — | — | — | **S** `zones[].state.current_temperature` | °C. FLAGS=0x01 (stable RO). From room sensor |
| 0x0010 | (unknown) | C | u16 | — | — | — | — | | FLAGS=0x03 (user RW). Discovered in VRC Explorer scan, not in ebusd/CSV |
| 0x0011 | (unknown) | C | u16 | — | — | — | — | | FLAGS=0x03 (user RW). Discovered in VRC Explorer scan, not in ebusd/CSV |
| 0x0012 | valve_status | S | u16 | Zone{z}ValveStatus | — | `0=closed 1=open` | — | | FLAGS=0x01 (stable RO). Used for hvac_action derivation |
| 0x0013 | room_temperature_zone_mapping | C | u16 | Zone{z}RoomZoneMapping | — | →zmapping | — | **S** (internal: circuit type lookup) | Maps zone to room temperature sensor source. ebusd name confirms semantics |
| 0x0014 | heating_manual_mode_setpoint | S | f32 | Zone{z}ActualRoomTempDesired | — | — | — | **S** `zones[].state.desired_temperature` (fallback) | °C. FLAGS=0x01 (stable RO) — computed output, not user-settable. Current setpoint considering all conditions |
| 0x0015 | cooling_manual_mode_setpoint | S | f32 | — | — | — | cooling_enabled | | °C. FLAGS=0x01 (stable RO) — computed output, not user-settable. ebusd: `(commented) Unknown15Temp, in FlusterBetrieb 24 sonst 99` |
| 0x0016 | zone_name | C | string | Zone{z}Shortname | — | — | — | **S** `zones[].name` | maxLength 6 |
| 0x0017 | zone_name_prefix | C | string | Zone{z}Name1 | — | — | — | | maxLength 5. Part 1 |
| 0x0018 | zone_name_suffix | C | string | Zone{z}Name2 | — | — | — | | maxLength 5. Part 2 |
| 0x0019 | heating_time_slot_active | S | u16 | — | — | `0=off 1=on` | — | | Timer schedule flag |
| 0x001A | cooling_time_slot_active | S | u16 | — | — | `0=off 1=on` | cooling_enabled | | Timer schedule flag |
| 0x001B | zone_status | S | u16 | — | — | — | — | | Raw zone status code |
| 0x001C | zone_index | P | bytes | Zone{z}Index | — | — | — | **S** (discovery) | Presence marker |
| 0x001E | quick_veto_end_time | C | time | Zone{z}QuickVetoEndTime | — | — | — | | FLAGS=0x03 (user RW) — writable, can extend/set veto end time |
| 0x0020 | holiday_end_time | C | time | — | — | — | — | | |
| 0x0021 | holiday_start_time | C | time | — | — | — | — | | |
| 0x0022 | heating_desired_setpoint | C | f32 | Zone{z}DayTemp | — | — | — | **S** `zones[].state.desired_temperature` (primary) | °C. 15..30 step 0.5 per ebusd |
| 0x0023 | cooling_desired_setpoint | C | f32 | — | — | — | cooling_enabled | | °C |
| 0x0024 | quick_veto_end_date | C | date | Zone{z}QuickVetoEndDate | — | — | — | | FLAGS=0x03 (user RW) — writable, can extend/set veto end date |
| 0x0026 | quick_veto_duration | C | f32 | Zone{z}QuickVetoDuration | — | — | — | | Hours. 0.5..12 step 0.5. Writing enables quick veto mode. |
| 0x0027 | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x00 (volatile RO). Discovered in VRC Explorer scan |
| 0x0028 | current_room_humidity | S | f32 | — | — | — | — | **S** `zones[].state.current_room_humidity` | %. FLAGS=0x01 (stable RO). From room sensor |
| 0x0029 | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002A | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002B | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002C | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002D | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002E | (unknown) | S | u16 | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |

### Zone Mode Derivation

The `operating_mode` and `preset` exposed in the zones semantic plane are derived from:
- `heating_operation_mode` (0x0006): →opmode (Helianthus: 0=off, 1=auto, 2=manual)
- `current_special_function` (0x000E): →sfmode (Helianthus: 2=quickveto, 3/4=away)
- Associated circuit's `cooling_enabled` (GG=0x02 RR=0x0006): determines heat vs cool capability for the zone

---

## GG=0x04 — Solar Circuit

Entire group gated by `fm5_config ≤ 2`. All registers use opcode `0x02`, instance `0x00`.

**No ebusd coverage exists for GG=0x04** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | solar_enabled | C | u8 | — | 0..1 | `0=off 1=on` | fm5_config≤2 | | † |
| 0x0002 | solar_function_mode | C | u8 | — | 0..1 | `0=off 1=on` | fm5_config≤2 | | Not pump status (pump is at 0x0008). † |
| 0x0003 | collector_temperature | S | f32 | — | -40..155 | — | fm5_config≤2 | | °C. † |
| 0x0004 | delta_t_on_threshold | C | f32 | — | 0..99 | — | fm5_config≤2 | | °C. Not storage temp. † |
| 0x0005 | max_collector_temperature | C | f32 | — | 110..150 | — | fm5_config≤2 | | °C. † |
| 0x0006 | max_cylinder_temperature_solar | C | f32 | — | 75..115 | — | fm5_config≤2 | | °C. Not collector shutdown. † |
| 0x0007 | solar_return_temperature | S | f32 | — | — | — | fm5_config≤2 | | °C. † |
| 0x0008 | solar_pump_active | S | u8 | — | — | `0=off 1=on` | fm5_config≤2 | | † |
| 0x0009 | solar_yield_current | S | f32 | — | — | — | fm5_config≤2 | | Current yield. † |
| 0x000B | solar_pump_hours | S | u32 | — | — | — | fm5_config≤2 | | Cumulative runtime. † |

---

## GG=0x05 — Cylinders (multi-instance)

Entire group gated by `fm5_config ≤ 2`. These are solar charging parameters per cylinder. General cylinder config (max temp, charge hysteresis) is in GG=0x00 system config.

**No ebusd coverage exists for GG=0x05** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | cylinder_max_setpoint | C | f32 | — | 0..99 | — | fm5_config≤2 | | °C. † |
| 0x0002 | cylinder_charge_hysteresis | C | f32 | — | 2..25 | — | fm5_config≤2 | | K. † |
| 0x0003 | cylinder_charge_offset | C | f32 | — | 1..20 | — | fm5_config≤2 | | K. † |
| 0x0004 | cylinder_temperature | S | f32 | — | -10..110 | — | fm5_config≤2 | | °C. † |

---

## GG=0x09 — Room Sensors, Regulator (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0A. Register range 0x0001-0x000F observed in VRC Explorer scans. No myVaillant CSV mapping exists for this group.

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | (unknown) | — | u16 | — | 0..255 | — | — | | Sensor ID / address |
| 0x0002 | (unknown) | — | u16 | — | 1..3 | — | — | | Sensor type / protocol |
| 0x0003 | (unknown) | — | u8 | — | 0..1 | `0=off 1=on` | — | | Enable flag |
| 0x0004 | (unknown) | — | u16 | — | 0..10 | — | — | | Zone association |
| 0x0005 | (unknown) | — | u16 | — | 0..32768 | — | — | | Timer/counter |
| 0x0006 | (unknown) | — | u16 | — | 0..32768 | — | — | | Timer/counter |

Further register identification requires controlled testing with paired room sensors.

---

## GG=0x0A — Room Sensors, VR92 (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0A. Instance 0 has 78+ responsive registers in VRC Explorer scan, including serial numbers (ASCII strings) and temperature profile schedules.

| RR | Name | Cat | Type | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|-------|------------|--------|-------|----------|-------|
| 0x0001 | (unknown) | — | u8 | — | 0..3 | — | — | | Sensor mode |
| 0x0002 | (unknown) | — | u8 | — | 1..2 | — | — | | Protocol type |
| 0x0003 | (unknown) | — | u8 | — | 1..2 | — | — | | Communication mode |
| 0x0005 | (unknown) | — | u8 | — | 0..3 | — | — | | Status flags |
| 0x0006 | (unknown) | — | u8 | — | 0..1 | `0=off 1=on` | — | | Enable flag |

Notable scan observations:
- RR=0x001D: ASCII string "212134" (possibly serial/version)
- RR=0x001E: ASCII string "002026" (possibly date component)
- RR=0x0022-0x0039: Incrementing/decrementing byte sequences (25→45→45→25→10→30) — likely a temperature profile or weekly schedule

---

## GG=0x0C — Unknown Remote (multi-instance, remote)

Uses opcode `0x06` (remote). Instances 0x00-0x0A. VRC Explorer scan returned `0x00` (empty) for all registers across all instances on the test system. No active data.

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
| `[].properties.frost_protection_threshold` | GG=0x02, RR=0x001D | f32 | **Stale path**: FLAGS=0x02 (RW) — should be `config.*`. Pending gateway migration |

### `ebus.v1.semantic.zones.get`

Source: `refreshState()` / `refreshDiscovery()` in `semantic_vaillant.go`

| Semantic Path | B524 | Type |
|---------------|------|------|
| `[].name` | GG=0x03, RR=0x0016 | string |
| `[].state.operating_mode` | derived from GG=0x03 RR=0x0006 + 0x000E | — |
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

The constraint catalog was **downloaded from the BASV2 hardware** and is authoritative for value ranges. It uses a `(Group, Record)` selector where `Record` is a byte-swapped register address (endianness convention). Mapping: Register `0x00RR` → Record `0xRR00`.

| Group | Record | → RR | Type | Min | Max | Step |
|-------|--------|------|------|-----|-----|------|
| 0x00 | 0x0100 | 0x0001 | f32 | -20 | 50 | 1 |
| 0x00 | 0x0200 | 0x0002 | f32 | -26 | 10 | 1 |
| 0x00 | 0x0300 | 0x0003 | u16 | 0 | 12 | 1 |
| 0x00 | 0x0400 | 0x0004 | u16 | 0 | 300 | 10 |
| 0x00 | 0x8000 | 0x0080 | f32 | -10 | 10 | 1 |
| 0x01 | 0x0100 | 0x0001 | u16 | 0 | 1 | 1 |
| 0x01 | 0x0200 | 0x0002 | u8 | 0 | 1 | 1 |
| 0x01 | 0x0300 | 0x0003 | u16 | 0 | 2 | 1 |
| 0x01 | 0x0400 | 0x0004 | f32 | 35 | 70 | 1 |
| 0x01 | 0x0500 | 0x0005 | f32 | 0 | 99 | 1 |
| 0x01 | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |
| 0x02 | 0x0100 | 0x0001 | u16 | 1 | 2 | 1 |
| 0x02 | 0x0200 | 0x0002 | u16 | 0 | 4 | 1 |
| 0x02 | 0x0400 | 0x0004 | f32 | 15 | 80 | 1 |
| 0x02 | 0x0500 | 0x0005 | u8 | 0 | 1 | 1 |
| 0x02 | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |
| 0x03 | 0x0100 | 0x0001 | u16 | 0 | 2 | 1 |
| 0x03 | 0x0200 | 0x0002 | f32 | 15 | 30 | 0.5 |
| 0x03 | 0x0500 | 0x0005 | f32 | 5 | 30 | 1 |
| 0x03 | 0x0600 | 0x0006 | u16 | 0 | 2 | 1 |
| 0x04 | 0x0100 | 0x0001 | u8 | 0 | 1 | 1 |
| 0x04 | 0x0200 | 0x0002 | u8 | 0 | 1 | 1 |
| 0x04 | 0x0300 | 0x0003 | f32 | -40 | 155 | 1 |
| 0x04 | 0x0400 | 0x0004 | f32 | 0 | 99 | 1 |
| 0x04 | 0x0500 | 0x0005 | f32 | 110 | 150 | 1 |
| 0x04 | 0x0600 | 0x0006 | f32 | 75 | 115 | 1 |
| 0x05 | 0x0100 | 0x0001 | f32 | 0 | 99 | 1 |
| 0x05 | 0x0200 | 0x0002 | f32 | 2 | 25 | 1 |
| 0x05 | 0x0300 | 0x0003 | f32 | 1 | 20 | 1 |
| 0x05 | 0x0400 | 0x0004 | f32 | -10 | 110 | 1 |
| 0x08 | 0x0100 | 0x0001 | f32 | 0 | 99 | 1 |
| 0x08 | 0x0200 | 0x0002 | f32 | 0 | 99 | 1 |
| 0x08 | 0x0300 | 0x0003 | f32 | 2 | 25 | 1 |
| 0x08 | 0x0400 | 0x0004 | f32 | 1 | 20 | 1 |
| 0x08 | 0x0500 | 0x0005 | f32 | -10 | 110 | 1 |
| 0x08 | 0x0600 | 0x0006 | f32 | -10 | 110 | 1 |
| 0x09 | 0x0100 | 0x0001 | u16 | 0 | 255 | 1 |
| 0x09 | 0x0200 | 0x0002 | u16 | 1 | 3 | 1 |
| 0x09 | 0x0300 | 0x0003 | u8 | 0 | 1 | 1 |
| 0x09 | 0x0400 | 0x0004 | u16 | 0 | 10 | 1 |
| 0x09 | 0x0500 | 0x0005 | u16 | 0 | 32768 | 1 |
| 0x09 | 0x0600 | 0x0006 | u16 | 0 | 32768 | 1 |
| 0x0A | 0x0100 | 0x0001 | u8 | 0 | 3 | 1 |
| 0x0A | 0x0200 | 0x0002 | u8 | 1 | 2 | 1 |
| 0x0A | 0x0300 | 0x0003 | u8 | 1 | 2 | 1 |
| 0x0A | 0x0500 | 0x0005 | u8 | 0 | 3 | 1 |
| 0x0A | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |

**Notes:**
- TSP-style registers (`0x0100+`) are listed in the constraint catalog but are NOT accessible via standard B524 read operations — only standard registers (`0x0001-0x00FF`) work through gateway RPC.
- GG=0x00 Record 0x8000 → RR=0x0080 is orphaned — no known register at that address. Possibly related to `smart_photovoltaic_buffer_offset` (0x0081) or an undiscovered register.

---

## Enum Reference

Enum definitions used by B524 registers. Where Helianthus interprets values differently from ebusd, both mappings are shown.

### opmode — Operation mode

Used by: GG=0x03 RR=0x0006, GG=0x01 RR=0x0003

| Value | ebusd | Helianthus (zones) | Helianthus (DHW) |
|-------|-------|-------------------|------------------|
| 0 | off | off | off |
| 1 | auto | auto | auto |
| 2 | day | manual | heat |
| 3 | night | night *(not implemented)* | night *(not implemented)* |

Note: ebusd defines this as `UIN` with 4 values. Helianthus uses only 0-2; value 3 is not observed in practice on VRC720. Proposed: expose as "night" to distinguish from manual mode 2.

### sfmode — Special function

Used by: GG=0x03 RR=0x000E, GG=0x01 RR=0x000D

| Value | ebusd | Helianthus (zones) | Helianthus (DHW) |
|-------|-------|-------------------|------------------|
| 0 | auto | (none — normal operation) | (none — normal operation) |
| 1 | ventilation | ventilation *(not implemented)* | — |
| 2 | party | quickveto | — |
| 3 | veto | away | — |
| 4 | onedayaway | away | — |
| 5 | onedayathome | home *(not implemented)* | — |
| 6 | load | — | load *(not implemented)* |

Note: Helianthus collapses 3+4 into "away" preset. ebusd also defines `sfmodezone` (0=auto, 1=ventilation, 3=veto) and `sfmodehwc` (0=auto, 6=load) as restricted subsets. Proposed additions: "ventilation" for party-like fan override, "home" for one-day-at-home schedule override, "load" for forced DHW charge.

### mctype — Circuit type

Used by: GG=0x02 RR=0x0002

| Value | ebusd | Helianthus | Vaillant manual name | Description |
|-------|-------|-----------|---------------------|-------------|
| 0 | inactive | inactive | Inactive | Circuit unused |
| 1 | mixer | heating | Heating | Weather-compensated heating. Mixing or direct depending on basic system diagram. |
| 2 | fixed | fixed_value | Fixed value | Circuit held at a fixed target flow temperature. Applications: swimming pool heating, door air curtain heating. |
| 3 | hwc | dhw *(not implemented)* | DHW | Heating circuit used as DHW circuit for an additional cylinder. |
| 4 | returnincr | return_increase *(not implemented)* | Increase in return | Return temperature raise circuit. Target return temperature at RR=0x0004 (factory setting 30°C). |

**Naming note:** ebusd templates label value 1 as "mixer" — this is a community naming convention; the Vaillant VRC720 operating & installation manual calls it "Heating" (Heizen). The mixing valve is an implementation detail of the hydraulic system, not the circuit type itself.

**Pool is a derived application, not a raw enum value.** The Vaillant manual describes "fixed value control" as suitable for "swimming pool heating" — so pool heating is an _application_ of `fixed_value` (mctype=2) when the system topology includes swimming pool hydraulics (sensor, circulation pump). It is NOT a separate enum value on VRC720/CTLV2/BASV2 systems. Constraint catalog confirms range 0..4.

**ebusd extended enums:** ebusd `mctype` defines 0-5 (adding `pool=5`), and `mctype7` defines 0-6 (adding `circulation=6`; see ebusd-config issue #182 and PR #174). Neither value 5 nor 6 is within the BASV2 constraint range (0..4). These values may be valid on other Vaillant controller platforms.

**Zone capabilities** depend on (a) circuit type supporting heating, and (b) `cooling_enabled` flag (RR=0x0006) for cooling capability. Cooling is a separate function/mode, not derived from circuit type.

Sources: VRC720 operating & installation instructions (circuit type table, fixed value control description, abbreviations list for swimming pool); ebusd `_templates.tsp` mctype/mctype7 definitions; ebusd-config issue #182, PR #174 (translations: Heizen/Festwert/WW/Rückl.anh.).

### offmode — Auto-off behavior

Used by: GG=0x02 RR=0x000E

| Value | ebusd | Helianthus |
|-------|-------|-----------|
| 0 | eco | eco *(not implemented)* |
| 1 | night | night *(not implemented)* |

Note: Controls operation during lowering time. No influence if room temp modulation set to thermostat. Not yet exposed in semantic layer — propose as `circuits[].config.setback_mode`.

### rcmode — Room temperature control mode

Used by: GG=0x02 RR=0x0015

| Value | ebusd | Helianthus |
|-------|-------|-----------|
| 0 | off | off |
| 1 | modulating | modulating |
| 2 | thermostat | thermostat |

Note: Currently exposed as raw u16 in `circuits[].config.room_temperature_control_mode`. Proposed: expose as string enum with these values.

### onoff

Used by: GG=0x00 RR=0x000A (HwcParallelLoading), and various bool registers

| Value | ebusd | Helianthus |
|-------|-------|-----------|
| 0 | off | false |
| 1 | on | true |

Note: Helianthus decodes `onoff` registers as `bool`. Already implemented for registers exposed via semantic layer.

### yesno

Used by: GG=0x00 RR=0x0014 (AdaptHeatCurve), RR=0x0096 (MaintenanceDue)

| Value | ebusd | Helianthus |
|-------|-------|-----------|
| 0 | no | false |
| 1 | yes | true |

Note: Helianthus decodes `yesno` registers as `bool`. Already implemented for `adaptive_heating_curve` and `maintenance_due`.

### zmapping — Zone room temperature sensor mapping

Used by: GG=0x03 RR=0x0013 (`room_temperature_zone_mapping`)

| Value | ebusd | Helianthus | Notes |
|-------|-------|-----------|-------|
| 0 | none | none *(not implemented)* | No room sensor assigned |
| 1 | VRC700 | regulator *(not implemented)* | Built-in sensor of the /f split regulator (wireless UI + base station). Same hardware class as VR91 with added UI firmware |
| 2 | VR91_1 | thermostat_1 *(not implemented)* | External RF temperature/humidity sensor + UI endpoint |
| 3 | VR91_2 | thermostat_2 *(not implemented)* | Second VR91 sensor |
| 4 | VR91_3 | thermostat_3 *(not implemented)* | Third VR91 sensor |

Note: ebusd uses hardware model names (VRC700, VR91). Helianthus uses user-facing names since VRC700 and VR91 are functionally the same (RF temperature/humidity sensor + UI) — the VRC700 is the /f regulator's wireless display unit which IS a VR91 with extra UI firmware. Currently used internally to resolve associated circuit, not exposed in semantic output. Proposed: expose as `zones[].config.room_sensor_mapping` string enum.

### mamode — Multi-relay setting

Used by: GG=0x00 RR=0x004D

| Value | ebusd | Helianthus |
|-------|-------|-----------|
| 0 | circulation | circulation *(not implemented)* |
| 1 | dryer | dryer *(not implemented)* |
| 2 | zone | zone *(not implemented)* |
| 3 | legiopump | legionella_pump *(not implemented)* |

Note: Not yet exposed in semantic layer. Proposed: expose as `system.config.multi_relay_mode` string enum.

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
| 0x0015 | paralell_tank_loading_allowed | (not at this address) | CSV value-matching false positive. ebusd places HwcParallelLoading at 0x000A. 0x0015 purpose unknown. |

One pending:

| RR | myPyllant CSV leaf | TSP name | Status |
|----|-------------------|----------|--------|
| 0x0024 | hybrid_control_strategy (BIVALENCE_POINT) | BackupBoiler | Pending. TSP puts HybridManager at 0x000F. |

---

## Sources

- **BASV2 constraint catalog** (`b524_constraints.go`) — Downloaded from hardware via constraint probe. **Authoritative** for value ranges. Uses byte-swapped Record addressing (endianness convention).
- **ebusd community TSP** (`15.ctlv2.tsp`) — Community-maintained register definitions using `@ext(RR, 0)` addressing. **Highest authority** for register↔name mapping where coverage exists. Covers GG=0x00, 0x01, 0x02 (partial), 0x03. No coverage for GG=0x04, 0x05.
- **myVaillant register map CSV** (`myvaillant_register_map.csv`) — Helianthus-curated mapping built by value-matching live B524 reads against myPyllant cloud API field values. 115 entries across groups 0x00-0x05. **NOT a Vaillant-published source** — carries false-positive risk where multiple registers share the same value (see Mapping Conflicts).
- **Gateway production code** (`semantic_vaillant.go`) — Authoritative for which registers are actively polled and how they map to semantic planes.
- **Live B524 scan** (2026-03-04) — MCP RPC reads from BASV2 via Helianthus gateway.
- **VRC Explorer full group scan** — Raw register data for GG=0x02-0x0C across all instances. FLAGS byte (response payload byte[0]) used for access/writability verification of Cat column.

### FLAGS Verification Summary

Category corrections applied from VRC Explorer FLAGS analysis (GG=0x02, 0x03):

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

Notable FLAGS-confirmed assignments (no change needed):
- GG=0x02 0x0002 (heating_circuit_type): FLAGS=0x03 (user RW), kept as P — writable but used as immutable discovery probe in Helianthus
- GG=0x03 0x001C (zone_index): FLAGS=0x01 (stable RO), kept as P — presence marker

Registers without FLAGS data: all of GG=0x00 and GG=0x01 (not yet scanned by `b524_grab_op.py`).

## Related Files

- `_work_register_mapping/mypyllant_b524_system_mapping.json` — Original mapping analysis with confidence ratings (historical)
- `_work_register_mapping/B524/` — Raw VRC Explorer scan data per group
- `helianthus-ebusreg/vaillant/system/b524_profile.go` — Discovery profiles
- `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/15.ctlv2.tsp` — ebusd TSP source
- `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/_templates.tsp` — ebusd enum definitions
