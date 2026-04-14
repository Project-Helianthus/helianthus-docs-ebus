# Vaillant B514 Service Test-Menu / Heat-Pump Live Sensor Protocol

`PB=0xB5`, `SB=0x14`.

## Status

> **Reclassification (2026-04-14 enrichment):** This protocol was previously
> documented as "Service Test-Menu Values" with 5 TypeSpec-derived selectors only.
> Enrichment from two independent live-install sources (P1: cyberthom42/vaillant-arotherm-plus,
> P5: OpenHAB eBUS binding hmu08_config.json) shows B514 carries **37 live sensor
> registers** across two device groups, plus 1 unresolved TypeSpec-only entry (0x45).
> The protocol delivers continuous compressor temperatures, refrigerant pressures,
> fan speeds, valve states, and hydraulic readings — readable without documented
> service-mode activation (see OQ-2 caveat).

**Device gate:** HMU heat pump outdoor units (HMU00 at address 0x08) and VWZIO
indoor hydraulic stations (address 0x76). Not applicable to BAI boiler devices.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.
- `P1`: cyberthom42/vaillant-arotherm-plus GitHub repo — `08.hmu.csv` (live-install).
- `P5`: OpenHAB eBUS binding community thread — `hmu08_config.json` (live-install).
- `BOTH`: present in P1 AND P5 (HIGH confidence).
- `P1-ONLY`: present in P1 only (MEDIUM confidence).
- `TYPESPEC`: john30 TypeSpec only (LOW confidence for live use).

## Wire Shape

> **CORRECTION C1 (2026-04-14):** The previous wire format described a 2-byte read
> form `05 <selector>` and a separate write form `05 03 FF FF <selector>`. This was
> derived from TypeSpec template parsing only. Both P1 (38 registers) and P5 (20
> registers) use a **5-byte read payload** for ALL reads. The 2-byte short-form read
> has no live capture evidence.

Corrected universal read request payload:

```text
05 [REG] 03 FF FF
```

- `05` — fixed sub-protocol discriminator (both HMU and VWZIO groups)
- `[REG]` — 1-byte register index (hex)
- `03 FF FF` — service-mode read qualifier + padding, present on ALL read requests

Evidence: P5 `hmu08_config.json` field `"command": "05 [REG] 03 FF FF"` for all 20
registers. P1 `08.hmu.csv` uses the same 5-byte payload for all 38 distinct registers.

Falsification test: capture any B514 read on a live arotherm plus installation and
show the request payload is `05 <REG>` (2 bytes) rather than `05 [REG] 03 FF FF`
(5 bytes).

The TypeSpec write templates (`05 03 FF FF <selector>` for VWZ/VWZIO, `00 00 00` for
some HMU EEV tests) remain as documented. Treat write constants as target-specific
until verified by capture.

## Register Map

### Type notation

- `word` — unsigned 16-bit integer (uint16)
- `uchar` — unsigned 8-bit integer (uint8)
- `signed/10` — signed 16-bit integer (int16) x 0.1 (see Correction C2)
- `word/10` — unsigned 16-bit integer x 0.1
- `UIN/10` — same encoding as word/10 (different naming convention)
- `D2B` — ebusd 2-byte BCD-like scaled format
- `openclose` — 1-byte contact state (0=open / 1=closed or device-specific)
- `calibration` — ebusd calibration/signed-delta type (K offset)
- `vuv` — valve/unit-valve type (VWZIO specific)
- `onoff` — 1-byte boolean (0=off / 1=on)

### Group T.0 — HMU Outdoor Unit (HMU00, address 0x08)

