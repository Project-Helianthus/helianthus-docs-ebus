# Vaillant Message Identifiers (Observed)

This document is the top-level reference for Vaillant message identifiers (`PB/SB`) observed by Helianthus tooling.

For detailed coverage of selector-heavy identifiers, see:
- `0xB5 0x16` (B516, Energy statistics): [`protocols/ebus-vaillant-B516-energy.md`](ebus-vaillant-B516-energy.md)
- `0xB5 0x24` (B524, GetExtendedRegisters): [`protocols/ebus-vaillant-B524.md`](ebus-vaillant-B524.md)
- `0xB5 0x55` (B555, timer/schedule protocol): [`protocols/ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)

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
0xB5 0x55  Timer/schedule protocol (B555; per-day weekly schedule access)
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
  [`protocols/ebus-vaillant-B524.md`](ebus-vaillant-B524.md)
- This includes opcode families, selector structures (`GG/II/RR`), response headers (`TT/GG/RR`), discovery rules, and schedule/table read notes.

## Timer/Schedule Protocol (0xB5 0x55, B555)

`0xB5 0x55` is the dedicated Vaillant timer/schedule protocol for weekly
heating, DHW, and circulation programs.

- Dedicated reference:
  [`protocols/ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
- This includes config/read/write opcode families (`0xA3`..`0xA6`), `ZONE`
  semantics, day/slot layout, and the documented B524 interaction caveats.

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

---

## Protocol Support Matrix (Observed per Device)

> **Added 2026-04-06** — observed via gateway 0x71 active probing + passive bus capture. Counts from current gateway session bus summary.

### Devices Tested

| Device | Master Address | Slave Address | Identity |
|--------|---------------|---------------|----------|
| BAI00 | 0x03 | 0x08 | Vaillant ecoTEC exclusive (boiler) |
| BASV2 | 0x10 | 0x15 | Vaillant sensoCOMFORT RF VRC 720f/2 (regulator) |
| VR_71 | 0x21 | 0x26 | Vaillant VR 71 (functional module) |
| NETX3 | 0xF1 | 0xF6 | Vaillant sensoNET VR 921 (internet gateway) |

### Standard eBUS Protocols

| PBSB | Protocol | BAI00 (0x03/0x08) | BASV2 (0x10/0x15) | VR_71 (0x21/0x26) | NETX3 (0xF1/0xF6) |
|------|----------|-------------------|--------------------|--------------------|---------------------|
| 0x0704 | Identification | slave | slave + master scan | slave | slave |
| 0x0700-0x07FF | All other 0x07xx | stub | stub | stub | stub |
| 0x0304-0x0310 | Service Data | stub | stub | stub | stub |
| 0x0500-0x050D | Burner Control | stub | stub | stub | stub |
| 0x0900 | RAM Read | stub | slave | stub | stub |
| 0x0902 | EEPROM Read | stub | slave | stub | stub |

**Notes:**

- `0x0704` is the only standard eBUS command with a real implementation (10-byte identification response). All other standard profiles (Service Data, Burner Control, Date/Time, etc.) are transport-level stubs — devices ACK them but return no data.
- `0x0900`/`0x0902` (Memory Server) works only on BASV2. SOL00 (slave address `0xEC`) is the same physical MCU as BASV2, exposing a secondary slave address.

### Vaillant Proprietary Protocols (0xB5xx)

| PBSB | Protocol | BAI00 (0x03/0x08) | BASV2 (0x10/0x15) | VR_71 (0x21/0x26) | NETX3 (0xF1/0xF6) |
|------|----------|-------------------|--------------------|--------------------|---------------------|
| 0xB504 | GetOperationalData | slave | slave | slave | slave |
| 0xB505 | SetOperationalData | slave | slave | slave | slave |
| 0xB509 | Register Access | slave (1533 rx) | slave (12 rx) | slave (5 rx) | slave (12 rx) |
| 0xB510 | Status/Diagnostic | slave (rx from BASV2) | master (→ BAI00) | — | — |
| 0xB511 | Remote Control | master (→ NETX3) + slave (rx from BASV2) | master (→ BAI00) | — | slave (rx from BAI00) |
| 0xB512 | Modulation/Fan | master (→ 0x64) | — | — | — |
| 0xB516 | Energy Statistics | — | master (broadcast → 0xFE, 146 tx) | — | — |
| 0xB524 | Extended Register | slave (1 rx) | slave (12124 rx) | slave (1 rx) | master (→ BASV2, 2 tx) |
| 0xB555 | Timer/Schedule | — | slave (465 rx) | — | master (→ BASV2) |

### Legend

- **slave** — device responds to queries on its slave address (tested actively by gateway 0x71)
- **master** — device initiates communication from its master address (observed passively on bus)
- **stub** — transport-level ACK, response `0x00`, no real data
- **—** — not observed on this device
- **tx/rx counts** — from gateway bus summary (current session)

---

## B510 Status/Diagnostic (0xB5 0x10)

B510 forms one half of the BASV2-to-BAI00 control channel. The regulator (BASV2) uses its master address to push status/diagnostic queries to the boiler (BAI00). The boiler responds on its slave address.

Direction: `BASV2 master (0x10) → BAI00 slave (0x08)`

No dedicated document exists yet. Payload structure is under investigation.

## B511 Remote Control (0xB5 0x11)

B511 implements a triangular multi-role communication pattern:

1. **BAI00 → NETX3**: The boiler master (0x03) sends remote control data to the internet gateway slave (0xF6). This is how the boiler reports state to the cloud.
2. **BASV2 → BAI00**: The regulator master (0x10) sends control commands to the boiler slave (0x08). This is how heating demand and setpoints are communicated.
3. **BAI00 receives from BASV2**: The boiler also acts as slave, receiving commands from the regulator.

Together with B510, these two protocols form the primary control loop between regulator, boiler, and internet gateway.

## B512 Modulation/Fan (0xB5 0x12)

B512 is observed only from BAI00 master address (0x03) targeting address 0x64. Address 0x64 is not in the device registry — it may be a virtual/internal address or an undiscovered device on some installations.

Direction: `BAI00 master (0x03) → 0x64`

Payload structure is unknown. Likely related to burner modulation or fan speed control.
