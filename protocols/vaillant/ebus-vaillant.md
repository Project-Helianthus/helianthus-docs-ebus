# Vaillant Message Identifiers (Observed)

This document is the top-level reference for observed Vaillant message identifiers (`PB/SB`).

For detailed coverage of selector-heavy identifiers, see:
- `0xB5 0x03` (B503, diagnostic / service / HMU live-monitor — **normative L7 spec**): [`ebus-vaillant-B503.md`](ebus-vaillant-B503.md)
- `0xB5 0x04` (B504, GetOperationalData): [`ebus-vaillant-B504.md`](ebus-vaillant-B504.md)
- `0xB5 0x05` (B505, SetOperationalData): [`ebus-vaillant-B505.md`](ebus-vaillant-B505.md)
- `0xB5 0x06` (B506, I/O and test services): [`ebus-vaillant-B506.md`](ebus-vaillant-B506.md)
- `0xB5 0x07` (B507, heat pump load/poll): [`ebus-vaillant-B507.md`](ebus-vaillant-B507.md)
- `0xB5 0x08` (B508, NoiseReduction broadcast): [`ebus-vaillant-B508.md`](ebus-vaillant-B508.md)
- `0xB5 0x09` (B509, register access / scan-id): [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md)
- `0xB5 0x10` (B510, SetMode): [`ebus-vaillant-B510.md`](ebus-vaillant-B510.md)
- `0xB5 0x11` (B511, remote control): [`ebus-vaillant-B511.md`](ebus-vaillant-B511.md)
- `0xB5 0x12` (B512, circulation pump / VR65-style state): [`ebus-vaillant-B512.md`](ebus-vaillant-B512.md)
- `0xB5 0x13` (B513, value-range query): [`ebus-vaillant-B513.md`](ebus-vaillant-B513.md)
- `0xB5 0x14` (B514, service test-menu values): [`ebus-vaillant-B514.md`](ebus-vaillant-B514.md)
  — [diagnostic-menu feedback and pressure candidates supplement](ebus-b514-menu-feedback.md) (**Hypothesis**)