| REG hex | REG dec | T.idx | `snake_case` name | ebusd `camelCase` | Type | Unit | Confidence | Evidence | Falsifiable claim |
|---------|---------|-------|-------------------|-------------------|------|------|------------|----------|-------------------|
| 0x01 | 1 | T.0.01 | `building_pump_power` | `BuildgPumpPower` | word | % | BOTH | P1: 08.hmu.csv T.0.01 (UIN); P5: hmu08_config.json reg 1 (word x 1) | Read 0x01 during active pump operation; value must be 0-100% tracking pump modulation demand. |
| 0x11 | 17 | T.0.17 | `power_fan1` | `PowerFan1` | word | % | BOTH | P1: 08.hmu.csv T.0.17 (UIN); P5: hmu08_config.json reg 17 (word x 1) | Read 0x11; value must be 0-100% tracking fan 1 PWM duty cycle. |
| 0x12 | 18 | T.0.18 | `power_fan2` | `PowerFan2` | word | % | BOTH | P1: 08.hmu.csv T.0.18 (UIN); P5: hmu08_config.json reg 18 (word x 1) — dual-fan VWLS only | Read 0x12 on dual-fan VWLS; 0-100% for fan 2. Single-fan units: 0 or NAK. |
| 0x13 | 19 | T.0.19 | `condenser_pan_heat` | `CondensPanHeat` | uchar | 0/1 | BOTH | P1: 08.hmu.csv T.0.19 (onoff); P5: hmu08_config.json reg 19 (uchar x 1) | Read 0x13 during frost risk (<=2C); must be 0x01. Above 5C: 0x00. |
| 0x14 | 20 | T.0.20 | `pos_4way_valve` | `Pos4WayValve` | uchar | 0=Heat / 1=Defrost | BOTH | P1: 08.hmu.csv T.0.20 (onoff); P5: hmu08_config.json reg 20 (uchar x 1) | Read 0x14; heating=0x00, defrost=0x01. |
| 0x15 | 21 | T.0.21 | `eev_position` | `EEVPosition` | word | % | BOTH | P1: 08.hmu.csv T.0.21 (UIN); P5: hmu08_config.json reg 21 (word x 1) | Read 0x15; value 0-100% tracking EEV step position. **CORRECTION C5:** was `EnableTestEEVPosition` (TypeSpec write-enable). P1+P5 confirm live read of EEV position in %. |
| 0x17 | 23 | T.0.23 | `comp_heat` | `CompHeat` | uchar | 0/1 | BOTH | P1: 08.hmu.csv T.0.23 (onoff); P5: hmu08_config.json reg 23 (uchar x 1) | Read 0x17; compressor off=0x01 (crankcase heater active), running=0x00. |
| 0x28 | 40 | T.0.40 | `flow_temp` | `FlowTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.40 (UIN/10); P5: hmu08_config.json reg 40 (number(2) x 0.1) | Read 0x28 during heating; value -10..80C matching HC flow sensor within +/-1C. |
| 0x29 | 41 | T.0.41 | `return_temp` | `ReturnTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.41 (UIN/10); P5: hmu08_config.json reg 41 (number(2) x 0.1) | Read 0x29; must match HC return sensor and be lower than FlowTemp (0x28). |
| 0x2A | 42 | T.0.42 | `water_pressure` | `WaterPressure` | UIN/10 | bar | P1-ONLY | P1: 08.hmu.csv T.0.42 (UIN/10); absent from P5 | Read 0x2A; value 0.5-3.5 bar matching hydraulic gauge within +/-0.2 bar. |
| 0x2B | 43 | T.0.43 | `water_throughput` | `WaterThroughput` | word | l/h | BOTH | P1: 08.hmu.csv T.0.43 (UIN); P5: hmu08_config.json reg 43 (word x 1) | Read 0x2B during pump operation; 200-2000 l/h. Pump off: 0. |
| 0x30 | 48 | T.0.48 | `air_in_temp` | `AirInTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.48 (UIN/10); P5: hmu08_config.json reg 48 (number(2) x 0.1) | Read 0x30; value -30..50C matching outdoor ambient within +/-2C. |
| 0x37 | 55 | T.0.55 | `compressor_out_temp` | `CompressorOutTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.55 (UIN/10); P5: hmu08_config.json reg 55 (number(2) x 0.1) | Read 0x37 during compressor operation; 40-120C discharge temperature. |
| 0x38 | 56 | T.0.56 | `compressor_in_temp` | `CompressorInTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.56 (UIN/10); P5: hmu08_config.json reg 56 (number(2) x 0.1) | Read 0x38 in heating mode; -30..20C, lower than AirInTemp (0x30). |
| 0x39 | 57 | T.0.57 | `eev_out_temp` | `EEVOutTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.57 (UIN/10); P5: hmu08_config.json reg 57 (number(2) x 0.1) | Read 0x39; close to or below EvaporTemp (0x55), range -30..40C. |
| 0x3B | 59 | T.0.59 | `condenser_out_temp` | `CondenserOutTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.59 (UIN/10); P5: hmu08_config.json reg 59 (number(2) x 0.1) | Read 0x3B during heating; 30-90C tracking condenser outlet. **CORRECTION C4:** was `EnableTestEEVTemp` (TypeSpec). P1+P5 confirm live condenser outlet temperature. |
| 0x3F | 63 | T.0.63 | `high_pressure` | `HighPressure` | **UNRESOLVED** (D2B vs word/10) | bar | BOTH (type conflict) | P1: 08.hmu.csv T.0.63 (D2B); P5: hmu08_config.json reg 63 (word x 0.1). Type discrepancy unresolved — see OQ-1. | Decode with both methods; correct decode gives 10-40 bar (R32/R290 high-side). |
| 0x40 | 64 | T.0.64 | `low_pressure` | `LowPressure` | **UNRESOLVED** (D2B vs word/10) | bar | BOTH (type conflict) | P1: 08.hmu.csv T.0.64 (D2B); P5: hmu08_config.json reg 64 (word x 0.1). Type discrepancy unresolved — see OQ-1. | Decode with both methods; correct decode gives 2-8 bar (R32/R290 low-side). |
| 0x43 | 67 | T.0.67 | `high_pressure_switch` | `HighPressureSwitch` | openclose | -- | P1-ONLY | P1: 08.hmu.csv T.0.67 (openclose); absent from P5 | Read 0x43; normal=0x01 (closed), tripped=0x00 (open). |
| 0x55 | 85 | T.0.85 | `evapor_temp` | `EvaporTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.85 (UIN/10); P5: hmu08_config.json reg 85 (number(2) x 0.1) | Read 0x55 in heating; -25..10C, at least 5C below outdoor ambient. |
| 0x56 | 86 | T.0.86 | `condens_temp` | `CondensTemp` | signed/10 | C | BOTH | P1: 08.hmu.csv T.0.86 (UIN/10); P5: hmu08_config.json reg 86 (number(2) x 0.1) | Read 0x56 during heating; 30-90C tracking condensing temperature. |
| 0x57 | 87 | T.0.87 | `superheat_setpoint` | `SuperheatSetpoint` | calibration | K | P1-ONLY | P1: 08.hmu.csv T.0.87 (calibration); absent from P5 | Read 0x57; value 2-20 K (typical EEV superheat setpoint). |
| 0x58 | 88 | T.0.88 | `superheat_actual` | `SuperheatActual` | calibration | K | P1-ONLY | P1: 08.hmu.csv T.0.88 (calibration); absent from P5 | Read 0x58; must match CompressorInTemp(0x38) minus EvaporTemp(0x55) within +/-2 K. |
| 0x59 | 89 | T.0.89 | `subcooling_setpoint` | `SubcoolingSetpoint` | calibration | K | P1-ONLY | P1: 08.hmu.csv T.0.89 (calibration); absent from P5 | Read 0x59; value 2-15 K (typical EEV subcooling setpoint). |
| 0x5A | 90 | T.0.90 | `subcooling_actual` | `SubcoolingActual` | calibration | K | P1-ONLY | P1: 08.hmu.csv T.0.90 (calibration); absent from P5 | Read 0x5A; must match CondensTemp(0x56) minus EEVOutTemp(0x39) within +/-2 K. |
| 0x5D | 93 | T.0.93 | `compressor_speed` | `CompressorSpeed` | word/10 | rev/s | BOTH | P1: 08.hmu.csv T.0.93 (UIN/10); P5: hmu08_config.json reg 93 (word x 0.1) | Read 0x5D; active compressor: 20-120 rev/s. Compressor off: 0. |
| 0x7B | 123 | T.0.123 | `comp_temp_switch` | `CompTempSwitch` | openclose | -- | P1-ONLY | P1: 08.hmu.csv T.0.123 (openclose); absent from P5 | Read 0x7B; normal(closed)=0x01, tripped(open)=0x00. |

