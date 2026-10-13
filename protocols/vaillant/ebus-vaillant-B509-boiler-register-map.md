# Vaillant B509 Boiler Register Map (BAI00)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document records candidate direct BAI00 register semantics for `PB=0xB5`, `SB=0x09`. Each mapping remains device-specific and requires target-qualified evidence.

Each register carries a canonical `Name`: `snake_case`, describing the quantity, with unit, codec, scaling and access kept in separate fields and no API prefix. The `Legacy API path` column keeps the earlier API path as correspondence only; it is not a name. Vaillant and community ebusd names for every register are in the [register name correspondence fixture](fixtures/b509-register-name-correspondence.csv), described in the [protocol page](ebus-vaillant-B509.md#register-name-correspondence-fixture). Register ids are written as the two address bytes in wire order (see [Address byte order](ebus-vaillant-B509.md#address-byte-order)). A register is identified by target class, operation and complete selector; equal names never merge entries.

## Semantic Mapping

### Direct read candidates

| Name | Legacy API path | B509 register | Codec / scale | Notes |
|------|-----------------|---------------|---------------|-------|
| `flow_temperature` | `state.flowTemperatureC` | `0x1800` | `DATA2c` | Live boiler flow temperature |
| `central_heating_pump_active` | `state.centralHeatingPumpActive` | `0x4400` | `on/off` | CH pump state |
| `water_pressure` | `state.waterPressureBar` | `0x0200` | `DATA2b` | Boiler water pressure |
| `flame_active` | `state.flameActive` | `0x0500` | `UCH (0x0F=on, 0xF0=off)` | Burner flame status. Wire encoding uses UCH sentinel, not simple 0/1 boolean |
| `gas_valve_active` | `state.gasValveActive` | `0xBB00` | `UCH (0x0F=on, 0xF0=off)` | Gas valve state. Wire encoding uses UCH sentinel, not simple 0/1 boolean |
| `fan_speed` | `state.fanSpeedRpm` | `0x8300` | `UIN` | Fan speed in RPM |
| `modulation_setpoint` | `state.modulationPct` | `0x2E00` | `SIN / 10` | Modulation (legacy reading: percent). Candidate: a modulation set point; another reading is the current modulation in percent; unresolved (see Open questions) |
| `boiler_state_code` | `state.stateNumber` | `0xAB00` | `UCH` | Raw boiler state number |
| `diverter_valve_position` | `state.diverterValvePositionPct` | `0x5400` | `UCH` | Diverter valve position (legacy reading: percent). Candidate: an enumerated position code rather than a percentage; see Open questions |
| `dhw_demand_active` | `state.dhwDemandActive` | `0x5800` | `on/off` | DHW demand state |
| `dhw_water_flow_rate` | `state.dhwWaterFlowLpm` | `0x5500` | `UIN / 100` | DHW water flow in L/min |

### Additional read candidates

| Name | Legacy API path | B509 register | Codec / scale | Notes |
|------|-----------------|---------------|---------------|-------|
| `maximum_heating_flow_temperature_setpoint` | `config.flowsetHcMaxC` | `0x0E04` | `DATA2c` | Primary register for max HC flow setpoint |
| `maximum_heating_flow_temperature_setpoint` | `config.flowsetHcMaxC` | `0xA500` | `DATA2c` | Separate selector with the same community name; which devices of the class use which id is unresolved |
| `maximum_dhw_flow_temperature_setpoint` | `config.flowsetHwcMaxC` | `0x0F04` | `DATA2c` | Max HWC flow setpoint |
| `heating_partial_load_power` | `config.partloadHcKW` | `0x0704` | `UCH` | Whole-number; the unit (kW or %) is unresolved |
| `dhw_partial_load_power` | `config.partloadHwcKW` | `0x0804` | `UCH` | Whole-number; the unit (kW or %) is unresolved |
| `storage_loading_pump_level` | `state.storageLoadPumpPct` | `0x9E00` | `percent0` | Storage load pump percent |
| `flow_temperature_setpoint` | `state.flowTempDesiredC` | `0x3900` | `DATA2c` | Desired boiler flow temperature |
| `dhw_temperature_setpoint` | `state.dhwTempDesiredC` | `0xEA03` | `DATA2c` | Desired DHW temperature |
| `circulation_pump_active` | `state.circulationPumpActive` | `0x7B00` | `on/off` | Circulation pump state |
| `external_pump_active` | `state.externalPumpActive` | `0x3F00` | `on/off` | External pump state |
| `heating_switch_active` | `state.heatingSwitchActive` | `0xF203` | `on/off` | Heating switch state |
| `fan_speed_setpoint` | `state.targetFanSpeedRpm` | `0x2400` | `UIN` | Target fan speed in RPM |
| `flame_ionization_current` | `state.ionisationVoltageUa` | `0xA400` | `SIN / 10` | Ionisation current. The unit µA is a candidate; it is not confirmed on the wire (another reading is a voltage level; see Open questions) |
| `primary_circuit_flow_rate` | `state.primaryCircuitFlowLpm` | `0xFB00` | `UIN / 100` | Primary circuit flow; the unit (l/min or l/h) is unresolved |

### Counter candidates

| Name | Legacy API path | B509 register | Codec / scale | Notes |
|------|-----------------|---------------|---------------|-------|
| `central_heating_operating_time` | `diagnostics.centralHeatingHours` | `0x2800` | `Hoursum2` | CH operating hours |
| `dhw_operating_time` | `diagnostics.dhwHours` | `0x2200` | `Hoursum2` | DHW operating hours |
| `central_heating_start_count` | `diagnostics.centralHeatingStarts` | `0x2900` | `UIN` | CH starts count. Candidate scale factor 100; see Open questions |
| `dhw_start_count` | `diagnostics.dhwStarts` | `0x2300` | `UIN` | DHW starts count. Candidate scale factor 100; see Open questions |
| `pump_operating_time` | `diagnostics.pumpHours` | `0x1400` | `Hoursum2` | Pump operating hours |
| `fan_operating_time` | `diagnostics.fanHours` | `0x1B00` | `Hoursum2` | Fan operating hours |
| `fire_control_deactivation_count` | `diagnostics.deactivationsIFC` | `0x1F00` | `UCH` | IFC deactivations; candidate expansion of IFC: internal fire control system, unconfirmed on the wire; see Open questions |
| `temperature_limiter_deactivation_count` | `diagnostics.deactivationsTemplimiter` | `0x2000` | `UCH` | Temperature limiter deactivations |

### Sensitive configuration candidates

| Name | Legacy API path | B509 register | Codec / scale | Access | Notes |
|------|-----------------|---------------|---------------|--------|-------|
| `central_heating_pump_mode` | `config.installerMenuCode` | `0x4904` | `UCH` (1 byte) | r;ws | Candidate interpretation, unconfirmed on the wire: central heating pump mode (0 post-run, 1 permanent, 2 winter). Another reading is an installer access code (range 0..255); see Open questions |
| `installer_phone_number` | `config.phoneNumber` | `0x8104` | `HEX:8` (8 bytes) | r;wi | Installer phone number as raw hex string (16 hex chars). |
| `service_time_remaining` | `config.hoursTillService` | `0x2004` | `Hoursum2` (2 bytes) | r | Service countdown in hours. **Read-only by design** — service counter must not be written |

### Further BAI00 registers

The following registers are from public community configurations (ebusd-configuration forks: john30/<!-- legacy-role-mapping:begin -->master<!-- legacy-role-mapping:end -->, bumaas/xerion3800). They are candidates.

The Confidence column rates the public configuration evidence for the register and its codec; it does not confirm the meaning on the wire.

**Diagnostics and hardware feedback:**

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `air_control_ok` | `diagnostics.airControlOk` | `0x0300` | `UCH (0x0F=ok, 0xF0=fault)` | R | HIGH | public `bai.csv` | Air control system status |
| `flame_sensing_asic_output` | `diagnostics.flameSensingAsic` | `0x2F00` | `UIN` (raw ADC count) | R | HIGH | public `bai.csv` | Raw ADC output of flame sensing ASIC |
| `flue_gas_valve_active` | `state.flueGasValve` | `0x3C00` | `on/off` | R | HIGH | public `bai.csv` | Flue gas valve state |
| `gas_valve_asic_feedback` | `diagnostics.gasValveAsicFeedback` | `0x4700` | `UCH` (state enum) | R | HIGH | public `bai.csv` | Gas valve ASIC feedback signal |
| `gas_valve_microcontroller_feedback` | `diagnostics.gasValveUcFeedback` | `0x4800` | `UCH` (state enum) | R | HIGH | public `bai.csv` | Gas valve microcontroller feedback; distinct from `0x4700` (ASIC vs UC path) |
| `external_gas_valve_active` | `state.externGasValve` | `0xE400` | `on/off` | R | MEDIUM | single-source hypothesis | External gas valve state. **Address collision**: same ID means `compressorState` on EHP00/HMU |
| `predictive_air_pressure_switch_event_count` | `diagnostics.prApsCounter` | `0xF200` | `UCH` (count) | R | HIGH | public `bai.csv` | APS event counter (expansion of APS as predictive air pressure switch: candidate, unconfirmed on the wire); the event counted is unresolved (see Open questions) |
| `predictive_air_pressure_switch_accumulated_time` | `diagnostics.prApsSum` | `0xF300` | `seconds2` (seconds) | R | HIGH | public `bai.csv` | APS accumulated time in seconds (expansion of APS as predictive air pressure switch: candidate, unconfirmed on the wire); the accumulated interval is unresolved (see Open questions) |

**Configuration and identity:**

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `device_specific_number` | `identity.dsn` | `0x9A00` | `UIN` (candidate: device-type/configuration code) | R | HIGH | public `bai.csv` | Device Specific Number (DSN): a device-type or configuration code, not a serial number (candidate interpretation, unconfirmed on the wire). Candidate use: product-type gate for register collision resolution |
| `display_mode` | `config.displayMode` | `0xDA00` | `UCH` (enum) | R | MEDIUM | single-source hypothesis | Current display state on boiler PCB |
| `minimum_operating_fan_speed` | `config.fanMinSpeedOperation` | `0xDF00` | `UIN` (RPM) | R | HIGH | public `bai.csv` | Configured minimum fan speed during operation |
| `maximum_operating_fan_speed` | `config.fanMaxSpeedOperation` | `0xE000` | `UIN` (RPM) | R | HIGH | public `bai.csv` | Configured maximum fan speed during operation |
| `dcf_time_date` | `state.dcfTimeDate` | `0xE500` | `HEX:8` (time struct) | R | MEDIUM | single-source hypothesis | DCF77-style 8-byte time/date sync state. Format not live-confirmed; the width is unresolved (see Open questions) |

**Energy yield (product-specific):**

These two rows are the read and write operations `0D` and `0E`, not
registers; which energy quantities, if any, are reached through them is
unresolved (see Open questions), and the legacy API paths are correspondence
only.

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `read_symbolic_address` | `energy.yieldRead` | `0x0D` | `*r` stub (raw) | R | MEDIUM | public fork evidence → bumaas `bai.0010005400.inc`, xerion3800 `yield3f40.inc` | The register read operation `0D`, not a register; the legacy path is a correspondence only (unconfirmed on the wire) |
| `write_symbolic_address` | `energy.yieldWrite` | `0x0E` | `*w` / `*wi` / `*ws` (raw) | W | MEDIUM | public fork evidence → bumaas `bai.0010005400.inc`, `bai.0010015600.inc` | The register write operation `0E`, not a register; `*ws` marks a persistent write (**Hypothesis**, unconfirmed on the wire) |

**Unenumerated clusters (reported by public configurations, unconfirmed on the wire; individual registers not mapped):**
- `0xC500–0xFA00`: `PrEnergy*` cluster — approximately 20 candidate energy accounting registers (ULG type); candidate, unconfirmed on the wire: they are read and written with the generic operations `0D` and `0E`; which selectors belong to the cluster is unresolved.
- `0x3501–0x4801`: `Pred*` analytics cluster — approximately 20 predictive/diagnostic registers (UCH/UIN).

## Open questions

- `0x4904`: candidate interpretation, unconfirmed on the wire: central heating
  pump mode (`0` post-run, `1` permanent, `2` winter). Another reading is an
  installer access code (r;ws), which the earlier API path uses for this id.
  Which devices of the class use which meaning is unresolved.
- `0x2E00`: candidate: a modulation set point; another reading is the current
  modulation in percent (the earlier API path describes a modulation
  percentage). Whether the value is the requested or the achieved modulation is
  unresolved.
- `0x5400`: candidate interpretation, unconfirmed on the wire: an enumerated
  position code (community comment: `100` domestic hot water, `0` heating, `40`
  middle position) rather than a percentage. Whether the value is the commanded
  or the measured position is unresolved.
- `0x0E04` and `0xA500` are separate selectors with the same community name;
  which devices of the class use which id is unresolved.
- `0xA400`: the unit µA is a candidate; it is not confirmed on the wire. Another
  reading is a voltage level.
- `0x2900` and `0x2300`: candidate interpretation, unconfirmed on the wire: the
  raw value is scaled by 100. The codec column above lists `UIN` without a
  factor.
- `0x1F00`: candidate expansion of IFC: internal fire control system,
  unconfirmed on the wire. Community comments describe ignition-device cut-offs
  or ignition failures. The exact event counted is unresolved.
- `0xF200` and `0xF300`: candidate interpretation, unconfirmed on the wire: a
  counter of predictive air pressure switch events and an accumulated value
  related to it. The event counted and the accumulated interval are unresolved.
- `0x9A00`: candidate interpretation, unconfirmed on the wire: the value is a
  16-bit number followed by a 16-bit inverse field (4 bytes), while the community
  codec reads 2 bytes.
- `0xE500`: community configurations give 8 bytes (`HEX:8`); a 7-byte layout is
  also a candidate. The time format is unresolved.
- `0x0704` and `0x0804`: one community configuration lists the unit as kW or %;
  the unit is unresolved. `0xFB00`: one community configuration lists l/h with a
  plain unsigned codec; the unit is unresolved.
- The meaning of some of these ids may differ between devices of the class; the
  register meaning is therefore device specific and the product has to be
  identified first (see the Device-Type Gate in the protocol page).
- The `0x0D` and `0x0E` rows are operations. Which energy quantities, if any, are
  reached through them, and with which complete selectors, is unresolved.
- `0xAB00`: the meaning of the individual state codes is not established.
- `0x3900`: whether the set point is the flow or, with return regulation set,
  the return temperature is unresolved.

For the separate controller-mediated OP06 namespace, see the [B524 register map](ebus-vaillant-B524-register-map.md#op0x06--controller-mediated-device-parameters).
