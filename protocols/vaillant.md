# Vaillant Message Identifiers (Observed)

This document lists Vaillant-family message identifiers and payload layouts that are currently supported. The same identifier may decode differently depending on target address or device class.

## Primary/Secondary Identifiers

```text
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x09  Register access (read/write selector + 16-bit address)
0xB5 0x24  Extended register access (selector + 16-bit register id)
0xB5 0x16  Energy statistics (selector-encoded request; EXP Wh response)
0xFE 0x01  System-level broadcast (payload unspecified here)
```

## GetOperationalData (0xB5 0x04)

The `0xB5 0x04` identifier is used for multiple payload layouts. The request payload is a single 1-byte `op` selector; the response payload layout depends on `op` (and potentially device class/target).

```text
Request payload (1 byte):
  op : byte
```

### op = 0x00 (DateTime)

Two response layouts are currently observed and supported. The decoder uses `dcfstate`, `time_hour`, `time_minute`, `date_day`, `date_month`, `date_year`, and `temp` in both cases. Seconds (layout A) and weekday (layout A) are present on the wire but currently ignored by the decoder.

```text
DateTime layout A (BTI/BDA + temp2, 10 bytes):
  dcfstate      : byte
  time_second   : BCD  (BTI[0] on wire, SS,MM,HH) [ignored]
  time_minute   : BCD  (BTI[1])
  time_hour     : BCD  (BTI[2])
  date_day      : BCD  (BDA[0] on wire, DD,MM,<weekday>,YY)
  date_month    : BCD  (BDA[1])
  date_weekday  : byte (BDA[2]) [ignored]
  date_year     : BCD  (BDA[3])
  temp          : DATA2b (temp2)
```

```text
DateTime layout B (legacy, 8 bytes):
  dcfstate      : byte
  time_hour     : BCD
  time_minute   : BCD
  date_day      : BCD
  date_month    : BCD
  date_year     : BCD
  temp          : DATA2b (temp2)
```

### Common op selectors (observed)

```text
0x09  Parameters (5 bytes; layout depends on target class)
0x0D  Status (1 byte)
```

### Other observed payload layouts (examples)

```text
Boiler parameters (5 bytes):
  flow_temp     : DATA2b
  return_temp   : DATA2b
  pump_status   : DATA1b

Controller parameters (5 bytes):
  room_temp     : DATA2b
  target_temp   : DATA2b
  mode          : DATA1b
```

```text
Solar status (4 bytes):
  collector_temp : DATA2b
  tank_temp      : DATA2b
```

```text
Solar parameters (3 bytes):
  pump_speed : DATA1b
  delta_temp : DATA2b
```

```text
Simple status (1 byte):
  status : DATA1b
```

## SetOperationalData (0xB5 0x05)

The `0xB5 0x05` identifier is used for op-coded writes. The request payload starts with a 1-byte `op` selector, followed by an optional payload.

```text
Request payload (1+ bytes):
  op      : byte
  payload : bytes (optional)
```

Response payload is device/op-specific and may be empty (ack-only).

## Register Access (0xB5 0x09)

`0xB5 0x09` is used for register-like access using a selector byte plus a 16-bit address. The same primary/secondary is used for both reads and writes; the selector byte indicates the operation.

```text
Read request payload (3 bytes):
  op      : 0x0D
  addr_hi : byte
  addr_lo : byte

Write request payload (3+ bytes):
  op      : 0x0E
  addr_hi : byte
  addr_lo : byte
  data    : bytes (0+)
```

Response payload layout is device/register-specific. In some cases, a single `0x00` byte is observed instead of a typed value (commonly reported as “invalid position” by ebusd).

### Vaillant scan.id chunks (QQ=0x24..0x27)

In addition to the `0x0D`/`0x0E` register access sub-format above, Vaillant devices are also observed to use `0xB5 0x09` with a **1-byte selector** (`QQ`) to return fixed-size ASCII chunks that can be assembled into a “scan id” string.

See `protocols/basv.md` for the observed request/response layout and assembly rules.

## Extended Register Access (0xB5 0x24)

`0xB5 0x24` (often referred to as “B524”) is used by Vaillant regulators as a selector-based extended register mechanism. The request/response format is multiplexed by the first payload byte (`opcode`).

This section documents the **payload bytes** inside an eBUS frame (not including eBUS CRC/escaping). When interacting via ebusd’s TCP `hex` command, note that ebusd typically prefixes the slave response with a 1-byte eBUS response length; see `protocols/ebusd-tcp.md`.

Opcode family (observed):

- `0x00`: directory probe (group descriptor scan)
- `0x02`: local register read/write
- `0x06`: remote register read/write (commonly groups `0x09`, `0x0A`, `0x0C`)
- `0x03`: timer read
- `0x04`: timer write

### Directory Probe (opcode 0x00)

The directory probe is used to enumerate groups (GG). Each request probes one group id and returns a float descriptor.

```text
Request payload (3 bytes):
  0: 0x00          opcode (directory probe)
  1: GG            group id
  2: 0x00          padding

Response payload (4 bytes):
  0..3: descriptor float32le
```

Notes (observed):
- The descriptor is an IEEE 754 `float32` (little-endian).
- `NaN` is used as an end-of-directory marker.
- `0.0` may appear for “holes” (unassigned group ids).

### Register Read/Write (opcode 0x02 / 0x06)

Register access uses two opcode families that share the same selector layout:

- `0x02`: “local” register space (common for regulator-internal groups)
- `0x06`: “remote” register space (commonly used for room sensor/remote groups)