**Group T.0 total: 27 registers (16 BOTH, 8 P1-ONLY, 2 pressure type-UNRESOLVED, 1 TypeSpec-legacy 0x45)**

### Group T.1 — VWZIO Indoor Hydraulic Station (address 0x76)

All T.1 registers are P1-ONLY (P5 tested HMU00 only, does not cover VWZIO).

| REG hex | REG dec | T.idx | `snake_case` name | ebusd `camelCase` | Type | Unit | Confidence | Evidence | Falsifiable claim |
|---------|---------|-------|-------------------|-------------------|------|------|------------|----------|-------------------|
| 0x02 | 2 | T.1.02 | `dhw_priority_valve` | `DHWPriorityValve` | vuv | -- | P1-ONLY (+ TYPESPEC) | P1: 08.hmu.csv VWZIO T.1.02 (vuv); TypeSpec 76.vwzio.tsp | Read 0x02 on VWZIO during active DHW priority; value must return valve-active state. **Note:** existing doc named this `TestThreeWayValve` (TypeSpec). P1 names it DHWPriorityValve — same register, different semantic. |
| 0x2C | 44 | T.1.44 | `storage_temp` | `StorageTemp` | UIN | -- | P1-ONLY (+ TYPESPEC) | P1: 08.hmu.csv VWZIO T.1.44 (UIN); TypeSpec 76.vwzio.tsp (selector 0x2C) | Read 0x2C; value 30-80C matching DHW storage sensor. **Note:** existing doc named this `TestHwcTemp` (TypeSpec). P1 names it StorageTemp — same physical quantity. |
| 0x2E | 46 | T.1.46 | `lock_contact_s20` | `LockContactS20` | openclose | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.46 (openclose) | Read 0x2E; S20 closed=0x01, open=0x00. |
| 0x46 | 70 | T.1.70 | `system_temp` | `SystemTemp` | UIN | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.70 (UIN) | Read 0x46; value 0-80C matching system mixed temperature sensor. |
| 0x48 | 72 | T.1.72 | `lock_contact_s21` | `LockContactS21` | openclose | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.72 (openclose) | Read 0x48; S21 closed=0x01, open=0x00. |
| 0x77 | 119 | T.1.119 | `ma1_output` | `MA1Output` | onoff | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.119 (onoff) | Read 0x77; energised=0x01, de-energised=0x00. |
| 0x7D | 125 | T.1.125 | `ma_input` | `MAInput` | openclose | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.125 (openclose) | Read 0x7D; contact closed=0x01, open=0x00. |
| 0x7E | 126 | T.1.126 | `ma2_output` | `MA2Output` | onoff | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.126 (onoff) | Read 0x7E; energised=0x01, de-energised=0x00. |
| 0x7F | 127 | T.1.127 | `ma_output` | `MAOutput` | onoff | -- | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.127 (onoff) | Read 0x7F; active=0x01, inactive=0x00. |
| 0x82 | 130 | T.1.130 | `backup_heater_flow_temp` | `BackupHeaterFlowTemp` | UIN/10 | C | P1-ONLY | P1: 08.hmu.csv VWZIO T.1.130 (UIN/10) | Read 0x82 during backup heater operation; 30-80C. |

