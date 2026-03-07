# Vaillant B524 Extended Register Map

> **Status:** Authoritative reference. Single source of truth for B524 register semantics in Helianthus.
>
> **Last updated:** 2026-03-05 (v4 — MCP proof scan: 5500 probes, 2751 valid registers, dual-namespace discovery, 100+ new registers, radio device identification)
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

The instance is **not** echoed in the response — the gateway correlates replies using the original request parameters.

**Short responses:** A response payload shorter than 4 bytes is **not** a successful register read. Treat as unsupported/wrong-route/write-ack. A single-byte `0x00` has been observed for incorrect telegram routing (wrong opcode or group defaults — ebusd reports `invalid position … / 00`). Write operations may return short acknowledgements rather than value-bearing replies.

### FLAGS Byte (Response Header)

The FLAGS byte in the response header encodes register access mode. Discovered via VRC Explorer full-group B524 scans (`_work_register_mapping/B524/`), verified against ebusd TSP r/rw annotations (89% agreement, 48/54 match).

| FLAGS | Bit 1 (writable) | Bit 0 (sub-cat) | Access | Category | Description |
|-------|-------------------|------------------|--------|----------|-------------|
| `0x00` | 0 | 0 | RO | State (volatile) | Changes frequently — external pushes, counters |
| `0x01` | 0 | 1 | RO | State (stable) | Computed outputs, sensor readings, properties |
| `0x02` | 1 | 0 | RW | Config (technical) | Offsets, thresholds, numeric ranges |
| `0x03` | 1 | 1 | RW | Config (user-facing) | Modes, schedules, names, setpoints |

**Opcode-specific behavior:** Opcode 0x06 remote read (`OC=0x06, OT=0x00`) is heavily RO — across all groups, remote access exposes far fewer writable registers. When it does allow writes, they are always FLAGS=0x02 (technical), never 0x03 (user-facing). All user-configurable settings are exclusively on the opcode 0x02 local path.

**Coverage:** FLAGS data complete for all groups from MCP proof scan 2026-03-05 (5500 probes). FLAGS column populated for every responsive register across GG=0x00-0x05, 0x08, 0x09, 0x0A, 0x0C.

### Wire Type Encoding

| Wire | Encoding | Size | Notes |
|------|----------|------|-------|
| `u8` | Unsigned byte | 1 byte | Boolean-range values and small enums. ebusd `onoff`/`yesno` (UCH) |
| `u16` | Little-endian uint16 | 2 bytes | Primary integer type. ebusd may decode only low byte for some enums (e.g. `mctype;IGN:1`) |
| `u32` | Little-endian uint32 | 4 bytes | Energy counters, pump hours/starts |
| `f32` | Little-endian IEEE 754 float32 | 4 bytes | Primary numeric type for temperatures, pressures, percentages |
| `string` | Null-terminated C string | Variable | Zone names, installer info |
| `bytes` | Raw byte sequence | Variable | Opaque payload, not decoded as numeric |
| `date` | BCD-encoded `DD MM YY` | 3 bytes | Year = 2000 + YY. See constraint type `0x0C` in GetExtendedRegisters |
| `time` | BCD-encoded `HH MM [SS]` | 2-3 bytes | 2 bytes (HH:MM) for timers, 3 bytes (HH:MM:SS) for system clock |

### Opcode Routing

> **Verified 2026-03-05** via MCP proof scan (5500 calls, 2751 valid). See `_work_register_mapping/B524/proof_2026-03-05/`.

| Opcode | Name | Groups | Notes |
|--------|------|--------|-------|
| `0x02` | Local | 0x00-0x05, 0x08 | Controller-local registers |
| `0x06` | Remote | 0x08, 0x09, 0x0A, 0x0C | Room sensor / remote device registers |

