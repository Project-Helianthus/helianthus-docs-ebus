# Vaillant B509 Heat Pump Register Map (EHP00 / HMU)

This document covers the B509 register space for heat pump devices at eBUS
address `0x08`. It is separate from the
[boiler register map](ebus-vaillant-B509-boiler-register-map.md) because **the
same eBUS address hosts either a BAI00 (boiler) or an EHP00/HMU (heat pump),
and many register addresses have different semantics depending on the device
type**. See the
[Device-Type Gate section](ebus-vaillant-B509.md#device-type-gate-register-address-collision)
in the protocol doc.

Each register carries a canonical `Name`: `snake_case`, describing the quantity,
with unit, codec, scaling and access kept in separate fields and no API prefix.
The `Legacy API path (candidate)` column keeps the earlier API path as
correspondence only; it is not a name. Vaillant and community ebusd names for
every register are in the
[register name correspondence fixture](fixtures/b509-register-name-correspondence.csv),
described in the
[protocol page](ebus-vaillant-B509.md#register-name-correspondence-fixture).
Register ids are written as the two address bytes in wire order (see
[Address byte order](ebus-vaillant-B509.md#address-byte-order)). The two-byte
registers of section 1 belong to the `heat_pump` class and the five-byte
selectors of section 2 to the `heat_pump_interface_unit` class. A register is
identified by target class, operation and complete selector; equal names never
merge entries.

## Device-Type Gate

The registers of section 1 are documented for devices with the identity
string `EHP00`, and those of section 2 for heat-pump interface units (identity
strings starting `HMU`), at address `0x08` (candidate; whether other classes
answer these ids is not established). They MUST NOT be read from a BAI00
boiler at the same address.
Product identification must be established first via B514 identity frame or
B509 `0x9A00` (DSN, a device-specific number that is a device-type or
configuration code and not a serial number; candidate interpretation,
unconfirmed on the wire) before interpreting any register in this map.

Known address collisions with the BAI00 boiler register map:

| Register ID | BAI00 (boiler) meaning | EHP00 (heat pump) meaning |
|------------:|------------------------|-------------------------------|
| `0x3F00` | `externalPumpActive` (on/off) | `ICLOut` -- inrush current limiter (on/off) |
| `0xBB00` | `gasValveActive` (UCH 0x0F/0xF0) | `ActualEnvPowerPercentage` (percent0, %) |
| `0x1400` | `pumpHours` (Hoursum2, hours) | `CompPressHigh` -- high-side compressor pressure (sensor, bar) |
| `0xE400` | `externGasvalve` (on/off) | `compressorState` (UCH enum) |

The heat-pump meanings in this table belong to the `EHP00` identity of section
1; the meaning of these ids on an `HMU` identity is unresolved (see Open
Questions item 5).

## Status

All registers in this document are from public community configurations. They
are candidates for interpretation and validation.

Evidence labels:

- `FORK1`: community fork primary source (single fork)
- `FORK2`: confirmed by two independent forks

The Confidence column rates the public configuration evidence for the register and its codec; it does not confirm the meaning on the wire.

---

## 1. EHP00 Standard Registers (2-byte B509 IDs)

These use the standard 2-byte B509 ID format, identical to BAI00 wire shape.

### Operating state and yield

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `heat_pump_status` | `state.heatPumpStatus` | `0xD000` | `hpstatus` enum | R | HIGH | FORK2 | Heat pump operating state (heating, cooling, defrost, standby, etc.) |
| `environmental_energy_yield_total` | `energy.yieldTotal` | `0xBC00` | `energy4` (kWh) | R | HIGH | FORK2 | Lifetime energy in kWh (4-byte value). Candidate: energy taken from the environment; another reading is the delivered heat yield; unresolved (see Open questions) |
| `environmental_power` | `state.actualEnvironmentPower` | `0xBA00` | `power` (kW) | R | MEDIUM | FORK1 | Actual environmental (source) power in kW |
| `environmental_power_ratio` | `state.actualEnvPowerPercentage` | `0xBB00` | `percent0` (%) | R | MEDIUM | FORK1 | Environmental power as percentage (0-100). **Collision**: same address as BAI00 `gasValveActive` |

### Refrigerant circuit

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `refrigerant_superheat` | `state.superheat` | `0x8D00` | `temp` (K delta) | R | HIGH | FORK2 | Refrigerant superheat at compressor inlet (signed temperature delta in Kelvin) |
| `refrigerant_subcooling` | `state.subcooling` | `0x8E00` | `temp` (K delta) | R | HIGH | FORK2 | Refrigerant subcooling at condenser outlet (signed temperature delta in Kelvin) |
| `source_inlet_temperature` | `state.sourceTempInput` | `0x0F00` | `tempsensor` (C) | R | MEDIUM | FORK1 | Source-side (air or ground) inlet temperature |
| `refrigerant_high_pressure` | `state.compressorPressureHigh` | `0x1400` | `sensor` (bar) | R | MEDIUM | FORK1 | High-side compressor pressure. **Collision**: same address as BAI00 `pumpHours` |
| `refrigerant_low_pressure` | `state.compressorPressureLow` | `0x1500` | `sensor` (bar) | R | MEDIUM | FORK1 | Low-side compressor pressure |

### Compressor control and timing

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `compressor_state` | `state.compressorState` | `0xE400` | `UCH` enum | R | MEDIUM | FORK1 | Compressor state machine position. **Collision**: same address as BAI00 `externGasvalve` |
| `compressor_control_state` | `state.compressorControlState` | `0xE900` | `UCH` enum | R | MEDIUM | single source | Compressor control algorithm state |
| `compressor_minimum_on_duration` | `config.timeCompOnMin` | `0xE600` | `seconds` (s) | R | MEDIUM | FORK1 | Minimum compressor-on time |
| `compressor_minimum_off_duration` | `config.timeCompOffMin` | `0xE700` | `seconds` (s) | R | MEDIUM | FORK1 | Minimum compressor-off time |
| `compressor_minimum_start_interval` | `config.timeBetweenTwoCompStartsMin` | `0xE800` | `seconds` (s) | R | MEDIUM | FORK1 | Minimum required interval between two compressor start events |
| `compressor_dhw_start_count` | `diagnostics.compressorStartsHwc` | `0xA800` | `counter` (count) | R | MEDIUM | FORK1 | Compressor starts attributed to DHW operation |
| `compressor_high_pressure_cutout_count` | `diagnostics.compressorCutPressHighCount` | `0xB400` | `counter` (count) | R | MEDIUM | FORK1 | High-pressure cut-out event counter |

### Defrost

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `defrost_active` | `state.deicingActive` | `0xCE01` | `yesno` (bool) | R | MEDIUM | FORK1 | Defrost/de-icing cycle active. The `01` suffix may indicate register page/bank |

### Electrical / phase

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `phase_order_status` | `state.phaseOrder` | `0x5701` | `phaseok` enum | R | MEDIUM | FORK1 | Phase-order check result (correct L1-L2-L3 sequence) |
| `phase_status_flags` | `state.phaseStatus` | `0x8800` | `phase flags` (bitmask) | R | MEDIUM | FORK1 | Phase status flags (phase loss, undervoltage, etc.) |
| `inrush_current_limiter_output_active` | `state.iclOut` | `0x3F00` | `on/off` | R | MEDIUM | FORK1 | Inrush current limiter output state. **Collision**: same address as BAI00 `externalPumpActive`. Candidate interpretation, unconfirmed on the wire: an inrush current limiter output; whether it is a bypass output is unresolved (see Open questions) |

### Noise reduction (VWLS)

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `noise_reduction_active` | `state.noiseReduction` | `0xA901` | `yesno` (bool) | R | MEDIUM | FORK1 | Night/noise reduction mode active |
| `noise_reduction_factor` | `config.noiseReductionFactor` | `0x2401` | `percent0` (unit unresolved) | R | MEDIUM | FORK1 | Candidate: active noise reduction factor (candidate range 0-100%). Another meaning is possible on some devices of the class, and the name is provisional; see Open questions |

### Other

| Name | Legacy API path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|------|-----------------------------|---------------|---------------|-----|------------|----------|-------|
| `environmental_power` | `state.actualEnvPowerFine` | `0xE201` | `UCH` (100W units) | R | MEDIUM | FORK1 | Actual environmental power in units of 100 W (multiply byte by 100). Separate native selector with its own scale; the name equals that of `0xBA00` but the entries stay separate |
| `bivalent_mode` | `state.bivalentMode` | `0xE301` | `UCH` enum | R | MEDIUM | single source | Bivalence operating mode (heat pump only, backup boiler active, etc.) |
| `source_temperature_limit_at_maximum_flow` | `config.sourceLimitAtMaxFlow` | `0xE401` | `SCH` (C, signed) | R | MEDIUM | FORK1 | Signed source temperature limit at maximum flow |
| `source_temperature_limit_slope` | `config.sourceLimitSlope` | `0xE501` | `UCH` (slope) | R | MEDIUM | community comment | Source temperature limit slope characteristic. The unit is unresolved |
| `refrigerant_low_pressure_maximum` | `state.maxNdPressure` | `0xE901` | `ULG` (unit unresolved) | R | MEDIUM | FORK1 | Maximum ND pressure (unit unresolved; Pa is a candidate) (4-byte ULG). Candidate interpretation, unconfirmed on the wire: ND is the refrigerant low-pressure side (Niederdruck). Unusual type for pressure |
| `compressor_energy_integral` | `state.integral` | `0x8000` | `value` (unknown) | R | LOW | FORK1 | Control algorithm integral value. Type and unit unconfirmed; candidate: an energy integral in degree-minutes |

### Note on `01`-suffix EHP registers

Registers `0xCE01`, `0xA901`, `0x5701`, `0x2401`, `0xE201`, `0xE301`,
`0xE401`, `0xE501`, `0xE901` use a `01` second byte. This may indicate a
second register page/bank or instance selector. A live scan comparing `XX00`
vs `XX01` is needed to confirm the semantics. The pattern is consistent:
`XX01` where `XX` is the primary register byte.

Under the little-endian hypothesis for the address bytes (see
[Address byte order](ebus-vaillant-B509.md#address-byte-order)) the second byte
is the high byte of the number, so a `01` suffix is a number above 255 and
`XX00` and `XX01` are different numbers; this reading does not support a
separate page/bank selector, but it is unconfirmed on the wire.

---

## 2. Heat pump interface unit registers (`54 02 00 REG TYPE` selectors)

The selectors of this section are documented for the heat pump interface units
covered by the community configuration named in the Evidence paragraph below;
whether other heat pump interface units use the same selectors is not
established (candidate). The heat pump interface unit uses a **5-byte B509 selector**: `54 02 00
[REG] [TYPE]`. This is an HP-specific extension of B509, not a separate
protocol. The `54 02 00` prefix is the key. The fifth byte (TYPE) is **part of
the register address** and encodes the expected data type. Sending the wrong
type byte will read a different register or cause a protocol error.

Wire format: `B509 54 02 00 [REG] [TYPE]` sent to HMU at address `0x08`.

**Hypothesis** (unconfirmed on the wire): the selector has the shape of the
data-point read `54` described in the
[protocol page](ebus-vaillant-B509.md#configuration-and-data-point-read-54):
`02` is the PeBUS address byte, `00` the configuration byte (read), and `REG`
and `TYPE` are the low and high byte of a 16-bit data-point address. On that
reading the "type byte" is the high byte of the address, which is consistent
with the same `REG` under different type bytes being different selectors (for
example `C5 09` and `C5 0B`). Each entry in the tables below carries its
canonical `Name`; the operation byte of every entry is `54` and the
correspondence fixture records the complete five-byte selector.

### Type byte encoding

| Type byte | Encoding | Description |
|-----------|----------|-------------|
| `0x08` | tempv | Temperature (D2C/16 signed, C) |
| `0x09` | EXP | Exponential (floating-point-like, various units) |
| `0x0A` | EXP | RPM (exponential, rotational) |
| `0x0B` | word (UIN) | Hours/counts (2-byte unsigned) |
| `0x0D` | enum | Status/diagnostic code |
| `0x0E` | tempv signed | Temperature (D2C, diagnostic variant, C) |

### Evidence

All heat pump interface unit registers:
burmistrzak/ebusd-configuration `src/vaillant/08.hmu.HW5103.tsp` [L14-L400].
Corroborated structurally by pulquero `08.hmu.HW5103.SW0607.csv`,
morphZ `08.hmu00.HW5103.csv`, jonesPD `08.hmu.csv`, xerion3800 `08.hmu.csv`.

All registers are MEDIUM confidence (single primary TSP source with structural
corroboration).

### Operational sensors

The earlier map names are kept for cross-reference only; the canonical name is the `Name` column.

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | Notes |
|---------------------|------|-----|-----------------------------------|------|------|-------|
| `54 02 00 0D 0A` | `compressor_speed` | `0D` | `compressor_speed` (`CompressorSpeed`) | EXP | -- | Zero when compressor is stopped. The unit is unresolved: another community configuration gives rps; see Open questions |
| `54 02 00 28 0A` | `electronic_expansion_valve_absolute_position` | `28` | `eev_position_abs` (`EevPositionAbs`) | EXP | steps | Absolute EEV (electronic expansion valve) position |
| `54 02 00 47 0A` | `fan_1_speed` | `47` | `fan1_speed` (`Fan1Speed`) | EXP | RPM | Fan 1 speed |
| `54 02 00 49 0A` | `fan_2_speed` | `49` | `fan2_speed` (`Fan2Speed`) | EXP | RPM | Fan 2 speed; 0 if fan 2 absent on units with a single fan |
| `54 02 00 5B 09` | `electrical_input_power` | `5B` | `electric_power_consumption` (`ElectricPowerConsumption`) | EXP | -- | Current electrical power; the unit is unresolved. Distinct from B51A `CurrentConsumedPower` (kW). Other community configurations give type byte `0D` for the same register; see Open questions |
| `54 02 00 BD 09` | `water_flow_rate` | `BD` | `diag_water_throughput` (`DiagWaterThroughput`) | EXP | l/h | Water flow rate; complements B512 StatusHydraulics flow |
| `54 02 00 C5 09` | `building_pump_output_level` | `C5` | `building_pump_power` (`BuildingPumpPower`) | EXP | -- | Building pump output level. No B51A equivalent -- only source for this metric. The unit is unresolved (community configurations give W or %; see Open questions) |

### Status and diagnostics

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | Notes |
|---------------------|------|-----|-----------------------------------|------|------|-------|
| `54 02 00 53 0D` | `operating_status_code` | `53` | `statuscode` (`Statuscode`) | enum | -- | Diagnostic status code; non-zero indicates active fault. Another community configuration enumerates operating states for this selector; see Open questions |

### Pressures

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | Notes |
|---------------------|------|-----|-----------------------------------|------|------|-------|
| `54 02 00 6A 09` | `refrigerant_high_pressure` | `6A` | `high_pressure` (`HighPressure`) | EXP | bar | High-side refrigerant pressure; may be higher precision than generic EHP `0x1400` |

### Temperatures

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | Notes |
|---------------------|------|-----|-----------------------------------|------|------|-------|
| `54 02 00 98 08` | `compressor_inlet_temperature` | `98` | `compressor_inlet_temp` (`CompressorInletTemp`) | tempv | C | Compressor inlet refrigerant temperature (absolute); distinct from generic `0x8D00` Superheat (delta) |
| `54 02 00 A2 08` | `compressor_outlet_temperature` | `A2` | `compressor_outlet_temp` (`CompressorOutletTemp`) | tempv | C | Compressor outlet refrigerant temperature |
| `54 02 00 AC 08` | `electronic_expansion_valve_outlet_temperature` | `AC` | `eev_outlet_temp` (`EevOutletTemp`) | tempv | C | EEV outlet refrigerant temperature. Whether this sensor is the expansion valve outlet is unresolved; see Open questions |
| `54 02 00 DE 08` | `air_inlet_temperature` | `DE` | `air_inlet_temp` (`AirInletTemp`) | tempv | C | Outdoor air temperature at heat pump inlet; important for COP estimation and defrost control |

### Diagnostic temperatures

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | Notes |
|---------------------|------|-----|-----------------------------------|------|------|-------|
| `54 02 00 A6 0E` | `refrigerant_condensation_temperature` | `A6` | `diag_flow_temp` (`DiagFlowTemp`) | tempv | C | Diagnostic flow temperature; may differ from B524 FlowTemp under fault conditions. Whether this is a refrigerant condensation temperature is unresolved; see Open questions |
| `54 02 00 A7 0E` | `refrigerant_evaporation_temperature` | `A7` | `diag_evaporation_temp` (`DiagEvaporationTemp`) | tempv | C | Diagnostic evaporator temperature |
| `54 02 00 A9 0E` | `refrigerant_superheat` | `A9` | `diag_overheating_actual_value` (`DiagOverheatingActualValue`) | tempv | K (delta) | Diagnostic overheating value; should correlate with generic EHP `0x8D00` Superheat. The name equals that of `0x8D00` but the entries stay separate |

### Lifecycle counters

| Full selector (hex) | Name | REG | Earlier map name (community ebusd name) | Type | Unit | B51A parallel | Notes |
|---------------------|------|-----|-----------------------------------|------|------|---------------|-------|
| `54 02 00 B8 0B` | `total_operating_time` | `B8` | `hours_total` (`HoursTotal`) | word | h | -- | Total HMU operating hours |
| `54 02 00 B9 0B` | `heating_operating_time` | `B9` | `hours_heating` (`HoursHeating`) | word | h | -- | Heating-mode hours |
| `54 02 00 BC 0B` | `dhw_operating_time` | `BC` | `hours_hwc` (`HoursHwc`) | word | h | -- | DHW-mode hours |
| `54 02 00 C2 0B` | `compressor_operating_time` | `C2` | `compressor_hours` (`CompressorHours`) | word | h | `05FF34` REG 0x00 | Parallel to B51A lifecycle counter |
| `54 02 00 C3 0B` | `compressor_start_count` | `C3` | `compressor_starts` (`CompressorStarts`) | word | count | `05FF34` REG 0x01 | Parallel to B51A lifecycle counter |
| `54 02 00 C4 0B` | `building_pump_operating_time` | `C4` | `building_pump_hours` (`BuildingPumpHours`) | word | h | `05FF34` REG 0x02 | Parallel to B51A lifecycle counter |
| `54 02 00 C5 0B` | `building_pump_start_count` | `C5` | `building_pump_starts` (`BuildingPumpStarts`) | word | count | -- | Note: sub-ID `C5` dual-use with type byte `09`=output level vs `0B`=starts |
| `54 02 00 C8 0B` | `four_way_valve_operating_time` | `C8` | `four_way_valve_hours` (`FourWayValveHours`) | word | h | `05FF34` REG 0x06 | Also known as Umschaltventil (4-way valve) |
| `54 02 00 C9 0B` | `four_way_valve_switch_count` | `C9` | `four_way_valve_switches` (`FourWayValveSwitches`) | word | count | `05FF34` REG 0x07 | 4-way valve switch count |
| `54 02 00 D7 0B` | `fan_1_operating_time` | `D7` | `fan1_hours` (`Fan1Hours`) | word | h | `05FF34` REG 0x51 | Fan 1 total operating hours |
| `54 02 00 D8 0B` | `fan_1_start_count` | `D8` | `fan1_starts` (`Fan1Starts`) | word | count | `05FF34` REG 0x52 | Fan 1 start count |
| `54 02 00 D9 0B` | `fan_2_operating_time` | `D9` | `fan2_hours` (`Fan2Hours`) | word | h | `05FF34` REG 0x5E | Fan 2 total operating hours; 0 on units with a single fan |
| `54 02 00 DA 0B` | `fan_2_start_count` | `DA` | `fan2_starts` (`Fan2Starts`) | word | count | `05FF34` REG 0x5F | Fan 2 start count |

### Note on `C5` dual-use

Sub-ID `0xC5` appears twice with different type bytes: `0x09` (EXP =
`building_pump_output_level`) and `0x0B` (word = `building_pump_starts`
count). The full 5-byte selector differs, and the HMU distinguishes them by
type byte. Both must be sent as independent requests.

### Note on B51A lifecycle counter parallels

Several HMU TypeSpec B509 lifecycle registers (CompressorHours, CompressorStarts,
BuildingPumpHours, FourWayValveHours, FourWayValveSwitches, Fan1Hours,
Fan1Starts, Fan2Hours, Fan2Starts) are parallel paths to the B51A `05FF34`
lifecycle counters. Both expose the same physical counters. If the values
diverge on a live scan, the discrepancy points to a firmware variant difference.

### Naming note (HWC/DHW)

Canonical naming uses `dhw_*` (snake_case) for domestic hot water.
The community ebusd names use `Hwc*` (camelCase). Both refer to the same thing.
The earlier map name column keeps the ebusd-style `Hwc` names.

---

## Open Questions

1. **Heat pump interface unit TypeSpec single-fork risk:** The public evidence
   for all 29 registers is a single community TypeSpec file (burmistrzak).
   Priority for live validation: `CompressorSpeed` (`0D`), `Fan1Speed` (`47`),
   `ElectricPowerConsumption` (`5B`), `AirInletTemp` (`DE`).

2. **C5 type byte disambiguation:** Does the HMU accept both `C5 09`
   (BuildingPumpPower) and `C5 0B` (BuildingPumpStarts) in a single polling
   session without confusion? Is there a defined ordering requirement?

3. **EHP `01`-suffix registers:** Page/bank vs instance selector semantics.
   Live scan comparing `XX00` vs `XX01` needed.

4. **DSN availability on EHP:** Can B509 `0x9A00` (DSN) reliably identify
   EHP00/HMU before attempting any other register, or must B514 be used?

5. **Two-byte ids on HMU-class units:** the section 1 ids are known only for
   the EHP00 identity (candidate). For the HMU product families the same
   numbers carry other meanings or none (candidate). Whether an HMU-class unit
   answers these ids is not established.

6. **`0x2401`:** candidate: noise reduction factor for air-to-brine-water heat
   pumps (community configuration). Another candidate meaning, unconfirmed on
   the wire, is a short error entry; which meaning applies to which devices of
   the class is unresolved, and so is the canonical name, which is provisional.

7. **`0xBC00`:** candidate: energy taken from the environment; another reading is
   the delivered heat yield (the earlier API path describes total heat yield).
   Which is correct is unresolved.

8. **`0xE901`, `0xE501` and `0x8000`:** the unit of `0xE901` is unresolved, and
   whether it is a limit or a recorded maximum is unresolved (the community
   comment reads maximum allowed low pressure for compressor protection). The
   unit of `0xE501` is unresolved. For `0x8000` the community comment is actual
   energy balancing integral; the degree-minute interpretation, the unit and the
   compressor qualifier are unconfirmed.

9. **`0x3F00`:** candidate interpretation, unconfirmed on the wire: an inrush
   current limiter output. Whether it is a bypass output is unresolved.

10. **HMU unit and type-byte conflicts:** `54 02 00 0D 0A` is given in rps by
    another community configuration and the map lists RPM; the unit is unresolved. `54 02 00 C5 09` is given in
    W by some community configurations and in % by others; the unit is
    unresolved. `54 02 00 5B 09`: other community configurations give type byte
    `0D` for the same register; which type byte is correct is unresolved.

11. **HMU naming conflicts:** the map's table text calls
    `54 02 00 A6 0E` a diagnostic flow temperature; another candidate meaning,
    unconfirmed on the wire, is a refrigerant condensation temperature (the
    canonical name follows that candidate); which reading is correct is
    unresolved. Whether `54 02 00 AC 08` is the expansion valve outlet sensor is
    unresolved; another candidate meaning, unconfirmed on the wire, is an
    environment-circuit heat-exchanger inlet temperature. Whether
    `54 02 00 A9 0E` equals `0x8D00` is unresolved.
    `54 02 00 53 0D` is described here as a fault code while another community
    configuration enumerates operating states for it. A community comment
    questions the scale of `54 02 00 28 0A`.

12. **HMU selector shape:** the equivalence of `54 02 00 REG TYPE` with the
    `54` data-point read (PeBUS address byte `02`, configuration byte `00`,
    address `REG` `TYPE`) is unconfirmed on the wire.

## Appendix: Semantic FSMs (Heat Pump)

> **Hypothesis:** The following state-machine interpretations derive from register meanings; transitions require correlated native observations before qualification.

### `heat_pump_status` (0xD000)

Register `0xD000` encodes the top-level heat pump operating mode as a `hpstatus` UCH enum. Public community configurations list the register for EHP00 and HMU at address `0x08` (candidate; whether HMU-class units answer the section 1 ids is not established, see Open questions).

| Value | State | Description |
|-------|-------|-------------|
| 0x00 | `standby` | Heat pump idle, no demand |
| 0x01 | `heating` | Active heating cycle |
| 0x02 | `cooling` | Active cooling cycle (reversible HP only) |
| 0x03 | `dhw` | DHW heating cycle |
| 0x04 | `defrost` | Defrost/de-icing cycle |

> WARNING: Exact numeric values are NOT fully confirmed. Encoding confidence: LOW. Register existence confidence: HIGH.

**Transitions:** standby -> heating/dhw/cooling (demand). heating -> defrost (evaporator icing). defrost -> heating (DeicingActive 0xCE01 drops to `no`). All active states -> standby (demand satisfied).

**Related registers:** `0xCE01` DeicingActive, `0xE400` CompState, `0xE900` CompControlState, B511 selector `0x07`, B51A `0x23` CurrentYieldPower.

### `compressor_state` (0xE400)

Register `0xE400` encodes the compressor sub-state as a UCH enum. Runs in parallel with `heat_pump_status`.

| Value | State | Description |
|-------|-------|-------------|
| 0x00 | `off` | Compressor not running |
| 0x01 | `starting` | Start sequence in progress |
| 0x02 | `running` | Operating normally |
| 0x03 | `stopping` | Stop sequence (anti-short-cycle lockout) |
| 0x04 | `blocked` | Blocked by high-pressure cut-out or timing constraint |

> WARNING: Exact numeric values are NOT confirmed. Encoding confidence: LOW. Register existence confidence: HIGH.

**Timing gates:** `0xE600` TimeCompOnMin (minimum on-time), `0xE700` TimeCompOffMin (minimum off-time), `0xE800` TimeBetweenTwoCompStartsMin (inter-start delay). The compressor cannot transition off->starting until both TimeCompOffMin and inter-start intervals have elapsed.

### `deicing_active` (0xCE01)

Register `0xCE01` is a `yesno` bool: `0x00` = normal, `0x01` = defrost cycle active.

Transitions: normal -> defrost_active when evaporator icing sensor threshold exceeded. defrost_active -> normal when defrost cycle completes. Related: B514 REG `0x14` (four-way valve switches to defrost position), B51A `0x23` CurrentYieldPower (goes negative during defrost).

**Confidence:** HIGH.

---

## References

- Protocol spec: [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md)
- Boiler register map: [`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md)
- Register name correspondence fixture: [`fixtures/b509-register-name-correspondence.csv`](fixtures/b509-register-name-correspondence.csv)
- Public TypeSpec: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration)