**Group T.1 total: 10 registers (all P1-ONLY)**

### Legacy TypeSpec Entries

These selectors exist in the john30 TypeSpec files. They overlap with enriched
registers as noted below. REG 0x45 is the sole unresolved entry — absent from
both P1 and P5 live-install sources.

| REG hex | REG dec | TypeSpec name | Direction | Source | Status |
|---------|---------|---------------|-----------|--------|--------|
| 0x02 | 2 | `TestThreeWayValve` | read/write | TYPESPEC | Overlap with T.1.02 `DHWPriorityValve` on VWZIO |
| 0x15 | 21 | `EnableTestEEVPosition` | write | TYPESPEC | Same REG as T.0.21 `EEVPosition` — see Correction C5 |
| 0x2C | 44 | `TestHwcTemp` | read/write | TYPESPEC | Overlap with T.1.44 `StorageTemp` |
| 0x3B | 59 | `EnableTestEEVTemp` | read/write | TYPESPEC | Same REG as T.0.59 `CondenserOutTemp` — see Correction C4 |
| 0x45 | 69 | `TestOutdoorTemp` | read | TYPESPEC | **ABSENT from P1 and P5 — UNRESOLVED (OQ-3)**. Possibly firmware-variant specific or alias for AirInTemp (0x30). |

