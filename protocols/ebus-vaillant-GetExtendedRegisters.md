# Vaillant GetExtendedRegisters (`0xB5 0x24`, B524)

This document is the dedicated reference for Vaillant `GetExtendedRegisters` (`PB=0xB5`, `SB=0x24`).

It is structured by:
- command families (opcode-based),
- shared selector/response data structures,
- discovery/scanning behavior used by Helianthus.

## 1. Scope and Framing

B524 is a selector-opcode multiplexed payload protocol carried inside a standard eBUS frame.

```text
eBUS telegram request body used with ebusd `hex`:
DST PB SB LEN DATA...

For B524:
PB=0xB5
SB=0x24
DATA... starts with B524 opcode family byte.
```

When using ebusd TCP `hex`, the response line is typically prefixed with an eBUS response length byte (`LEN DATA...`). See `protocols/ebusd-tcp.md`.

## 2. Shared Data Structures

### 2.1 Request selectors

```text
GG      Group id (u8)
II      Instance id (u8)
RR      Register id (u16 little-endian)
SEL*    Timer selector bytes (u8)
WD      Weekday (u8, 0x00..0x06)
```

### 2.2 Common read-response header (`0x02` / `0x06`)

```text
TT GG RR_LO RR_HI [value...]

TT = reply kind / status (empirical):
  0x00  no data / not present / invalid
  0x01  live / operational value
  0x02  parameter / limit
  0x03  parameter / config
```

Notes:
- `II` is not echoed in the response.
- Some replies are status-only: a single-byte `TT` with no `GG/RR/value`.
- Correlation must retain request context (`GG/II/RR/opcode`).
- Exception: the `0x01` constraint dictionary request is `01 GG RR` (no `II`), so correlation there is `GG/RR`.

### 2.3 Directory descriptor semantics

Directory probe returns `float32le` descriptor values.

```text
descriptor == NaN  -> end-of-directory marker (terminator)
descriptor == 0.0  -> hole / unassigned group id
other float values -> class marker (treated as enum-like class tags)
```

## 3. Opcode Family Map

```text
Opcode  Name                 Request shape                     Status
0x00    Directory probe      00 <GG> 00                        Confirmed
0x01    Constraint dictionary 01 <GG> <RR>                     Confirmed
0x02    Local register I/O   02 <RW> <GG> <II> <RR_LO> <RR_HI> Confirmed
0x03    Timer read           03 <SEL1> <SEL2> <SEL3> <WD>      Confirmed
0x04    Timer write          04 <SEL1> <SEL2> <SEL3> <WD> ...  Confirmed
0x06    Remote register I/O  06 <RW> <GG> <II> <RR_LO> <RR_HI> Confirmed
0x0B    Array/table read     Shape unresolved (non-scalar)     Observed/partial
```

`RW` is `0x00` for read and `0x01` for write.

## 4. Family Details

### 4.1 `0x00` Directory Probe

```text
Request payload (3 bytes):
  0: 0x00
  1: GG
  2: 0x00

Response payload (4 bytes):
  0..3: descriptor float32le
```

Discovery rules:
- Iterate GG upward.
- Stop on first `NaN` descriptor.
- Skip `0.0` holes.
- Treat transport/timeouts as non-terminating errors.

### 4.2 `0x01` Constraint Dictionary (min/max/step)

This family exposes an undocumented constraint dictionary for configuration parameters.

Canonical request form:

```text
Request payload (3 bytes):
  0: 0x01
  1: GG
  2: RR
```

Example ebusd `hex` command for `GG=0x03`, `RR=0x01`:

```text
hex 15B52403010301
```

#### 4.2.1 Type tags and decoding

`TT` is the first byte in the returned payload and defines the constraint value encoding:

```text
TT=0x06: u8 range
  06 GG RR 00 MIN MAX STEP

TT=0x09: u16le range
  09 GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are u16 little-endian

TT=0x0F: float32le range
  0F GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are IEEE754 float32 little-endian

TT=0x0C: date range (HDA3-like)
  0C GG RR 00 MIN(d,m,y) MAX(d,m,y) STEP(u16le) 00
  year is interpreted as 2000 + y
```

#### 4.2.2 Discovery method (practical)

Current Helianthus runtime behavior:

