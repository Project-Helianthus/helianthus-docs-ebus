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
FLAGS GG RR_LO RR_HI [value...]
```

`FLAGS` is an access/writability byte:

```text
FLAGS = 0x00  volatile read-only state (changes frequently)
FLAGS = 0x01  stable read-only state (computed outputs, sensor readings)
FLAGS = 0x02  technical read-write config (offsets, thresholds)
FLAGS = 0x03  user-facing read-write config (modes, schedules, names)
```

See [`ebus-vaillant-B524-register-map.md` § FLAGS Byte](./ebus-vaillant-B524-register-map.md#flags-byte-response-header) for full documentation including opcode-specific behavior and verification methodology.

Notes:
- `II` is not echoed in the response.
- **Short responses** (payload < 4 bytes) are **not** successful register reads. A single-byte `0x00` indicates wrong route, unsupported opcode, or group default — ebusd reports `invalid position … / 00`. Write operations may return short acknowledgements. Treat as not-a-register-value.
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

The first byte of the constraint response is a **type tag** (distinct from the FLAGS byte in register read responses) that defines the constraint value encoding:

```text
0x06: u8 range
  06 GG RR 00 MIN MAX STEP

0x09: u16le range
  09 GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are u16 little-endian

0x0F: float32le range
  0F GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are IEEE754 float32 little-endian

0x0C: date range (HDA3-like)
  0C GG RR 00 MIN(d,m,y) MAX(d,m,y) STEP(u16le) 00
  year is interpreted as 2000 + y
```

#### 4.2.2 Discovery method (practical)

Current Helianthus runtime behavior:

1. For each discovered group, iterate `RR=0x00..min(rr_max,0xFF)`.
2. Probe optional shared IDs above the window (currently `RR=0x80`).
3. Send `15 b5 24 03 01 GG RR`.
4. Keep responses where:
   - type tag `in {0x06,0x09,0x0C,0x0F}`
   - response echoes request `GG RR`.
5. Filter stdout noise/non-hex lines before decode.

#### 4.2.3 Constraint catalog

For the full decoded constraint catalog with register names, types, enum values, and eBUSd cross-references, see [`ebus-vaillant-B524-register-map.md` § Constraint Catalog](./ebus-vaillant-B524-register-map.md#constraint-catalog-ebusreg).

#### 4.2.4 Circuit type interpretation (`GG=0x02 RR=0x02`)

`GG=0x02 RR=0x02` (`heating_circuit_type` / `mctype`) is a configuration register with raw values 0..4. See [`ebus-vaillant-B524-register-map.md` § mctype](./ebus-vaillant-B524-register-map.md#mctype--circuit-type) for the authoritative enum definition.

**Layer A — Raw register meaning (Vaillant VRC720 manual):**

```text
0 = Inactive       Circuit unused
1 = Heating         Weather-compensated heating (mixing or direct)
2 = Fixed value     Circuit held at fixed target flow temperature
3 = DHW             Heating circuit used as DHW for additional cylinder
4 = Increase in return   Return temperature raise circuit
```

These raw values are the complete Layer A meaning. No resolution or context inputs are needed to interpret them.

**Layer B — Derived projections (Helianthus semantic layer):**

Higher-level semantic projections may combine the raw circuit type with other registers:

- **Cooling capability**: derived from `cooling_enabled` (GG=0x02 RR=0x0006), NOT from circuit type. A heating circuit (type=1) with `cooling_enabled=1` supports both heating and cooling modes.
- **Pool heating**: an APPLICATION of `fixed_value` (type=2) when the system topology includes pool hydraulics (sensor, circulation pump). NOT a separate raw enum value on VRC720/BASV2.
- **Cylinder charging**: `type=3` (DHW) combined with GG=0x05 group presence indicates a cylinder-charging circuit.

These projections are Helianthus runtime logic and are NOT part of the B524 wire protocol.

#### 4.2.5 Room influence type behavior (`GG=0x02 RR=0x0003`)

This register controls how the room temperature sensor influences the heating curve. See [`ebus-vaillant-B524-register-map.md` § GG=0x02](./ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance) for the register definition.

Behavioral semantics (`enum_u8`, default `0`):

- `0 = INACTIVE` — pure weather compensation. Flow temperature derived from outdoor temp + heating curve. Room controller acts as display/setpoint input only. Controller placement in technical room is acceptable.
- `1 = ACTIVE` — weather compensation + room-temperature modulation. Flow temperature adjusted from room deviation vs setpoint. Heating may continue outside time windows at reduced temperature. Controller should be in representative living space. Practical: if room is `0.5°C` below setpoint, flow setpoint is increased proportionally.
- `2 = EXTENDED` — weather compensation + modulation + thermostat-like on/off gating. Zone deactivates when `room_temp > setpoint + 0.125°C` (`2/16 K`), activates when `room_temp < setpoint - 0.1875°C` (`3/16 K`). Hysteresis bandwidth is `0.3125°C` (`5/16 K`). Caution: tight hysteresis can increase heat-pump cycling risk.

Practical guidance:

- `INACTIVE`: useful with external room controllers or radiator valves
- `ACTIVE`: commonly preferred for slower floor-heating systems
- `EXTENDED`: commonly preferred for faster radiator systems; disabled during absence mode

#### 4.2.6 Register catalogs

All register definitions (names, categories, types, constraints, enum values, gates, semantic mapping) are maintained exclusively in [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md). This document covers only B524 wire protocol methods and their logic.

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
- headered: `FLAGS GG RR_LO RR_HI [value...]`
- or status-only short form: `FLAGS`

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

For the authoritative group topology (names, instance ranges, opcodes, semantic plane mapping), see [`ebus-vaillant-B524-register-map.md` § Group Topology](./ebus-vaillant-B524-register-map.md#group-topology).

Directory probe descriptor values observed on VRC720-class targets:

```text
GG   Descriptor(s)  Typical opcode  Notes
0x00 3.0            0x02            singleton
0x01 3.0            0x02            singleton
0x02 1.0            0x02            instanced
0x03 1.0            0x02            instanced
0x04 6.0 / 5.0      0x02            model-dependent
0x05 1.0 / absent   0x02            model-/system-dependent
0x06 (varies)       0x0B            program/timetable domain
0x07 (varies)       0x0B            program/timetable domain
0x08 1.0 / absent   unknown         constraint-only, no responsive registers observed
0x09 1.0            0x06            instanced
0x0A 1.0            0x06            instanced
0x0C 1.0 / absent   0x06            model-/system-dependent
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