## Corrections Log (2026-04-14 Enrichment)

### C1 — Wire format: read payload is 5 bytes, not 2

**Was:** `05 <selector>` is the read form; `05 03 FF FF <selector>` is write-only.
**Now:** `05 [REG] 03 FF FF` is universal for all reads.
**Evidence:** P5 (20 registers, all 5-byte); P1 (38 registers, same pattern).
**Falsifiable:** Show a live capture with a 2-byte B514 read request that returns valid data.

### C2 — Temperature registers must be decoded as signed int16

**Was:** P1 CSV uses `UIN` (unsigned 16-bit) for temperature registers.
**Now:** Registers 0x28, 0x29, 0x30, 0x37, 0x38, 0x39, 0x3B, 0x55, 0x56 must be
decoded as int16 x 0.1 to handle sub-zero readings. UIN produces impossible values
for negative temperatures (e.g., -10C encodes as 0xFF9C; decoded unsigned = 6543.6C).
**Evidence:** P5 uses `number(2)` (signed). TypeSpec 08.hmu.tsp uses signed for
TestOutdoorTemp (0x45). Refrigeration physics: AirInTemp, EvaporTemp, and suction-line
temperatures routinely go below 0C.
**Falsifiable:** Capture AirInTemp (0x30) at below-zero outdoor ambient. Unsigned
decode gives >6000C; signed decode matches sensor within +/-1C.

### C3 — Protocol scope: not service-only, covers continuous live sensors

**Was:** "B514 belongs to service/test-menu behavior."
**Now:** The safety warning for writes remains valid. B514 reads deliver continuous
live sensor data not gated behind service-mode activation in P5's implementation.
The "Service Test-Menu" label reflects the controller UI menu path, not wire-level
data availability.
**Evidence:** P5 is a passive monitoring config with no enable writes; it reads all
20 registers successfully. P1 defines read templates without mandatory enable
prerequisites.
**Falsifiable:** Configure read-only B514 polling (no enable writes) on an arotherm
plus; registers 0x28, 0x30, 0x37 must return valid sensor values.

> **Service-gate caveat (CE-11):** P5 evidence shows passive monitoring works, but
> whether firmware requires prior service-menu activation is not confirmed (OQ-2).
> Implementations should attempt reads and handle rejection gracefully.

### C4 — Register 0x3B is CondenserOutTemp, not EEV test enable

**Was:** 0x3B = `EnableTestEEVTemp` (write/read, EEV temperature test enable).
**Now:** 0x3B = `condenser_out_temp` / `CondenserOutTemp` (T.0.59), signed/10, C.
**Evidence:** P1 T.0.59 = CondenserOutTemp (UIN/10). P5 reg 59 = CondenserOutTemp
(number(2) x 0.1). Two independent live-install sources agree.
**Falsifiable:** Read 0x3B on a live unit; response must be 30-90C tracking condenser outlet.