1. For each discovered group, iterate `RR=0x00..min(rr_max,0xFF)`.
2. Probe optional shared IDs above the window (currently `RR=0x80`).
3. Send `15 b5 24 03 01 GG RR`.
4. Keep responses where:
   - `TT in {0x06,0x09,0x0C,0x0F}`
   - response echoes request `GG RR`.
5. Filter stdout noise/non-hex lines before decode.

#### 4.2.3 Observed constraints (decoded, with eBUSd cross-reference)

Cross-reference sources:
- `15.720.tsp` for `@base(... group=GG ...)` and `@ext(RR,0)` mapping.
- `vaillant/_templates.tsp` for enum labels (`@values(Values_*)`).

| GG | RR | MIN | MAX | STEP | Type | Notes | eBUSd register(s) | Enum values (eBUSd) | HEX |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00 | 01 | -20 | 50 | 1 | f32_range |  | HwcBivalencePoint |  | 0f0001000000a0c1000048420000803f |
| 00 | 02 | -26 | 10 | 1 | f32_range |  | ContinuosHeating |  | 0f0002000000d0c1000020410000803f |
| 00 | 03 | 0 | 12 | 1 | u16_range |  | FrostOverrideTime |  | 0900030000000c000100 |
| 00 | 04 | 0 | 300 | 10 | u16_range | No matching `@ext()` in `15.720.tsp` for this `(GG,RR)` |  |  | 0900040000002c010a00 |
| 00 | 80 | -10 | 10 | 1 | f32_range | Shared constraint-id (not an `@ext` index) | DewPointOffset, Hc{1..3}DewPointOffset |  | 0f008000000020c1000020410000803f |
| 01 | 01 | 0 | 1 | 1 | u16_range |  | HwcEnabled | 0=no, 1=yes | 09010100000001000100 |
| 01 | 02 | 0 | 1 | 1 | u8_range |  | HwcCircPumpStatus |  | 06010200000101 |
| 01 | 03 | 0 | 2 | 1 | u16_range |  | HwcOpMode | 0=off, 1=auto, 2=manual | 09010300000002000100 |
| 01 | 04 | 35 | 70 | 1 | f32_range |  | HwcTempDesired |  | 0f01040000000c4200008c420000803f |
| 01 | 05 | 0 | 99 | 1 | f32_range |  | HwcStorageTemp |  | 0f010500000000000000c6420000803f |
| 01 | 06 | 0 | 1 | 1 | u8_range |  | HwcReheatingActive |  | 06010600000101 |
| 02 | 01 | 1 | 2 | 1 | u16_range | `heating_circuit_type` |  | 1=direct_heating_circuit, 2=mixer_circuit_external | 09020100010002000100 |
| 02 | 02 | 0 | 4 | 1 | u16_range | `mixer_circuit_type_external` (contextual enum) | Hc{1..3}CircuitType | 0=inactive, 1=heating_or_cooling, 2=fixed_value_or_pool, 3=dhw_or_cylinder_charging, 4=return_increase | 09020200000004000100 |
| 02 | 04 | 15 | 80 | 1 | f32_range |  | Hc{1..3}DesiredReturnTemp |  | 0f020400000070410000a0420000803f |
| 02 | 05 | 0 | 1 | 1 | u8_range |  | Hc{1..3}DewPointMonitoring |  | 06020500000101 |
| 02 | 06 | 0 | 1 | 1 | u8_range |  | Hc{1..3}CoolingEnabled |  | 06020600000101 |
| 03 | 01 | 0 | 2 | 1 | u16_range |  | Z{1..3}CoolingOpMode | 0=off, 1=auto, 2=manual | 09030100000002000100 |
| 03 | 02 | 15 | 30 | 0.5 | f32_range |  | Z{1..3}CoolingSetbackTemp |  | 0f030200000070410000f0410000003f |
| 03 | 03 | 2001-01-01 | 2099-12-31 | 1 | date_range |  | Z{1..3}HolidayStartPeriod |  | 0c0303000101011f0c63010000 |
| 03 | 04 | 2001-01-01 | 2099-12-31 | 1 | date_range |  | Z{1..3}HolidayEndPeriod |  | 0c0304000101011f0c63010000 |
| 03 | 05 | 5 | 30 | 1 | f32_range | TSP mismatch: `15.720.tsp` commonly shows step `0.5` | Z{1..3}HolidayTemp |  | 0f0305000000a0400000f0410000803f |
| 03 | 06 | 0 | 2 | 1 | u16_range |  | Z{1..3}HeatingOpMode | 0=off, 1=auto, 2=manual | 09030600000002000100 |
| 04 | 01 | 0 | 1 | 1 | u8_range | No matching `@ext()` in `15.720.tsp` for this `(GG,RR)`; closest match: `SolarPump` (`@ext=0x08`) |  |  | 06040100000101 |
| 04 | 02 | 0 | 1 | 1 | u8_range |  | SolarPumpKick |  | 06040200000101 |
| 04 | 03 | -40 | 155 | 1 | f32_range |  | SolarCollectorTemp |  | 0f040300000020c200001b430000803f |
| 04 | 04 | 0 | 99 | 1 | f32_range |  | SolarCollectorTempMin |  | 0f040400000000000000c6420000803f |
| 04 | 05 | 110 | 150 | 1 | f32_range |  | SolarCollectorTempMax |  | 0f0405000000dc42000016430000803f |
| 04 | 06 | 75 | 115 | 1 | f32_range | No matching `@ext()` in `15.720.tsp` for this `(GG,RR)`; closest match: `SolarYieldTemp` (`@ext=0x07`) |  |  | 0f040600000096420000e6420000803f |
| 05 | 01 | 0 | 99 | 1 | f32_range |  | SolarCylinder1TempMax |  | 0f050100000000000000c6420000803f |
| 05 | 02 | 2 | 25 | 1 | f32_range |  | SolarCylinder1SwitchOnDifferential |  | 0f050200000000400000c8410000803f |
| 05 | 03 | 1 | 20 | 1 | f32_range |  | SolarCylinder1SwitchOffDifferential |  | 0f0503000000803f0000a0410000803f |
| 05 | 04 | -10 | 110 | 1 | f32_range | No matching `@ext()` in `15.720.tsp` for this `(GG,RR)` |  |  | 0f050400000020c10000dc420000803f |
| 08 | 01 | 0 | 99 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f080100000000000000c6420000803f |
| 08 | 02 | 0 | 99 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f080200000000000000c6420000803f |
| 08 | 03 | 2 | 25 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f080300000000400000c8410000803f |
| 08 | 04 | 1 | 20 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f0804000000803f0000a0410000803f |
| 08 | 05 | -10 | 110 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f080500000020c10000dc420000803f |
| 08 | 06 | -10 | 110 | 1 | f32_range | No `GG=0x08` blocks found in `15.720.tsp` |  |  | 0f080600000020c10000dc420000803f |
| 09 | 01 | 0 | 255 | 1 | u16_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 090901000000ff000100 |
| 09 | 02 | 1 | 3 | 1 | u16_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 09090200010003000100 |
| 09 | 03 | 0 | 1 | 1 | u8_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 06090300000101 |
| 09 | 04 | 0 | 10 | 1 | u16_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 0909040000000a000100 |
| 09 | 05 | 0 | 32768 | 1 | u16_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 09090500000000800100 |
| 09 | 06 | 0 | 32768 | 1 | u16_range | No `GG=0x09` blocks found in `15.720.tsp` |  |  | 09090600000000800100 |
| 0A | 01 | 0 | 3 | 1 | u8_range | No `GG=0x0A` blocks found in `15.720.tsp` |  |  | 060a0100000301 |
| 0A | 02 | 1 | 2 | 1 | u8_range | No `GG=0x0A` blocks found in `15.720.tsp` |  |  | 060a0200010201 |
| 0A | 03 | 1 | 2 | 1 | u8_range | No `GG=0x0A` blocks found in `15.720.tsp` |  |  | 060a0300010201 |
| 0A | 05 | 0 | 3 | 1 | u8_range | No `GG=0x0A` blocks found in `15.720.tsp` |  |  | 060a0500000301 |
| 0A | 06 | 0 | 1 | 1 | u8_range | No `GG=0x0A` blocks found in `15.720.tsp` |  |  | 060a0600000101 |