- `0xB5 0x15` (B515, legacy timer template): [`ebus-vaillant-B515.md`](ebus-vaillant-B515.md)
- `0xB5 0x16` (B516, Energy statistics): [`ebus-vaillant-B516-energy.md`](ebus-vaillant-B516-energy.md)
- `0xB5 0x1A` (B51A, heat-pump statistics and live-monitor): [`ebus-vaillant-B51A.md`](ebus-vaillant-B51A.md)
- `0xB5 0x20` (B520, simulator actuator ranges and ADC quantities): [`ebus-vaillant-B520.md`](ebus-vaillant-B520.md)
- `0xB5 0x21` (B521, OMU service registers): [`ebus-vaillant-B521.md`](ebus-vaillant-B521.md)
- `0xB5 0x22` (B522, recoVAIR ventilation commands): [`ebus-vaillant-B522.md`](ebus-vaillant-B522.md)
- `0xB5 0x23` (B523, functional-module actor/sensor data): [`ebus-vaillant-B523.md`](ebus-vaillant-B523.md)
- `0xB5 0x24` (B524, GetExtendedRegisters): [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md)
- `0xB5 0x55` (B555, timer/schedule protocol): [`ebus-vaillant-b555-timer-protocol.md`](ebus-vaillant-b555-timer-protocol.md)
- VR90 room controller protocol: [`ebus-vaillant-vr90-emulation.md`](ebus-vaillant-vr90-emulation.md)
- B5 services without a dedicated page (B501, B502, B50A to B50D, B50F, B517 to B519, B525, header-only identities): [Other B5 services](#other-b5-services-candidate-layouts)

## Scope

- This document describes payload bytes inside eBUS frames (CRC/escaping omitted).
- Layouts are observation-based and may vary by target class.
- `PB/SB` identifiers can multiplex multiple payload shapes.
- A layout marked "candidate layout" is unconfirmed on the wire.

## EBUS and PeBUS protocol profiles

Candidate interpretation, unconfirmed on the wire: B5 service layouts belong to
one of two protocol profiles, `EBUS` and `PeBUS`. The expansion of the name
PeBUS is not known, so this repository does not expand it.

- No op of the B5 services B501 to B525 and B555 is known to be available only on
  PeBUS (candidate), with one candidate exception, unresolved: `B5 09 34`, which
  may be available only under PeBUS on some installations. The
  [B509 page](ebus-vaillant-B509.md) states instead that no B509 subcommand is
  known to be available only on PeBUS (candidate); `B5 09 34` is not in its
  subcommand table, and the disagreement is unresolved.
- The pages of [B503](ebus-vaillant-B503.md) (with `B5 09 18`),
  [B50E](ebus-vaillant-B50E.md), [B509](ebus-vaillant-B509.md),
  [B510](ebus-vaillant-B510.md), [B511](ebus-vaillant-B511.md),
  [B512](ebus-vaillant-B512.md), [B513](ebus-vaillant-B513.md),
  [B514](ebus-vaillant-B514.md), [B515](ebus-vaillant-B515.md),
  [B516](ebus-vaillant-B516-energy.md) and
  [B555](ebus-vaillant-b555-timer-protocol.md) state, as a candidate
  unconfirmed on the wire, that the operations they list are available under
  both the eBUS and the PeBUS profiles; each page names the operations its
  statement covers and any entries it leaves open. For the other B5 services,
  and for the operations those pages leave open, whether they are available
  under the PeBUS profile is not established.
- An endpoint that is available only on PeBUS is marked inline where it is
  described. The layout of `B5 09 34` is not established (see the
  [identifier index](#identifier-index)).

The word PeBus also has other meanings in candidate layouts:

- Candidate, unconfirmed on the wire: the B5 09 54 request carries a PeBus-address
  byte directly after the subcommand byte, and the B5 09 28 request carries a
  PeBus-address `u8`.
- Candidate, unconfirmed on the wire: bit 3 of the B5 11 0E status byte is a
  PeBus flag; its effect is unknown.

The [B509](ebus-vaillant-B509.md) and [B511](ebus-vaillant-B511.md) pages spell
these address bytes and this flag "PeBUS".

The profile assignment is a candidate, unconfirmed on the wire; it does not state
which bus, device or wiring uses which profile.

## Device ID Prefix Glossary

Vaillant `0x07 0x04` identification scans commonly return short ASCII device
IDs or prefixes. The following expansions are useful when interpreting scan
results and mapping a physical target to its product family:

| Prefix | Meaning |
|--------|---------|
| `BAI` | Burner Adjustment Interface |
| `BMU` | Burner Management Unit |
| `HMU` | Heat Management Unit |
| `UI` | User Interface |
| `VMS` | Vaillant Multi-circuit Solarmodul |
| `VRC` | Vaillant Regulator Control |
| `VWL` | Vaillant Waermepumpe Luft |
| `VWS` | Vaillant Waermepumpe Sole |
| `VWZ` | Vaillant Waermepumpe Zusatz |

Notes:
- These are identity hints from scan payloads, not semantic proof by
  themselves. Device-specific register evidence remains necessary before
  assigning protocol semantics.
- `VWL`, `VWS`, and `VWZ` are German product-family abbreviations. The ASCII
  spellings above normalize `Waermepumpe` for repository-wide portability.

## Identifier Index

```text
0xB5 0x01  Symbolic access / service PC interface request (B501; candidate layout)
0xB5 0x02  Symbolic access reply / service PC interface data (B502; candidate layout)
0xB5 0x03  Error history (B503; error log retrieval)
0xB5 0x04  GetOperationalData (request parameter op; response is op-dependent)
0xB5 0x05  SetOperationalData (request parameter op + optional payload; response is op-dependent)
0xB5 0x06  I/O and test services (B506; remote-control outputs, input tests, check requests, end-of-line and radio tests; candidate layouts)
0xB5 0x07  Heat pump load/poll (B507; VRC720-family controller -> heat-pump unit at 0x08, heat-pump-only (candidate; see the B507 Open questions); not live-validated)
0xB5 0x08  NoiseReduction broadcast (B508; ZZ=FE broadcast; not live-validated) and candidate controller-to-heat-generator ops, of which `0A` and `0B` have a reply (candidate layouts)
0xB5 0x09  Register access / scan-id chunk discovery (selector-dependent payload forms)
0xB5 0x09 0x34 / 0x35  Absolute-address read / write (candidate memory access services; layouts not established; `B5 09 34` may be available only under PeBUS on some installations: candidate, unresolved)
0xB5 0x0A  Room temperature status of a remote control (B50A; candidate layout)
0xB5 0x0B  Remote-control room action, holiday period and setpoint, keycode and circuit-name writes (B50B; candidate layout)
0xB5 0x0C  Remote-control keycode-digits (OP00), signed-value (OP01; unit Unknown) and heating-circuit-name (OP02) reads (B50C; Hypothesis)
0xB5 0x0D  UI-direction room-action (OP00) and holiday-status (OP01) writes (B50D; Hypothesis)
0xB5 0x0F  Safety-relevant and non-safety temperature, status and demand exchange (B50F; candidate layout)
0xB5 0x10  SetMode (B510; regulator->boiler mode and setpoint commands)
0xB5 0x11  Remote Control (B511; triangular control loop between regulator, boiler, and NETX3)
0xB5 0x12  Circulation Pump / VR65-Style State (B512; pump state and VR65 control data)
0xB5 0x13  Value-range query
0xB5 0x14  Service test-menu values
0xB5 0x15  Legacy timer template
0xB5 0x16  Energy statistics (selector-encoded request; EXP Wh response)
0xB5 0x17  Sub-eBUS tunnel request (B517; candidate layout)
0xB5 0x18  Sub-eBUS tunnel positive prefix (candidate layout); B518 is also a header-only service identity (candidate); whether the two candidate readings describe the same service is unresolved
0xB5 0x19  Test and echo services (B519; candidate layout)
0xB5 0x1A  Heat-pump statistics and live-monitor values
0xB5 0x1B  Layout not established (candidate service identifier)
0xB5 0x1C  Header-only service identities (candidate; layout not established; meaning Unknown)
0xB5 0x1D  Header-only service identities (candidate; layout not established; meaning Unknown)
0xB5 0x20  Simulator and Simbox services (B520; candidate layout)
0xB5 0x21  OMU service register family
0xB5 0x22  recoVAIR ventilation commands
0xB5 0x23  Functional-module actor and sensor data for VR70/VR71-like targets
0xB5 0x24  GetExtendedRegisters (B524; selector-opcode multiplexed)
0xB5 0x25  Radio diagnosis (B525; candidate layout)
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

The candidate layouts of B504 give different lengths for `0x09` (11 data bytes)
and `0x0D` (5 data bytes) than the examples above; the relation is unresolved.
The candidate op catalogue is on the page
[`ebus-vaillant-B504.md`](ebus-vaillant-B504.md) (see also the open questions
below).

## SetOperationalData (0xB5 0x05)

`0xB5 0x05` uses op-coded writes.

```text
Request payload (1+ bytes):
  op      : byte
  payload : bytes (optional)
```

Response is device/op-specific and may be empty (ack-only).

## Register Access (0xB5 0x09)

`0xB5 0x09` multiplexes at least two payload forms; see also
[`ebus-vaillant-B509.md`](ebus-vaillant-B509.md). This section keeps both forms.

### Form A: register-like read/write

Subcommands `0D` (read) and `0E` (write) are operations, not registers; the
register is the address that follows.

```text
Read request payload (3 bytes):
  op      : 0x0D
  a1      : byte (first address byte on the wire)
  a2      : byte (second address byte on the wire)

Write request payload (3+ bytes):
  op      : 0x0E
  a1      : byte (first address byte on the wire)
  a2      : byte (second address byte on the wire)
  data    : bytes (0+)
```

A register id such as `0x1800` is written as the two address bytes in wire order, first byte first. Whether the first byte is the low or the high byte of a 16-bit address is unresolved; the little-endian reading is a **Hypothesis**, see [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md).

Response is device/register-specific. In some cases, only a single `0x00` status byte is observed.

<a id="vaillant-scanid-chunks-qq0x240x27"></a>
### Form B: scan.id chunk discovery (QQ=0x24..0x27)

This subsection is the Vaillant extended discovery function used by VRC720-family discovery (`0xB5 0x09` with well-known selector values).

Some Vaillant devices (manufacturer byte `0xB5`) use one-byte selectors to return fixed-size ASCII chunks.

```text
Request payload (1 byte):
  QQ : byte (typically one of 0x24, 0x25, 0x26, 0x27)

Response payload (9 bytes):
  0: status   byte (0x00 indicates success)
  1..8: ascii 8 bytes (NUL/space padded)
```

Candidate, unconfirmed on the wire: on some devices the four replies are
consecutive 9-byte slices of one 36-byte stream (`00`, then 28 serial bytes, then
7 bytes of `FF` fill), so only the `24` reply starts with `00` and the replies
`25`..`27` carry serial bytes in byte 0. Such replies read as one 36-byte stream:
byte 0 is `00`, bytes `1..28` are the serial bytes and bytes `29..35` are `FF`
fill, so the `27` reply carries two serial bytes followed by seven `FF` bytes.
This differs from the layout above (a status byte and eight ASCII bytes per
window), which is the layout known for controllers; whether controllers slice the
serial the same way is not established, and the discrepancy is unresolved; see
also [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md).

For deterministic target emulation:
- treat this format as valid only when payload is exactly one selector byte
- evaluate this strict `QQ=0x24..0x27` form before broader `0xB5 0x09` selector maps
- avoid shadowing scan-id chunk reads with generic register handlers

Assembly rule:
1. Query `QQ=0x24..0x27`.
2. Concatenate bytes `1..8` from each response. For the 36-byte stream form
   (candidate form, unconfirmed on the wire), concatenate whole replies, drop
   only byte 0 of the first one and take 28 characters (stop at 28 characters or
   trim the trailing `FF` fill).
3. Trim trailing NUL/whitespace.

The resulting string is often parsed into model/product and serial-like fields; exact formatting varies by Vaillant generation.


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

`0xB5 0x16` sub-command `0x10` is a selector-encoded energy statistics read
returning a float32 watt-hour value. Bytes 6-7 of the request and bytes 5-6
of the reply are a single little-endian packed date (day/month/year), not a
separate month/day nibble pair and a half-year year-selector byte.

- Dedicated reference:
  [`ebus-vaillant-B516-energy.md`](ebus-vaillant-B516-energy.md)
- This includes the packed-date formula and worked, read-only decode
  examples; the period/source/usage selector values; the `PERIOD_IDX` /
  `ENERGY_IDX` reply fields; and the VWZ/VWZIO alternative access path
  (sub-ID `0x18`) at address `0x76`.

---

## Device-Type Reference

> **Hypothesis:** Family/model associations below require model-qualified native observations. The [regulator crosswalk](ebus-vaillant-regulators.md) records exact observed identifier pairs separately.

### VRC720 Family (720-Series Controllers)

Candidate, subject to the qualification of each operation: the family uses eBUS
address `0x15`, B524 (OP=0x02/0x06), and B555 timer transport. The
[regulator crosswalk](ebus-vaillant-regulators.md) treats B524 and B555 as
candidate capabilities that a matching identity pair does not establish, and the
physical product behind one of its VRC720-family rows is **Unknown**.

The family has wireless base-station variants (an RF bridge near the
boiler or heat pump) and wired wall-mounted variants, each sold under the
Vaillant and the Saunier Duval brand. The identity strings a variant returns
and their decoded product numbers are in the
[regulator crosswalk](ebus-vaillant-regulators.md).

### VRC700 Family (700-Series Controllers)

Separate older family. eBUS address `0x15`. B524 (OP=0x02 shared, OP=0x03/0x04 VRC700-specific timer access). Does **NOT** support B555.

| Device ID | Notes |
|-----------|-------|
| 70000 | VRC700-family controller |
| B7S00 | Candidate VRC700-family identity, unconfirmed on the wire; not catalogued in the [regulator crosswalk](ebus-vaillant-regulators.md), which is the reference for VRC700-family identity rows |

The [Vaillant regulator identity crosswalk](ebus-vaillant-regulators.md)
provides bounded model-row context. It does not change this operation family's
existing identity guard.

### Device-Type Protocol Support Matrix

| Device Class | eBUS Addr | Key Protocols | Timer Transport |
|--------------|-----------|---------------|-----------------|
| Boiler (gas appliance) | 0x08 | B503, B504, B505, B509 (1533 rx), B510, B511, B512 | N/A |
| Heat pump | 0x08 | B504, B505, B507 (candidate), B509 (heat-pump registers), B511, B514, B51A | N/A |
| Heat-pump interface unit | 0x08 | B504, B505, B507 (candidate), B509 (`54 02 00` sub-addressing), B511, B512, B514, B51A | N/A |
| VRC720-family controller | 0x15 | B504, B505, B509, B524 (OP=0x02/0x06) | B555 |
| VRC700-family controller | 0x15 | B524 (OP=0x02/0x03/0x04) | B524 0x03/0x04 |
| Legacy room-controller family | 0x15 | B509 only (7 regs) | None |
| Functional module | 0x26 | B504, B505, B509, B523, B524 (stub) | N/A |
| NETX3 / VR921 | 0xF6 | B504, B505, B509, B511, B524 initiator, B555 initiator | N/A |
| Solar module (secondary target address of a VRC720-family controller) | 0xEC | Same MCU as the VRC720-family controller (secondary target). Protocol support on 0xEC is uncharacterized beyond memory server (0x0900/0x0902). | N/A |
| Heat-pump accessory (indoor hydraulic station) | 0x76 | B511, B512, B514 (T.1), B516, B51A | N/A |

### eBUS Address Collision Warning

Address `0x08` hosts completely different device types depending on installation:
- **Boiler** (gas appliance) — B509 register `0xBB00` = `gasValveActive` (UCH sentinel 0x0F/0xF0)
- **Heat pump** — same address `0xBB00` = `ActualEnvPowerPercentage` (percent, %; candidate, see the collision table of [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md)). On a heat-pump interface unit the meaning of these register ids is unresolved.

Device type MUST be established before decoding any B509 register at address `0x08`; the identification sources are listed in the device-type gate of [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md).

### f32 Byte Order Gate

B524 f32 registers have a profile-dependent byte order; the rows below state the
byte order per family or device class (observed for the VRC720 family, a
candidate for the heat-pump interface unit), and a destination address alone
does not select it (see [`ebus-vaillant-B524.md`](ebus-vaillant-B524.md)):

| Device Class | eBUS Address | f32 Byte Order |
|--------------|-------------|----------------|
| VRC720-family controller | 0x15 | Little-endian |
| Heat-pump interface unit | 0x08 | **Big-endian** (candidate) |

The byte order is given per family and device class; that it holds for every
controller of the VRC720 family and for every heat-pump interface unit is not
established (other installations not observed); qualify the codec independently
before reversing bytes.

---

## Protocol Support Matrix (Observed per Device)

> **Observation status:** address and role claims require a publishable capture.

### Devices Tested

| Device | Initiator Address | Target Address | Identity |
|--------|-------------------|----------------|----------|
| Boiler | 0x03 | 0x08 | Vaillant boiler (gas appliance) |
| VRC720-family controller | 0x10 | 0x15 | Vaillant VRC720-family controller |
| Functional module | 0x21 | 0x26 | Vaillant functional module |
| NETX3 | 0xF1 | 0xF6 | Vaillant sensoNET VR 921 (internet gateway) |

The rows above describe one installation; other installations of these device
classes and families were not observed, and the observations below do not
extend to them.

### Standard eBUS Protocols

| PBSB | Protocol | Boiler (0x03/0x08) | VRC720-family controller (0x10/0x15) | Functional module (0x21/0x26) | Internet gateway (0xF1/0xF6) |
|------|----------|--------------------|--------------------------------------|-------------------------------|---------------------|
| 0x0704 | Identification | target | target + initiator scan | target | target |
| 0x0700-0x07FF | All other 0x07xx | stub | stub | stub | stub |
| 0x0304-0x0310 | Service Data | stub | stub | stub | stub |
| 0x0500-0x050D | Burner Control | stub | stub | stub | stub |
| 0x0900 | RAM Read | stub | target | stub | stub |
| 0x0902 | EEPROM Read | stub | target | stub | stub |

**Notes:**

The following are **Proven** distinctions within the observations above, not
family-wide peer support. Each target-response qualification stands separately.

| Service | Qualified path | Grade | Boundary |
|---|---|---|---|
| 07/04 | working identification response, 10 bytes | Proven | observed targets only |
| 09/00 | RAM target response | Proven | observed controller only |
| 09/02 | EEPROM target response | Proven | observed controller only |

Other standard-service rows marked stub describe acknowledgements without data
in this observation scope. They do not establish support or absence of support
for every other standard service or every peer. The solar-module secondary
target belongs to the same controller MCU; this does not extend qualification
to a device family.

### Vaillant Proprietary Protocols (0xB5xx)

| PBSB | Protocol | Boiler (0x03/0x08) | VRC720-family controller (0x10/0x15) | Functional module (0x21/0x26) | Internet gateway (0xF1/0xF6) |
|------|----------|--------------------|--------------------------------------|-------------------------------|---------------------|
| 0xB504 | GetOperationalData | target | target | target | target |
| 0xB505 | SetOperationalData | target | target | target | target |
| 0xB509 | Register Access | target (1533 rx) | target (12 rx) | target (5 rx) | target (12 rx) |
| 0xB510 | SetMode | target (rx from the controller) | initiator (-> boiler) | — | — |
| 0xB511 | Remote Control | initiator (-> internet gateway) + target (rx from the controller) | initiator (-> boiler) | — | target (rx from the boiler) |
| 0xB512 | Circulation Pump / VR65 | initiator (-> 0x64) | — | — | — |
| 0xB516 | Energy Statistics | — | initiator (broadcast -> 0xFE, 146 tx) | — | — |
| 0xB524 | Extended Register | target (1 rx) | target (12124 rx) | target (1 rx) | initiator (-> controller, 2 tx) |
| 0xB555 | Timer/Schedule | — | target (465 rx) | — | initiator (-> controller) |

### Legend

- **target** — device responds to queries on its target address
- **initiator** — device initiates communication from its initiator address (observed passively on bus)
- **stub** — transport-level ACK, response `0x00`, no real data
- **—** — not observed on this device

---

## SetMode (0xB5 0x10, B510)

`0xB5 0x10` carries SetMode commands from the regulator to the boiler (VRC720-family controller initiator 0x10 -> boiler target 0x08).

- Dedicated reference: [`ebus-vaillant-B510.md`](ebus-vaillant-B510.md)
- Payload includes hcmode, flowtempdesired, hwctempdesired, hwcflowtempdesired, and disable/release bits.

## Remote Control (0xB5 0x11, B511)

B511 implements a triangular multi-role communication pattern:

1. **Boiler -> internet gateway**: The boiler initiator (0x03) sends remote control data to the internet gateway target (0xF6).
2. **VRC720-family controller -> boiler**: The regulator initiator (0x10) sends control commands to the boiler target (0x08). This is how heating demand and setpoints are communicated.
3. **Boiler receives from the controller**: The boiler also acts as target, receiving commands from the regulator.

Together with B510, these protocols form a control loop between regulator, boiler, and NETX3.

On heat pump systems with VWZIO (0x76), B511 traffic involving that device has also been observed.

- Dedicated reference: [`ebus-vaillant-B511.md`](ebus-vaillant-B511.md)

## Circulation Pump / VR65-Style State (0xB5 0x12, B512)

`0xB5 0x12` carries circulation pump state and VR65-style control data. Observed from the boiler initiator (0x03) targeting address 0x64.

- Dedicated reference: [`ebus-vaillant-B512.md`](ebus-vaillant-B512.md)
- Known selectors include StatusCirPump (off=0, on=100), VR65-style shape (0x02), and heat-pump-specific shapes.

## Other B5 services (candidate layouts)

The services below have no dedicated page except for
[B520](ebus-vaillant-B520.md). Every layout in this section is a candidate layout,
unconfirmed on the wire. No exchange of any of these services
on the wire is known (see [Open questions](#open-questions)). No service in this
section is documented as safe to send; the state-changing ones (including, but
not limited to, the B501 write, the `B5 09 35` write, the B50B writes, the B519
test and B520 simulator services and the `B5 09 51` binding) need a
separately established safety procedure and target qualification, and an ACK
does not show the resulting device state. The B51A reset and parameter write are
documented on [`ebus-vaillant-B51A.md`](ebus-vaillant-B51A.md), which states
the same rule for its ops.

Offset convention of the candidate layouts: offsets count from the first byte of
the service prefix (PB, SB and the op byte). Offset 0 is `B5` (PB), offset 1 is
the second identifier byte (SB) and offset 2 is the first byte after it. For a
request, the payload index (counted after SB) is the offset minus 2. A target
response on the bus carries no such prefix (eBUS framing: `NN`, data, CRC); how
the candidate response offsets map onto the bytes of a bus response is
unconfirmed on the wire. **Hypothesis**: response offset 3 is the first data byte
of a bus response, which agrees with the observed 10-byte B504 `00` date/time
layout, where the first response byte is the DCF state at offset 3. The B501
positive-status forms below place `Status` at offset 2, which this hypothesis does
not cover; whether a B501 positive-status form carries its own service prefix is
unresolved (see [Open questions](#open-questions)). A response
described as "no response data (candidate)" carries no data bytes. Field-level
detail for B504 to B508 is in the fixtures linked from those pages; "u8",
"i16 LE" and similar names state width, signedness and byte order.

### B501 and B502: symbolic access and service PC interface

**Hypothesis:** B502 is an independent return-data service, distinct
from a B501 positive-status form even when candidate prefixes look similar.
The synthetic examples keep these candidate identities separate; native service
identity remains **Unknown** without wire evidence.
The candidate `B5 02 Status` notation below does not identify a B502 service
exchange. B502 variable data remains opaque; the alternative candidate reading
of a leading zero as no error and a nonzero value as an error number remains
unresolved.

| Tagged case | Service identity | Interpretation | Grade |
|---|---|---|---|
| B501-status | B501 | positive-status form; candidate prefix B5 02 | Hypothesis |
| B502-data | B502 | independent return-data service; variable data opaque | Hypothesis |

- Candidate layout: request `B5 01 Flags 00 AddressLE16` (read), or the same
  followed by data (write). `Flags` is offset 2: bits 0..1 address mode (0
  symbolic, 1 absolute, 2 command), bits 2..3 device (0 BMU, 1 mixer, 2
  control), bits 4..5 reserved, bit 6 remote (1 = enable), bit 7
  read/write (1 = write). There is no constant op byte at offset 2.
- Candidate layout: the write service defaults `Flags` to read (`40`); a write
  needs bit 7 set explicitly, which gives `C0` with the other defaults. On the
  service PC interface, constants replace the bit layout: read `00`, write `80`,
  software-version read `4A` or `42`.
- Candidate layout: read positive `B5 02 Status Data...`, write positive
  `B5 02 Status`. `Status` is a scalar, not the request `Flags`: `00` no error,
  `01` CRC error, `02` invalid address mode, `03` invalid address, `29` amount of
  data too big, `56` no write access, `78` unknown command; other values have no
  known meaning.
- Candidate layout: write data starts at offset 6; its length and type depend on
  the target (address `FFFF` carries opaque bytes to the end of the telegram).
- Candidate layout: symbolic addresses are `u16` LE keys whose meaning depends on
  the target; the same key can mean different things on different targets (key
  `0001` is a domestic-hot-water bivalence point on a controller and an accessory
  relay on an appliance). `FFFF` is a candidate all-addresses value; wildcard behaviour is not
  established; no multi-response mechanism is known. **Hypothesis**, unconfirmed
  on the wire: the appliance symbolic addresses are the same key space as the
  B5 09 54 / B5 13 04 reads.
- Candidate layout: software-version read: request `Flags` at offset 2 and a
  big-endian 24-bit address at offsets 3..5 (fixed to 0 for the service PC
  interface); positive 8 bytes `B5 02 Status ProductNumber(BE16)@3..4 Version(u8)@5
  Revision(u8)@6 CRC(u8)@7`. Version and revision are raw `u8` (not BCD or
  ASCII). The CRC algorithm is unknown.
- Service PC interface data exchange (candidate, meaning Unknown): B501 is
  `Flags` `u8`@2, a little-endian 24-bit address @3..5, a length `u8`@6 and opaque
  data from offset 7, with no response data (candidate). B502 is `B5 02`
  followed by opaque data from offset 2 in both directions; a second candidate
  reading describes 0 as no error and greater than 0 as an error number.

### B50A to B50D: room and remote-control families

The declarations below are **Hypothesis**. Synthetic representation checks are
**Proven** software behavior only; physical qualification, native adaptation and
peer effects remain **Unknown**. Relative field order is not an absolute byte
offset. No absolute offset is assigned to the B50A, B50C or B50D fields here.
Unresolved response alternatives retain raw bytes; an Unknown extent is not zero.

| Family | Variant | Direction | Service | Operation | Request extent | Positive extent | Negative extent | Grade |
|---|---|---|---|---|---|---|---|---|
| B50A | room-action-temperature | read | B50A | OP00 | 0 | 3 | Unknown | Hypothesis |
| B50C | keycode-digits | read | B50C | OP00 | 0 | 4 | Unknown | Hypothesis |
| B50C | signed-value | read | B50C | OP01 | 0 | 2 | Unknown | Hypothesis |
| B50C | circuit-names | read | B50C | OP02 | Unknown | Unknown | Unknown | Hypothesis |
| B50D | ui-room-action | UI-write | B50D | OP00 | 1 | Unknown | Unknown | Hypothesis |
| B50D | ui-holiday-status | UI-write | B50D | OP01 | 1 | Unknown | Unknown | Hypothesis |

Extents are candidate argument/result byte counts, excluding any service prefix.
B50A OP00 and B50C OP00/OP01 have no arguments. Positive and negative alternatives
whose extents are Unknown remain unresolved, rather than empty results.

| Family / operation | Candidate fields in relative order | Carrier / conversion | Labels / defaults | Grade |
|---|---|---|---|---|
| B50A / OP00 positive | room-action byte, then temperature | unsigned 0..255; signed LE16 / 16 degrees C | 0 no-action, 1 switch-on, 2 thermostat; 3..255 unlabeled | Hypothesis |
| B50C / OP00 positive | four independent numeric digit bytes | each 0..9; not ASCII/BCD/u32 | each default zero | Hypothesis |
| B50C / OP01 positive | signed value | signed LE16; factor 1, offset 0 | unit and sentinel Unknown | Hypothesis |
| B50C / OP02 positive | circuit name | extent Unknown | independent per-circuit values/failures | Hypothesis |
| B50D / OP00 request | raw room-action byte | unsigned 0..255 | 0 no-action, 1 switch-on, 2 thermostat; default zero; 3..255 unlabeled | Hypothesis |
| B50D / OP01 request | raw holiday-status byte | unsigned 0..255 | labels 0/1; default zero; 2..255 unlabeled | Hypothesis |

B50A's signed carrier range is -32768..32767, giving -2048..2047.9375 degrees C.
Unavailable sentinel is **Unknown**: neither `8000` nor `FFFF` is a qualified
unavailable marker. Synthetic `02 80 FF` is candidate thermostat and -8 degrees C;
`03 00 00` retains unlabeled action 3. Temperature bytes `00 80` remain the signed
candidate -2048; `FF FF` remains -0.0625, with no unavailable promotion.

B50C digits `01 02 03 04` remain four values [1, 2, 3, 4]. OP01 `FE FF` is
candidate signed -2 with **Unknown** unit and sentinel; no temperature unit is
inferred. For OP02, echoed circuit, string trimming, B524 namespace equivalence
and wildcard semantics of zero are **Unknown**. Raw name bytes remain
uninterpreted; a failed read or unresolved response alternative supplies no
qualified name value.

B50D is the UI family: UI-direction writes are distinct from remote-control
writes and completed UI effects. Unknown raw 255 remains unlabeled for both
operations. These declarations grant no runtime capability or write admission.

The separate B50B remote-control variants below remain candidate layouts;
their located offsets use the PB-based convention above. They do not locate
B50D fields or establish physical behavior for another family.

| Service | Candidate layout |
|---|---|
| `B5 0B 00` request | room action `u8` @3: 0 no action, 1 switch on, 2 thermostat |
| `B5 0B 01` | holiday period: number `u8` @3, start day/month/year @4/5/6, end day/month/year @7/8/9; plain `u8` values (day 1..31, month 1..12, year 0..99), not BCD |
| `B5 0B 02` | holiday setpoint `u8` °C, 5..30 |
| `B5 0B 05` | holiday status `u8`: 0 stop, 1 start |
| `B5 0B 03` (write) | 4-digit keycode as four `u8` digits (0..9) @3..6 |
| `B5 0B 04` | circuit name written as 10 ASCII bytes @3..12 (default: the ten characters `0000000000`); no explicit circuit index |

### B50F: safety-relevant temperature, status and demand

Candidate layout: all four services put their values in the request and reply
with a `u8` feedback @3 (1 accepted; 0 and 2..255 not accepted).

- Candidate layout: `B5 0F 00` safety-relevant temperature: three `i16` LE ÷16
  °C values @3, @6 and @9, each followed by a channel-error `u8` (@5, @8, @11),
  then two CRC bytes @12 and @13.
- Candidate layout: `B5 0F 01` non-safety temperature: inlet @3, stack inlet @6
  and a field @9 that may be a voltage but is carried as a temperature value
  (unresolved; see Open questions).
- Candidate layout: `B5 0F 02` status: six structures @3..8, burner state @9, gas
  pump state @10, CRC @11 and @12.
- Candidate layout: `B5 0F 03` demand: one byte @3, CRC @4 and @5.

The CRC algorithm and its coverage are unknown.

### B517 and B518: sub-eBUS tunnel

Candidate layout: request `B5 17 <Dest u8, default 8> <data, opaque, 0..65535
bytes>` (there is no op byte; offset 2 is the destination). Positive
`B5 18 <data, opaque>`. A data length up to 65535 bytes cannot be carried in one
eBUS telegram, whose length field is one byte; how longer data is carried is
unresolved (candidate; see Open questions). B518 is also listed as a
header-only identity (see
[Header-only service identities](#header-only-service-identities)). Two
candidate readings are not reconciled: `B5 18` as the B517 positive above, and
B518 as a header-only service identity that may be a separate service; which
reading holds is unresolved.

### B519: test and echo services

Candidate layout, `B5 19 <selector>`:

| Selector | Candidate meaning |
|---|---|
| `00`, `01` | test command 1, test command 2 (reply: CRC `u8` @3) |
| `02` | read back the CRC store (reply: CRC `u8` @3) |
| `03` | send back the received data (data @3 in both directions) |
| `04` | send the received data as a broadcast in a BLK5 block (reply: CRC) |
| `05` | answer to a BLK4 block (no response data, candidate) |
| `06` | initiator-target telegram to the source |
| `07` | initiator-initiator telegram to the source (reply: CRC) |
| `08` | initiator-initiator telegram to the destination (target address `u8` @3, data @4; reply: CRC) |
| `AA` | return a telegram filled with `0xAA` |

The CRC is a raw `u8`; its algorithm is unknown.

### B520: simulator and Simbox services

- Candidate layout: `B5 20 00` request: relay `u8` @3, two PWM `u8` ÷2 % fields @4 and @5 (whether they are two channels is not established),
  stepper @6, LED @7, ED % @8, NTC table @9 (0 standard 3K3, 1 extended 1K, 2
  low-temperature 15K, 3 standard 1K). Positive: ADC `u16` LE @3..4, four NTC
  `i16` LE ÷16 °C @5, @7, @9, @11, the meaning of offset 13 not established, impeller Hz `u16` LE @14, vortex Hz `u16` LE
  @16.
- Candidate layout: `B5 20 01` clear configuration; `02` add variable (offset 3 not
  established; address `u32` LE @4); `03` and `04` read and write a data block; `05` system
  information; `06` write and read; `07` Simbox (InterID `u32` LE @3, address
  offset `u16` LE @7, data 0..23 bytes).

### B525: radio diagnosis

Candidate layout, `B5 25 <selector>`:

- `00` radio preamble: layer address `u8` @3, network identity `u16` LE @4,
  status character @6, source @7, destination @8, request id @9.
- `01` and `02` raw and decrypted payload; `03` RSSI `i8` @3 with link quality
  and a CRC-ok bit (bit 7) @4.
- `04` AES key write (candidate; layout not established).
- `10`..`17` eight clusters of 32 `i8` spectrum values; `18`..`1B` calibration
  (bit 0: 0 read, 1 write).
- Radio addresses use their own table (candidate; for example 15 base station, 10
  control unit, FD diagnosis tool, FE range extender); they are not eBUS
  addresses.

### B5 09 51: RF device binding (candidate)

Candidate layout (14 bytes with prefix): `B5 09 51`, component `u8` @3 (0..7), RF
initiator address `u8` @4 (a payload field, not the eBUS QQ/ZZ), 5-byte fixed
ASCII id @5..9, and four bytes @10..13 (software version, revision, product
number low byte, product number high byte; each decimal 0..99; candidate
interpretation: packed BCD, nibble order unresolved). The positive carries no
response data (candidate). A candidate envelope would be
`QQ ZZ B5 09 0C 51 ...` (NN = 12, 17 bytes before the CRC). Candidate
interpretation, unconfirmed on the wire: the service is mutative and intended to
bind an RF device; its effect on a target is unknown. `B5 09 51`, and `B5 09 34`
and `B5 09 35` in the [identifier index](#identifier-index), are documented on
this page; they are not in the subcommand table of
[`ebus-vaillant-B509.md`](ebus-vaillant-B509.md).

### Header-only service identities

The wire layout of the following service identities (subcommand byte, request
and reply data) is not established (candidate). An eBUS telegram
always carries PB and SB, so these identities are not one-byte requests. Their
Vaillant names are in
[`fixtures/b5-header-only-service-labels.csv`](fixtures/b5-header-only-service-labels.csv);
the meaning of each is Unknown.

Other pages give candidate statements, unconfirmed on the wire, for some of
these identities; they do not change the Unknown status above. The
[B509 page](ebus-vaillant-B509.md) gives a candidate request service byte `B5`
and a candidate positive reply byte `F5` for B509 `38`, `5A`, `5B` and `5C`, and
the [B555 page](ebus-vaillant-b555-timer-protocol.md) gives the same two
candidate bytes and a candidate meaning for B555 `04` and `06`. The
[B511](ebus-vaillant-B511.md), [B512](ebus-vaillant-B512.md) and
[B514](ebus-vaillant-B514.md) pages give candidate names for B511 `10` and `11`,
B512 `14` and B514 `09`.

## Open questions

- Whether the f32 byte order of the B524 registers holds for every controller of
  the VRC720 family and for every heat-pump interface unit is not established.
- Whether the first B509 address byte is the low or the high byte of a 16-bit
  address is unresolved, and the meaning of the B509 register ids on a heat-pump
  interface unit is unresolved; see
  [`ebus-vaillant-B509.md`](ebus-vaillant-B509.md).
- The services in "Other B5 services (candidate layouts)" and the candidate
  layouts on the B504 to B508, B51A and B521 to B523 pages are known only as
  candidate layouts; no exchange was observed beyond the observations on those
  pages. Whether any device implements the candidate ops of B501, B502, B50A to
  B50F, B504 to B508 and B517 to B525 that are not otherwise described on these
  pages is not established.
- The packed-BCD (candidate interpretation) details for the solar yield and the
  flow rate (nibble order, invalid nibbles, overflow) are unresolved, and so is
  the nibble order of the four version and product-number bytes of `B5 09 51`.
- The CRC or check-byte algorithms and their coverage are not established for
  B50F (FCS), B519, B51A (mirror CRC), the B501/B502 software-version read and
  the B506 check requests.
- Conflicting candidate values are unresolved: a default outside the candidate
  interval for B5 04 0B (default 0 against 3..9 minutes); the B5 23 mixer
  setpoint, a signed byte ×0.5 °C (range -64..63.5), against a second candidate
  range of 190 to 95; and the B5 0F 01 field at offset 9, whose quantity (voltage
  or temperature) is unresolved. Several candidate default values lie outside
  their candidate intervals (see the fixtures); the intended defaults are
  unresolved. The intended default `FFFF` of B5 07 0B, for which no interval
  other than the raw range is recorded, is unresolved (see the
  [B507 page](ebus-vaillant-B507.md)).
- How the candidate response offsets (counted from the first byte of the service
  prefix) map onto the data bytes of a bus response is unconfirmed on the wire.
  The B501 positive-status forms place `Status` at offset 2, which the offset-3
  **Hypothesis** does not cover; whether a B501 positive-status form carries its
  own service prefix is unresolved.
- Whether the B5 services without a profile statement on their own page (see
  [EBUS and PeBUS protocol profiles](#ebus-and-pebus-protocol-profiles)) are
  available under the PeBUS profile is not established.
- How the candidate B517 tunnel data, up to 65535 bytes, is carried, given that
  one eBUS telegram cannot hold that length, is unresolved. Whether `B5 18` is
  the B517 positive or the header-only identity B518 is a separate service is
  unresolved; the two candidate readings are not reconciled.
- The relation between the candidate B504 `09` (11 data bytes) and `0D` (5 data
  bytes) layouts and the 5-byte and 1-byte examples above is unresolved.
- The actual effect of B5 09 51 on a target (the binding of an RF device) is
  unknown.
- Whether `B5 09 34` is available only under PeBUS on some installations is a
  candidate, unresolved; whether its layout differs under PeBUS is not
  established. The [B509 page](ebus-vaillant-B509.md) states that no B509
  subcommand is known to be available only on PeBUS (candidate); this
  disagreement is unresolved.
- Whether controllers slice the serial windows of B5 09 24..27 as one 36-byte
  stream, as some devices do, is not established.
- The expansion of the name PeBUS is not known.
- Whether the appliance symbolic addresses of B501/B502 are the same key space as
  the B5 09 54 / B5 13 04 reads is not established.
- The layouts of B5 1B, of B5 09 34 and B5 09 35 and of B5 25 04 are not
  established.
- The wire layout (subcommand byte, request and reply data) of the header-only
  service identities is not established.