### C5 — Register 0x15 is EEVPosition, not EEV test enable

**Was:** 0x15 = `EnableTestEEVPosition` (write, EEV position test enable).
**Now:** 0x15 = `eev_position` / `EEVPosition` (T.0.21), word, %.
**Evidence:** P1 T.0.21 = EEVPosition (UIN, %). P5 reg 21 = EEVPos (word x 1, %).
**Falsifiable:** Read 0x15 continuously during compressor load change; value must
vary 0-100% tracking EEV step count.

## Safety

B514 write requests can actuate service/test-menu functions. Do not issue B514 writes
on a live installation unless the actuator or test mode is understood and the system
is in a safe state.

B514 reads are passive sensor queries and are safe for continuous polling (see C3
and OQ-2 for the service-gate caveat).

## Open Questions

### OQ-1 — D2B vs word/10 for pressure registers (BLOCKING)

Registers 0x3F (HighPressure) and 0x40 (LowPressure) have conflicting type
assignments: P1 uses D2B, P5 uses word/10. Resolution requires live pressure capture
comparing both decodings against physical plausibility (high-side 10-35 bar, low-side
2-8 bar).

### OQ-2 — Whether `03 FF FF` requires prior service-mode activation

P5 reads registers without documented enable sequences. Whether some firmware
versions require a prior service-menu write to activate the B514 read window is
unresolved. Resolution: poll a known register (e.g., 0x30 AirInTemp) on a fresh
unit with no service-menu session open.

### OQ-3 — Register 0x45 (TestOutdoorTemp)

REG 0x45 (decimal 69) appears in the TypeSpec as `TestOutdoorTemp` but is absent
from both P1 (38 registers) and P5 (20 registers). Possibly a firmware-variant
artifact, an alias for AirInTemp (0x30), or a remapped register.

### OQ-4 — T.1 register addressing on VWZIO

All T.1 registers are P1-only. Whether they require direct targeting of VWZIO at
address 0x76 or can be addressed via HMU00 (0x08) with a group-select byte is
unknown.

### OQ-5 — PowerFan2 (0x12) on single-fan units

P1 annotates 0x12 as "dual-fan VWLS only". Behavior on single-fan arotherm plus
is unknown (NAK, zero, or stale value).

## Enrichment Summary (2026-04-14)

| Metric | Before | After |
|--------|--------|-------|
| Total registers | 5 (TypeSpec-only) | 38 distinct REG indices (+33 new) |
| Live sensor registers | 0 | 25 confirmed + 2 type-unresolved |
| Wire format | Partial (2-byte read assumed) | Corrected: `05 [REG] 03 FF FF` |
| Group T.0 (HMU outdoor) | 2 (TypeSpec, misidentified) | 27 registers |
| Group T.1 (VWZIO indoor) | 2 (TypeSpec, misidentified) | 10 registers |
| Confidence | TypeSpec-only (LOW) | 16 BOTH (HIGH), 8 P1-ONLY (MEDIUM) |
| Corrections | 0 | 5 (C1-C5) |
| Open questions | 3 | 5 (refined + new) |

## References

### Primary sources (live-install)

- **P1**: `cyberthom42/vaillant-arotherm-plus` GitHub repo — `08.hmu.csv`
  (38 B514 registers, arotherm plus HMU00 + VWZIO)
- **P5**: OpenHAB eBUS binding community thread — `hmu08_config.json`
  (20 B514 registers, HMU00 only)

### Secondary sources (TypeSpec / protocol spec)

- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [76.vwz.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/76.vwz.tsp)
- Public TypeSpec: [76.vwzio.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/76.vwzio.tsp)

### Enrichment sources

- Enrichment report: `_work_enrichment/final/FINAL-B514.md`
- Cross-check: `_work_enrichment/final/CROSSCHECK-B514.md`
- Deep analysis: `_work_enrichment/phase2/D2-B514-deep.md`
