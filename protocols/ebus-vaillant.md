# Vaillant Message Identifiers (Observed)

This document is the top-level reference for Vaillant message identifiers (`PB/SB`) observed by Helianthus tooling.

For detailed coverage of selector-heavy identifiers, see:
- `0xB5 0x16` (B516, Energy statistics): [`protocols/ebus-vaillant-B516-energy.md`](ebus-vaillant-B516-energy.md)
- `0xB5 0x24` (B524, GetExtendedRegisters): [`protocols/ebus-vaillant-GetExtendedRegisters.md`](ebus-vaillant-GetExtendedRegisters.md)

## Scope

- This document describes payload bytes inside eBUS frames (CRC/escaping omitted).
- Layouts are observation-based and may vary by target class.
- `PB/SB` identifiers can multiplex multiple payload shapes.

## Identifier Index

```text
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x09  Register access / scan-id chunk discovery (selector-dependent payload forms)
0xB5 0x16  Energy statistics (selector-encoded request; EXP Wh response)
0xB5 0x24  GetExtendedRegisters (B524; selector-opcode multiplexed)
0xFE 0x01  System-level broadcast (payload unspecified here)
```

## GetOperationalData (0xB5 0x04)

The `0xB5 0x04` identifier uses a 1-byte `op` selector. Response layout depends on `op` and target class.

```text
Request payload (1 byte):
  op : byte
```

### op = 0x00 (DateTime)

Two response layouts are currently observed and supported.

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

### Other observed selectors/layouts

```text
Common op selectors:
  0x09  Parameters (5 bytes; layout depends on target class)
  0x0D  Status (1 byte)

Example payload families:
  Boiler parameters (5 bytes): flow_temp(DATA2b), return_temp(DATA2b), pump_status(DATA1b)
  Controller parameters (5 bytes): room_temp(DATA2b), target_temp(DATA2b), mode(DATA1b)
  Solar status (4 bytes): collector_temp(DATA2b), tank_temp(DATA2b)
  Solar parameters (3 bytes): pump_speed(DATA1b), delta_temp(DATA2b)
  Simple status (1 byte): status(DATA1b)
```

## SetOperationalData (0xB5 0x05)

`0xB5 0x05` uses op-coded writes.

```text
Request payload (1+ bytes):
  op      : byte
  payload : bytes (optional)
```

Response is device/op-specific and may be empty (ack-only).

## Register Access (0xB5 0x09)

`0xB5 0x09` multiplexes at least two payload forms.

### Form A: register-like read/write

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

Response is device/register-specific. In some cases, only a single `0x00` status byte is observed.

This subsection is the Vaillant extended discovery function used by BASV-style discovery enrichment (`0xB5 0x09` with well-known selector values).

<a id="vaillant-scanid-chunks-qq0x240x27"></a>
### Form B: scan.id chunk discovery (QQ=0x24..0x27)

Some Vaillant devices (manufacturer byte `0xB5`) use one-byte selectors to return fixed-size ASCII chunks.

```text
Request payload (1 byte):
  QQ : byte (typically one of 0x24, 0x25, 0x26, 0x27)

Response payload (9 bytes):
  0: status   byte (0x00 indicates success)
  1..8: ascii 8 bytes (NUL/space padded)
```

For deterministic target emulation:
- treat this format as valid only when payload is exactly one selector byte
- evaluate this strict `QQ=0x24..0x27` form before broader `0xB5 0x09` selector maps
- avoid shadowing scan-id chunk reads with generic register handlers

Assembly rule:
1. Query `QQ=0x24..0x27`.
2. Concatenate bytes `1..8` from each response.
3. Trim trailing NUL/whitespace.

The resulting string is often parsed into model/product and serial-like fields; exact formatting varies by Vaillant generation.

See `development/target-emulation.md` for Helianthus implementation details.

## GetExtendedRegisters (0xB5 0x24, B524)

`0xB5 0x24` is a selector-opcode multiplexed protocol used heavily by Vaillant regulators.

- Dedicated reference:
  [`protocols/ebus-vaillant-GetExtendedRegisters.md`](ebus-vaillant-GetExtendedRegisters.md)
- This includes opcode families, selector structures (`GG/II/RR`), response headers (`TT/GG/RR`), discovery rules, and schedule/table read notes.

## Energy Statistics (0xB5 0x16)

Energy statistics use selector-encoded requests with an `EXP` value response.
The format is reverse engineered from observed traffic (see `john30/ebusd-configuration` issue `#490`).

```text
Request payload (8 bytes):
  0: 0x10          constant prefix
  1: 0x0X          period selector (X in low nibble)
  2: 0xFF
  3: 0xFF
  4: 0x0Y          source selector (Y in low nibble)
  5: 0x0Z          usage selector (Z in low nibble)
  6: 0xWV          month/day selector (W high nibble, V low nibble)
  7: 0xQQ          year selector byte
```

```text
Observed selectors:
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

```text
Response payload (11 bytes):
  0: 0x0X          period selector (X in low nibble)
  1: (unknown)
  2: (unknown)
  3: 0x0Y          source selector (Y in low nibble)
  4: 0x0Z          usage selector (Z in low nibble)
  5: 0xWV          month/day selector (W high nibble, V low nibble)
  6: 0xQQ          year selector byte
  7..10: EXP       Wh value (IEEE 754 float32, little-endian)
```

Encoding of `W/V/QQ` is regulator-dependent; observations indicate:
- For X=0 (all): `W/V/QQ` ignored.
- For X=3 (year): `QQ` is the number of half-years since year 2000.
  - `QQ = 0x34` (52) → first half of 2026 (`2000 + floor(52/2)`).
  - `QQ = 0x35` (53) → second half of 2026.
- For X=2 (month): month is still selected via `W`, while `QQ` provides the year context using the same half-year timeline.
- For X=1 (day): only the last 16 days are available; `W` parity selects first/second half of month, `V` selects day within half, and `QQ+W` determine year/month context.
