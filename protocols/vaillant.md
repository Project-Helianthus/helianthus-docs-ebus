# Vaillant Message Identifiers (Observed)

This document lists Vaillant-family message identifiers and payload layouts that are currently supported. The same identifier may decode differently depending on target address or device class.

## Primary/Secondary Identifiers

```text
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x16  Energy statistics (request parameters: period/source/usage)
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
DateTime (8 bytes):
  dcfstate    : byte
  time_hour   : BCD
  time_minute : BCD
  date_day    : BCD
  date_month  : BCD
  date_year   : BCD
  temp        : DATA2b
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

## Energy Statistics

Energy statistics use primary/secondary `0xB5 0x16` and a 3-byte request payload:

```text
Request payload:
  period : byte
  source : byte
  usage  : byte
```

Responses are a single `WORD` (2 bytes, little-endian).