```text
Request payload (read, 6 bytes; RR is little-endian u16):
  0: opcode        0x02 (local) or 0x06 (remote)
  1: optype        0x00 (read)
  2: GG            group id
  3: II            instance id
  4: RR_LO         register id low byte
  5: RR_HI         register id high byte

Request payload (write, 6+ bytes):
  0: opcode        0x02 (local) or 0x06 (remote)
  1: optype        0x01 (write)
  2: GG            group id
  3: II            instance id
  4: RR_LO
  5: RR_HI
  6..: value bytes

Response payload (read, observed):
  0: TT            reply kind / status
  1: GG            group id (echo)
  2: RR_LO         register id low byte (echo)
  3: RR_HI         register id high byte (echo)
  4..: value bytes (optional)
```

Notes (observed):
- `RR` is encoded little-endian: `RR = RR_LO + (RR_HI << 8)`.
- The response header is `TT GG RR_LO RR_HI`.
- The response does **not** include `II` (instance) and does **not** echo the request opcode/optype.
- Some replies are status-only and contain only `TT` (1 byte, no GG/RR/value bytes).
- `TT` semantics (empirical):
  - `0x00`: no data / not present / invalid
  - `0x01`: live / operational value
  - `0x02`: parameter / limit
  - `0x03`: parameter / config

### Timer Read/Write (opcode 0x03 / 0x04)

Some Vaillant regulators expose timer schedules via B524 selector opcodes `0x03` and `0x04`.

```text
Request payload (read timer, 5 bytes):
  0: 0x03          opcode (timer read)
  1: SEL1          selector tuple byte 1
  2: SEL2          selector tuple byte 2
  3: SEL3          selector tuple byte 3
  4: WD            weekday (0x00..0x06)

Request payload (write timer, 5+ bytes):
  0: 0x04          opcode (timer write)
  1: SEL1
  2: SEL2
  3: SEL3
  4: WD
  5..: blocks      timer blocks (format device-/model-specific)
```

### Known Groups (Observed on VRC720-class Regulators)

The directory probe descriptor (`float32le`) appears stable per group and can be used as a coarse group “type”. The table below lists observed groups and typical scan defaults used by Helianthus tooling.

```text
GG   Name                  Descriptor  Instanced  Typical opcode  Notes
0x00 Regulator Parameters  3.0         no         0x02           RR extends beyond 0x00FF (seen up to 0x01FF)
0x01 Hot Water Circuit     3.0         no         0x02
0x02 Heating Circuits      1.0         yes        0x02
0x03 Zones                 1.0         yes        0x02
0x04 Solar Circuit         6.0         no         0x02
0x05 Hot Water Cylinder    1.0         yes/varies 0x02           (instancing varies by model)
0x09 Room Sensors          1.0         yes        0x06
0x0A Room State            1.0         yes        0x06
0x0C Unknown               1.0         yes        0x06
```

### B524 Discovery Profile (Helianthus)

Helianthus uses a static discovery profile to bound B524 group scans. Each entry specifies the opcode family and the **inclusive** upper limits for instance id and register id when probing a group. The directory probe should still be used to verify group presence; these are defaults based on observed VRC720-class regulators.

```text
GG   Opcode  InstanceMax  RegisterMax  Notes
0x02 0x02    0x0A         0x0021       Heating circuits (local)
0x03 0x02    0x0A         0x002F       Zones (local)
0x09 0x06    0x0A         0x002F       Room sensors (remote)
0x0A 0x06    0x0A         0x003F       Room state (remote)
0x0C 0x06    0x0A         0x003F       Unknown (remote)
```

## Energy Statistics (0xB5 0x16)

Energy statistics use primary/secondary `0xB5 0x16` and a selector-encoded payload. This format is reverse engineered from observed traffic (see `john30/ebusd-configuration` issue `#490`).

```text
Request payload (8 bytes):
  0: 0x10          constant prefix
  1: 0x0X          period selector (X in low nibble)
  2: 0xFF
  3: 0xFF
  4: 0x0Y          source selector (Y in low nibble)
  5: 0x0Z          usage selector (Z in low nibble)
  6: 0xWV          month/day selector (W high nibble, V low nibble)
  7: 0x3Q          Q selector (Q in low nibble; high nibble observed as 0x3)

Selectors (observed):
  period X:
    0 = all (since installation)
    1 = day
    2 = month
    3 = year

  source Y:
    1 = solar
    2 = environmental
    3 = electricity
    4 = gas
    9 = heat_pump (unidentified, seen on some heat pumps)

  usage Z:
    0 = all
    3 = heating
    4 = hot water
    5 = cooling
```

W/V/Q encoding is device-/regulator-dependent and was reverse engineered for Vaillant `ctlv2`-style regulators. In brief:

- For X=0 (all): W/V/Q are ignored.
- For X=3 (year): Q selects previous/current; W/V are ignored.
- For X=2 (month): W selects month; Q selects previous/current year (encoding differs for months 1–7 vs 8–12); V is ignored.
- For X=1 (day): only the last 16 days are available; W parity selects first/second half of the month; V selects day within that half; Q+W determine year/month.

```text
Response payload (11 bytes):
  0: 0x0X          period selector (X in low nibble)
  1: (unknown)
  2: (unknown)
  3: 0x0Y          source selector (Y in low nibble)
  4: 0x0Z          usage selector (Z in low nibble)
  5: 0xWV          month/day selector (W high nibble, V low nibble)
  6: 0x3Q          Q selector (Q in low nibble; high nibble observed as 0x3)
  7..10: EXP       Wh value (IEEE 754 float32, little-endian)
```
