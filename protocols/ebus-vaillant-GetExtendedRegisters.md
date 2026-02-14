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
0x01    Group metadata       01 <GG> <II>                      Confirmed (short form)
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

### 4.2 `0x01` Group Metadata

Canonical short request form:

```text
Request payload (3 bytes):
  0: 0x01
  1: GG
  2: II
```

Example ebusd `hex` command for `GG=0x03`, `II=0x01`:

```text
hex 15B52403010301
```

Observed usage in Helianthus:
- probe with `II=0x01` to derive bounds
- parse returned bytes as metadata payload

Observed response handling:
- Some targets return a headered form that can be interpreted like:
  `TT GG RR_LO RR_HI <meta...>`
- Some targets return short/bare payloads.

Current practical interpretation used for scan planning:
- first 2 metadata bytes: `RR_max` (u16 little-endian), if present
- next 2 metadata bytes: `II_max` (u16 little-endian), if present
- on parse/transport failure: fallback to static defaults

Important:
- The short `01 <GG> <II>` form is the canonical form for Helianthus scanners.
- Longer variants may be accepted by some targets but are not required.

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

Implication:
- `RR_max` from metadata (`0x01`) for schedule groups may be small and does not imply scalar register coverage.

## 5. Group Taxonomy and Descriptor Classes

Observed groups on VRC720-class targets:

```text
GG   Name                  Descriptor(s)  Typical opcode  Notes
0x00 Regulator Parameters  3.0            0x02            RR extends beyond 0x00FF (seen up to 0x01FF)
0x01 Hot Water Circuit     3.0            0x02            singleton
0x02 Heating Circuits      1.0            0x02            instanced
0x03 Zones                 1.0            0x02            instanced
0x04 Solar Circuit         6.0 / 5.0      0x02            descriptor may vary by system state
0x05 Hot Water Cylinder    1.0 / absent   0x02            model-/system-dependent
0x06 Heating schedule      (varies)       0x0B            program/timetable domain
0x07 DHW schedule          (varies)       0x0B            program/timetable domain
0x09 Room Sensors          1.0            0x06            instanced
0x0A Room State            1.0            0x06            instanced
0x0C Unknown               1.0 / absent   0x06            model-/system-dependent
```

Descriptor class values behave like coarse enum tags, not physical numeric quantities.

## 6. Helianthus Discovery and Scan Strategy

### 6.1 Phase A: group discovery

- probe `0x00` directory sequentially
- stop on first `NaN`
- record unknown groups and unknown descriptor classes for follow-up

### 6.2 Phase B: metadata bounds

- probe each discovered group with `0x01` short metadata form
- derive planning bounds (`RR_max`, `II_max`) when present
- fallback to static defaults when metadata is unavailable

### 6.3 Phase C: instance detection (instanced groups)

- evaluate all `II=0x00..II_max` (no early stop on holes)
- mark present slots based on group-specific heuristics

### 6.4 Phase D: register scan

- scan selected groups/instances/ranges from planner
- for unknown groups, scanners may probe both `0x02` and `0x06` and keep best response

### 6.5 Static fallback profile (when metadata is missing)

```text
GG   Opcode  InstanceMax  RegisterMax
0x02 0x02    0x0A         0x0021
0x03 0x02    0x0A         0x002F
0x09 0x06    0x0A         0x002F
0x0A 0x06    0x0A         0x003F
0x0C 0x06    0x0A         0x003F
```

This profile is fallback behavior, not the primary source of truth when `0x01` metadata is available.

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
