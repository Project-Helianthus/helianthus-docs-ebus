# ebusd CSV Conventions (Type Specs + Selectors) (Observed)

ebusd configuration files are commonly distributed as CSVs that include:

- an **id selector** (how to address a value on the bus), and
- a **type spec** (how to decode the value bytes).

This document summarizes the minimal set of conventions needed for tools that consume ebusd CSVs for eBUS decoding.

## Type Specs

The following type spec strings are commonly seen in ebusd CSVs:

```text
EXP    : 4 bytes, IEEE754 float32 little-endian (NaN indicates invalid/unknown)
UIN    : 2 bytes, unsigned u16 little-endian
UCH    : 1 byte, unsigned u8
I8     : 1 byte, signed i8
I16    : 2 bytes, signed i16 little-endian
U32    : 4 bytes, unsigned u32 little-endian
I32    : 4 bytes, signed i32 little-endian
BOOL   : 1 byte, 0x00=false, non-zero=true
STR:*  : N bytes, C string (latin1/ASCII; trailing NUL padding stripped)
HEX:n  : n bytes, raw bytes rendered as hex
HDA:3  : 3 bytes, date encoded as DDMMYY (BCD per byte; year is 2-digit)
HTI    : 3 bytes, time encoded as HH:MM:SS (BCD per byte)
```

Notes:
- For `HDA:3` / `HTI`, each byte is packed BCD (tens in high nibble, ones in low nibble).
- ebusd configs often define “replacement values” (sentinels) that mean “unknown/not available”. For floats, NaN and/or a dedicated replacement bit pattern are commonly used.

## Vaillant B524 Selectors (id field)

Many Vaillant-related ebusd CSVs encode B524 selectors as hex in the `id` field. A common convention is:

```text
b524,<PAYLOAD_HEX>
```

Where `<PAYLOAD_HEX>` is the raw B524 request payload bytes (no eBUS framing, no CRC).

Detailed semantics and response layouts are documented in:
- [`protocols/ebus-vaillant-GetExtendedRegisters.md`](../protocols/ebus-vaillant-GetExtendedRegisters.md)

### Directory Probe (opcode 0x00)

```text
00 GG 00
```

### Constraint Dictionary (opcode 0x01)

```text
01 GG RR
```

Notes:
- `RR` is the constraint-record selector byte for the `(GG, RR)` dictionary entry.
- Instance-selector form is not supported/documented in Helianthus (no programmatic evidence on observed buses).

### Register Read/Write (opcode 0x02 / 0x06)

Register selectors use a fixed 6-byte header (`RR` is little-endian u16):

```text
<opcode> <RW> <GG> <II> <RR_LO> <RR_HI>

opcode: 0x02 (local) or 0x06 (remote)
RW    : 0x00 (read) or 0x01 (write)
GG    : group id
II    : instance id
RR    : register id
```

Some ebusd CSVs use `II=0xFF` as a wildcard instance marker (“applies to all instances”).

### Timer Read/Write (opcode 0x03 / 0x04)

Timer selectors are 5 bytes:

```text
<opcode> <SEL1> <SEL2> <SEL3> <WD>

opcode: 0x03 (read timer) or 0x04 (write timer)
WD    : weekday 0x00..0x06 (Monday..Sunday)
```

### Array/Table Read (opcode 0x0B)

`0x0B` has been observed on B524 schedule/program domains (notably groups `0x06`/`0x07`), but a stable selector schema for CSV use is still under consolidation.

Current recommendation:
- keep `0x0B` mappings in dedicated experimental CSVs until selector/index semantics are finalized.