#### 4.2.4 Heating-circuit enum interpretation (`GG=0x02`, `RR=0x01/0x02`)

`GG=0x02 RR=0x01` (`heating_circuit_type`) is stable:

- `1` = `DIRECT_HEATING_CIRCUIT`
- `2` = `MIXER_CIRCUIT_EXTERNAL`

`GG=0x02 RR=0x02` (`mixer_circuit_type_external`) is **contextual**:

- `0` = `INACTIVE`
- `1` = `HEATING_OR_COOLING`
  - resolves to `COOLING` when `GG=0x02 RR=0x06 (cooling_enabled) == 1`
  - resolves to `HEATING` otherwise
- `2` = `FIXED_VALUE_OR_POOL`
  - resolves to `POOL` when system schema is in `{8,9,12,13}` and an external pool sensor path is present (typically via VR70/VR71 S1/S2 mapping)
  - resolves to `FIXED_VALUE` otherwise
- `3` = `DHW_OR_CYLINDER_CHARGING`
  - resolves to `CYLINDER_CHARGING` when a cylinder group (`GG=0x05`) is present
  - resolves to `DHW` otherwise
- `4` = `RETURN_INCREASE`

Resolution helper:

```text
if raw == 1:
  resolved = (cooling_enabled == 1) ? COOLING : HEATING
if raw == 2:
  resolved = (schema in {8,9,12,13} && pool_sensor_present) ? POOL : FIXED_VALUE
if raw == 3:
  resolved = (gg05_present) ? CYLINDER_CHARGING : DHW
```

