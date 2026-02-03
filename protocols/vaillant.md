# Vaillant Message Identifiers (Observed)

This document lists Vaillant-family message identifiers and payload layouts that are currently supported. The same identifier may decode differently depending on target address or device class.

## Primary/Secondary Identifiers

```text
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x09  Register access (read/write selector + 16-bit address)
0xB5 0x24  Extended register access (prefix + 16-bit address)
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

If present, the response payload can be decoded as:

```text
DateTime (10 bytes):
  dcfstate      : byte
  time_second   : BCD  (BTI[0] on wire, SS,MM,HH)
  time_minute   : BCD  (BTI[1])
  time_hour     : BCD  (BTI[2])
  date_day      : BCD  (BDA[0] on wire, DD,MM,<weekday>,YY)
  date_month    : BCD  (BDA[1])
  date_weekday  : byte (BDA[2], typically ignored)
  date_year     : BCD  (BDA[3])
  temp          : DATA2b (temp2)
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

## Extended Register Access (0xB5 0x24)

`0xB5 0x24` is used by Vaillant regulators (e.g., `ctlv2`) as an extended register-like access mechanism. Requests start with a 4-byte prefix and a 16-bit address.

```text
Read request payload (6 bytes):
  0: 0x02          constant prefix
  1: 0x00          read selector
  2: group         byte
  3: instance      byte
  4: addr_hi       byte
  5: addr_lo       byte

Write request payload (6+ bytes):
  0: 0x02          constant prefix
  1: 0x01          write selector
  2: group         byte
  3: instance      byte
  4: addr_hi       byte
  5: addr_lo       byte
  6..: data        bytes (0+)
```

Read responses are commonly observed with the first 4 bytes matching the prefix (`0x02 0x00 group instance`) followed by value bytes (many ebusd CSV definitions use `IGN:4` before decoding the value).

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
