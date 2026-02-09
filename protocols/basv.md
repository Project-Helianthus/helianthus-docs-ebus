# Device Discovery (BASV) (Observed)

This document describes common eBUS discovery messages used to enumerate devices on the bus and read basic identity metadata. The layouts here describe the **payload bytes** inside an eBUS frame (not including CRC/escaping).

## QueryExistence (0x07 0xFE)

QueryExistence is commonly used as a best-effort “who is present?” broadcast.

```text
Master telegram:
  DST = 0xFE (broadcast)
  PB  = 0x07
  SB  = 0xFE
  LEN = 0x00
  DATA = (empty)
```

Notes:
- Broadcast messages do not have a response telegram.
- Some stacks (including ebusd) use QueryExistence as a trigger to refresh internal address state that can later be queried (e.g. via the ebusd TCP `info` command).

## Identification Scan (0x07 0x04)

Identification (often “scan” in ebusd terminology) reads a device’s manufacturer, device id, and software/hardware versions.

```text
Master telegram:
  DST = <candidate slave address>
  PB  = 0x07
  SB  = 0x04
  LEN = 0x00
  DATA = (empty)
```

Observed slave response payload layout:

```text
  0: manufacturer   byte
  1..(N-5): device_id ASCII (NUL-padded; length varies)
  (N-4)..(N-3): sw   2 bytes (opaque)
  (N-2)..(N-1): hw   2 bytes (opaque)
```

Notes:
- The response length varies by device because the device id field is variable-length.
- Many tools treat `sw`/`hw` as opaque hex.

## Vendor Extension: Vaillant scan.id via 0xB5 0x09

Some Vaillant devices (manufacturer byte `0xB5`) expose a “scan id” string via `0xB5 0x09` requests with a 1-byte selector (`QQ`).

```text
Request payload (1 byte):
  QQ : byte

Where QQ is typically one of: 0x24, 0x25, 0x26, 0x27
```

Each response returns one chunk:

```text
Response payload (9 bytes):
  0: status   byte (0x00 indicates success)
  1..8: ascii 8 bytes (NUL/space padded)
```

To assemble the full scan id:
1. Request chunks for `QQ=0x24..0x27` (4 chunks).
2. Concatenate the 8-byte ASCII segments (total 32 bytes).
3. Strip trailing NULs and whitespace.

The resulting string is often parsed into fields such as product/model number and a serial-like suffix; the exact format may vary across Vaillant device generations.