Context inputs used for interpretation:

- `cooling_enabled`: `GG=0x02 RR=0x06`
- `system_schema`: installation/hydraulic-schema metadata source (not `GG=0x00 RR=0x01`, which maps to `HwcBivalencePoint`)
- `pool_sensor_present`: VR70/VR71 external sensor mapping (S1/S2)
- `gg05_present`: group-presence check for `GG=0x05`

#### 4.2.5 Additional heating-circuit registers (`GG=0x02`, `II=*`)

The following register aliases are now part of the documented `GG=0x02` catalog:

| RR | Canonical name | eBUSd alias | Class |
| --- | --- | --- | --- |
| `0x001D` | `frost_protection_threshold` | `Hc{hc}FrostProtThreshold` | `config_limits` |
| `0x001F` | `room_temperature_setpoint` | `Hc{hc}RoomSetpoint` | `config_limits` |
| `0x0020` | `calculated_flow_temperature` | `Hc{hc}FlowTempCalc` | `state` |
| `0x0021` | `mixer_position_percentage` | `Hc{hc}MixerPosition` | `state` |
| `0x0022` | `current_room_humidity` | `Hc{hc}Humidity` | `state` |
| `0x0023` | `dew_point_temperature` | `Hc{hc}DewPointTemp` | `state` |
| `0x0024` | `pump_operating_hours` | `Hc{hc}PumpHours` | `state` |
| `0x0025` | `pump_starts_count` | `Hc{hc}PumpStarts` | `state` |

Operational notes:

- `RR=0x0003`: controls room-sensor influence mode (`0=inactive`, `1=modulation/adjustment`, `2=thermostat on-off`).
- `RR=0x001F`: practical thermostat linkage register; typically reflects the room setpoint shown on VRC UI (for example `21.0°C`).
- `RR=0x0020`: useful for diagnostics; it can show curve-requested flow temperature even when `RR=0x0007` (`FlowTempDesired`) is clamped by limits such as `RR=0x0010` (`MaxFlow`).

### 4.3 `0x02` / `0x06` Register Read/Write

```text
Read request payload (6 bytes):
  0: opcode  (0x02 local / 0x06 remote)
  1: RW      (0x00)
  2: GG
  3: II
  4: RR_LO
  5: RR_HI

Write request payload (6+ bytes):
  0: opcode  (0x02 local / 0x06 remote)
  1: RW      (0x01)
  2: GG
  3: II
  4: RR_LO
  5: RR_HI
  6..: value bytes
```

Read response:
- headered: `TT GG RR_LO RR_HI [value...]`
- or status-only short form: `TT`

Addressing notes:
- `0x02` is typically local regulator space.
- `0x06` is typically remote/sensor-oriented space (`0x09/0x0A/0x0C` are common).

### 4.4 `0x03` / `0x04` Timer Schedules

```text
Timer read request (5 bytes):
  0: 0x03
  1: SEL1
  2: SEL2
  3: SEL3
  4: WD (0x00..0x06)

Timer write request (5+ bytes):
  0: 0x04
  1: SEL1
  2: SEL2
  3: SEL3
  4: WD
  5..: timer blocks (model-specific)
```

