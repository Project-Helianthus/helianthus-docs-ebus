# Vaillant B51A Heat-Pump Statistics and Live-Monitor Values

`PB=0xB5`, `SB=0x1A`.

## Status

`B51A` is a selector-heavy heat-pump family in john30 HMU TypeSpec files. It
contains energy/yield/COP statistics, live-monitor values, compressor runtime
statistics, and installer-level test-menu statistics. Response prefix bytes are
not fully explained.

> **Enrichment (2026-04-14):** This protocol was enriched from 11 known selectors
> (across 2 sub-groups, most with no register detail) to a comprehensive map of
> ~40 new registers across 4 sub-groups. Four critical corrections applied (pressure
> divisor, COP encoding, D1B type, IDX column). Sources: P4 (issue #335 live scan),
> P5 (OpenHAB eBUS IDX-aware live session), D3 (all-source merge), D11 (7-fork
> cross-validation).

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.
- `P4`: Live session, issue #335 author, IDX=0xFF scan (partial coverage).
- `P5`: Live session, IDX-aware scan, COP correction, 05FF34 lifecycle counters.
- `D3`: B51A Deep All-Source Merge (P1+P2+P4+P5).
- `D11`: Fork cross-validation (7 forks: burmistrzak, jonesPD, koen-lee, kolibrie-eric, djwmarcx, bumaas, xerion3800).

## Wire Shape

Common configured read shape:

```text
Request payload:
  05 [IDX] [SUBGROUP_HI] [SUBGROUP_LO] [REG]
```

> **CORRECTION (2026-04-14) — IDX byte is per-register, not fixed per sub-group.**
> The existing documentation presented sub-group requests as `05 FF 32 [REG]` with
> 0xFF implied universally. The IDX byte (second byte after `05`) varies by register.
> Using the wrong IDX returns no valid response. See Section "IDX Byte Pattern" below.

Known configured `@base(MF, 0x1a, ...)` forms include:

| Static suffix after `1a` | IDX | Context | Evidence | Falsification test |
|---|---|---|---|---|
| `05 [IDX] 32` | varies (0xFF, 0x4D, 0x15) | heat-pump daily/month/year yield/COP/consumption statistics + live data | `LOCAL_TYPESPEC` + P4 + P5 | Query HMU devices and show selectors under `[IDX] 32` do not return energy/COP-style payloads. |
| `05 [IDX] 34` | varies (contested — see Section 3.2) | compressor runtime/statistics group (lifecycle counters) | `LOCAL_TYPESPEC` + P5 + D11/forks | Query HMU devices and show selectors under `[IDX] 34` are unsupported or map to unrelated fields. |
| `05 e5 34` | 0xE5 | passive alternate for compressor runtime/statistics group | `LOCAL_TYPESPEC` | Capture matching firmware and show `e5 34` traffic is unrelated to the `ff 34` group. |
| `05 00 32` | 0x00 | live-monitor desired/current supply, current power, compressor utilization, air intake temp | `LOCAL_TYPESPEC` | Enable live monitor and show selectors under `00 32` do not track live values. |
| `05 FF 33` | 0xFF | backup heater config (VWZIO) | P1 | Query VWZIO and show `FF 33` does not return backup heater data. |
| `04 05` | -- | compressor modulation live monitor | P1 | Query HMU and show `04 05` does not return compressor modulation data. |
| `05` | -- | installer statistics with selector-defined subgroups | `LOCAL_TYPESPEC` | Query installer-level stats on isolated hardware and show selector identity is not prefix-tuple dependent. |

## IDX Byte Pattern (CRITICAL for Implementation)

The IDX byte is the second byte in the B51A request frame (`05 [IDX] [SUBGROUP] [REG]`).
It is **per-register, not fixed per sub-group**. Using IDX=0xFF for registers that
require a different IDX value will return no valid response or an error.

Known IDX values for sub-group 05xx32:

| IDX | Scope | Registers |
|-----|-------|-----------|
| 0xFF | Most live data + hour counters | 0x00, 0x20, 0x22, 0x23, 0x24, 0x27, 0x3C, 0x3D, 0x3E, 0x40, 0x41, 0x43, 0x44 |
| 0x4D | Energy/COP statistics | 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x16, 0x17, 0x21, 0x2A, 0x2B, 0x2C, 0x2D, 0x4D |
| 0x15 | Compressor utilization | 0x25 |
| 0x00 | Live-monitor group (existing doc) | 0x1F, 0x20, 0x26 |

Evidence: P4's IDX=0xFF-only scan missed all 0x4D-IDX and 0x15-IDX registers. P5
confirmed correct IDX values by iteration.

Falsifiable: Query `B51A 05 FF 32 0F` (IDX=0xFF for CopHcMonth). HMU returns no
valid response. Then query `B51A 05 4D 32 0F` (IDX=0x4D). HMU must return a valid
word decodable as COP 1.0-6.0 (raw / 10).

## Corrections Log (2026-04-14 Enrichment)

### Correction 1 — Pressure divisor = 64, not 16 (registers 0x3D, 0x3E)

**Was:** D2C inherent divisor of 16 implied (raw / 16 = bar).
**Now:** Effective divisor = **64** (D2C inherent /16 x additional CSV field /4 = `D2C,4`).
Formula: `raw_wire_value / 64 = physical bar`.
**Affected:** `B51A 05 FF 32 3D` (FlowPressure), `B51A 05 FF 32 3E` (SourcePressure).
**Evidence:** D3 Correction 1. P4 (issue #335); ebusd CSV definition `D2C,4`.
**Falsifiable:** Query 0x3D during pump operation. Divide raw D2C by 64; result must
be 1.5-3.5 bar. Dividing by 16 yields 4x too high.

### Correction 2 — COP encoding: raw / 10 = physical COP (registers 0x0F, 0x11, 0x13, 0x17)

**Was:** COP treated as dimensionless factor 1.0 (raw = COP value).
**Now:** `raw_wire_value / 10 = physical COP`. Example: raw=35 means COP 3.5.
**Affected (HIGH — live-validated):** 0x0F `CopHcMonth`, 0x11 `CopHc`, 0x13
`CopHwcMonth`, 0x17 `CopHwc`.
**Affected (MEDIUM — analogy, not independently confirmed):** 0x2B `CopCoolingMonth`,
0x2D `CopCooling` — /10 assumed by analogy with heating COP.
**Evidence:** D3 Correction 2. P5 live-corrected after COP=32 observed where 3.2
expected. Cross-confirmed by P4.
**Falsifiable:** Query `B51A 05 4D 32 11` (CopHc). Raw word must be 20-60 (i.e.,
COP 2.0-6.0). Raw > 99 without /10 is definitive bug indicator.

### Correction 3 — CurrentYieldPower / CurrentConsumedPower type = D1B (registers 0x23, 0x24)

**Was:** Type `UIN` (unsigned 16-bit integer) with /10 scale.
**Now:** Type `D1B` (signed 8-bit, also `data1b`) with /10 scale (kW). During defrost
cycles, compressor reversal causes negative yield power — appears correctly as small
negative with D1B, but as large positive spike (~25 kW) if misread as UIN.
**Affected:** 0x23 `CurrentYieldPower`, 0x24 `CurrentConsumedPower`.
**Evidence:** D3 Correction 3. P4+P5 use `data1b`. P4 notes defrost-cycle sign
artifacts vanish once corrected.
**Falsifiable:** During defrost, query 0x23. D1B: value <= 0. UIN: same byte decodes > 200.

**Secondary IDX note:** Existing doc places these at `00 32 23`/`00 32 24` (IDX=0x00).
Enrichment places them at IDX=0xFF. Both may work (firmware-variant) or one may be
wrong. Live probe of both `05 00 32 23` and `05 FF 32 23` is required.

### Correction 4 — IDX column missing from all register tables

**Was:** No IDX column; `05 FF 32 [REG]` with 0xFF implied universally.
**Now:** IDX is per-register. See "IDX Byte Pattern" section above.
**Impact:** Using IDX=0xFF for registers requiring 0x4D or 0x15 returns no valid
response. This caused P4's scan to miss all energy/COP registers entirely.

## Known Selectors

### Sub-Group 05xx32 — Live Data + Energy Statistics

Frame format: `B51A 05 [IDX] 32 [REG]`

> **Naming note:** Canonical Helianthus naming uses `dhw_*` (snake_case). ebusd
> source naming uses `Hwc*` (camelCase). Both refer to domestic hot water.

| REG | IDX | `snake_case` name | ebusd `camelCase` | Type | Div | Unit | Confidence | Evidence | Falsifiable claim |
|-----|-----|-------------------|-------------------|------|-----|------|------------|----------|-------------------|
| 0x00 | 0xFF | `yield_hc_day` | `YieldHcDay` | energy(4) | 1 | kWh | HIGH | LOCAL_TYPESPEC + P4 | Query at day-end; must match controller daily heating yield. |
| 0x01 | 0xFF | `yield_cooling_day` | `YieldCoolingDay` | energy(4) | 1 | kWh | LOW | D11/burmistrzak (B524 `020002 0001`) | Query during active cooling; non-zero. Zero in heating-only season. |
| 0x02 | 0xFF | `yield_hwc_day` | `YieldHwcDay` | energy(4) | 1 | kWh | LOW | D11/burmistrzak (B524 `020002 0002`) | Query during active DHW production; must increment over 24h. |
| 0x0E | **0x4D** | `yield_hc_month` | `YieldHcMonth` | word | /10 | kWh | HIGH | P4+P5+doc | Must match monthly heating energy on controller / 10. |
| 0x0F | **0x4D** | `cop_hc_month` | `CopHcMonth` | word | **/10** | ratio | HIGH | P4+P5 (corrected) | Raw / 10 must be 1.0-6.0. **CORRECTION 2 applied.** |
| 0x10 | **0x4D** | `yield_hc` | `YieldHc` | energy | 1 | kWh | HIGH | P4+P5 | Monotonically increasing lifetime counter; must be >= YieldHcMonth. |
| 0x11 | **0x4D** | `cop_hc` | `CopHc` | word | **/10** | ratio | HIGH | P4+P5 (corrected) | COP range 1.0-6.0. **CORRECTION 2 applied.** |
| 0x12 | **0x4D** | `yield_hwc_month` | `YieldHwcMonth` | energy | /10 | kWh | HIGH | P4+P5 | Must match monthly DHW yield / 10. |
| 0x13 | **0x4D** | `cop_hwc_month` | `CopHwcMonth` | word | **/10** | ratio | HIGH | P4+P5 (corrected) | COP range 1.0-4.0 for DHW typical. **CORRECTION 2 applied.** |
| 0x16 | **0x4D** | `yield_hwc` | `YieldHwc` | energy | 1 | kWh | HIGH | P4+P5 | Lifetime DHW yield; monotonically increasing. |
| 0x17 | **0x4D** | `cop_hwc` | `CopHwc` | word | **/10** | ratio | HIGH | P4+P5 (corrected) | COP range 1.0-4.0. **CORRECTION 2 applied.** |
| 0x1E | 0xFF | `compressor_blocktime` | `CompressorBlocktime` | word | ? | ? | LOW | D11/burmistrzak (B524 `020002 001E`) | Non-zero during defrost lockout; zero during normal operation. |
| 0x1F | 0x00 | `live_monitor_desired_supply_temp` | `LiveMonitorDesiredSupplyTemp` | temperature | -- | C | confirmed | LOCAL_TYPESPEC | Must track desired supply temperature in live-monitor. |
| 0x20 | 0xFF | `flow_temp` | `FlowTemp` | D2C | /16 | C | MEDIUM | P4 | Must match flow temp sensor +/-0.5C. |
| 0x20 | 0x00 | `live_monitor_current_supply_temp` | `LiveMonitorCurrentSupplyTemp` | temperature | -- | C | confirmed | LOCAL_TYPESPEC | Must track current supply temperature in live-monitor. |
| 0x21 | **0x4D** | `energy_integral` | `EnergyIntegral` | int16 | 1 | min | MEDIUM | P4+P5 | Sign-aware; negative during defrost. |
| 0x22 | 0xFF | `source_temp_input` | `SourceTempInput` | D2C | /16 | C | HIGH | P4+doc(live) | Must match outdoor/source temperature sensor +/-1C. |
| 0x23 | 0xFF | `current_yield_power` | `CurrentYieldPower` | **D1B** | /10 | kW | HIGH | P4+P5+doc (type corrected) | **CORRECTION 3 applied.** See Correction 3 falsifiable claim. |
| 0x24 | 0xFF | `current_consumed_power` | `CurrentConsumedPower` | **D1B** | /10 | kW | HIGH | P4+P5+doc (type corrected) | **CORRECTION 3 applied.** Must be >= 0 during normal operation. |
| 0x25 | **0x15** | `current_compressor_util` | `CurrentCompressorUtil` | D2C | /16 | % | HIGH | P4+P5+doc | Must be 0 when compressor off; 20-100% during active heating. |
| 0x26 | 0x00 | `live_monitor_air_intake_temp` | `LiveMonitorAirIntakeTemp` | temperature | -- | C | confirmed | LOCAL_TYPESPEC | Must track air intake temperature in live-monitor. |
| 0x27 | 0xFF | `source_temp_output` | `SourceTempOutput` | D2C | /16 | C | HIGH | P4+doc(live) | Air-source: equals SourceTempInput. Brine: lower due to heat extraction. |
| 0x2A | **0x4D** | `yield_cooling_month` | `YieldCoolingMonth` | word | /10 | kWh | LOW | D11/burmistrzak (B524 `020002 002A`) | Non-zero only in cooling season. |
| 0x2B | **0x4D** | `cop_cooling_month` | `CopCoolingMonth` | word | /10 | ratio | MEDIUM | D11/burmistrzak (B524 `020002 002B`) | COP range 2.0-8.0. /10 factor assumed by analogy — see Q6. |
| 0x2C | **0x4D** | `yield_cooling` | `YieldCooling` | energy | 1 | kWh | LOW | D11/burmistrzak (B524 `020002 002C`) | Lifetime cooling yield; zero on heating-only systems. |
| 0x2D | **0x4D** | `cop_cooling` | `CopCooling` | word | /10 | ratio | MEDIUM | D11/burmistrzak (B524 `020002 002D`) | Lifetime cooling COP. /10 assumed — see Q6. |
| 0x3C | 0xFF | `water_throughput` | `WaterThroughput` | EXP/word | ? | l/h | LOW | D11/burmistrzak (B524 `020002 003C`) | Must correlate with pump speed. |
| 0x3D | 0xFF | `flow_pressure` | `FlowPressure` | D2C | **/64** | bar | HIGH | P4 (corrected) | **CORRECTION 1 applied.** Divide raw D2C by 64; 1.5-3.5 bar range. |
| 0x3E | 0xFF | `source_pressure` | `SourcePressure` | D2C | **/64** | bar | HIGH | P4 (corrected) | **CORRECTION 1 applied.** Same pressure divisor check as 0x3D. |
| 0x40 | 0xFF | `hours` | `Hours` | energy | 1 | h | HIGH | P4+P5 | Monotonically increasing; see Q1 (possible alias for CompressorHours). |
| 0x41 | 0xFF | `hours_hc` | `HoursHc` | energy | 1 | h | HIGH | P4+P5 | Hours of active heating; <= 0x40. |
| 0x43 | 0xFF | `hours_cool` | `HoursCool` | energy | 1 | h | MEDIUM | P4 | Hours of active cooling; zero on heating-only hardware. |
| 0x44 | 0xFF | `hours_hwc` | `HoursHwc` | energy | 1 | h | HIGH | P4+P5 | Hours of DHW production; <= 0x40. |
| 0x4D | **0x4D** | `total_energy_usage` | `TotalEnergyUsage` | word | ? | kWh? | LOW | D11/burmistrzak (B524 `020002 004D`) | If available: must be sum of heating + DHW + cooling energy. See Q7. |

> **Note:** Unnamed `ch_*` placeholders from P4 scan (0x01-0x07, 0x18, 0x3F,
> 0x46-0x63) are scan artifacts with no semantic claim. They remain in RE working
> notes only and are excluded from the production register map.

### Sub-Group 05xx34 — Lifecycle Counters

Frame format: `B51A 05 [IDX] 34 [REG]`

> **WARNING: IDX bytes are contested between D3/P5 and fork sources. Both IDX sets
> are listed below. Live verification required before implementation. See Open
> Questions section.**

| REG | `snake_case` name | ebusd `camelCase` | Type | Unit | D3/P5 IDX | Fork IDX | Fork sources | Confidence | Falsifiable claim |
|-----|-------------------|-------------------|------|------|-----------|----------|--------------|------------|-------------------|
| 0x00 | `compressor_hours` | `CompressorHours` | word | h | **0x68** | **0xB4** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | One IDX will return word matching B509 `540200 C2` CompressorHours. |
| 0x01 | `compressor_starts` | `CompressorStarts` | word | count | **0xA1** | **0xB4** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must increment by 1 per compressor start cycle. |
| 0x02 | `building_pump_hours` | `BuildingPumpHours` | word | h | **0x38** | **0xB4** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must be <= CompressorHours. |
| 0x03 | `building_pump_starts` | `BuildingPumpStarts` | word | count | **0x9D** | **0xB4** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must be >= CompressorStarts. |
| 0x04 | `stat5` | `Stat5` | UIN | ? | (absent) | **0xB4** | bumaas only | LOW | Unknown counter; may be pump or heater related. |
| 0x06 | `four_way_valve_hours` | `FourWayValveHours` | word | h | **0xD8** | **0x07** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must increment only during 4-way valve active (cooling/defrost). |
| 0x07 | `four_way_valve_switches` | `FourWayValveSwitches` | word | count | **0xD8** | **0x36** | koen-lee, bumaas | MEDIUM (D3 IDX shared with 0x06); IDX CONTESTED | Must increment per defrost cycle. |
| 0x0D | `eev_steps` | `EEVSteps` | word | steps | **0x02** | **0xE4** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Cumulative step counter; must be non-zero on any running HP. |
| 0x51 | `hours_fan1` | `HoursFan1` | word | h | **0xB1** | **0x3C** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must be <= total hours; parallel to B509 `540200 D7`. |
| 0x52 | `starts_fan1` | `StartsFan1` | word | count | **0x03** | **0xD6** | koen-lee, bumaas | HIGH (name+reg); IDX CONTESTED | Must increment per fan start event. |
| 0x5E | `hours_fan2` | `HoursFan2` | word | h | **0xC1** | (no fork data) | D3/P5 only | HIGH (D3 only) | Non-zero on dual-fan HP variants; parallel to B509 `540200 D9`. |
| 0x5F | `starts_fan2` | `StartsFan2` | word | count | **0x01** | (no fork data) | D3/P5 only | HIGH (D3 only) | Must increment per Fan2 start; zero on single-fan models. |

IDX discrepancy hypothesis: May reflect different HMU firmware variants or a protocol
revision. Both D3/P5 (per-register unique IDX) and fork (IDX=0xB4 for REG 0x00-0x03)
values may be correct for their respective firmware.

Resolution procedure: For each register, send two requests (one D3 IDX, one fork IDX).
Valid response = non-zero, non-error, plausible for counter type. B509 parallel path
(`B509 54 02 00 [REG]`) is IDX-free and recommended for verification.

### Sub-Group 05FF33 — Backup Heater Config (Stub)

Frame format: Read = `B51A 05 FF 33`, Write = `B51A 06 FF 33`

**Device scope:** VWZIO (0x76). D11 (xerion3800) extends this to VWZ (0x76) as well.

**Known register:** `heizstab_power_limit` / `HeizstabPowerLimit` — backup heater
power limit. Register offset, type, IDX, and range all TBD. P1 source only.

**Write capability:** `06 FF 33` write path confirmed (P1). Extreme caution — writes
the backup heater power ceiling. No write format decoding available.

**Confidence:** LOW. Single source (P1), no fork confirmation.

### Sub-Group 0405 — Compressor Modulation Live Monitor (Stub)

Frame format: `B51A 04 05 [??]`

**Device scope:** HMU (0x08) only. P1 source.

**Context:** Distinct from `B51A 04` single-byte selector. The `04 05` sub-command
suggests a two-byte selector for compressor modulation data.

**D11 addition:** `B51A 04 *r` (single-byte selector 0x04, no sub-group byte) is
independently confirmed by jonesPD and xerion3800 on HMU. Content unknown (`:IGN:*`
in forks). MEDIUM confidence (two independent forks; no data).

**Confidence:** LOW-MEDIUM. No content decoding available.

## Local Captures

Operator-provided traffic included several `B51A` frames such as:

```text
REQ:  f1 08 b5 1a 04 05 00 0c 00
RESP: 0a 00 02 46 ff 00 25 00 ff 00 0a

REQ:  f1 08 b5 1a 04 05 00 0c 4d
RESP: 0a 00 02 47 46 01 25 00 46 01 0a
```

These use prefix `00 0c`, not the HMU `00 32` live-monitor prefix documented
above. Treat the `00 0c` group as observed but not decoded here.

## Open Questions

### Q1 — 05FF32/0x40 (Hours) vs 05FF34/0x00 (CompressorHours): Same counter?

D3 notes 05FF32/0x40 as `Hours` (IDX=0xFF) and 05FF34/0x00 as `CompressorHours`
(contested IDX). The B509 parallel `540200 C2` is also named CompressorHours. Whether
all three read the same counter or 05FF32/0x40 counts total HP uptime (including
standby) while 05FF34/0x00 counts compressor-only uptime is unresolved. Compare
values live.

### Q2 — `05 00 32` vs `05 FF 32`: Firmware-variant-specific path?

Whether IDX=0x00 exists as a firmware-variant path to the same 05FF32 sub-group
is unresolved. Probe: send `B51A 05 00 32 00` and compare to `B51A 05 FF 32 00`.

### Q3 — Config menu `8F352D`-style encoding

D3 documents a structural encoding pattern; no community forks implement it.
Requires TypeSpec deep-dive (P2 source).

### Q4 — B51A `04` selector on HMU: Content unknown

Two forks (jonesPD, xerion3800) confirm `B51A 04 *r` on HMU with `:IGN:*`. Distinct
from `04 05` sub-command. Content and structure TBD.

### Q5 — VWZ (0x76) B51A scope vs VWZIO

D3 attributed 05FF33 to VWZIO only. D11 shows both VWZ and VWZIO carry `05`/`06`
selectors. Whether VWZ maps to the same register is unresolved.

### Q6 — COP divisor confirmation for cooling registers (0x2B, 0x2D)

/10 assumed by analogy with heating COP. Requires live confirmation on a system with
reversible heat pump (VWZ series with cooling enabled).

### Q7 — TotalEnergyUsage (0x4D) divisor and unit

Unit may be Wh (not kWh), requiring /1000. Cross-check against sum of yield counters.

### Q8 — 05FF34 REG=0x04 (`stat5`): Identity of unnamed counter

bumaas documents as `stat5` (UIN, IDX=0xB4). Between BuildingPumpStarts (0x03) and
FourWayValveHours (0x06). Candidates: total system starts, backup heater starts,
source pump starts.

## Unknowns

- Meaning of response prefix bytes and whether they echo request selectors,
  encode status, or identify data groups.
- Whether prefix tuples are firmware-specific, hardware-specific, or both.
- Mapping for the locally observed `05 00 0c xx` request group.
- IDX discrepancy resolution for 05FF34 lifecycle counters (see Sub-Group 05xx34).

## References

### Primary sources (live sessions)

- **P4**: Live session, issue #335 author — IDX=0xFF scan, pressure/COP corrections.
- **P5**: OpenHAB eBUS binding community thread — IDX-aware scan, COP correction,
  05FF34 lifecycle counters.

### Fork sources (D11 cross-validation)

- **F-burmistrzak**: HW5103 TypeSpec; cooling-season registers; B524-B51A structural path.
- **F-koen-lee**: 05FF34 lifecycle counters with contested IDX values.
- **F-bumaas**: Same as koen-lee; adds stat5 (REG=0x04).
- **F-jonesPD**: B51A 04 selector on HMU; VWZIO stub.
- **F-xerion3800**: VWZ B51A scope; yield3f40.inc.
- **F-kolibrie-eric**: 05FF32 sub-group header confirmation.
- **F-djwmarcx**: 05FF33 sub-group header confirmation.

### Derived sources

- **D3**: B51A Deep All-Source Merge (P1+P2+P4+P5).
- **D11**: Fork B509/B51A Cross-Validation (7 forks).

### TypeSpec

- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Public TypeSpec: [08.hmu.HW5103.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.HW5103.tsp)

### Enrichment sources

- Enrichment report: `_work_enrichment/final/FINAL-B51A.md`
- Cross-check: `_work_enrichment/final/CROSSCHECK-B51A.md`
- Deep analysis: `_work_enrichment/phase2/D3-B51A-deep.md`
- Fork cross-validation: `_work_enrichment/phase2/D11-fork-B509-B51A.md`