**Dual-namespace groups:** GG=0x08, 0x09, 0x0A respond to **both** opcodes with **different data**. Opcode 0x02 returns local configuration (sensor slots, schedules, serial numbers). Opcode 0x06 returns live remote data (temperatures, humidity, device status). The two namespaces share no register addresses — they are independent address spaces selected by opcode. GG=0x0C responds only to 0x06 (no local config namespace).

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
| **Cat** | **S**=state (RO), **C**=config (RW), **P**=property (RO, stable), **E**=energy (RO, counter), **—**=unknown/unclassified. Verified against observed FLAGS where scan data exists |
| **Wire** | On-wire encoding: `u8`, `u16`, `u32`, `f32`, `string`, `date`, `time`, `bytes`. All multi-byte integers are little-endian |
| **Decode** | Semantic interpretation: `bool`, `°C`, `K`, `bar`, `%`, `kWh`, `hrs`, `min`, `count`, `enum`, `text`, `date`, `time`, `state`, `raw`, `—` (unknown) |
| **ebusd** | ebusd community TSP name. `—` = not in TSP |
| **Constraint** | From BASV2 constraint catalog (authoritative, downloaded from hardware). `—` = no catalog entry |
| **Values** | Enum mapping. Inline for ≤3 values, otherwise `→enum_name` referencing [Enum Reference](#enum-reference) |
| **Gates** | Condition for register to be present/meaningful. `—` = always available |
| **Semantic** | MCP semantic field path. **S** prefix = actively polled by gateway |

**Source annotations** (in Notes):
- No annotation = confirmed by multiple independent sources (ebusd + gateway + scan)
- `†` = CSV value-matched only, not independently confirmed (false-positive risk)
- `ebusd: "..."` = ebusd community note about this register (e.g., special value meanings)

---

## Group Topology

| GG | Name | Instanced | II Range | Opcode | Regs (scan) | Semantic Planes |
|----|------|-----------|----------|--------|-------------|-----------------|
| 0x00 | System/Regulator | No | 0x00 | 0x02 | 179 (0x0001-0x00FF) | system, energy_totals, boiler_status (partial) |
| 0x01 | DHW | No | 0x00 | 0x02 | 17 (0x0001-0x0013) | dhw |
| 0x02 | Heating Circuits | Yes | 0x00-0x0A | 0x02 | 291 (26/inst, 11 inst) | circuits, boiler_status (partial) |
| 0x03 | Zones | Yes | 0x00-0x0A | 0x02 | 416 (38/inst, 11 inst) | zones |
| 0x04 | Solar Circuit | No | 0x00 | 0x02 | 10 (0x0001-0x000B) | solar (gated) |
| 0x05 | Cylinders | Yes | 0x00-0x01 | 0x02 | 8 (4/inst, 2 inst) | cylinders (gated) |
| 0x08 | Buffer/Solar Cylinder 2 | Yes | 0x00 (local), 0x00-0x0A (remote) | **0x02 + 0x06** | 7 local + 44 remote | — |
| 0x09 | Radio Sensors (VRC7xx) | Yes | 0x00-0x0A | **0x02 + 0x06** | 165 local + 352 remote | — |
| 0x0A | Radio Sensors (VR92) | Yes | 0x00-0x0A | **0x02 + 0x06** | 759 local + 338 remote | — |
| 0x06 | Programs/Timetables | — | — | 0x0B | — | — |
| 0x07 | Programs/Timetables | — | — | 0x0B | — | — |
| 0x0C | Remote Accessories / functional-module slots | Yes | 0x00-0x0A | 0x06 only | 165 (15/inst) | — |

**GG=0x08 — Buffer/Solar Cylinder 2:** Dual-opcode confirmed by scan. Local (0x02): 7 singleton registers — cylinder max setpoint, charge hysteresis/offset, two NaN temperatures, pump status. Remote (0x06): 4 registers per instance across all 11 instances — likely buffer-tank sensor data. Constraint catalog has 6 entries matching GG=0x05 (cylinders) structure. ebusd does not define GG=0x08.

**Radio sensor groups (0x09, 0x0A):** Both support dual-namespace. The local namespace (0x02) stores per-slot configuration (sensor enable flags, temperature schedules, BASV2 serial number fragments). The remote namespace (0x06) stores live data from paired radio devices (temperature, humidity, device type, firmware version). Instance II selects the sensor slot (II=0x00 = slot 0, up to II=0x0A = slot 10).

**GG=0x0C — Remote Accessories / functional-module slots:** Responds only to opcode 0x06 (remote data). No local config namespace. 15 registers per instance. Uses the same remote-device slot schema as GG=0x09/0x0A. In the current lab, `II=0x01` with `device_class_address=0x26` correlates to the eBUS-identified `VR_71` hardware at slave address `0x26`, but that family identification comes from eBUS identity correlation rather than from B524 alone.

**Discovery:** Directory probe (`opcode=0x00`) is unreliable for GG=0x05 (terminator quirk). Use static topology. Multi-instance groups: scan all instances up to II=0x0A, expose only active ones.

### Discovery Profiles (ebusreg)

Source: `helianthus-ebusreg/vaillant/system/b524_profile.go`

| Group | Opcode | Instance Max | Register Max | Scan Observed Max | Notes |
|-------|--------|-------------|-------------|-------------------|-------|
| 0x00 | 0x02 (local) | 0x00 | 0x00A2 | **0x00FF** | System/Regulator. Singleton. **Code stale**: profile says 0x00A2 but 179 registers extend to 0x00FF. TODO: fix in ebusreg |
| 0x01 | 0x02 (local) | 0x00 | 0x0011 | **0x0013** | DHW. Singleton. 4 undocumented registers 0x0007-0x0013. TODO: fix in ebusreg |
| 0x02 | 0x02 (local) | 0x0A | 0x0025 | 0x0025 | Heating circuits. **Code is stale** (`b524_profile.go` says 0x0021, should be 0x0025). TODO: fix in ebusreg |
| 0x03 | 0x02 (local) | 0x0A | 0x002F | **0x002E** | Zones. Scan confirms 38 regs/instance. Profile accurate |
| 0x04 | 0x02 (local) | 0x00 | 0x000B | 0x000B | Solar circuit. Singleton, gated by fm5_config≤2 |
| 0x05 | 0x02 (local) | 0x01 | 0x0004 | 0x0004 | Cylinders. **Only 2 instances** (0x00-0x01), not 0x0A. Gated by fm5_config≤2 |
| 0x08 | 0x02 (local) | 0x00 | — | **0x0007** | Buffer/Solar Cylinder 2. Singleton config. **NEW** |
| 0x08 | 0x06 (remote) | 0x0A | — | **0x0004** | Buffer/Solar Cylinder 2. 4 regs/instance. **NEW** |
| 0x09 | 0x02 (local) | 0x0A | — | **0x000F** | Radio sensors VRC7xx. 15 regs/instance. **NEW** (dual-namespace) |
| 0x09 | 0x06 (remote) | 0x0A | 0x002F | **0x0030** | Radio sensors VRC7xx. 32 regs/instance |
| 0x0A | 0x02 (local) | 0x0A | — | **0x004D** | Radio sensors VR92. 69 regs/instance. **NEW** (dual-namespace) |
| 0x0A | 0x06 (remote) | 0x0A | 0x003F | **0x0035** | Radio sensors VR92. 32 regs/instance |
| 0x0C | 0x06 (remote) | 0x0A | 0x003F | **0x002F** | Remote misc. 15 regs/instance. No local namespace |

---

## Gate Conditions (Quick Reference)

Several registers are conditionally available based on system configuration. Gates are also annotated per-register in the group tables below.

| Gate | Source Register | Controls |
|------|----------------|----------|
| `hwc_enabled` | GG=0x01 RR=0x0001 | DHW registers in GG=0x01, HWC-related config in GG=0x00 |
| `fm5_config` | GG=0x00 RR=0x002F | Solar registers (GG=0x04, GG=0x05), `solar_flow_rate_quantity` |
| `circuit_type` | GG=0x02 RR=0x0002 | Per-circuit: heating regs (type=1), fixed_value regs (type=2), return_increase regs (type=4) |
| `cooling_enabled` | GG=0x02 RR=0x0006 | Cooling-related config in circuits and zones. Required for dew point functions (see below) |
| `room_temp_control_mode` | GG=0x02 RR=0x0015 | Dew point monitoring requires `cooling_enabled=true` AND `room_temp_control_mode != off` |
| `ext_hwc_active` | GG=0x02 RR=0x0018 | External HWC temp/mode |

**Rule:** Gated-off registers are omitted from semantic plane responses. Explicit queries to gated-off registers return an error with gate status explanation.

---

## GG=0x00 — System/Regulator

All registers use opcode `0x02`, instance `0x00`.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | dhw_bivalence_point | C | f32 | °C | — | -20..50 step 1 | — | — | **S** `system.config.dhw_bivalence_point` | FLAGS=0x02 |
| 0x0002 | continuous_heating_start_setpoint | C | f32 | °C | ContinuousHeating | -26..10 step 1 | — | — | | FLAGS=0x03. ebusd: `-26=off` disables function |
| 0x0003 | frost_override_time | C | u16 | hrs | FrostOverRideTime | 0..12 step 1 | — | — | | FLAGS=0x03 |
| 0x0004 | maximum_preheating_time | C | u16 | min | — | 0..300 step 10 | — | — | | FLAGS=0x03. † |
| 0x0007 | system_off | C | u8 | bool | — | — | `0=off 1=on` | — | **S** `system.state.system_off` | FLAGS=0x03 (user RW). System on/off switch, not a sensor reading |
| 0x0008 | temporary_allow_backup_heater | C | u8 | bool | — | — | — | — | | † |
| 0x0009 | external_energy_management_activation | C | u8 | bool | — | — | `0=off 1=on` | — | | FLAGS=0x02 (technical RW). MCP scan: 1 byte. † |
| 0x000A | parallel_tank_loading_allowed | C | u16 | bool | HwcParallelLoading | — | →onoff | — | | ebusd confirmed at `@ext(0xa,0)` |
| 0x000B | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 0. Near boolean cluster |
| 0x000E | max_room_humidity | C | u16 | % | MaxRoomHumidity | — | — | — | **S** `system.config.max_room_humidity` | |
| 0x000F | (unknown) | — | u16 | — | — | — | — | — | | Possibly HybridManager per TSP |
| 0x0010 | (unknown) | — | u16 | — | — | — | — | — | | Near config cluster |
| 0x0011 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 16. Possible temp threshold |
| 0x0012 | continuous_heating_room_setpoint | C | u16 | °C | — | — | — | — | | Confirmed exact, value=20 |
| 0x0014 | adaptive_heating_curve | C | u8 | bool | AdaptHeatCurve | — | →yesno | — | **S** `system.config.adaptive_heating_curve` | FLAGS=0x03 (user RW). MCP validated 1-byte |
| 0x0015 | (unknown) | — | u16 | — | — | — | — | — | | False positive in CSV (was `parallel_tank_loading`; actual is at 0x000A) |
| 0x0017 | dhw_maximum_loading_time | C | u16 | min | MaxCylinderChargeTime | — | — | hwc_enabled | | |
| 0x0018 | hwc_lock_time | C | u16 | min | HwcLockTime | — | — | hwc_enabled | | |
| 0x0019 | solar_flow_rate_quantity | C | f32 | — | — | — | — | fm5_config≤2 | | See [Mapping Conflicts](#mapping-conflicts) |
| 0x001B | pump_additional_time | C | u16 | min | PumpAdditionalTime | — | — | — | | |
| 0x001C | dhw_maximum_temperature | C | f32 | °C | — | — | — | — | | † |
| 0x001E | (unknown) | — | u8 | — | — | — | — | — | | Scan value: 1. Possible pump/flag |
| 0x0022 | alternative_point | C | f32 | °C | — | — | — | — | **S** `system.config.alternative_point` | -21..40 per TSP |
| 0x0023 | heating_circuit_bivalence_point | C | f32 | °C | — | — | — | — | **S** `system.config.heating_circuit_bivalence_point` | -20..30 per TSP |
| 0x0024 | backup_heater_mode | C | u16 | enum | — | — | values unknown | — | | See [Mapping Conflicts](#mapping-conflicts) |
| 0x0025 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 0 |
| 0x0026 | hc_emergency_temperature | C | f32 | °C | — | — | — | — | **S** `system.config.hc_emergency_temperature` | 20..80 per TSP |
| 0x0027 | dhw_hysteresis | C | f32 | K | CylinderChargeHyst | — | — | hwc_enabled | | 3..20 step 0.5 per TSP |
| 0x0029 | hwc_storage_charge_offset | C | f32 | K | CylinderChargeOffset | — | — | hwc_enabled | | 0..40 per TSP |
| 0x002A | hwc_legionella_time | C | time | time | — | — | — | hwc_enabled | | HH:MM |
| 0x002B | is_legionella_protection_activated | C | u16 | enum | — | — | `0=off 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun` | hwc_enabled | | Day-of-week selector. 0=disabled |
| 0x002C | maintenance_date | P | date | date | MaintenanceDate | — | — | — | | |
| 0x002D | offset_outside_temperature | C | f32 | K | — | — | — | — | | -3..3 step 0.5 per TSP |
| 0x002F | module_configuration_vr71 | P | u16 | count | — | — | — | — | **S** `system.properties.module_configuration_vr71` | 1..11 |
| 0x0031 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 0 |
| 0x0034 | system_date | S | date | date | Date | — | — | — | | BCD |
| 0x0035 | system_time | S | time | time | Time | — | — | — | | HH:MM:SS |
| 0x0036 | system_scheme | P | u16 | count | HydraulicScheme | — | — | — | **S** `system.properties.system_scheme` | 1..16 |
| 0x0038 | cooling_outside_temperature_threshold | C | f32 | °C | — | — | — | — | | 10..30 per TSP |
| 0x0039 | system_water_pressure | S | f32 | bar | WaterPressure | — | — | — | **S** `system.state.system_water_pressure` | Read-only |
| 0x003A | dew_point_offset | C | f32 | K | — | — | — | — | | -10..10 per TSP |
| 0x003D | solar_yield_total | E | u32 | kWh | SolarYieldTotal | — | — | fm5_config≤2 | | |
| 0x003E | environmental_yield_total | E | u32 | kWh | YieldTotal | — | — | — | | |
| 0x0045 | esco_block_function | C | u16 | enum | — | — | values unknown | — | | |
| 0x0046 | hwc_max_flow_temp_desired | C | f32 | °C | HwcMaxFlowTempDesired | — | — | — | **S** `system.config.hwc_max_flow_temp_desired` | 15..80 per TSP |
| 0x0048 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 1 |
| 0x004B | system_flow_temperature | S | f32 | °C | SystemFlowTemp | — | — | — | **S** `system.state.system_flow_temperature`, `boiler_status.state.flow_temperature` | Read-only |
| 0x004D | multi_relay_setting | C | u16 | enum | MultiRelaySetting | — | →mamode | — | | |
| 0x004E | fuel_consumption_heating_this_month | E | u32 | kWh | PrFuelSumHcThisMonth | — | — | — | | |
| 0x004F | energy_consumption_heating_this_month | E | u32 | kWh | PrEnergySumHcThisMonth | — | — | — | | |
| 0x0050 | energy_consumption_dhw_this_month | E | u32 | kWh | PrEnergySumHwcThisMonth | — | — | — | | |
| 0x0051 | fuel_consumption_dhw_this_month | E | u32 | kWh | PrFuelSumHwcThisMonth | — | — | — | | |
| 0x0052 | fuel_consumption_heating_last_month | E | u32 | kWh | PrFuelSumHcLastMonth | — | — | — | | |
| 0x0053 | energy_consumption_heating_last_month | E | u32 | kWh | PrEnergySumHcLastMonth | — | — | — | | |
| 0x0054 | energy_consumption_dhw_last_month | E | u32 | kWh | PrEnergySumHwcLastMonth | — | — | — | | |
| 0x0055 | fuel_consumption_dhw_last_month | E | u32 | kWh | PrFuelSumHwcLastMonth | — | — | — | | |
| 0x0056 | fuel_consumption_heating_total | E | u32 | kWh | PrFuelSumHc | — | — | — | **S** `energy_totals.gas.climate` | |
| 0x0057 | energy_consumption_heating_total | E | u32 | kWh | PrEnergySumHc | — | — | — | **S** `energy_totals.electric.climate` | |
| 0x0058 | energy_consumption_dhw_total | E | u32 | kWh | PrEnergySumHwc | — | — | — | **S** `energy_totals.electric.dhw` | |
| 0x0059 | fuel_consumption_dhw_total | E | u32 | kWh | PrFuelSumHwc | — | — | — | **S** `energy_totals.gas.dhw` | |
| 0x005C | energy_consumption_total | E | u32 | kWh | PrEnergySum | — | — | — | | |
| 0x005D | fuel_consumption_total | E | u32 | kWh | PrFuelSum | — | — | — | | |
| 0x006C | installer_name_1 | P | string | text | Installer1 | — | — | — | | maxLength 6 |
| 0x006D | installer_name_2 | P | string | text | Installer2 | — | — | — | | maxLength 6 |
| 0x006F | installer_phone_1 | P | string | text | PhoneNumber1 | — | — | — | | maxLength 6 |
| 0x0070 | installer_phone_2 | P | string | text | PhoneNumber2 | — | — | — | | maxLength 6 |
| 0x0073 | outdoor_temperature | S | f32 | °C | DisplayedOutsideTemp | — | — | — | **S** `system.state.outdoor_temperature` | Read-only |
| 0x0076 | installer_menu_code | P | u16 | count | KeyCodeforConfigMenu | — | — | — | | 0..999 |
| 0x0081 | smart_photovoltaic_buffer_offset | P | f32 | K | — | — | — | — | | † |
| 0x0086 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 60. PV/smart cluster |
| 0x0089 | (unknown) | — | u16 | — | — | — | — | — | | Scan value: 15. PV/smart cluster |
| 0x008A | (unknown) | — | f32 | — | — | — | — | — | | Scan value: 1.0. PV/smart cluster |
| 0x008B | (unknown) | — | f32 | — | — | — | — | — | | Scan value: 90.0. PV/smart cluster, possible max flow temp |
| 0x0095 | outdoor_temperature_average24h | S | f32 | °C | OutsideTempAvg | — | — | — | **S** `system.state.outdoor_temperature_avg24h` | Rounded avg updated every 3h |
| 0x0096 | maintenance_due | S | u8 | bool | MaintenanceDue | — | →yesno | — | **S** `system.state.maintenance_due` | FLAGS=0x01 (stable RO). MCP validated 1-byte |
| 0x009A | green_iq | S | u16 | bool | — | — | — | — | | |
| 0x009D | hwc_cylinder_temperature_top | S | f32 | °C | HwcStorageTempTop | — | — | — | **S** `system.state.hwc_cylinder_temperature_top` | Read-only |
| 0x009E | hwc_cylinder_temperature_bottom | S | f32 | °C | HwcStorageTempBottom | — | — | — | **S** `system.state.hwc_cylinder_temperature_bottom` | Read-only |
| 0x009F | hc_cylinder_temperature_top | S | f32 | °C | HcStorageTempTop | — | — | — | | Read-only |
| 0x00A0 | hc_cylinder_temperature_bottom | S | f32 | °C | HcStorageTempBottom | — | — | — | | Read-only |
| 0x00A2 | buffer_charge_offset | C | f32 | K | — | — | — | — | | 0..15 per TSP |
| 0x003C | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x0047 | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0 |
| 0x004A | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x005E | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0. Near energy counters |
| 0x005F | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x0060 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 2 |
| 0x0061 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x0065 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. Scan value: 0 |
| 0x0067 | vr70_module_status_1 | S | f32 | — | — | — | — | — | | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 1" |
| 0x0068 | vr70_module_status_2 | S | f32 | — | — | — | — | — | | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 2" |
| 0x006A | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. Scan value: 1 |
| 0x0075 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0. Near installer_menu_code cluster |
| 0x0077 | (unknown) | C | u8 | bool | — | — | — | — | | FLAGS=0x03. Scan value: 1 |
| 0x007E | (unknown) | C | f32 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0.0 |
| 0x0080 | (unknown) | C | f32 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0.0. Constraint: -10..10 step 1. Possibly PV offset |
| 0x0085 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. NaN |
| 0x008C | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0. Near PV/smart cluster |
| 0x008D | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x008E | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x008F | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x0097 | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0. Near maintenance cluster |
| 0x0098 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x009B | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0. Near green_iq |
| 0x00A1 | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0. Between cylinder temps and buffer_charge_offset |
| 0x00A5 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00AB | (unknown) | C | u8 | bool | — | — | — | — | | FLAGS=0x02. Scan value: 1 |
| 0x00AF | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00B0 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00B1 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00B2 | (unknown) | C | u16 | raw | — | — | — | — | | FLAGS=0x02. Scan value: 0xBDA9 (48553). Possibly firmware hash |
| 0x00B3 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x02. Scan value: 0 |
| 0x00B5 | (unknown) | P | u8 | bool | — | — | — | — | | FLAGS=0x01. Scan value: 1 |
| 0x00B6 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x00B8 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x00B9 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0. Energy/counter region start |
| 0x00BA | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00BB | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00BC | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00BD | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00BF | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00C0 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00C1 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=6. Energy sub-counter cluster start |
| 0x00C2 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=1 |
| 0x00C3 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=2 |
| 0x00C4 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=6 |
| 0x00C5 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=0 |
| 0x00C6 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=122. Matches energy_heating_total (0x0057)=122 |
| 0x00C7 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=1 |
| 0x00C8 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=470. Matches fuel_heating_total (0x0056)=470 |
| 0x00C9 | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=203 |
| 0x00CA | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=267. Close to PrFuelSumHcLastMonth=266 |
| 0x00CB | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=471 |
| 0x00CC | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=0 |
| 0x00CD | (unknown_energy_counter) | P | u32 | kWh | — | — | — | — | | FLAGS=0x01. Scan u32=471. Same as 0x00CB — total? |
| 0x00CE | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00CF | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D0 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D1 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D2 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00D3 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00D4 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00D5 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00D6 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D7 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D8 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00D9 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. Scan value: 0 |
| 0x00DA | (unknown) | C | date | date | — | — | — | — | | FLAGS=0x02. Scan: 01.01.2013 (BCD default) |
| 0x00DB | (unknown) | C | date | date | — | — | — | — | | FLAGS=0x02. Scan: 01.01.2013 (BCD default) |
| 0x00DD | heating_curve_day_1 | C | bytes | schedule | — | — | — | — | | FLAGS=0x03. 10 bytes: [25,30,35,40,45,45,45,45,45,45] — hourly temp profile (°C/2) |
| 0x00DE | heating_curve_day_2 | C | bytes | schedule | — | — | — | — | | FLAGS=0x03. 10 bytes: [45,45,40,35,30,25,10,10,10,10] — hourly temp profile continued |
| 0x00DF | heating_curve_day_3 | C | bytes | schedule | — | — | — | — | | FLAGS=0x03. 9 bytes: [10,10,10,30,35,40,45,35,25] — hourly temp profile end. 29 values total across DD-DF |
| 0x00E0 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0.0 |
| 0x00E3 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E4 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E5 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E6 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E7 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E8 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00E9 | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00EA | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00EB | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00EC | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00ED | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00EE | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0.0 |
| 0x00EF | (unknown_temp_config) | C | f32 | °C | — | — | — | — | | FLAGS=0x03. Scan value: 20.0. Temperature setpoint |
| 0x00F0 | (unknown) | P | u16 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F1 | (unknown) | P | u16 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F2 | (unknown_holiday_start_1) | C | date | date | — | — | — | — | | FLAGS=0x03. Scan: 01.01.2015 (BCD) |
| 0x00F3 | (unknown_holiday_end_1) | C | date | date | — | — | — | — | | FLAGS=0x03. Scan: 01.01.2015 (BCD) |
| 0x00F4 | (unknown_holiday_start_2) | C | date | date | — | — | — | — | | FLAGS=0x03. Scan: 00.00.2000 (BCD reset) |
| 0x00F5 | (unknown_holiday_end_2) | C | date | date | — | — | — | — | | FLAGS=0x03. Scan: 00.00.2000 (BCD reset) |
| 0x00F6 | (unknown_temp_config) | C | f32 | °C | — | — | — | — | | FLAGS=0x03. Scan value: 10.0 |
| 0x00F7 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x00F8 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0. ebusd TSP hinted 5-byte — scan sees 1 byte |
| 0x00F9 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. Scan value: 0 |
| 0x00FA | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x02. Scan value: 0 |
| 0x00FB | (unknown_temp_config) | C | f32 | °C | — | — | — | — | | FLAGS=0x03. Scan value: 10.0 |
| 0x00FC | (unknown_max_flow_temp) | P | f32 | °C | — | — | — | — | | FLAGS=0x01. Scan value: 90.0. Likely max flow temperature |
| 0x00FE | (unknown_temp_config) | C | f32 | °C | — | — | — | — | | FLAGS=0x03. Scan value: 13.0 |
| 0x00FF | (unknown_temp_config) | C | f32 | °C | — | — | — | — | | FLAGS=0x03. Scan value: 25.0 |

**Note:** 100 new registers discovered in the 0x003C-0x00FF range by MCP proof scan 2026-03-05. The 0x00C1-0x00CD cluster contains u32 energy counters (decode as u32, NOT f32 — the tiny float values like 6.586e-43 are mis-decoded u32 integers). The 0x00DD-0x00DF cluster contains packed hourly temperature schedule bytes. The 0x00E3-0x00EE cluster (13 consecutive f32=0.0 with FLAGS=0x01) may be per-month energy statistics. The 0x00F2-0x00F5 cluster contains holiday date pairs.

---

## GG=0x01 — DHW

All registers use opcode `0x02`, instance `0x00`. All registers except `hwc_status` (0x000F) are gated by `hwc_enabled` (0x0001).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | hwc_enabled | C | u16 | bool | — | 0..1 | `0=off 1=on` | — | | Gate register for GG=0x01. Constraint tag u16, MCP verified 2-byte |
| 0x0002 | hwc_circulation_pump_status | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | | Constraint tag u8 |
| 0x0003 | operation_mode_dhw | C | u16 | enum | HwcOpMode | 0..2 | →opmode | hwc_enabled | **S** `dhw.operating_mode` | |
| 0x0004 | dhw_target_temperature | C | f32 | °C | HwcTempDesired | 35..70 | — | hwc_enabled | **S** `dhw.desired_temperature` | |
| 0x0005 | current_dhw_temperature | S | f32 | °C | HwcStorageTemp | 0..99 | — | hwc_enabled | **S** `dhw.current_temperature` | Read-only |
| 0x0006 | hwc_reheating_active | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | | Constraint tag u8 |
| 0x0008 | hwc_flow_temperature_desired | S | f32 | °C | HwcFlowTemp | — | — | hwc_enabled | | Read-only |
| 0x0009 | hwc_holiday_start_date | C | date | date | HwcHolidayStartPeriod | — | — | hwc_enabled | | |
| 0x000A | hwc_holiday_end_date | C | date | date | HwcHolidayEndPeriod | — | — | hwc_enabled | | |
| 0x000B | hwc_bank_holiday_start | C | date | date | HwcBankHolidayStartPeriod | — | — | hwc_enabled | | ebusd confirmed |
| 0x000C | hwc_bank_holiday_end | C | date | date | HwcBankHolidayEndPeriod | — | — | hwc_enabled | | ebusd confirmed |
| 0x000D | hwc_special_function_mode | C | u8 | enum | HwcSFMode | — | →sfmode | hwc_enabled | **S** `dhw.state` | FLAGS=0x03 (user RW). MCP validated 1-byte |
| 0x000F | hwc_status | S | u16 | state | — | — | — | — | | Not gated |
| 0x0010 | hwc_holiday_start_time | C | time | time | — | — | — | hwc_enabled | | |
| 0x0011 | hwc_holiday_end_time | C | time | time | — | — | — | hwc_enabled | | |
| 0x0007 | (unknown) | C | u8 | — | — | — | — | hwc_enabled | | FLAGS=0x03. Scan value: 0 |
| 0x000E | (unknown) | P | u8 | bool | — | — | — | — | | FLAGS=0x01. Scan value: 1. Near hwc_status, possibly active flag |
| 0x0012 | (unknown) | C | u8 | — | — | — | — | hwc_enabled | | FLAGS=0x03. Scan value: 0 |
| 0x0013 | (unknown) | C | u8 | — | — | — | — | hwc_enabled | | FLAGS=0x03. Scan value: 0 |

---

## GG=0x02 — Heating Circuits (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active circuits discovered by probing `heating_circuit_type` (RR=0x0002) — value `0` (`mctype=inactive`) indicates unused circuit slot. Absent instances (beyond the highest configured slot) return empty/null response (no valid payload from bus). Verified via MCP: II=0,1 return mctype=1 (heating), II=2-9 return mctype=0 (inactive), II=10 returns null (absent).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | (unknown) | — | u16 | — | — | 1..2 | — | — | | CSV says `heating_circuit_type` but gateway uses 0x0002. Purpose unverified. † |
| 0x0002 | heating_circuit_type | P | u16 | enum | Hc{hc}CircuitType | 0..4 | →mctype | — | **S** `circuits[].properties.heating_circuit_type` | Discovery probe. Also `mixer_circuit_type_external` |
| 0x0003 | room_influence_type | C | u8 | enum | Hc{hc}RoomInfluenceType | — | `0=inactive 1=active 2=extended` | — | | Controls room sensor influence on heating curve. Not responsive on II=0x00 in VRC Explorer scan. See GetExtendedRegisters §4.2.5 for behavioral semantics |
| 0x0004 | target_return_temperature | C | f32 | °C | Hc{hc}ReturnTempDesired | 15..80 | — | circuit_type=4 (return_increase) | | Factory setting 30°C. jonesPD CTLV2 confirmed. Only meaningful for "Increase in return" circuits |
| 0x0005 | dew_point_monitoring_enabled | C | u8 | bool | — | 0..1 | `0=off 1=on` | cooling_enabled | | Constraint tag u8. ebusd onoff=UCH. † |
| 0x0006 | cooling_enabled | C | u8 | bool | Hc{hc}CoolingEnabled | 0..1 | `0=off 1=on` | — | **S** `circuits[].config.cooling_enabled` | Gate register. Constraint tag u8. ebusd onoff=UCH |
| 0x0007 | heating_circuit_flow_setpoint | S | f32 | °C | Hc{hc}FlowTempDesired | — | — | — | **S** `circuits[].state.heating_circuit_flow_setpoint` | Read-only |
| 0x0008 | current_circuit_flow_temperature | S | f32 | °C | Hc{hc}FlowTemp | — | — | — | **S** `circuits[].state.current_circuit_flow_temperature` | Read-only. Circuit flow sensor VF[x], NOT boiler return temperature |
| 0x0009 | ext_hwc_temperature_setpoint | C | f32 | °C | — | — | — | ext_hwc_active | | † |
| 0x000A | dew_point_offset | C | f32 | K | — | — | — | cooling_enabled | | † |
| 0x000B | flow_setpoint_excess_offset | C | f32 | K | Hc{hc}ExcessTemp | — | — | circuit_type=1 (heating) | | Flow temp increased by this value to keep mixing valve in control range |
| 0x000C | fixed_desired_temperature | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | | Fixed-value circuit target flow temp. † |
| 0x000D | fixed_setback_temperature | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | | Fixed-value circuit setback temp. † |
| 0x000E | set_back_mode_enabled | C | u16 | enum | Hc{hc}SetbackMode | — | →offmode | circuit_type=1 (heating) | | |
| 0x000F | heating_curve | C | f32 | — | Hc{hc}HeatCurve | — | — | — | **S** `circuits[].config.heating_curve` | Dimensionless ratio |
| 0x0010 | heating_flow_temp_max_setpoint | C | f32 | °C | Hc{hc}MaxFlowTempDesired | — | — | — | **S** `circuits[].config.heating_flow_temperature_maximum_setpoint` | 15..80 per ebusd |
| 0x0011 | cooling_flow_temp_min_setpoint | C | f32 | °C | Hc{hc}MinCoolingTempDesired | — | — | cooling_enabled | | |
| 0x0012 | heating_flow_temp_min_setpoint | C | f32 | °C | Hc{hc}MinFlowTempDesired | — | — | — | **S** `circuits[].config.heating_flow_temperature_minimum_setpoint` | |
| 0x0013 | ext_hwc_operation_mode | C | u16 | enum | — | — | values unknown | ext_hwc_active | | |
| 0x0014 | heat_demand_limited_by_outside_temp | C | f32 | °C | Hc{hc}SummerTempLimit | — | — | — | **S** `circuits[].config.heat_demand_limited_by_outside_temp` | Summer cutoff |
| 0x0015 | room_temperature_control_mode | C | u16 | enum | Hc{hc}RoomTempSwitchOn | — | →rcmode | — | **S** `circuits[].config.room_temperature_control_mode` | Gate for dew point |
| 0x0016 | screed_drying_day | C | u16 | count | Hc{hc}ScreedDryingDay | — | — | — | | Screed drying program |
| 0x0017 | screed_drying_desired_temperature | S | f32 | °C | Hc{hc}ScreedDryingTempDesired | — | — | — | | FLAGS=0x01 (stable RO) — computed setpoint, not user-configurable |
| 0x0018 | ext_hwc_active | S | u16 | bool | Hc{hc}ExternalHWCActive | — | — | — | | Gate register for ext HWC. FLAGS=0x00 (volatile RO) — status, not config |
| 0x0019 | external_heat_demand | S | u16 | state | Hc{hc}ExternalHeatDemand | — | — | — | | External heat source. FLAGS=0x00 (volatile RO) — status, not config |
| 0x001A | mixer_movement | S | f32 | % | Hc{hc}MixerMovement | — | — | — | | Signed float: `<0`=closing, `>0`=opening. MCP verified: -100.0 when fully closing. Read-only |
| 0x001B | circuit_state | S | u16 | state | Hc{hc}Status | — | — | — | **S** `circuits[].state.circuit_state` | Raw state code |
| 0x001C | epsilon | S | f32 | — | Hc{hc}HeatCurveAdaption | — | — | — | | Heat curve adaption factor. Dimensionless. Read-only |
| 0x001D | frost_protection_threshold | C | f32 | °C | Hc{hc}FrostProtThreshold | — | — | — | **S** `circuits[].properties.frost_protection_threshold` | FLAGS=0x02 (technical RW) — writable config, not property. Semantic path needs migration to `config.*` |
| 0x001E | pump_status | S | u16 | bool | Hc{hc}PumpStatus | — | — | — | **S** `circuits[].state.pump_status` | Also `boiler_status.state.pump_running` (II=0) |
| 0x001F | room_temperature_setpoint | C | f32 | °C | Hc{hc}RoomSetpoint | — | — | — | | |
| 0x0020 | calculated_flow_temperature | S | f32 | °C | Hc{hc}FlowTempCalc | — | — | — | **S** `circuits[].state.calculated_flow_temperature` | |
| 0x0021 | mixer_position_percentage | S | f32 | % | Hc{hc}MixerPosition | — | — | — | **S** `circuits[].state.mixer_position_percentage` | |
| 0x0022 | current_room_humidity | S | f32 | % | Hc{hc}Humidity | — | — | — | **S** `circuits[].state.current_room_humidity` | From room sensor |
| 0x0023 | dew_point_temperature | S | f32 | °C | Hc{hc}DewPointTemp | — | — | — | **S** `circuits[].state.dew_point_temperature` | |
| 0x0024 | pump_operating_hours | S | u32 | hrs | Hc{hc}PumpHours | — | — | — | **S** `circuits[].state.pump_operating_hours` | |
| 0x0025 | pump_starts_count | S | u32 | count | Hc{hc}PumpStarts | — | — | — | **S** `circuits[].state.pump_starts_count` | |

---

## GG=0x03 — Zones (multi-instance)

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones discovered by probing `zone_index` (RR=0x001C).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | cooling_operation_mode | C | u16 | enum | — | 0..2 | →opmode | cooling_enabled | | Same enum as heating_operation_mode |
| 0x0002 | cooling_set_back_temperature | C | f32 | °C | Zone{z}CoolingTemp | 15..30 step 0.5 | — | cooling_enabled | | |
| 0x0003 | holiday_start_date | C | date | date | Zone{z}HolidayStartPeriod | — | — | — | | |
| 0x0004 | holiday_end_date | C | date | date | Zone{z}HolidayEndPeriod | — | — | — | | |
| 0x0005 | holiday_setpoint | C | f32 | °C | Zone{z}HolidayTemp | 5..30 | — | — | | |
| 0x0006 | heating_operation_mode | C | u16 | enum | Zone{z}OpMode | 0..2 | →opmode | — | **S** (derived) `zones[].state.operating_mode` | |
| 0x0008 | quick_veto_temperature | C | f32 | °C | Zone{z}QuickVetoTemp | — | — | — | | Veto override target |
| 0x0009 | heating_set_back_temperature | C | f32 | °C | Zone{z}NightTemp | — | — | — | | Night setpoint |
| 0x000C | bank_holiday_start | C | date | date | Zone{z}BankHolidayStartPeriod | — | — | — | | ebusd confirmed |
| 0x000D | bank_holiday_end | C | date | date | Zone{z}BankHolidayEndPeriod | — | — | — | | ebusd confirmed |
| 0x000E | current_special_function | C | u8 | enum | Zone{z}SFMode | — | →sfmode | — | **S** (derived) `zones[].state.operating_mode` | FLAGS=0x03 (user RW). MCP validated 1-byte. Writable to set quickveto/away |
| 0x000F | current_room_temperature | S | f32 | °C | Zone{z}RoomTemp | — | — | — | **S** `zones[].state.current_temperature` | FLAGS=0x01 (stable RO). From room sensor |
| 0x0010 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03 (user RW). Discovered in VRC Explorer scan, not in ebusd/CSV |
| 0x0011 | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03 (user RW). Discovered in VRC Explorer scan, not in ebusd/CSV |
| 0x0012 | valve_status | S | u16 | bool | Zone{z}ValveStatus | — | `0=closed 1=open` | — | | FLAGS=0x01 (stable RO). Used for hvac_action derivation |
| 0x0013 | room_temperature_zone_mapping | C | u16 | enum | Zone{z}RoomZoneMapping | — | →zmapping | — | **S** `zones[].config.roomTemperatureZoneMapping` | Maps zone to room temperature sensor source. GraphQL exposes the raw numeric B524 enum directly (`0`, `1`, `2`, ...); `associatedCircuit` is resolved separately and is not an alias of this register |
| 0x0014 | heating_manual_mode_setpoint | S | f32 | °C | Zone{z}ActualRoomTempDesired | — | — | — | **S** `zones[].state.desired_temperature` (fallback) | FLAGS=0x01 (stable RO) — computed output, not user-settable. Current setpoint considering all conditions |
| 0x0015 | cooling_manual_mode_setpoint | S | f32 | °C | — | — | — | cooling_enabled | | FLAGS=0x01 (stable RO) — computed output, not user-settable |
| 0x0016 | zone_name | C | string | text | Zone{z}Shortname | — | — | — | **S** `zones[].name` | maxLength 6 |
| 0x0017 | zone_name_prefix | C | string | text | Zone{z}Name1 | — | — | — | | maxLength 5. Part 1 |
| 0x0018 | zone_name_suffix | C | string | text | Zone{z}Name2 | — | — | — | | maxLength 5. Part 2 |
| 0x0019 | heating_time_slot_active | S | u16 | bool | — | — | `0=off 1=on` | — | | Timer schedule flag |
| 0x001A | cooling_time_slot_active | S | u16 | bool | — | — | `0=off 1=on` | cooling_enabled | | Timer schedule flag |
| 0x001B | zone_status | S | u16 | state | — | — | — | — | | Raw zone status code |
| 0x001C | zone_index | P | bytes | raw | Zone{z}Index | — | — | — | **S** (discovery) | Presence marker |
| 0x001E | quick_veto_end_time | C | time | time | Zone{z}QuickVetoEndTime | — | — | — | | FLAGS=0x03 (user RW) — writable, can extend/set veto end time |
| 0x0020 | holiday_end_time | C | time | time | — | — | — | — | | |
| 0x0021 | holiday_start_time | C | time | time | — | — | — | — | | |
| 0x0022 | heating_desired_setpoint | C | f32 | °C | Zone{z}DayTemp | — | — | — | **S** `zones[].state.desired_temperature` (primary) | 15..30 step 0.5 per ebusd |
| 0x0023 | cooling_desired_setpoint | C | f32 | °C | — | — | — | cooling_enabled | | |
| 0x0024 | quick_veto_end_date | C | date | date | Zone{z}QuickVetoEndDate | — | — | — | | FLAGS=0x03 (user RW) — writable, can extend/set veto end date |
| 0x0026 | quick_veto_duration | C | f32 | hrs | Zone{z}QuickVetoDuration | — | — | — | | 0.5..12 step 0.5. Writing enables quick veto mode. |
| 0x0027 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x00 (volatile RO). Discovered in VRC Explorer scan |
| 0x0028 | current_room_humidity | S | f32 | % | — | — | — | — | **S** `zones[].state.current_room_humidity` | FLAGS=0x01 (stable RO). From room sensor |
| 0x0029 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002A | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002B | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002C | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002D | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |
| 0x002E | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x01 (stable RO). Discovered in VRC Explorer scan |

### Zone Mode Derivation

The `operating_mode` and `preset` exposed in the zones semantic plane are derived from:
- `heating_operation_mode` (0x0006): →opmode (Helianthus: 0=off, 1=auto, 2=manual)
- `current_special_function` (0x000E): →sfmode (Helianthus: 2=quickveto, 3/4=away)
- Associated circuit's `cooling_enabled` (GG=0x02 RR=0x0006): determines heat vs cool capability for the zone

---

## GG=0x04 — Solar Circuit

Entire group gated by `fm5_config ≤ 2`. All registers use opcode `0x02`, instance `0x00`.

**No ebusd coverage exists for GG=0x04** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | solar_enabled | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | | † |
| 0x0002 | solar_function_mode | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | | Not pump status (pump is at 0x0008). † |
| 0x0003 | collector_temperature | S | f32 | °C | — | -40..155 | — | fm5_config≤2 | | † |
| 0x0004 | delta_t_on_threshold | C | f32 | K | — | 0..99 | — | fm5_config≤2 | | Not storage temp. † |
| 0x0005 | max_collector_temperature | C | f32 | °C | — | 110..150 | — | fm5_config≤2 | | † |
| 0x0006 | max_cylinder_temperature_solar | C | f32 | °C | — | 75..115 | — | fm5_config≤2 | | Not collector shutdown. † |
| 0x0007 | solar_return_temperature | S | f32 | °C | — | — | — | fm5_config≤2 | | † |
| 0x0008 | solar_pump_active | S | u8 | bool | — | — | `0=off 1=on` | fm5_config≤2 | | † |
| 0x0009 | solar_yield_current | S | f32 | raw | — | — | — | fm5_config≤2 | | Current yield. † |
| 0x000B | solar_pump_hours | S | u32 | hrs | — | — | — | fm5_config≤2 | | Cumulative runtime. † |

---

## GG=0x05 — Cylinders (multi-instance)

Entire group gated by `fm5_config ≤ 2`. These are solar charging parameters per cylinder. General cylinder config (max temp, charge hysteresis) is in GG=0x00 system config.

**No ebusd coverage exists for GG=0x05** — all names are from value-matched CSV only (†) and carry false-positive risk.

Helianthus semantic publication rule:
- Raw config registers alone do **not** imply cylinder presence.
- A cylinder instance is published only when `RR=0x0004` (`cylinder_temperature`) yields a live decodable value for that instance.
- Config-only responses (`RR=0x0001..0x0003`) without temperature evidence must not create a semantic `cylinders[]` entry.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | cylinder_max_setpoint | C | f32 | °C | — | 0..99 | — | fm5_config≤2 | | † |
| 0x0002 | cylinder_charge_hysteresis | C | f32 | K | — | 2..25 | — | fm5_config≤2 | | † |
| 0x0003 | cylinder_charge_offset | C | f32 | K | — | 1..20 | — | fm5_config≤2 | | † |
| 0x0004 | cylinder_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2 | | † |

---

## GG=0x08 — Buffer/Solar Cylinder 2 (dual-opcode)

> **Verified 2026-03-05:** Responds to BOTH opcodes with different data.

### GG=0x08 Local Config (opcode 0x02)

Singleton (II=0x00 only). 7 registers. Structure mirrors GG=0x05 (Solar Cylinder 1) — same constraint catalog layout.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | cylinder2_max_setpoint | C | f32 | °C | — | 0..99 | — | fm5_config≤2? | | FLAGS=0x03. Scan value: 99.0 |
| 0x0002 | cylinder2_switch_off_diff | C | f32 | K | — | 0..99 | — | fm5_config≤2? | | FLAGS=0x03. Scan value: 0.0 |
| 0x0003 | cylinder2_charge_hysteresis | C | f32 | K | — | 2..25 | — | fm5_config≤2? | | FLAGS=0x03. Scan value: 12.0 |
| 0x0004 | cylinder2_charge_offset | C | f32 | K | — | 1..20 | — | fm5_config≤2? | | FLAGS=0x03. Scan value: 5.0 |
| 0x0005 | cylinder2_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | | FLAGS=0x01. NaN (no sensor) |
| 0x0006 | cylinder2_bottom_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | | FLAGS=0x01. NaN (no sensor) |
| 0x0007 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0. Possibly pump status |

### GG=0x08 Remote Data (opcode 0x06)

Instanced (II=0x00-0x0A). 4 registers per instance. All 11 instances respond.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. Scan value: 0. Status byte |
| 0x0002 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. Scan value: 0 |
| 0x0003 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. NaN on all instances |
| 0x0004 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. NaN on all instances |

---

## GG=0x09 — Radio Sensors, VRC7xx (multi-instance, dual-opcode)

> **Verified 2026-03-05:** Dual-namespace. Opcode 0x02 = local configuration (15 regs/inst). Opcode 0x06 = live sensor data (32 regs/inst).
>
> Your **VRC720f/2** appears at **II=0x01 OP=0x06** (software version 08.05, room humidity 40%, room temp 12.5°C).

### GG=0x09 Local Config (opcode 0x02)

Instanced (II=0x00-0x0A). 15 registers per instance. All identical — template config.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | sensor_address | C | u16 | — | — | 0..255 | — | — | | FLAGS=0x02. All instances: 0 |
| 0x0002 | sensor_type | C | u16 | enum | — | 1..3 | — | — | | FLAGS=0x02. All instances: 1 |
| 0x0003 | sensor_enabled | S | u8 | bool | — | 0..1 | `0=off 1=on` | — | | FLAGS=0x00. All instances: 1 |
| 0x0004 | (unknown) | S | u16 | — | — | 0..10 | — | — | | FLAGS=0x00. All instances: 0 |
| 0x0005 | (unknown) | S | u16 | — | — | 0..32768 | — | — | | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0006 | (unknown) | S | u16 | — | — | 0..32768 | — | — | | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0007 | holiday_start_date | C | date | date | — | — | — | — | | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x0008 | holiday_start_time | C | time | time | — | — | — | — | | FLAGS=0x02. 00:00:00 |
| 0x0009 | holiday_end_date | C | date | date | — | — | — | — | | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x000A | holiday_end_time | C | time | time | — | — | — | — | | FLAGS=0x02. 00:00:00 |
| 0x000B | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. All instances: 0 |
| 0x000C | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. All instances: 0 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. All instances: 0 |
| 0x000E | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. All instances: 0 |
| 0x000F | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x02. All instances: 0 |

### GG=0x09 Remote Data (opcode 0x06)

Instanced (II=0x00-0x0A). 32 registers per instance. **Active devices are identified by non-default values.** Empty slots have all NaN/0xFF/0x8000.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | | FLAGS=0x01. II=1: 1 (VRC720f/2 paired) |
| 0x0002 | device_class_address | P | u8 | enum | — | — | `0x15=VRC720 0x35=VR92 0x26=VR71` | — | | FLAGS=0x01. Canonical Vaillant eBUS address for device family (ebusd: 0x15→CTLV2, 0x35→VR_92, 0x26→VR_71) |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | | FLAGS=0x01. II=1: 0 (OK). Empty: 0xFF. 0=no error |
| 0x0004 | device_firmware_version | P | time | version | — | — | — | — | | FLAGS=0x01. 3 bytes: major.minor.patch (byte-decimal, NOT BCD). II=1: 08.05.00 → VRC720f/2 sw 08.05 |
| 0x0005 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0006 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0007 | current_room_air_humidity | S | f32 | % | — | — | — | — | | FLAGS=0x01. II=1: 40.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". NaN if no sensor |
| 0x0008 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0009 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x000A | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. Empty: 0xFF, II=1: 0 |
| 0x000C | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. All: 1 |
| 0x000E | room_temp_offset | C | f32 | °C | — | — | — | — | | FLAGS=0x03 (user RW). II=1: 0.0. Calibration offset for measured temperature |
| 0x000F | current_room_temperature | S | f32 | °C | — | — | — | — | | FLAGS=0x01. II=1: 12.5°C. VR92f/3 manual: "Current room temperature in the zone". NaN if no sensor |
| 0x0010 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0011 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | | FLAGS=0x01. Empty: 0xFF, II=1: 0 (OK) |
| 0x0013 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0014 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0015 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0016 | (unknown) | S | u16 | — | — | — | — | — | | FLAGS=0x00 |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. Empty: 0xFF, II=1: 0 |
| 0x0019 | remote_control_address | S | u8 | count | — | — | — | — | | FLAGS=0x01. VR92f/3 manual: "each remote control has a unique address starting at 1". VRC720=0 (master), VR92=1. Installer-settable per zone assignment |
| 0x001B | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00 |
| 0x001E | device_paired | P | u8 | bool | — | — | `0=no 1=yes` | — | | FLAGS=0x01. II=1: 1. Confirms active pairing. Empty: 0xFF |
| 0x001F | reception_strength | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 7 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | P | u16 | raw | — | — | — | — | | FLAGS=0x01. II=1: 0x1504. Byte 0 = device_class_address on VRC720 (0x15) |
| 0x0025 | zone_assignment | P | u8 | count | — | — | — | — | | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x002F | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. All: 5 |
| 0x0030 | max_time_periods_per_day | P | u8 | count | — | — | — | — | | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |

---

## GG=0x0A — Radio Sensors, VR92 (multi-instance, dual-opcode)

> **Verified 2026-03-05:** Dual-namespace. Opcode 0x02 = local configuration (69 regs/inst, all instances identical). Opcode 0x06 = live sensor data (32 regs/inst, per-device variation).
>
> Your **VR92f** appears at **II=0x01 OP=0x06** (firmware 02.17, room humidity 39%, room temp 13.625°C).

### GG=0x0A Local Config (opcode 0x02)

Instanced (II=0x00-0x0A). 69 registers per instance. **All 11 instances are byte-for-byte identical** — this is a template/default configuration from the BASV2, not per-VR92 data. Constraint catalog entries (0x0001-0x0006) define the writable config subset.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | sensor_mode | C | u8 | enum | — | 0..3 | — | — | | FLAGS=0x03. All: 0 |
| 0x0002 | protocol_type | C | u8 | enum | — | 1..2 | — | — | | FLAGS=0x03. All: 1 |
| 0x0003 | communication_mode | C | u8 | enum | — | 1..2 | — | — | | FLAGS=0x03. All: 1 |
| 0x0005 | (unknown) | C | u8 | — | — | 0..3 | — | — | | FLAGS=0x03. All: 1 |
| 0x0006 | sensor_enabled | C | u8 | bool | — | 0..1 | `0=off 1=on` | — | | FLAGS=0x03. All: 0 |
| 0x0007 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 1 |
| 0x0008 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 1 |
| 0x000C | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 0 |
| 0x000D | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 0 |
| 0x000E | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. All: NaN |
| 0x000F | (unknown) | P | f32 | — | — | — | — | — | | FLAGS=0x01. All: NaN |
| 0x0010-0x001A | (unknown, 8 regs) | P | f32 | — | — | — | — | — | | FLAGS=0x01. All: NaN. Large NaN block |
| 0x001B | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. All: 0 |
| 0x001D | basv2_serial_part1 | P | string | text | — | — | — | — | | FLAGS=0x01. First 6 chars of BASV2 serial number (redacted in public docs) |
| 0x001E | basv2_serial_part2 | P | string | text | — | — | — | — | | FLAGS=0x01. Chars 7-12 of BASV2 serial number (redacted in public docs) |
| 0x0020 | (unknown) | C | f32 | — | — | — | — | — | | FLAGS=0x03. All: 0.0 |
| 0x0021 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 0 |
| 0x0022-0x003E | temperature_schedule | C | u8 | °C/2 | — | — | — | — | | FLAGS=0x03. 29 u8 values: hourly temperature profile. Pattern: 25→45 day, 45→10 night, 10→45→25 evening. Values are degrees × 2 (e.g. 45 = 22.5°C, 10 = 5°C) |
| 0x003F | (unknown) | P | u8 | — | — | — | — | — | | FLAGS=0x01. All: 0 |
| 0x0040 | (unknown) | P | time | time | — | — | — | — | | FLAGS=0x01. All: 00:00:00 |
| 0x0042-0x004A | (unknown, 9 regs) | C | u16 | — | — | — | — | — | | FLAGS=0x03. All: 0. Config block |
| 0x004B | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 0 |
| 0x004D | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. All: 0 |

### GG=0x0A Remote Data (opcode 0x06)

Instanced (II=0x00-0x0A). 32 registers per instance. **Active VR92 devices are identified by non-default values.** Empty slots have NaN/0xFF.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | | FLAGS=0x01. II=1: 1 (VR92f paired) |
| 0x0002 | device_class_address | S | u8 | enum | — | — | `0x15=VRC720 0x35=VR92 0x26=VR71` | — | | FLAGS=0x01. Canonical Vaillant eBUS address for device family. II=1: 0x35 (53) |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | | FLAGS=0x01. II=empty: 0xFF, II=1: 0 (OK) |
| 0x0004 | device_firmware_version | S | time | version | — | — | — | — | | FLAGS=0x01. 3 bytes: major.minor.patch (byte-decimal, NOT BCD). II=1: 02.17.00 → VR92f sw 02.17 |
| 0x0006 | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x01. II=1: 0.0, empty: NaN |
| 0x0007 | current_room_air_humidity | S | f32 | % | RoomHumidity | — | — | — | | FLAGS=0x01. II=1: 39.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". ebusd confirmed. NaN if no sensor |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. II=empty: 0xFF, II=1: 0 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x03. All: 1 |
| 0x000E | room_temp_offset | C | f32 | °C | — | — | — | — | | FLAGS=0x03 (user RW). II=1: 0.0, empty: NaN. Calibration offset for measured temperature |
| 0x000F | current_room_temperature | S | f32 | °C | RoomTemp | — | — | — | | FLAGS=0x01. II=1: 13.625°C. VR92f/3 manual: "Current room temperature in the zone". ebusd confirmed. NaN if no sensor |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | | FLAGS=0x01. II=empty: 0xFF, II=1: 0 (OK) |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0019 | remote_control_address | S | u8 | count | — | — | — | — | | FLAGS=0x01. VR92f/3 manual: "each remote control has a unique address starting at 1". II=1: 1. Installer-settable per zone assignment |
| 0x001B | (unknown) | S | f32 | — | — | — | — | — | | FLAGS=0x00. All: NaN |
| 0x001E | device_paired | S | u8 | bool | — | — | `0=no 1=yes` | — | | FLAGS=0x01. II=1: 1. Empty: 0xFF |
| 0x001F | reception_strength | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 10 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | S | u16 | raw | — | — | — | — | | FLAGS=0x01. II=1: 0x8201. Byte 0 = 0x82 (purpose unclear, does NOT match device_class_address 0x35) |
| 0x0025 | zone_assignment | S | u8 | count | — | — | — | — | | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x0028-0x002E | (unknown, 7 regs) | C | u8 | — | — | — | — | — | | FLAGS=0x03. All: 0. User RW config block |
| 0x002F | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. All: 5 |
| 0x0030 | max_time_periods_per_day | S | u8 | count | — | — | — | — | | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |
| 0x0032 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0033 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x01. All: 0 |
| 0x0035 | (unknown) | C | u8 | — | — | — | — | — | | FLAGS=0x02. All: 0 |

**Radio device enumeration:** To enumerate all paired remote devices, scan **three groups** with opcode 0x06:

1. **GG=0x09** (VRC7xx / system controls) — II=0x00 through II=0x0A
2. **GG=0x0A** (VR92 / remote controls) — II=0x00 through II=0x0A
3. **GG=0x0C** (remote accessories / functional-module slots) — II=0x00 through II=0x0A

For each slot, read `device_connected` (0x0001). If =1, read:
- `device_class_address` (0x0002) — resolve to a controller-ecosystem family hint; in the current lab, `0x26` correlates with the eBUS-identified `VR_71`
- `device_firmware_version` (0x0004) — byte-decimal triplet
- `reception_strength` (0x001F) — 0-10 scale (4=acceptable, <4=unstable)
- `remote_control_address` (0x0019) — unique per remote (1..N), 0 for master
- `current_room_air_humidity` (0x0007) — f32 %, NaN if no sensor
- `current_room_temperature` (0x000F) — f32 °C, NaN if no sensor

**ebusd baseline:** ebusd `15.ctlv2.csv` defines only RR=0x0007 (RoomHumidity, EXP decode) and RR=0x000F (RoomTemp, EXP decode) for VR92 addresses 1-8, routed via `B524,06000a..`.

**ebusd decode note:** B524 remote responses carry a 4-byte header before the register value. When defining ebusd message templates, skip 4 bytes then decode the payload (e.g., for humidity: `B524,060009010700` → skip 4B → IEEE-754 LE float).

---

## GG=0x06 — Programs/Timetables

Uses opcode `0x0B` (array/table transport). Scalar register scanning is not applicable — this group uses a different selector schema than `0x02`/`0x06` register reads. See [GetExtendedRegisters §4.5](./ebus-vaillant-GetExtendedRegisters.md#45-0x0b-arraytable-read-schedules) for wire protocol details.

No register table. Schema under investigation.

---

## GG=0x07 — Programs/Timetables

Uses opcode `0x0B` (array/table transport). Same transport as GG=0x06.

No register table. Schema under investigation.

---

## GG=0x0C — Remote Accessories / functional-module slots (multi-instance, remote only)

> **Verified 2026-03-05:** Responds only to opcode 0x06 (no local config namespace — opcode 0x02 returns 0 valid registers). 15 registers per instance, 165 total valid. Uses the same remote-device slot schema as GG=0x09/0x0A.
>
> In the current lab, the slot at **II=0x01** has `device_class_address=0x26` and firmware 01.00.00. This correlates with the eBUS-identified `VR_71` hardware at slave address `0x26`. The family/product identification comes from eBUS identity, not from B524 alone.

### GG=0x0C Remote Data (opcode 0x06)

Instanced (II=0x00-0x0A). 15 registers per instance. Uses the shared remote-device slot schema. In the current lab, **II=0x01 has `device_class_address=0x26`**, matching the eBUS-identified hardware at slave address `0x26`, but `device_connected=0` — the slot is recognized but currently not reporting as "live" (wired module, not radio — may use a different liveness mechanism).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Semantic | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|----------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | | FLAGS=0x01. All: 0 |
| 0x0002 | device_class_address | S | u8 | enum | — | — | `0x26` in current lab | — | | FLAGS=0x00. II=1: 0x26 (38). In the current lab, this matches the eBUS-identified `VR_71` hardware at slave address `0x26`; treat as correlation, not standalone B524 proof. |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | | FLAGS=0x00. All empty: 0xFF |
| 0x0004 | device_firmware_version | S | time | version | — | — | — | — | | FLAGS=0x00. II=1: 01.00.00 (byte-decimal). Empty: FF/FF/FF |
| 0x000A | (unknown) | C | u16 | — | — | — | — | — | | FLAGS=0x02. All: 0 |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | | FLAGS=0x00. All empty: 0xFF |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. All empty: 0xFF, II=1: 1 when type code present |
| 0x0028-0x002E | (unknown, 7 regs) | C | u8 | — | — | — | — | — | | FLAGS=0x02. All: 0 |
| 0x002F | (unknown) | S | u8 | — | — | — | — | — | | FLAGS=0x00. All: 5 |

**Current-lab VR_71 correlation:** B524 yields `device_class_address=0x26` at `II=0x01`. The conclusion that this slot corresponds to `VR_71` comes from correlating that hint with eBUS identity data, where slave address `0x26` identifies itself as `VR_71`. Vaillant controller documentation then constrains the profile interpretation by describing `FM5` as "instead of VR 71". This is useful and strong for the current lab/profile, but it is not standalone protocol proof that `GG=0x0C` universally means `VR71/FM5`.

Architectural note:

- current Helianthus functional-module semantics are documented in [`../architecture/functional-modules.md`](../architecture/functional-modules.md)
- the current implemented semantic surface is FM5-centered; the generic `functionalModules[]` target is deferred

---

## Semantic Plane Mapping

The raw register tables below document what exists on the wire. The separate structural decision catalog documents how gateway code turns those raw values into semantic families, instance counts, gates, and ownership fields:

- architecture flow: [`../architecture/semantic-structure-discovery.md`](../architecture/semantic-structure-discovery.md)
- structural decision catalog: [`./ebus-vaillant-B524-structural-decisions.md`](./ebus-vaillant-B524-structural-decisions.md)

This is where decisions such as zone publication, `associatedCircuit`, FM5 gating, and circuit `managingDevice` are documented as contract rather than left implicit in code.

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

Ownership note:
- `circuits[].managing_device` is a semantic contract, not a direct single-register read.
- The gateway now emits explicit ownership only for proven topologies.
- For the currently proven live topology (`system_scheme=1`, `module_configuration_vr71=2`, FM5 interpreted), all discovered circuits are marked as managed by `VR_71` (`FUNCTION_MODULE`, address `0x26`).
- Unproven topologies are emitted as `UNKNOWN`; the gateway does not synthesize a replacement threshold heuristic.
- Broader architectural treatment of FM3/FM5/VR66 as functional-module families is documented in [`../architecture/functional-modules.md`](../architecture/functional-modules.md).

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
| `[].managing_device` | derived semantic ownership | object |
| `[].config.cooling_enabled` | GG=0x02, RR=0x0006 | bool (u8) |
| `[].properties.heating_circuit_type` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.mixer_circuit_type_external` | GG=0x02, RR=0x0002 | u16 |
| `[].properties.frost_protection_threshold` | GG=0x02, RR=0x001D | f32 | **Stale path**: FLAGS=0x02 (RW) — should be `config.*`. Pending gateway migration |

Consumer note:
- `[].config.cooling_enabled` remains a gateway-level raw semantic field derived from `GG=0x02 RR=0x0006`.
- It is **not** yet a validated Home Assistant-facing configuration contract and should not be materialized as an HA control entity until the register semantics are confirmed end-to-end.

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

The current PASS-profile boiler status plane is no longer a B524-only composite. Helianthus now prefers direct BAI00 B509 reads for the boiler semantic surface and keeps only a small B524 fallback/mirror set in the controller path.

Authoritative direct-boiler mapping:
- see [`ebus-vaillant-B509-boiler-register-map.md`](./ebus-vaillant-B509-boiler-register-map.md)

The B524 contribution that still feeds the current boiler semantic contract is:

| Semantic Path | B524 | Type | Notes |
|---------------|------|------|-------|
| `state.dhwTemperatureC` | GG=0x01, RR=0x0005 | f32 | Controller mirror from DHW group |
| `state.dhwTargetTemperatureC` | GG=0x01, RR=0x0004 | f32 | Controller mirror from DHW group |
| `config.dhwOperatingMode` | GG=0x01, RR=0x0003 | u16 | Decoded into the public enum string |
| `diagnostics.heatingStatusRaw` | GG=0x02, II=0x00, RR=0x001B | u16 | Controller-side raw heating status |

Fields currently present in the schema but not populated from a validated source:
- `state.returnTemperatureC`
- `diagnostics.dhwStatusRaw`

### `ebus.v1.semantic.energy_totals.get`

Source: `refreshEnergy()` in `semantic_vaillant.go`

Semantics:
- After the first valid sample, Helianthus keeps the last known `energyTotals` snapshot across temporary B524 read gaps.
- A refresh cycle with no accepted energy points does **not** clear the semantic snapshot and does **not** reset any series to `0` or `null`.

| Semantic Path | B524 | Type |
|---------------|------|------|
| `gas.climate` | GG=0x00, RR=0x0056 | u32 (kWh) |
| `electric.climate` | GG=0x00, RR=0x0057 | u32 (kWh) |
| `electric.dhw` | GG=0x00, RR=0x0058 | u32 (kWh) |
| `gas.dhw` | GG=0x00, RR=0x0059 | u32 (kWh) |

### `ebus.v1.semantic.solar.get`

Not implemented. Gated by `fm5_config≤2`. Source registers would come from GG=0x04 (solar circuit).

### `ebus.v1.semantic.cylinders.get`

Source: `readCylinderSnapshots()` / `publishFM5Semantic()` in `semantic_vaillant.go`

Publication gate:
- Entire family is gated by `fm5_config≤2`.
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
- GG=0x00 Record 0x8000 → RR=0x0080 is now confirmed responsive (FLAGS=0x03, f32=0.0, constraint: -10..10 step 1). Adjacent to `smart_photovoltaic_buffer_offset` (0x0081). Possibly PV-related offset config.

---

## Enum Reference

Enum definitions used by B524 registers. Where Helianthus interprets values differently from ebusd, both mappings are shown.

### opmode — Operation mode

Used by: GG=0x03 RR=0x0001, GG=0x03 RR=0x0006, GG=0x01 RR=0x0003

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

| Numeric value (gateway payload) | ebusd | Human alias only | Notes |
|-------------------------------|-------|------------------|-------|
| 0 | none | none | No room sensor assigned |
| 1 | VRC700 | regulator | Built-in sensor of the /f split regulator (wireless UI + base station). Same hardware class as VR91 with added UI firmware |
| 2 | VR91_1 | thermostat_1 | External RF temperature/humidity sensor + UI endpoint |
| 3 | VR91_2 | thermostat_2 | Second VR91 sensor |
| 4 | VR91_3 | thermostat_3 | Third VR91 sensor |

Note: ebusd uses hardware model names (VRC700, VR91). Helianthus may use user-facing labels such as `regulator` and `thermostat_*`, but those labels are aliases for documentation/UI only. The authoritative GraphQL payload is the raw integer enum in `zones[].config.roomTemperatureZoneMapping`. The separate `zones[].config.associatedCircuit` field is a resolved 0-based circuit index used for circuit type lookup and must not be treated as the raw `RR=0x0013` value.

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

Category corrections applied from VRC Explorer FLAGS analysis (GG=0x02, 0x03) and MCP validation (GG=0x00, 0x01):

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
| 0x00 | 0x0007 | system_off | S | C | 0x03 | User-writable on/off switch, not a sensor reading (MCP validated) |

Wire type corrections from MCP validation (2026-03-05):

| Group | RR | Name | Old Wire | New Wire | Evidence |
|-------|-----|------|----------|----------|----------|
| 0x00 | 0x0007 | system_off | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x00 | 0x0014 | adaptive_heating_curve | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x00 | 0x0096 | maintenance_due | u16 | u8 | 1-byte response, FLAGS=0x01 |
| 0x01 | 0x000D | hwc_special_function_mode | u16 | u8 | 1-byte response, FLAGS=0x03 |
| 0x03 | 0x000E | current_special_function | u16 | u8 | 1-byte response, FLAGS=0x03 |

Notable FLAGS-confirmed assignments (no change needed):
- GG=0x02 0x0002 (heating_circuit_type): FLAGS=0x03 (user RW), kept as P — writable but used as immutable discovery probe in Helianthus
- GG=0x03 0x001C (zone_index): FLAGS=0x01 (stable RO), kept as P — presence marker
- GG=0x00 0x0036 (system_scheme): FLAGS=0x03 (user RW), kept as P — stable property rarely changed

Partial FLAGS data from MCP spot-checks (GG=0x00, 0x01):
- GG=0x00: 0x0007(0x03), 0x0014(0x03), 0x0036(0x03), 0x0039(0x01), 0x004B(0x01), 0x0056(0x01), 0x0073(0x01), 0x0095(0x00), 0x0096(0x01)
- GG=0x01: 0x0001(0x03), 0x0003(0x03), 0x0004(0x03), 0x0005(0x01), 0x000D(0x03)

Full FLAGS scan for GG=0x00 and GG=0x01 still pending (`b524_grab_op.py`).

## Related Files

- `_work_register_mapping/mypyllant_b524_system_mapping.json` — Original mapping analysis with confidence ratings (historical)
- `_work_register_mapping/B524/` — Raw VRC Explorer scan data per group
- `helianthus-ebusreg/vaillant/system/b524_profile.go` — Discovery profiles
- `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/15.ctlv2.tsp` — ebusd TSP source
- `helianthus-ebus-vaillant-productids/repos/john30-ebusd-configuration/src/vaillant/_templates.tsp` — ebusd enum definitions