These families do not use `RW` byte.

### 4.5 `0x0B` Array/Table Read (Schedules)

`0x0B` is observed for schedule/program-style groups (`GG=0x06`, `GG=0x07`) where simple register loops are insufficient.

Current status:
- family observed on wire
- full selector/body schema still under consolidation
- practical recommendation: treat as array/table transport, not scalar RR scan
- current Helianthus scanner does not parse `0x0B` payload bodies yet

Implication:
- sparse `0x01` constraints do not imply scalar coverage for schedule groups.

## 5. Group Taxonomy and Descriptor Classes

Observed groups on VRC720-class targets:

```text
GG   Name                  Descriptor(s)  Typical opcode  Notes
0x00 Regulator Parameters  3.0            0x02            `0x01` limits observed for RR {0x01,0x02,0x03,0x04,0x80}
0x01 Hot Water Circuit     3.0            0x02            singleton; `0x01` limits observed for RR 0x01..0x06
0x02 Heating Circuits      1.0            0x02            instanced; `0x01` limits observed for RR {0x01,0x02,0x04,0x05,0x06}
0x03 Zones                 1.0            0x02            instanced; `0x01` limits observed for RR 0x01..0x06 (includes date ranges)
0x04 Solar Circuit         6.0 / 5.0      0x02            `0x01` limits observed for RR 0x01..0x06
0x05 Hot Water Cylinder    1.0 / absent   0x02            model-/system-dependent; `0x01` limits observed for RR 0x01..0x04
0x06 Heating schedule      (varies)       0x0B            program/timetable domain
0x07 DHW schedule          (varies)       0x0B            program/timetable domain
0x08 Solar Aux/unknown     1.0 / absent   0x06            `0x01` limits observed for RR 0x01..0x06; not mapped in `15.720.tsp`
0x09 Room Sensors          1.0            0x06            instanced; `0x01` limits observed for RR 0x01..0x06
0x0A Room State            1.0            0x06            instanced; `0x01` limits observed for RR {0x01,0x02,0x03,0x05,0x06}
0x0C Unknown               1.0 / absent   0x06            model-/system-dependent; no confirmed `0x01` limit rows yet
```

Descriptor class values behave like coarse enum tags, not physical numeric quantities.

## 6. Helianthus Discovery and Scan Strategy

### 6.1 Phase A: group discovery

- probe `0x00` directory sequentially
- stop on first `NaN`
- record unknown groups and unknown descriptor classes for follow-up

### 6.2 Phase B: constraint dictionary sampling (`0x01`)

- probe `0x01 GG RR` over bounded per-group RR windows
- decode and persist `min/max/step` domains (`u8`, `u16le`, `f32le`, `date`)
- persist decoded entries under artifact metadata (`meta.constraint_dictionary`)
- current implementation keeps constraints advisory (they do not resize planner ranges yet)

### 6.3 Phase C: instance detection (instanced groups)

- evaluate all `II=0x00..II_max` (no early stop on holes)
- `II_max` comes from planner/static profile and observed valid instances, not from `0x01`.
- mark present slots based on group-specific heuristics

### 6.4 Phase D: register scan

- scan selected groups/instances/ranges from planner
- for unknown groups, scanners may probe both `0x02` and `0x06` and keep best response

### 6.5 Static fallback profile (when dynamic evidence is missing)

```text
GG   Opcode  InstanceMax  RegisterMax
0x02 0x02    0x0A         0x0025
0x03 0x02    0x0A         0x002F
0x09 0x06    0x0A         0x002F
0x0A 0x06    0x0A         0x003F
0x0C 0x06    0x0A         0x003F
```

This profile is currently the primary planner bound source; dynamic evidence (`0x01` constraints and successful read probes) is persisted as advisory metadata.

## 7. ebusd TCP Interop Notes

For `hex` command integration (`protocols/ebusd-tcp.md`):
- send `DST PB SB LEN DATA...`
- parse first valid hex response line
- strip leading ebusd length prefix when present
- accept short status-only payloads
- ignore trailing noisy lines after a valid parsed payload

## 8. Open Items / Validation Queue

- Finalize complete selector schema for `0x0B` array/table read.
- Expand response exemplars per family (`0x01` and `0x0B` especially).
- Track descriptor-class transitions (e.g., `0x04` class `6.0` vs `5.0`) against system topology changes.
