# Vaillant B509 Heat Pump Register Map (EHP00 / HMU)

This document covers the B509 register space for heat pump devices at eBUS
address `0x08`. It is separate from the
[boiler register map](ebus-vaillant-B509-boiler-register-map.md) because **the
same eBUS address hosts either a BAI00 (boiler) or an EHP00/HMU (heat pump),
and many register addresses have different semantics depending on the device
type**. See the
[Device-Type Gate section](ebus-vaillant-B509.md#device-type-gate-register-address-collision)
in the protocol doc.

## Device-Type Gate

All registers in this document apply ONLY to EHP00 and HMU heat pump devices at
address `0x08`. They MUST NOT be read from a BAI00 boiler at the same address.
Product identification must be established first via B514 identity frame or
B509 `0x9A00` (DSN) before interpreting any register in this map.

Known address collisions with the BAI00 boiler register map:

| Register ID | BAI00 (boiler) meaning | EHP00/HMU (heat pump) meaning |
|------------:|------------------------|-------------------------------|
| `0x3F00` | `externalPumpActive` (on/off) | `ICLOut` -- inrush current limiter (on/off) |
| `0xBB00` | `gasValveActive` (UCH 0x0F/0xF0) | `ActualEnvPowerPercentage` (percent0, %) |
| `0x1400` | `pumpHours` (Hoursum2, hours) | `CompPressHigh` -- high-side compressor pressure (sensor, bar) |
| `0xE400` | `externGasvalve` (on/off) | `compressorState` (UCH enum) |

## Status

All registers in this document are from enrichment analysis (2026-04-14). None
are currently mapped into the Helianthus semantic plane. They are documented
for future integration and live validation.

Evidence labels:

- `ENRICHMENT_D1`: `_work_enrichment/phase2/D1-B509-deep.md` -- EHP deep analysis
- `ENRICHMENT_D10`: `_work_enrichment/phase2/D10-new-devices-deep.md` -- HMU HW5103 analysis
- `ENRICHMENT_D11`: `_work_enrichment/phase2/D11-fork-B509-B51A-enrichment.md` -- cross-fork delta
- `P1`: community fork primary source (single fork)
- `P1+P2`: confirmed by two independent forks

---

## 1. EHP00 Standard Registers (2-byte B509 IDs)

These use the standard 2-byte B509 ID format, identical to BAI00 wire shape.

### Operating state and yield

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.heatPumpStatus` | `0xD000` | `hpstatus` enum | R | HIGH | ENRICHMENT_D1 -> P1+P2 | Heat pump operating state (heating, cooling, defrost, standby, etc.) |
| `energy.yieldTotal` | `0xBC00` | `energy4` (kWh) | R | HIGH | ENRICHMENT_D1 -> P1+P2 | Total lifetime heat yield in kWh (4-byte value) |
| `state.actualEnvironmentPower` | `0xBA00` | `power` (kW) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Actual environmental (source) power in kW |
| `state.actualEnvPowerPercentage` | `0xBB00` | `percent0` (%) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Environmental power as percentage (0-100). **Collision**: same address as BAI00 `gasValveActive` |

### Refrigerant circuit

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.superheat` | `0x8D00` | `temp` (K delta) | R | HIGH | ENRICHMENT_D1 -> P1+P2 | Refrigerant superheat at compressor inlet (signed temperature delta in Kelvin) |
| `state.subcooling` | `0x8E00` | `temp` (K delta) | R | HIGH | ENRICHMENT_D1 -> P1+P2 | Refrigerant subcooling at condenser outlet (signed temperature delta in Kelvin) |
| `state.sourceTempInput` | `0x0F00` | `tempsensor` (C) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Source-side (air or ground) inlet temperature |
| `state.compressorPressureHigh` | `0x1400` | `sensor` (bar) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | High-side compressor pressure. **Collision**: same address as BAI00 `pumpHours` |
| `state.compressorPressureLow` | `0x1500` | `sensor` (bar) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Low-side compressor pressure |

### Compressor control and timing

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.compressorState` | `0xE400` | `UCH` enum | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Compressor state machine position. **Collision**: same address as BAI00 `externGasvalve` |
| `state.compressorControlState` | `0xE900` | `UCH` enum | R | MEDIUM | ENRICHMENT_D1 -> single source | Compressor control algorithm state |
| `config.timeCompOnMin` | `0xE600` | `seconds` (s) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Minimum compressor-on time |
| `config.timeCompOffMin` | `0xE700` | `seconds` (s) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Minimum compressor-off time |
| `config.timeBetweenTwoCompStartsMin` | `0xE800` | `seconds` (s) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Minimum required interval between two compressor start events |
| `diagnostics.compressorStartsHwc` | `0xA800` | `counter` (count) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Compressor starts attributed to DHW operation |
| `diagnostics.compressorCutPressHighCount` | `0xB400` | `counter` (count) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | High-pressure cut-out event counter |

### Defrost

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.deicingActive` | `0xCE01` | `yesno` (bool) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Defrost/de-icing cycle active. The `01` suffix may indicate register page/bank |

### Electrical / phase

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.phaseOrder` | `0x5701` | `phaseok` enum | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Phase-order check result (correct L1-L2-L3 sequence) |
| `state.phaseStatus` | `0x8800` | `phase flags` (bitmask) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Phase status flags (phase loss, undervoltage, etc.) |
| `state.iclOut` | `0x3F00` | `on/off` | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Inrush current limiter bypass output state. **Collision**: same address as BAI00 `externalPumpActive` |

### Noise reduction (VWLS)

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.noiseReduction` | `0xA901` | `yesno` (bool) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Night/noise reduction mode active |
| `config.noiseReductionFactor` | `0x2401` | `percent0` (%) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Active noise reduction factor (0-100%) |

### Other

| Semantic Path (candidate) | B509 register | Codec / scale | R/W | Confidence | Evidence | Notes |
|---------------------------|---------------|---------------|-----|------------|----------|-------|
| `state.actualEnvPowerFine` | `0xE201` | `UCH` (100W units) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Actual environmental power in units of 100 W (multiply byte by 100) |
| `state.bivalentMode` | `0xE301` | `UCH` enum | R | MEDIUM | ENRICHMENT_D1 -> single source | Bivalence operating mode (heat pump only, backup boiler active, etc.) |
| `config.sourceLimitAtMaxFlow` | `0xE401` | `SCH` (C, signed) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Signed source temperature limit at maximum flow |
| `config.sourceLimitSlope` | `0xE501` | `UCH` (slope) | R | MEDIUM | ENRICHMENT_D1 -> slope unit not fully decoded | Source temperature limit slope characteristic |
| `state.maxNdPressure` | `0xE901` | `ULG` (Pa) | R | MEDIUM | ENRICHMENT_D1 -> P1 only | Maximum ND (fan duct) pressure in Pascal (4-byte ULG). Unusual type for pressure |
| `state.integral` | `0x8000` | `value` (unknown) | R | LOW | ENRICHMENT_D1 -> P1 only | Control algorithm integral value. Type and unit unconfirmed |

### Note on `01`-suffix EHP registers

Registers `0xCE01`, `0xA901`, `0x5701`, `0x2401`, `0xE201`, `0xE301`,
`0xE401`, `0xE501`, `0xE901` use a `01` second byte. This may indicate a
second register page/bank or instance selector. A live scan comparing `XX00`
vs `XX01` is needed to confirm the semantics. The pattern is consistent:
`XX01` where `XX` is the primary register byte.

---

## 2. HMU HW5103 TypeSpec Registers (`540200xx` sub-addressing)

The HMU HW5103 hardware variant uses a **5-byte B509 selector**: `54 02 00
[REG] [TYPE]`. This is an HP-specific extension of B509, not a separate
protocol. The `54 02 00` prefix is the key. The fifth byte (TYPE) is **part of
the register address** and encodes the expected data type. Sending the wrong
type byte will read a different register or cause a protocol error.

Wire format: `B509 54 02 00 [REG] [TYPE]` sent to HMU at address `0x08`.

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

All HMU HW5103 registers: ENRICHMENT_D10 S2 + ENRICHMENT_D11 S1.3 ->
burmistrzak/ebusd-configuration `src/vaillant/08.hmu.HW5103.tsp` [L14-L400].
Corroborated structurally by pulquero `08.hmu.HW5103.SW0607.csv`,
morphZ `08.hmu00.HW5103.csv`, jonesPD `08.hmu.csv`, xerion3800 `08.hmu.csv`.

All registers are MEDIUM confidence (single primary TSP source with structural
corroboration).

### Operational sensors

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | Notes |
|---------------------|-----|-----------------------------------|------|------|-------|
| `54 02 00 0D 0A` | `0D` | `compressor_speed` (`CompressorSpeed`) | EXP | RPM | Zero when compressor is stopped |
| `54 02 00 28 0A` | `28` | `eev_position_abs` (`EevPositionAbs`) | EXP | steps | Absolute EEV (electronic expansion valve) position |
| `54 02 00 47 0A` | `47` | `fan1_speed` (`Fan1Speed`) | EXP | RPM | Fan 1 speed |
| `54 02 00 49 0A` | `49` | `fan2_speed` (`Fan2Speed`) | EXP | RPM | Fan 2 speed; 0 if fan 2 absent on single-fan models |
| `54 02 00 5B 09` | `5B` | `electric_power_consumption` (`ElectricPowerConsumption`) | EXP | W | Current electrical power in Watts. Distinct from B51A `CurrentConsumedPower` (kW) |
| `54 02 00 BD 09` | `BD` | `diag_water_throughput` (`DiagWaterThroughput`) | EXP | l/h | Water flow rate; complements B512 StatusHydraulics flow |
| `54 02 00 C5 09` | `C5` | `building_pump_power` (`BuildingPumpPower`) | EXP | W | Building pump electrical power. No B51A equivalent -- only source for this metric |

### Status and diagnostics

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | Notes |
|---------------------|-----|-----------------------------------|------|------|-------|
| `54 02 00 53 0D` | `53` | `statuscode` (`Statuscode`) | enum | -- | Diagnostic status code; non-zero indicates active fault |

### Pressures

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | Notes |
|---------------------|-----|-----------------------------------|------|------|-------|
| `54 02 00 6A 09` | `6A` | `high_pressure` (`HighPressure`) | EXP | bar | High-side refrigerant pressure; may be higher precision than generic EHP `0x1400` |

### Temperatures

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | Notes |
|---------------------|-----|-----------------------------------|------|------|-------|
| `54 02 00 98 08` | `98` | `compressor_inlet_temp` (`CompressorInletTemp`) | tempv | C | Compressor inlet refrigerant temperature (absolute); distinct from generic `0x8D00` Superheat (delta) |
| `54 02 00 A2 08` | `A2` | `compressor_outlet_temp` (`CompressorOutletTemp`) | tempv | C | Compressor outlet refrigerant temperature |
| `54 02 00 AC 08` | `AC` | `eev_outlet_temp` (`EevOutletTemp`) | tempv | C | EEV outlet refrigerant temperature |
| `54 02 00 DE 08` | `DE` | `air_inlet_temp` (`AirInletTemp`) | tempv | C | Outdoor air temperature at heat pump inlet; important for COP estimation and defrost control |

### Diagnostic temperatures

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | Notes |
|---------------------|-----|-----------------------------------|------|------|-------|
| `54 02 00 A6 0E` | `A6` | `diag_flow_temp` (`DiagFlowTemp`) | tempv | C | Diagnostic flow temperature; may differ from B524 FlowTemp under fault conditions |
| `54 02 00 A7 0E` | `A7` | `diag_evaporation_temp` (`DiagEvaporationTemp`) | tempv | C | Diagnostic evaporator temperature |
| `54 02 00 A9 0E` | `A9` | `diag_overheating_actual_value` (`DiagOverheatingActualValue`) | tempv | K (delta) | Diagnostic overheating value; should correlate with generic EHP `0x8D00` Superheat |

### Lifecycle counters

| Full selector (hex) | REG | snake_case name (ebusd camelCase) | Type | Unit | B51A parallel | Notes |
|---------------------|-----|-----------------------------------|------|------|---------------|-------|
| `54 02 00 B8 0B` | `B8` | `hours_total` (`HoursTotal`) | word | h | -- | Total HMU operating hours |
| `54 02 00 B9 0B` | `B9` | `hours_heating` (`HoursHeating`) | word | h | -- | Heating-mode hours |
| `54 02 00 BC 0B` | `BC` | `hours_hwc` (`HoursHwc`) | word | h | -- | DHW-mode hours |
| `54 02 00 C2 0B` | `C2` | `compressor_hours` (`CompressorHours`) | word | h | `05FF34` REG 0x00 | Parallel to B51A lifecycle counter |
| `54 02 00 C3 0B` | `C3` | `compressor_starts` (`CompressorStarts`) | word | count | `05FF34` REG 0x01 | Parallel to B51A lifecycle counter |
| `54 02 00 C4 0B` | `C4` | `building_pump_hours` (`BuildingPumpHours`) | word | h | `05FF34` REG 0x02 | Parallel to B51A lifecycle counter |
| `54 02 00 C5 0B` | `C5` | `building_pump_starts` (`BuildingPumpStarts`) | word | count | -- | Note: sub-ID `C5` dual-use with type byte `09`=power vs `0B`=starts |
| `54 02 00 C8 0B` | `C8` | `four_way_valve_hours` (`FourWayValveHours`) | word | h | `05FF34` REG 0x06 | Also known as Umschaltventil (4-way valve) |
| `54 02 00 C9 0B` | `C9` | `four_way_valve_switches` (`FourWayValveSwitches`) | word | count | `05FF34` REG 0x07 | 4-way valve switch count |
| `54 02 00 D7 0B` | `D7` | `fan1_hours` (`Fan1Hours`) | word | h | `05FF34` REG 0x51 | Fan 1 total operating hours |
| `54 02 00 D8 0B` | `D8` | `fan1_starts` (`Fan1Starts`) | word | count | `05FF34` REG 0x52 | Fan 1 start count |
| `54 02 00 D9 0B` | `D9` | `fan2_hours` (`Fan2Hours`) | word | h | `05FF34` REG 0x5E | Fan 2 total operating hours; 0 on single-fan models |
| `54 02 00 DA 0B` | `DA` | `fan2_starts` (`Fan2Starts`) | word | count | `05FF34` REG 0x5F | Fan 2 start count |

### Note on `C5` dual-use

Sub-ID `0xC5` appears twice with different type bytes: `0x09` (EXP =
`building_pump_power` in Watts) and `0x0B` (word = `building_pump_starts`
count). The full 5-byte selector differs, and the HMU distinguishes them by
type byte. Both must be sent as independent requests.

### Note on B51A lifecycle counter parallels

Several HMU TypeSpec B509 lifecycle registers (CompressorHours, CompressorStarts,
BuildingPumpHours, FourWayValveHours, FourWayValveSwitches, Fan1Hours,
Fan1Starts, Fan2Hours, Fan2Starts) are parallel paths to the B51A `05FF34`
lifecycle counters. Both expose the same physical counters. If the values
diverge on a live scan, the discrepancy points to a firmware variant difference.

### Naming note (HWC/DHW)

Canonical Helianthus naming uses `dhw_*` (snake_case) for domestic hot water.
The ebusd source uses `Hwc*` (camelCase). Both refer to the same thing. Entries
above preserve the ebusd-style `Hwc` names as extracted from the TypeSpec source.

---

## Open Questions

1. **HMU HW5103 TypeSpec single-fork risk:** All 29 registers come from
   burmistrzak's TSP alone. Priority for live validation: `CompressorSpeed`
   (`0D`), `Fan1Speed` (`47`), `ElectricPowerConsumption` (`5B`),
   `AirInletTemp` (`DE`).

2. **C5 type byte disambiguation:** Does the HMU accept both `C5 09`
   (BuildingPumpPower) and `C5 0B` (BuildingPumpStarts) in a single polling
   session without confusion? Is there a defined ordering requirement?

3. **EHP `01`-suffix registers:** Page/bank vs instance selector semantics.
   Live scan comparing `XX00` vs `XX01` needed.

4. **DSN availability on EHP:** Can B509 `0x9A00` (DSN) reliably identify
   EHP00/HMU before attempting any other register, or must B514 be used?

## Appendix: Semantic FSMs (Heat Pump)

> Source: `GATES-semantic-fsms.md` Sections 1.1-1.3, 1.6. These FSMs document the state machines implicit in EHP00/HMU registers.

### `heat_pump_status` (0xD000)

Register `0xD000` encodes the top-level heat pump operating mode as a `hpstatus` UCH enum. The register is confirmed on EHP00 and HMU at address `0x08`.

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
- Enrichment report: `_work_enrichment/final/FINAL-B509.md`
- Cross-check: `_work_enrichment/final/CROSSCHECK-B509.md`
- Public TypeSpec: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration)
