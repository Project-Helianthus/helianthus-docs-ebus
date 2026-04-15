# Vaillant Message Identifiers (Observed)

This document is the top-level reference for Vaillant message identifiers (`PB/SB`) observed by Helianthus tooling.

For detailed coverage of selector-heavy identifiers, see:
- `0xB5 0x03` (B503, error history): [`ebus-vaillant-B503.md`](ebus-vaillant-B503.md)
- `0xB5 0x04` (B504, GetOperationalData): [`ebus-vaillant-B504.md`](ebus-vaillant-B504.md)
- `0xB5 0x05` (B505, SetOperationalData): [`ebus-vaillant-B505.md`](ebus-vaillant-B505.md)
- `0xB5 0x06` (B506, error flags): [`ebus-vaillant-B506.md`](ebus-vaillant-B506.md)
- `0xB5 0x07` (B507, heat pump load/poll): [`ebus-vaillant-B507.md`](ebus-vaillant-B507.md)
- `0xB5 0x08` (B508, NoiseReduction broadcast): [`ebus-vaillant-B508.md`](ebus-vaillant-B508.md)
- `0xB5 0x09` (B509, register access / scan-id): [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md)
- `0xB5 0x10` (B510, SetMode): [`ebus-vaillant-B510.md`](ebus-vaillant-B510.md)
- `0xB5 0x11` (B511, remote control): [`ebus-vaillant-B511.md`](ebus-vaillant-B511.md)
- `0xB5 0x12` (B512, circulation pump / VR65-style state): [`ebus-vaillant-B512.md`](ebus-vaillant-B512.md)
- `0xB5 0x13` (B513, value-range query): [`ebus-vaillant-B513.md`](ebus-vaillant-B513.md)
- `0xB5 0x14` (B514, service test-menu values): [`ebus-vaillant-B514.md`](ebus-vaillant-B514.md)
- `0xB5 0x15` (B515, legacy timer template): [`ebus-vaillant-B515.md`](ebus-vaillant-B515.md)
- `0xB5 0x16` (B516, Energy statistics): [`ebus-vaillant-B516-energy.md`](ebus-vaillant-B516-energy.md)
- `0xB5 0x1A` (B51A, heat-pump statistics and live-monitor): [`ebus-vaillant-B51A.md`](ebus-vaillant-B51A.md)
- `0xB5 0x21` (B521, OMU service registers): [`ebus-vaillant-B521.md`](ebus-vaillant-B521.md)
- `0xB5 0x22` (B522, recoVAIR ventilation commands): [`ebus-vaillant-B522.md`](ebus-vaillant-B522.md)
- `0xB5 0x23` (B523, functional-module actor/sensor data): [`ebus-vaillant-B523.md`](ebus-vaillant-B523.md)
- `0xB5 0x24` (B524, GetExtendedRegisters): [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md)
- `0xB5 0x55` (B555, timer/schedule protocol): [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
- VR90 room controller emulation: [`ebus-vaillant-vr90-emulation.md`](ebus-vaillant-vr90-emulation.md)

## Scope

- This document describes payload bytes inside eBUS frames (CRC/escaping omitted).
- Layouts are observation-based and may vary by target class.
- `PB/SB` identifiers can multiplex multiple payload shapes.

## Identifier Index

```text
0xB5 0x03  Error history (B503; error log retrieval)
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x06  Error flags (B506; active error status)
0xB5 0x07  Heat pump load/poll (B507; CTLV2->HMU, heat-pump-only — enrichment research, not live-validated)
0xB5 0x08  NoiseReduction broadcast (B508; ZZ=FE broadcast — enrichment research, not live-validated)
0xB5 0x09  Register access / scan-id chunk discovery (selector-dependent payload forms)
0xB5 0x10  SetMode (B510; regulator->boiler mode and setpoint commands)
0xB5 0x11  Remote Control (B511; triangular control loop between regulator, boiler, and gateway)
0xB5 0x12  Circulation Pump / VR65-Style State (B512; pump state and VR65 control data)
0xB5 0x13  Value-range query
0xB5 0x14  Service test-menu values
0xB5 0x15  Legacy timer template
0xB5 0x16  Energy statistics (selector-encoded request; EXP Wh response)
0xB5 0x1A  Heat-pump statistics and live-monitor values
0xB5 0x21  OMU service register family
0xB5 0x22  recoVAIR ventilation commands
0xB5 0x23  Functional-module actor and sensor data for VR70/VR71-like targets
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

<a id="vaillant-scanid-chunks-qq0x240x27"></a>
### Form B: scan.id chunk discovery (QQ=0x24..0x27)

This subsection is the Vaillant extended discovery function used by BASV-style discovery enrichment (`0xB5 0x09` with well-known selector values).

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
  [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md)
- This includes opcode families, selector structures (`GG/II/RR`), response headers (`FLAGS/GG/RR`), discovery rules, and schedule/table read notes.

## Timer/Schedule Protocol (0xB5 0x55, B555)

`0xB5 0x55` is the dedicated Vaillant timer/schedule protocol for weekly
heating, DHW, and circulation programs.

- Dedicated reference:
  [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
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
    9 = heat_pump (unconfirmed — observed on some heat pumps, not in dedicated B516 doc)

  usage Z:
    0 = all
    3 = heating
    4 = hot water
    5 = cooling
```

VWZ/VWZIO at address 0x76 uses an alternative query form (sub-ID 0x18); see dedicated doc Section 8.

```text
Response payload (~11 bytes, variable):
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

## Device-Type Reference

> Source: `GATES-protocol-level.md` Section 1, `FINAL-corrections-and-devices.md` Part B.

### VRC720 Family (720-Series Controllers)

All share eBUS address `0x15`, B524 (OP=0x02/0x06), and B555 timer transport.

| Variant | Device IDs | Form Factor |
|---------|-----------|-------------|
| Wireless base stations (Vaillant) | BASV0, BASV2, BASV3 | RF bridge near boiler/HP |
| Wireless base stations (Saunier Duval) | BASS0, BASS2, BASS3 | RF bridge near boiler/HP |
| Wired controllers (Vaillant) | CTLV0, CTLV2, CTLV3 | Wall-mounted wired unit |
| Wired controllers (Saunier Duval) | CTLS2 | Wall-mounted wired unit |

### VRC700 Family (700-Series Controllers)

Separate older family. eBUS address `0x15`. B524 (OP=0x02 shared, OP=0x03/0x04 VRC700-specific timer access). Does **NOT** support B555.

| Device ID | Notes |
|-----------|-------|
| 70000 | Vaillant multiMATIC VRC700 |
| B7S00 | Saunier Duval alias of VRC700 |

### Device-Type Protocol Support Matrix

| Device Type | eBUS Addr | Key Protocols | Timer Transport |
|-------------|-----------|---------------|-----------------|
| BAI00 (gas boiler) | 0x08 | B503, B504, B505, B509 (1533 rx), B510, B511, B512 | N/A |
| EHP00 (heat pump IDU) | 0x08 | B504, B505, B507, B509 (EHP regs), B511, B514, B51A | N/A |
| HMU00 (hydraulic mgmt) | 0x08 | B504, B505, B509 (`54 02 00` sub-addressing), B511, B512, B514, B51A | N/A |
| VRC720 family | 0x15 | B504, B505, B509, B524 (OP=0x02/0x06) | B555 |
| VRC700 | 0x15 | B524 (OP=0x02/0x03/0x04) | B524 0x03/0x04 |
| VRC Legacy (VRT 350/370/430/470) | 0x15 | B509 only (7 regs) | None |
| VR_71 (functional module) | 0x26 | B504, B505, B509, B523, B524 (stub) | N/A |
| NETX3 / VR921 (gateway) | 0xF6 | B504, B505, B509, B511, B524 initiator, B555 initiator | N/A |
| SOL00 (solar/FM5 module) | 0xEC | Same MCU as BASV2 (secondary target). Protocol support on 0xEC is uncharacterized beyond memory server (0x0900/0x0902). | N/A |
| VWZIO (indoor hydraulic station) | 0x76 | B511, B512, B514 (T.1), B516, B51A | N/A |

### eBUS Address Collision Warning

Address `0x08` hosts completely different device types depending on installation:
- **BAI00** (gas boiler) — B509 register `0xBB00` = `gasValveActive` (UCH sentinel 0x0F/0xF0)
- **EHP00/HMU** (heat pump) — same address `0xBB00` = `actualEnvPowerPercentage` (percent, %)

Device type MUST be established via B509 product ID scan (`0x9A00` DSN or scan-ID chunks `0x24`-`0x27`) before decoding any B509 register at address `0x08`.

### f32 Byte Order Gate

B524 f32 registers have device-dependent byte order:

| Device | eBUS Address | f32 Byte Order |
|--------|-------------|----------------|
| BASV2, CTLV2, VRC720 | 0x15 | Little-endian |
| HMU (heat pump) | 0x08 | **Big-endian** |

---

## Protocol Support Matrix (Observed per Device)

> **Added 2026-04-06** — observed via gateway 0x71 active probing + passive bus capture. Counts from current gateway session bus summary.

### Devices Tested

| Device | Initiator Address | Target Address | Identity |
|--------|-------------------|----------------|----------|
| BAI00 | 0x03 | 0x08 | Vaillant ecoTEC exclusive (boiler) |
| BASV2 | 0x10 | 0x15 | Vaillant sensoCOMFORT RF VRC 720f/2 (regulator) |
| VR_71 | 0x21 | 0x26 | Vaillant VR 71 (functional module) |
| NETX3 | 0xF1 | 0xF6 | Vaillant sensoNET VR 921 (internet gateway) |

### Standard eBUS Protocols

| PBSB | Protocol | BAI00 (0x03/0x08) | BASV2 (0x10/0x15) | VR_71 (0x21/0x26) | NETX3 (0xF1/0xF6) |
|------|----------|-------------------|--------------------|--------------------|---------------------|
| 0x0704 | Identification | target | target + initiator scan | target | target |
| 0x0700-0x07FF | All other 0x07xx | stub | stub | stub | stub |
| 0x0304-0x0310 | Service Data | stub | stub | stub | stub |
| 0x0500-0x050D | Burner Control | stub | stub | stub | stub |
| 0x0900 | RAM Read | stub | target | stub | stub |
| 0x0902 | EEPROM Read | stub | target | stub | stub |

**Notes:**

- `0x0704` is the only standard eBUS command with a real implementation (10-byte identification response). All other standard profiles (Service Data, Burner Control, Date/Time, etc.) are transport-level stubs — devices ACK them but return no data.
- `0x0900`/`0x0902` (Memory Server) works only on BASV2. SOL00 (target address `0xEC`) is the same physical MCU as BASV2, exposing a secondary target address.

### Vaillant Proprietary Protocols (0xB5xx)

| PBSB | Protocol | BAI00 (0x03/0x08) | BASV2 (0x10/0x15) | VR_71 (0x21/0x26) | NETX3 (0xF1/0xF6) |
|------|----------|-------------------|--------------------|--------------------|---------------------|
| 0xB504 | GetOperationalData | target | target | target | target |
| 0xB505 | SetOperationalData | target | target | target | target |
| 0xB509 | Register Access | target (1533 rx) | target (12 rx) | target (5 rx) | target (12 rx) |
| 0xB510 | SetMode | target (rx from BASV2) | initiator (-> BAI00) | — | — |
| 0xB511 | Remote Control | initiator (-> NETX3) + target (rx from BASV2) | initiator (-> BAI00) | — | target (rx from BAI00) |
| 0xB512 | Circulation Pump / VR65 | initiator (-> 0x64) | — | — | — |
| 0xB516 | Energy Statistics | — | initiator (broadcast -> 0xFE, 146 tx) | — | — |
| 0xB524 | Extended Register | target (1 rx) | target (12124 rx) | target (1 rx) | initiator (-> BASV2, 2 tx) |
| 0xB555 | Timer/Schedule | — | target (465 rx) | — | initiator (-> BASV2) |

### Legend

- **target** — device responds to queries on its target address (tested actively by gateway 0x71)
- **initiator** — device initiates communication from its initiator address (observed passively on bus)
- **stub** — transport-level ACK, response `0x00`, no real data
- **---** — not observed on this device
- **tx/rx counts** — from gateway bus summary (current session)

---

## SetMode (0xB5 0x10, B510)

`0xB5 0x10` carries SetMode commands from the regulator to the boiler (BASV2 initiator 0x10 -> BAI00 target 0x08).

- Dedicated reference: [`ebus-vaillant-B510.md`](ebus-vaillant-B510.md)
- Payload includes hcmode, flowtempdesired, hwctempdesired, hwcflowtempdesired, and disable/release bits.

## Remote Control (0xB5 0x11, B511)

B511 implements a triangular multi-role communication pattern:

1. **BAI00 -> NETX3**: The boiler initiator (0x03) sends remote control data to the internet gateway target (0xF6). This is how the boiler reports state to the cloud.
2. **BASV2 -> BAI00**: The regulator initiator (0x10) sends control commands to the boiler target (0x08). This is how heating demand and setpoints are communicated.
3. **BAI00 receives from BASV2**: The boiler also acts as target, receiving commands from the regulator.

Together with B510, these two protocols form the primary control loop between regulator, boiler, and internet gateway.

On heat pump systems with VWZIO (0x76), B511 traffic involving that device has also been observed.

- Dedicated reference: [`ebus-vaillant-B511.md`](ebus-vaillant-B511.md)

## Circulation Pump / VR65-Style State (0xB5 0x12, B512)

`0xB5 0x12` carries circulation pump state and VR65-style control data. Observed from BAI00 initiator (0x03) targeting address 0x64.

- Dedicated reference: [`ebus-vaillant-B512.md`](ebus-vaillant-B512.md)
- Known selectors include StatusCirPump (off=0, on=100), VR65-style shape (0x02), and heat-pump-specific shapes.
