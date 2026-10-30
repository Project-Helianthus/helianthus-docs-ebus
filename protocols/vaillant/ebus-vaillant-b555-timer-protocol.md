# B555 Timer/Schedule Protocol Specification

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

**Protocol:** eBUS B555 (PB=0xB5, SB=0x55)
**Status:** Reverse-engineered, validated on live hardware
**Date:** 2026-03-08
**Revision:** 2.16

## 1. Scope

This document specifies the eBUS B555 protocol used by **VRC720-family controllers only** for reading and writing weekly heating, DHW, and other timer/schedule programs.

See the [numeric range and contextual units supplement](ebus-b555-numeric-units.md)
for **Hypothesis** declarations and **Unknown** unit and sentinel contexts.

> **CORRECTION (2026-04-14):** B555 is NOT used by VRC700. The original scope statement "VRC700/VRC720 series" was incorrect. VRC700 (device ID `70000`, including Saunier Duval `B7S00`) uses [B524 opcodes 0x03/0x04](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules) for timer operations. The [VRC700 crosswalk](./ebus-vaillant-regulators.md#vrc700-operation-profile) adds model-row context without changing that command identity guard. Both device families share eBUS target address `0x15` but are different device classes with different timer transports.

### 1.0 Timer Transport Device Binding

| Device class | Device IDs | Timer transport | Reference |
|---|---|---|---|
| VRC720 family | BASV0, BASV2, BASV3, CTLV0, CTLV2, CTLV3, CTLS2 | **B555** (this document) | Validated on BASV2 |
| VRC700 | `70000` (including Saunier Duval `B7S00`) | **B524 opcodes 0x03/0x04** | [B524 section 4.4](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules) |

A scanner or schedule writer that does not check device identity before choosing transport will send B555 to a VRC700 (no response or error) or send B524 timer frames to a BASV2 (empty response). Device identity can be determined from the eBUS device ID returned during identification.

## 2. Frame Structure

B555 uses the standard eBUS Initiator-Target (MS) transaction format.

### 2.1 Initiator Frame

```
QQ ZZ B5 55 NN <data[0..NN-1]> CRC
```

| Field | Size | Description |
|-------|------|-------------|
| QQ | 1 | Source address |
| ZZ | 1 | Target address (controller) |
| PB | 1 | 0xB5 (primary command) |
| SB | 1 | 0x55 (secondary command) |
| NN | 1 | Data length (varies by opcode) |
| data | NN | Opcode + selector + payload |
| CRC | 1 | CRC-8 of QQ..data |

### 2.2 Target Response

```
ACK NN <response[0..NN-1]> CRC ACK
```

| Field | Size | Description |
|-------|------|-------------|
| ACK | 1 | 0x00 = accepted |
| NN | 1 | Response data length |
| response | NN | Response payload |
| CRC | 1 | CRC-8 of NN..response |
| ACK | 1 | Initiator ACK |

### 2.3 Notation Conventions

This document uses two distinct notations for bus data:

1. **Full wire captures** (Section 12.1): show QQ, ZZ, PB, SB, NN and payload
   as seen on the physical bus, using the format `Initiator: QQ ZZ ... / NN data`.
   Example: `F1 15 B5 55 0C A6 ... / 01 00`.

2. **ebusd `hex` command output**: the ebusd telnet interface strips ACK bytes
   and CRCs. It returns only `NN <response_payload>` for target responses.
   Example: `0100` = NN=0x01 followed by one payload byte 0x00.
   Similarly, `070006000c00e100` = NN=0x07 followed by 7 payload bytes.

All "Response:" lines in Sections 5 and 12 (except 12.1) use the ebusd
output format. An implementation decoding raw eBUS frames must parse the
full wire format from Section 2.1/2.2 instead.

### 2.4 Reply framing and outcomes (candidate)

In the candidate subsections and paragraphs of this document (Sections 2.4,
3.1, the candidate paragraphs of 4.1 and 4.2, 4.3.1, 5.2.1, 5.3.1, 5.4.1 to
5.4.4, 5.5, 5.6, 10 and 11) a *requester* is an
initiator that sends the B555 requests described there (source address `F1` in
the examples). Statements about a requester are candidate interpretation,
unconfirmed on the wire, and are not promoted to **Proven** by being listed
here. The Open questions section at the end of this document collects the
unresolved points.

- The validated exchanges of Section 5 carry no echoed `B5 55 <command>`
  prefix in the reply: a reply is `NN` followed by the status and data bytes
  (A3 `NN=0x09`, A4 `NN=0x09`, A5 `NN=0x07`, A6 `NN=0x01`). The command byte
  is not part of the reply data in those exchanges.
- For the status-bearing replies of A3 to A6, a bridge keeps three outcomes of
  a B555 exchange apart: the transport result, the service status (the first
  payload byte of the reply) and the physical ACK/CRC. A transport success is
  not a service status of 0, and neither establishes that a written program
  persisted (Section 6). A Vaillant requester evaluates the status byte of the
  A4 and A6 replies (not that of A5) and does not check a command, day or slot
  echo (candidate). The replies of 0x00 (EM flags), A0 and A7 (bit fields), A1,
  A2, A8 and A9 (reserved bits) and 0x04 and 0x06 (the service-identifier byte
  `F5`, reply layout otherwise unknown) carry no service status byte (candidate).

## 3. Opcodes

The first byte of the data field is the opcode.

| Opcode | Name | Direction | NN | Description |
|--------|------|-----------|-------|-------------|
| 0xA3 | CONFIG_READ | Read | 3 | Read timer configuration |
| 0xA4 | SLOTS_READ | Read | 3 | Read slots-per-weekday counts |
| 0xA5 | TIMER_READ | Read | 5 | Read one day/slot timer entry |
| 0xA6 | TIMER_WRITE | Write | 12 (0x0C) | Write one day/slot timer entry |

### 3.1 Sub-command inventory (candidate)

Candidate interpretation, unconfirmed on the wire: the B555 sub-commands
below form one time-window family. Only A3 to A6 are documented as validated
exchanges (Section 5). `NN` of a request counts the command byte; the reply
data length excludes `NN`. For A3 to A6 the lengths equal the validated
lengths of Section 5. The reply lengths in the table are eBUS lengths; on
PeBUS, the A3 to A6 and 0x00 replies would be three bytes longer if they
carry the candidate prefix fields described below, and the PeBUS reply
lengths are unresolved.

| Sub-command | Candidate name | Request `NN` | Reply data bytes (eBUS) | Profiles | Sent by a Vaillant requester (candidate) |
|---|---|---|---|---|---|
| 0x00 | EM status request (Section 5.6) | 1 | 1 | eBUS and PeBUS | yes, to destination `08` |
| 0x04 | Simple heating control entry (Section 5.6) | unresolved | unresolved | eBUS and PeBUS | not known |
| 0x06 | EMM activation broadcast entry (Section 5.6) | unresolved | unresolved | eBUS and PeBUS | not known |
| 0xA0 | Available functions and channels (Section 5.5) | 1 | 8 | eBUS and PeBUS | not known |
| 0xA1, 0xA2 | Reserved (48 bits) | 1 | 6 | eBUS and PeBUS | not known |
| 0xA3 | CONFIG_READ (Section 5.1) | 3 | 9 | eBUS and PeBUS | not known |
| 0xA4 | SLOTS_READ (Sections 5.2, 5.2.1) | 3 | 9 | eBUS and PeBUS | yes, ventilation program only |
| 0xA5 | TIMER_READ (Sections 5.3, 5.3.1) | 5 | 7 | eBUS and PeBUS | yes, ventilation program only |
| 0xA6 | TIMER_WRITE (Sections 5.4, 5.4.1 to 5.4.4) | 12 | 1 | eBUS and PeBUS | yes, types 0, 1, 2, 3 and 5 |
| 0xA7 | Visible functions and channels (Section 5.5) | 1 | 8 | eBUS and PeBUS | not known |
| 0xA8, 0xA9 | Reserved (48 bits) | 1 | 6 | eBUS and PeBUS | not known |

- A Vaillant requester issues A4, A5 and A6 to the controller and the EM
  status request 0x00 to destination `08` (candidate, unconfirmed on the
  wire); whether another initiator sends A0, A3 or A7 is not established.
- Candidate: B555 time-program requests are sent to VRC720-family
  controllers; VRC700-family controllers carry their time programs over B524
  `0x03`/`0x04` instead (Section 9).
- **PeBUS:** no B555 sub-command is available only on PeBUS (candidate,
  unconfirmed on the wire); every sub-command above is available under both
  profiles with the same field layouts. Candidate interpretation, unconfirmed
  on the wire: the three leading prefix fields of an A3, A4, A5, A6 or 0x00
  reply (`B5`, `55` and the command byte) are present only on PeBUS, which is
  consistent with the prefix-free replies of Section 5 on eBUS; for the other
  sub-commands the profile of these fields is not established. The reply
  offsets of the fixtures of Section 11 are eBUS offsets (status or flags at
  offset 0); on PeBUS, if the prefix fields are present, every reply offset
  would shift by three, which is unresolved.

## 4. Selector Bytes

All opcodes share a common selector namespace following the opcode byte.

### 4.1 ZONE (Zone Index)

| Value | Zone |
|-------|------|
| 0x00 | Zone 1 |
| 0x01 | Zone 2 |
| 0x02 | Zone 3 |
| 0xFF | Zone-agnostic (used by CC and DHW) |

VR940 uses ZONE=0xFF when writing CC and DHW schedules. Both are system-wide
services not bound to a specific heating zone. Heating timers use the actual
zone index (0x00-0x02). Validated by VR940 capture: CC writes carry ZONE=0xFF,
DHW writes carry ZONE=0xFF, Z1 Heating writes carry ZONE=0x00.

Candidate correspondence, unconfirmed on the wire: the ZONE byte is the
Vaillant *module index* (u8, default 0) and the HC byte of Section 4.2 is the
Vaillant *time-window type*. The range of module indices a controller accepts
is not established. The validated ZONE values (`0xFF` for the DHW and CC writes,
`0x00` to `0x02` for the zone heating writes; Sections 4.1 and 7) are not
reconciled with this correspondence (Open questions).

### 4.2 HC (Schedule Type / Heating Circuit Type)

| Value | Type | Temperature Field |
|-------|------|-------------------|
| 0x00 | Heating | Yes (target setpoint) |
| 0x01 | Cooling | Not observed (unavailable on test system) |
| 0x02 | HWC (Domestic Hot Water) | Yes (DHW target temp) |
| 0x03 | CC (DHW recirculation pump schedule) | No — time-only schedule, temp field carries 0xFFFF |
| 0x04 | NoiseReduction (Silent) | Not observed (answered as not available). One VRC720-family CSV uses `Silent`; another uses `NoiseReduction`. Both describe the same function: a quiet-hours schedule. Name aligns with B508 broadcast field `NoiseReduction`. See also [B524 section 4.4](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules), where ADDRESS `02` under GG `0x00` is Ventilation, with a conflict noted against the VRC700 community configuration; the VRC700 equivalent of this channel is unresolved. |
| 0x05 | Ventilation (candidate) | Unknown. The setpoint unit and scale of this type are unresolved (Sections 5.3.1 and 10). |
| 0x06 | High tariff (candidate) | Not observed |
| 0x07 | External DHW circuit (candidate) | Not observed |
| 0x08 | External fixed-flow circuit (candidate) | Not observed |

Candidate interpretation, unconfirmed on the wire: the HC byte values 0x00 to
0x08 above are the Vaillant time-window types; rows 0x05 to 0x08 are not
validated exchanges. A Vaillant requester sends the type values 0,
1, 2, 3 and 5 (candidate). The full enumeration is in
[b555-candidate-enumerations.csv](./fixtures/b555-candidate-enumerations.csv).

### 4.3 DD (Day of Week)

| Value | Day |
|-------|-----|
| 0x00 | Monday |
| 0x01 | Tuesday |
| 0x02 | Wednesday |
| 0x03 | Thursday |
| 0x04 | Friday |
| 0x05 | Saturday |
| 0x06 | Sunday |

#### 4.3.1 Group-day values in A6 (candidate)

**Hypothesis — aggregate-day mappings, unconfirmed on the wire:** the
[B524 timer section](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules)
already documents its candidate weekday table. The two transports differ:

| Family / transport | Operation | 0..6 | 7 (`0x07`) | 8 (`0x08`) | 9 (`0x09`) | Evidence status |
| --- | --- | --- | --- | --- | --- | --- |
| VRC720 family / B555 | A6 write | Monday..Sunday | Monday-Sunday | Monday-Friday | Saturday-Sunday | Hypothesis |
| VRC700 family / B524 | OP04 write | Monday..Sunday | Monday-Sunday | Saturday-Sunday | Monday-Friday | Hypothesis |
| VRC720 family / B555 | A5 read | Monday..Sunday | not used | not used | not used | Hypothesis |
| VRC700 family / B524 | OP03 read | Monday..Sunday | not used | not used | not used | Hypothesis |

Ordinary codes `0x00` through `0x06` mean Monday through Sunday in order.
A5 and OP03 do not inherit aggregate-day support from the write variants.
Retain the raw day code and operation with the family and selector context:
B555 `ZONE` and `HC`, or B524 group `GG`, instance `II` and `ADDRESS` as
documented in the linked timer section. Do not translate a raw aggregate-day
code between transports; codes 8 and 9 have opposite candidate meanings.

A requester issues the weekday values 0 to 6 only (candidate); no B555 request
carrying a group value is known. Physical acceptance of either aggregate-day
mapping, physical support and persistence remain **Unknown**. Neither table
qualifies those properties or grants permission to emit a schedule write.
A passing table check establishes documentation consistency only.

## 5. Opcode Details

### 5.1 CONFIG_READ (0xA3)

Reads timer configuration for a zone/HC combination. Returns capabilities
and constraints for the specified schedule type.

**Request data (3 bytes):**

```
A3 [ZONE] [HC]
```

**Response (9 bytes):**

```
[status] [max_slots] [time_res] [setpoint_step] [setpoint_unit] [num_setpoints] [min_temp] [max_temp] [time_program_mode]
```

| Byte | Name | Type | Description |
|------|------|------|-------------|
| [0] | status | UCH | 0x00 = available, 0x03 = unavailable |
| [1] | max_slots | UCH | Maximum time slots per day |
| [2] | time_resolution | UCH | Suggested time resolution in minutes (advisory) |
| [3] | setpoint_step | UCH | Setpoint step, raw value. Not a minimum duration; its enforcement has not been separately established in this capture. |
| [4] | setpoint_unit | UCH | Setpoint unit code: 0x00 = none, 0x01 = °C, 0x02 = fan stage |
| [5] | num_setpoints | UCH | Number of independent setpoint values. See Section 5.1.1. |
| [6] | min_temp_c | UCH | Minimum temperature in whole °C (0xFF = N/A). **Enforced.** |
| [7] | max_temp_c | UCH | Maximum temperature in whole °C (0xFF = N/A). **Enforced.** |
| [8] | time_program_mode | UCH | Time-program mode: 0x00 = weekly, 0x01 = 24-hour |

**Enforcement rules (validated by boundary testing):**

- `max_slots` is **enforced by the controller**. Writing SC > max_slots
  returns error code 0x01. Validated: SC=4 on CC (max_slots=3) → 0x01;
  SC=12 on DHW (max_slots=3) → 0x01; SC=12 on Heating (max_slots=12) → ACK.
  Observed max_slots values: 3 for DHW, CC, and Silent timers; 12 for Heating and Cooling timers. Excess slots beyond max_slots are rejected by the controller (error 0x01), not silently ignored.
- `min_temp_c` and `max_temp_c` are **enforced by the controller**. Writing a
  numeric temperature outside this range returns error code 0x06. Validated:
  34°C on DHW (min=35) → 0x06; 66°C on DHW (max=65) → 0x06; exact boundary
  values (35°C, 65°C) → ACK. Note: not all temp-field rejections use 0x06 —
  Heating rejects 0xFFFF with 0x01 (parameter out of range; Section 12.14).
- `time_resolution` is **advisory only**. The controller accepts any minute
  value (0-59) regardless of this field. This advisory timing metadata
  applies for all 4 visible schedule types (Heating Z1, Heating Z2, DHW,
  CC/circulation pump), matching the config `time_resolution=10` value.
  `setpoint_step` is a separate raw field (see above) and is not covered by
  this advisory-only observation; all observed configs carry `setpoint_step`
  values of `0`, `5`, or `10`.
  `time_program_mode` is `0x00` (weekly) in every configuration observed so
  far; `0x01` (24-hour) has not been observed on this hardware.

**Observed configs across all timer types:**

| Timer Type | [0] | [1] | [2] | [3] | [4] | [5] | [6] | [7] | [8] |
|------------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| Z1 Heating | 0x00 | 12 | 10 | 5 | 1 | 12 | 5 | 30 | 0 |
| Z2 Heating | 0x00 | 12 | 10 | 5 | 1 | 12 | 5 | 30 | 0 |
| HWC (DHW) | 0x00 | 3 | 10 | 10 | 1 | 1 | 35 | 65 | 0 |
| CC | 0x00 | 3 | 10 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |
| Z1 Cooling | 0x03 | 1 | 1 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |
| Z2 Cooling | 0x03 | 1 | 1 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |
| Z3 Heating | 0x03 | 1 | 1 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |
| Z3 Cooling | 0x03 | 1 | 1 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |
| Silent | 0x03 | 1 | 1 | 0 | 0 | 0 | 0xFF | 0xFF | 0 |

#### 5.1.1 Byte [5] (num_setpoints, formerly `temp_slots`) — temperature cardinality

This field (the number of setpoints) indicates how many independent
temperature setpoints can exist across the timer's slots. Three distinct
values are observed. The remainder of this section retains the `temp_slots`
and `has_temp` shorthand used in the original capture notes below to refer
to this byte and to byte [4] (`setpoint_unit`); the concrete observed values
(0, 1, 12) are unchanged by the renaming:

| Value | Meaning | Observed for | Validated |
|-------|---------|--------------|-----------|
| 0 | No temperature (has_temp=0). Timer controls time windows only. | CC | By config read (CC is active, status=0x00). Silent shows temp_slots=0 but config is unavailable (status=0x03) — same caveat as Cooling. |
| 1 | Shared temperature: one temperature value shared across all slots and all 7 days. Writing a temperature to any slot updates the B524 setpoint and propagates everywhere. | HWC | **Yes** — wrote 55.0°C to Monday, all 7 days updated (Section 12.8); wrote 52.0°C, B524 changed from 61→52°C (Section 12.13). VR940 writes 0xFFFF (temperature no-op — leaves B524 unchanged); myVaillant manages DHW temp via B524 only. |
| 12 | Independent temperatures: each slot carries its own setpoint, up to 12 per day. | Heating | **Yes** — VR940 wrote 12 distinct temps per day across 7 days (84 frames, Section 12.10); also validated 7 distinct per-day temps via ebusd (Section 12.9) |

**Cooling timers** are unavailable (status=0x03) on the test system. Their
config row shows `temp_slots=0`, but this may reflect the unavailable state
rather than the enabled protocol semantics. Do not infer that enabled
cooling timers lack temperature support based on this data alone.

**Heating temp_slots=12 interpretation:** The value 12 matches `max_slots`
(also 12) for heating timers and represents 12 independently-settable slot
temperatures per day. **Exhaustively validated:** VR940 wrote 84 frames
(12 slots × 7 days) with 12 distinct temperatures per day (22.5, 20.0,
18.0, 30.0, 5.0, 20.0, 14.0, 26.5, 16.0, 24.5, 11.5, 27.5°C), all
persisted and verified by read-back (Section 12.10).

When `temp_slots=1` (DHW), writing an explicit temperature to any slot
updates the B524 DHW setpoint and broadcasts to all 7 days. Writing 0xFFFF
leaves the B524 setpoint unchanged (temperature no-op); the controller fills
the read-back temp field with the current B524 value.

**B524↔B555 DHW temperature is tightly coupled.** The B555 temp field and
the B524 DHW setpoint (GG=0x01 RR=0x0006) behave as shared state — writes
to either side are immediately visible from the other:

- **B555→B524:** Writing 52.0°C to DHW Monday via B555 changed B524
  `target_temp_c` from 61→52°C. Writing 61.0°C back restored it (Section 12.13).
- **B524→B555:** Changing B524 DHW temp from 61→50°C via myVaillant caused all
  B555 timer slots to immediately reflect 50.0°C (Section 12.11).
- **0xFFFF = no-op:** VR940 writes 0xFFFF to schedule DHW time windows without
  side-effecting the B524 setpoint. The protocol behavior establishes only the resulting B524 setpoint update.

**Read-back is lossy:** reading a B555 DHW slot always returns the current
B524 setpoint. There is no way to distinguish between a slot that was written
with an explicit temperature and one that was written with 0xFFFF — both
read back as the B524 value.

**Wire-validated example:**

```
Initiator: 31 15 B5 55 03 A3 00 00
Target:  09 00 0C 0A 05 01 0C 05 1E 00
```

### 5.2 SLOTS_READ (0xA4)

Reads the number of configured time slots per weekday.

**Request data (3 bytes):**

```
A4 [ZONE] [HC]
```

**Response (9 bytes):**

```
[status] [Mon] [Tue] [Wed] [Thu] [Fri] [Sat] [Sun] [slot_count_24h]
```

| Field | Size | Description |
|-------|------|-------------|
| status | 1 | Timer status: 0x00 = active, 0x03 = unavailable (matches A3 byte[0]). See A5 status for comparison. |
| Mon..Sun | 7 | Slot count per day (UCH, 0x00-0x0C) |
| slot_count_24h | 1 | 24-hour slot count, not padding. `0x00` in every weekly-mode configuration observed so far (see A3 byte [8], `time_program_mode`); not yet observed non-zero. |

> **Cross-reference:** The first byte of A4 (status/slot-count context) and A5 (status/timer-entry context) responses share the same byte position but have different semantics. A4 byte[0] gates the validity of the per-weekday slot counts; A5 byte[0] gates the validity of a single timer slot entry. See the respective section for details.

**Wire-validated example (Z1 Heating, all single-slot):**

```
Initiator: 31 15 B5 55 03 A4 00 00
Target:  09 00 01 01 01 01 01 01 01 00
```

#### 5.2.1 A4 reply: acceptance by a requester (candidate)

The nine-byte layout above (status, seven daily counts, 24-hour count) is the
validated wire layout. The following gives the request and the acceptance
rules of a Vaillant requester; it is unconfirmed on the wire. The
field table is [b555-a4a5-fields.csv](./fixtures/b555-a4a5-fields.csv).

- Request for the ventilation program: `F1 ZZ B5 55 03 A4 00 05` (`NN=03`,
  module index 0, time-window type 5); `ZZ` is the controller address.
- Minimum accepted reply length: 8 bytes (status and seven counts); a ninth
  byte (the 24-hour count) is not interpreted.
- The requester accepts the reply only with status 0 and only if every daily
  count is at most 12; 12 is also the `max_slots` value observed for heating
  timers in Section 5.1. The ceiling is the requester's, not announced by the
  controller. Any other status, or a count above 12, ends the read and no A5
  request follows.

### 5.3 TIMER_READ (0xA5)

Reads a single timer slot for a specific day.

**Request data (5 bytes):**

```
A5 [ZONE] [HC] [DD] [SS]
```

| Field | Size | Description |
|-------|------|-------------|
| ZONE | 1 | Zone index (0x00-0x02, or 0xFF for system-wide schedules — see Section 7) |
| HC | 1 | Schedule type (0x00-0x04; candidate rows 0x05 to 0x08 in Section 4.2) |
| DD | 1 | Day of week (0x00-0x06; A5 carries no group-day value, Section 4.3.1) |
| SS | 1 | Slot index (0-based) |

**Response (7 bytes):**

```
[status] [Sh] [Sm] [Eh] [Em] [Tlo] [Thi]
```

| Field | Size | Encoding | Description |
|-------|------|----------|-------------|
| status | 1 | UCH | Timer status: 0x00 = active, 0x03 = unavailable (matches A3 byte[0]) |
| Sh | 1 | UCH | Start hour (0x00-0x18, where 0x18=24) |
| Sm | 1 | UCH | Start minute (0x00-0x3B) |
| Eh | 1 | UCH | End hour (0x00-0x18, where 0x18=24) |
| Em | 1 | UCH | End minute (0x00-0x3B) |
| Tlo | 1 | UIN LE low | Temperature low byte |
| Thi | 1 | UIN LE high | Temperature high byte |

**Temperature encoding:**

- Little-endian unsigned 16-bit integer
- Value = raw / 10.0 (unit: degrees Celsius) for the validated heating and DHW programs; for the other types, including the candidate types 0x05 to 0x08, unit and scale are **Unknown** (Section 5.3.1)
- `0xFFFF` semantics depend on `has_temp`:
  - **has_temp=0** (CC, Silent): literal "no temperature" — time-only schedule,
    no temp field validation (min/max = 0xFF)
  - **has_temp=1, DHW** (temp_slots=1): "don't change setpoint" — a temperature
    no-op. The controller leaves the B524 DHW setpoint unchanged and fills the
    temp field on read-back with the current B524 value. Writing an explicit
    temperature (not 0xFFFF) **updates the B524 DHW setpoint** and broadcasts
    to all 7 days. VR940 writes 0xFFFF to avoid side-effecting B524.
    Validated: wrote 52.0°C to DHW Monday via ebusd → B524 target_temp changed
    from 61→52°C; wrote 61.0°C back → B524 restored to 61°C. The B555 DHW temp
    field and B524 setpoint are **tightly coupled** (Section 12.13).
  - **has_temp=1, Heating** (temp_slots=12): **0xFFFF is rejected** with error
    0x01 (parameter out of range). Heating has no sentinel exemption — every
    slot must carry an explicit temperature within the [min, max] range
    (Section 12.14).

**Examples:**

| Temp (C) | Raw (dec) | Tlo | Thi |
|----------|-----------|-----|-----|
| 7.5 | 75 | 0x4B | 0x00 |
| 19.0 | 190 | 0xBE | 0x00 |
| 20.0 | 200 | 0xC8 | 0x00 |
| 22.5 | 225 | 0xE1 | 0x00 |
| 28.0 | 280 | 0x18 | 0x01 |
| 61.0 | 610 | 0x62 | 0x02 |
| None | 65535 | 0xFF | 0xFF |

**Wire-validated examples:**

```
# Z1 Heating Monday: 00:00-24:00 @ 22.5°C
Initiator: 31 15 B5 55 05 A5 00 00 00 00
Target:  07 00 00 00 18 00 E1 00

# Z1 Heating Sunday: 00:00-18:00 @ 22.5°C
Initiator: 31 15 B5 55 05 A5 00 00 06 00
Target:  07 00 00 00 12 00 E1 00

# Z2 Heating Monday: 00:00-24:00 @ 20.0°C
Initiator: 31 15 B5 55 05 A5 01 00 00 00
Target:  07 00 00 00 18 00 C8 00

# HWC Monday: 00:00-24:00 @ 61.0°C (DHW target)
Initiator: 31 15 B5 55 05 A5 00 02 00 00
Target:  07 00 00 00 18 00 62 02

# HWC Saturday: 06:00-24:00 @ 61.0°C
Initiator: 31 15 B5 55 05 A5 00 02 05 00
Target:  07 00 06 00 18 00 62 02

# CC Monday: 00:00-24:00 @ NONE
Initiator: 31 15 B5 55 05 A5 00 03 00 00
Target:  07 00 00 00 18 00 FF FF
```

#### 5.3.1 A5 reply: acceptance by a requester (candidate)

The seven-byte layout above (status, start hour and minute, end hour and
minute, little-endian setpoint; HTM and UIN in Section 8) is the validated
wire layout. The following gives the request and the acceptance rules of
a Vaillant requester; it is unconfirmed on the wire. The field table is
[b555-a4a5-fields.csv](./fixtures/b555-a4a5-fields.csv).

- Request for the ventilation program: `F1 ZZ B5 55 05 A5 00 05 dd ss`
  (`NN=05`, module index 0, time-window type 5), with `dd` the day 0 to 6 in
  query order Monday to Sunday and `ss` the slot 0 to count-1 of that day.
- Minimum accepted reply length: 7 bytes. The status byte is not evaluated by
  the requester (candidate).
- Start and end are read as hour and minute (hour 0..24, minute 0..59 as
  separate bytes, so 24:00 is representable, Section 8.1); the
  requester applies no range check.
- The setpoint is read as the u16 value divided by 10 (observed for heating
  and DHW, Section 5.3); for the ventilation program its unit is not
  established (candidate unit for the A3 setpoint-unit code 2: fan stage,
  unconfirmed on the wire) and `0xFFFF` has no established invalid meaning.
- A failed or undecodable A5 exchange (a reply shorter than 7 bytes) ends
  the read.

### 5.4 TIMER_WRITE (0xA6)

Writes a single timer slot for a specific day.

**Request data (12 bytes, NN=0x0C):**

```
A6 [ZONE] [HC] [DD] [SI] [SC] [Sh] [Sm] [Eh] [Em] [Tlo] [Thi]
```

| Field | Size | Encoding | Description |
|-------|------|----------|-------------|
| ZONE | 1 | UCH | Zone index (0x00-0x02, or 0xFF for system-wide schedules — see Section 7) |
| HC | 1 | UCH | Schedule type (0x00-0x04; candidate rows 0x05 to 0x08 in Section 4.2) |
| DD | 1 | UCH | Day of week (0x00-0x06; candidate group-day values 7 to 9, unconfirmed on the wire, Section 4.3.1) |
| SI | 1 | UCH | Slot index (0-based) |
| SC | 1 | UCH | Total slot count for this day (**enforced** ≤ max_slots; exceeding → error 0x01) |
| Sh | 1 | UCH | Start hour (0x00-0x18, **enforced**; 0x19+ → error 0x01) |
| Sm | 1 | UCH | Start minute (0x00-0x3B) |
| Eh | 1 | UCH | End hour (0x00-0x18, **enforced**; 0x19+ → error 0x01) |
| Em | 1 | UCH | End minute (0x00-0x3B) |
| Tlo | 1 | UIN LE low | Temperature low byte |
| Thi | 1 | UIN LE high | Temperature high byte |

**Response (1 byte after NN):**

| Value | Meaning | Validated |
|-------|---------|-----------|
| 0x00 | ACK — frame accepted by controller | Yes |
| 0x01 | Parameter out of range | Yes — hour ≥ 0x19 rejected; SC > max_slots rejected (e.g., SC=4 on CC with max_slots=3; SC=12 on DHW with max_slots=3); Heating 0xFFFF rejected (Section 12.14) |
| 0x03 | Timer type unavailable (status=0x03 in A3 config) | Yes — writes to Cooling/Z3/Silent rejected |
| 0x04 | Device-specific rejection; exact semantics unknown. |
| 0x05 | Device-specific rejection variant; exact semantics unknown. |
| 0x06 | Validation failure (temperature or parameter) | Yes — triggered by: (1) temperature below min or above max (e.g., 34°C on DHW min=35; 66°C on DHW max=65; boundary values accepted); (2) ZONE=0xFF + full-day (00:00-24:00) + explicit temperature on DHW writes, even when temp is in range (Section 12.13). Semantics broader than "temp out of range". |

**Important:** A response of 0x00 means the controller accepted the frame,
not that the data was persisted. For single-slot writes (SC=1), 0x00
reliably indicates persistence (confirmed by read-back from both ebusd and
VR940 sources). For multi-slot writes (SC > 1, SI > 0), the controller may
return 0x00 while silently discarding the slot data — see Section 6.2.2.
Always verify writes with a read-back (A5) when persistence must be confirmed.

**Wire-validated examples (VR940 cloud gateway writes):**

```
# Monday slot 0/2: 00:00-06:00 @ 28.0°C
Initiator: F1 15 B5 55 0C A6 00 00 00 00 02 00 00 06 00 18 01
Target:  01 00

# Monday slot 1/2: 06:00-23:50 @ 7.5°C
Initiator: F1 15 B5 55 0C A6 00 00 00 01 02 06 00 17 32 4B 00
Target:  01 00

# Tuesday slot 0/1: 00:00-24:00 @ 22.5°C (single slot)
Initiator: F1 15 B5 55 0C A6 00 00 01 00 01 00 00 18 00 E1 00
Target:  01 00

# Sunday slot 0/1: 00:00-18:00 @ 22.5°C (single slot)
Initiator: F1 15 B5 55 0C A6 00 00 06 00 01 00 00 12 00 E1 00
Target:  01 00
```

**Write verified by read-back (ebusd `hex -n` command):**

```
# Write Monday to 00:00-24:00 @ 22.5°C (SC=1)
hex -n 15b555a6000000000100001800e100
Response: 0100 (ACK)

# Read-back confirms:
read Z1HeatingTimer_Monday -> 00:00;24:00;22.5
```

#### 5.4.1 A6 request as built by a requester (candidate)

The twelve-byte request above is the validated wire layout. The following
describes the requests a Vaillant requester sends and is unconfirmed on the
wire. The field table (with the Vaillant field names as a correspondence
column) is
[b555-a6-request-fields.csv](./fixtures/b555-a6-request-fields.csv).

- Frame: `F1 ZZ B5 55 0C A6 module type day currentSlot totalSlots startHour
  startMinute endHour endMinute setpointLo setpointHi`; `ZZ` is the controller
  address.
- Time: start hour, start minute, end hour and end minute as four separate
  bytes (hour 0..24, minute 0..59); the requester applies no ordering,
  overlap or range check to the times before sending, so the controller
  statuses 4 (slot preceded by an empty slot) and 5 (not ascending) of
  Section 5.4.3 are the candidate controller-side checks of the times; status
  6 (validation failure; candidate meaning: setpoint out of range) is the
  candidate check of the setpoint, which the
  requester sends without a clamp (next item).
- Setpoint: the value multiplied by 10 as a u16 little-endian; a heating write
  carries an explicit setpoint, the other program kinds (cooling, DHW,
  circulation pump, ventilation) carry `FF FF`. For DHW and the circulation
  pump the meaning of `FF FF` is in Section 5.3; the controller response to
  `FF FF` in a cooling or ventilation write is not documented here. The
  scaled setpoint is truncated toward zero and only its low 16 bits are
  sent, with no clamp (candidate).
- Slots per day: at most 12 for heating, cooling and ventilation programs and
  at most 3 for DHW and circulation-pump programs are written (candidate).

#### 5.4.2 A6 write sequence (candidate)

Unconfirmed on the wire. A week write by a requester is a series of
single-slot requests:

1. Days 0 to 6 (Monday to Sunday) are written in order.
2. Within a day the slots are written in ascending order from slot 0, one
   request per slot, with `currentSlot` the slot index and `totalSlots` the
   count of that day. A request is not retried per slot.
3. A day with a count of 0 still sends one request, with slot 0 and total 0,
   carrying the bytes of the first slot. The clear or delete meaning of that
   request is not established.
4. A transport failure or a nonzero status stops the remaining slots of that
   day; later days are still sent, and no request reverts already-sent
   slots.
5. The group-day values 7 to 9 (Section 4.3.1) are not sent (candidate).

#### 5.4.3 A6 status labels (candidate)

Candidate interpretation, unconfirmed on the wire; it does not replace the
validated meanings in the response table of Section 5.4. On the validated
eBUS exchanges, which carry no echoed command (Section 2.4), a requester reads
the A6 status from the first byte of the reply data, the first byte after `NN`
(`NN=0x01`, status). Which byte a requester takes as the
status when a reply carries an echoed command byte or the PeBUS prefix fields
is unresolved. The table has
a neutral label for each value a requester distinguishes and a candidate
Vaillant label where one exists (full table with the effect on the sequence:
[b555-a6-status-codes.csv](./fixtures/b555-a6-status-codes.csv)).

| Value | Neutral label | Candidate Vaillant label | Relation to the response table above |
|---|---|---|---|
| 0 | frame accepted (persistence unknown until an A5 read-back) | OK | validated: ACK |
| 1 | illegal request | InvalidRequest | validated: parameter out of range |
| 2 | write response unknown | — | not in the validated table |
| 3 | module index and/or window type not supported | NotAvailable | validated: timer type unavailable |
| 4 | slot preceded by an empty slot | Skipped slot | the validated semantics stay unknown; this is a candidate label only |
| 5 | slot not in time ascendance | Slots not ascending | the validated semantics stay unknown; this is a candidate label only |
| 6 | validation failure | Setpoint out of range | validated: validation failure |
| 7 | different initiator within a sequence | — | not in the validated table |

The requester treats values above 7 as unknown failures. Every nonzero value
stops the remaining slots of that day (Section 5.4.2). The status values that
a controller actually returns are not established beyond Section 5.4.

#### 5.4.4 No read-back after a write (candidate)

After a write in which every day succeeded, no A4 or A5 read-back follows from
a Vaillant requester (candidate); the requester does not perform the A5
read-back that Section 5.4 describes as the only confirmation of
persistence.

### 5.5 Availability and visibility reads (candidate)

Candidate interpretation, unconfirmed on the wire; no Vaillant requester use
is known (Section 3.1). A0 and A7 have one reply layout and two
meanings: A0 is *available* and A7 is *visible*. The reply data is 8 bytes:

- Byte 0 bits 0 to 4: DHW, DHW circulation pump, noise reduction, ventilation,
  high tariff. Bits 5 to 7 of byte 0 and all of byte 1 are reserved.
- Bytes 2 to 7: channels 1 to 12, four bits per channel, two channels per
  byte with the lower channel in the low nibble. Within a channel, bit 0 is
  zone heating, bit 1 zone cooling, bit 2 external DHW circuit and bit 3
  external fixed-flow circuit.

A1 and A2 (available) and A8 and A9 (visible) carry 48 reserved bits. The
field tables are in
[b555-candidate-field-layouts.csv](./fixtures/b555-candidate-field-layouts.csv).

### 5.6 EM status request and EM control entries (candidate)

Candidate interpretation, unconfirmed on the wire:

- Sub-command 0x00 is an EM status request. The request carries the command
  byte only (`B5 55 01 00`); a requester sends it to destination `08` (the
  heat generator, not a VRC720-family controller), and only when the unit at
  address `0x15` identifies as an energy manager (candidate). The
  reply is one data byte: bit 0 = EM found, bit 1 = EM authorised, bits 2 to 7
  = future discovery flags. Candidate: bits 0 and 1 are the relevant flags.
  Candidate, unconfirmed on the wire: on eBUS the flags are the first data byte
  after `NN` (Section 3.1); which byte carries them in a reply with an echoed
  prefix or the PeBUS prefix fields is unresolved.
- Sub-commands 0x04 and 0x06 (Vaillant names `SimplHeatiContr` and
  `EMMActivBroad`, correspondence only) each have one candidate
  service-identifier byte (request `B5`, reply `F5`); its position, any further
  parameters and the request and reply lengths are not established. Candidate
  meaning, unconfirmed on the wire: a simple heating control entry and an
  energy-manager activation broadcast entry. Their meaning is not
  established.

## 6. Multi-slot write qualification

The device behavior for `SC > 1` is not established by a publishable, transport-independent capture. Treat multi-slot persistence and the required inter-frame conditions as `Unknown`; an ACK alone does not prove that every slot persisted.

## 7. Selector Namespace

The ZONE and HC selector bytes encode into the A5/A6 data field as follows:

```
A5/A6 [ZONE] [HC] [DD] ...
```

The ebusd CSV definitions confirm the following mappings:

| ebusd Name | Opcode | ZONE | HC |
|------------|--------|------|-----|
| Z1HeatingTimer_* | A5/A6 | 0x00 | 0x00 |
| Z1CoolingTimer_* | A5/A6 | 0x00 | 0x01 |
| HwcTimer_* | A5/A6 | 0x00 | 0x02 |
| CcTimer_* | A5/A6 | 0x00 | 0x03 |
| SilentTimer_* | A5/A6 | 0x00 | 0x04 |
| Z2HeatingTimer_* | A5/A6 | 0x01 | 0x00 |
| Z2CoolingTimer_* | A5/A6 | 0x01 | 0x01 |
| Z3HeatingTimer_* | A5/A6 | 0x02 | 0x00 |
| Z3CoolingTimer_* | A5/A6 | 0x02 | 0x01 |

Note: The ebusd CSV definitions use ZONE=0x00 for HWC, CC, and Silent
timers. VR940 uses ZONE=0xFF for HWC and CC writes (Section 12.11 for DHW;
CC write verified inline below). Both values are accepted for reads
(A3/A4/A5 proven identical in Section 12.15) and for most write shapes,
mapping to the same schedule. CC ZONE=0xFF writes are confirmed to persist:

```
# CC write with ZONE=0xFF (ebusd source 0x31):
hex -n 15b555a6ff0300000100001800ffff
Response: 0100  (ACK)

# Read-back:
hex -n 15b555a5ff030000
Response: 070000001800ffff  (persisted ✓)
```

However, **aliasing is not unconditional**: ZONE=0xFF + full-day
(00:00-24:00) + explicit DHW temp returns error 0x06, while the same
write with ZONE=0x00 succeeds (Section 12.13). Implementations should
prefer ZONE=0xFF for HWC and CC to match VR940 behavior, but be aware
of this edge case.

## 8. Data Type Reference

### 8.1 HTM (Hour:Minute Time)

Two consecutive UCH bytes: `[hour] [minute]`.

- Hour range: 0x00-0x18 (0-24). **Enforced**: values ≥ 0x19 return error 0x01.
- Minute range: 0x00-0x3B (0-59).
- 24:00 = `0x18 0x00` is valid as both start and end time.
- Inverted intervals (start > end) are accepted by the controller.

### 8.2 UIN (Unsigned Integer 16-bit, Little-Endian)

Two bytes: `[low] [high]`. Value = `(high << 8) | low`.

For temperature fields of the validated heating and DHW programs: physical
value = raw / 10.0, unit = degrees Celsius. For the other program types,
including the candidate types 0x05 to 0x08, unit and scale are **Unknown**
(Section 5.3.1).

Special value: `0xFFFF` (65535) = context-dependent. For `has_temp=0`
types (CC, Silent): no temperature. For DHW (`has_temp=1`, `temp_slots=1`):
"don't change setpoint" (temperature no-op; read-back returns current B524
value). For Heating (`has_temp=1`, `temp_slots=12`): **rejected** with error
0x01 (Section 12.14).

### 8.3 UCH (Unsigned Character)

Single byte, 0x00-0xFF. Used for slot counts, indices, hours, minutes.

## 9. B524 timer relation

B524 opcodes `0x03` and `0x04` are a distinct timer transport for VRC700-family controllers. B555 is the documented timer transport for the VRC720-family controllers listed in [Timer Transport Device Binding](#10-timer-transport-device-binding). The same eBUS target address does not establish interchangeability.

## 10. Ventilation program read (candidate)

Candidate interpretation, unconfirmed on the wire. The ventilation program
(time-window type 5, module index 0) is the only program a Vaillant requester
reads through B555 (Section 3.1). The read has this shape:

1. One A4 request (Section 5.2.1) returns the seven daily slot counts.
2. For each day 0 to 6 in order, and for each slot 0 to count-1 of that day,
   one A5 request (Section 5.3.1) returns the start time, the end time and a
   setpoint.
3. A failed exchange, an A4 reply rejected as described in Section 5.2.1, or
   an undecodable A5 exchange ends the read.
4. Per day at most 12 slots are accepted. The requester does not evaluate the
   A5 setpoint for the ventilation program.
5. A requester sends the read only when ventilation is indicated as
   available (candidate); what indicates it and what triggers the read are
   unresolved.

## 11. Candidate field layouts and enumerations

Fixtures for this page, in the `fixtures` directory next to it. All are
candidate interpretation, unconfirmed on the wire, except where Section 5 states a
validated layout. The field layouts and enumerations are the same under the
eBUS and PeBUS profiles (Section 3.1).

| Fixture | Content |
|---|---|
| [b555-a4a5-fields.csv](./fixtures/b555-a4a5-fields.csv) | A4 and A5 request frames and reply fields with the acceptance rules (Sections 5.2.1, 5.3.1) |
| [b555-a6-request-fields.csv](./fixtures/b555-a6-request-fields.csv) | The 16 fields of the A6 request frame (Section 5.4.1) |
| [b555-a6-status-codes.csv](./fixtures/b555-a6-status-codes.csv) | The A6 status values a requester distinguishes, with neutral label, candidate Vaillant label and effect on the sequence (Section 5.4.3) |
| [b555-candidate-field-layouts.csv](./fixtures/b555-candidate-field-layouts.csv) | Request and reply field layouts of every B555 sub-command in Section 3.1 |
| [b555-candidate-enumerations.csv](./fixtures/b555-candidate-enumerations.csv) | Enumerations for the sub-commands documented here |

In [b555-candidate-field-layouts.csv](./fixtures/b555-candidate-field-layouts.csv)
`offset_after_command` of a request row counts from the first byte after the
sub-command byte, and the Vaillant PDU offset is that value plus 3. For a reply
row it is an eBUS reply-data offset: an eBUS reply carries no sub-command byte
(Section 2.4), so the status or flags are at offset 0 and the plus-3 rule does
not apply; on PeBUS, if the prefix fields are present, every reply offset would
shift by three, which is unresolved (Section 3.1). The `vaillant_name` column and
the labels of the enumeration file are Vaillant names, kept as
correspondence values.

## Open questions

Every item below is unresolved. None is promoted by the candidate text above.

- Reply `NN` and framing: the reply lengths for A0, A1, A2, A7, A8, A9, 00, 04
  and 06 are not observed, nor for any sub-command on the ventilation program.
- No raw capture of a B555 exchange with its ACK and CRC bytes is included;
  Sections 2.1 to 2.3 give the generic eBUS framing applied to B555.
- The reply lengths of the B555 sub-commands under the PeBUS profile are not
  established.
- How the requester selects the controller address `ZZ` at run time is not
  established.
- The status values a controller returns beyond Section 5.4 are not
  established: candidate values 2 and 7 of A6, value 2 of A5, and values above
  7.
- The polarity of the A5 status (whether 0 is the accepted value) for the
  ventilation program is not observed; the requester does not test it.
- The unit and scale of the A5 and A6 setpoint for the ventilation program are
  unresolved (candidate unit for the A3 unit code 2: fan stage, unconfirmed
  on the wire), and
  `0xFFFF` has no established invalid meaning for that program. The scale of
  the A5 times for that program is also not observed.
- The clear or delete meaning of an A6 request with total 0 and slot 0
  carrying the first slot's bytes is not established.
- Whether a week write is atomic, whether a status of 0 means the slot
  persisted (multi-slot persistence is also **Unknown**, Section 6), and
  whether a partial failure leaves a partial program are not established; no
  request reverts already-sent slots.
- Whether a controller accepts the group-day values 7 to 9 of A6 is not
  established; no request carrying them is known.
- The range of accepted module indices, and the behaviour for time-window
  types 4 and 6 to 8, are not observed.
- The cadence of the ventilation read is not established, and neither is
  what indicates ventilation as available to the requester or what triggers
  the read.
- No A4 or A5 read of a heating or cooling program by the Vaillant requester
  is known, so its handling of such results is not established. No cooling
  A4 or A5 result is documented here: cooling timers were not observed (they
  answered as not available, Section 5.1); other installations of the
  VRC720 family were not observed.
- The position of the flags byte in the 00 reply (candidate: the first data
  byte after `NN` on eBUS; unresolved with an echoed or PeBUS prefix), the
  meaning of its future discovery flags and whether the target at destination `08` returns the reply
  as described in Section 5.6 are not observed.
- Which byte a requester takes as the status of A4 and A6 replies that carry
  an echoed command byte or the PeBUS prefix fields is unresolved (the A5
  status is not evaluated; candidate); the validated eBUS replies carry no
  echo, and their status is the first byte after `NN`.
- The A0 and A7 bit and channel layouts (Section 5.5) are candidates; no
  Vaillant requester use of A0, A1, A2, A7, A8 or A9 is known.
- The candidate enumerations and field layouts of Section 11 are unconfirmed
  on the wire for every value not covered by Section 5.
- The meaning of sub-commands 0x04 and 0x06 is not established.
- Which identification result of the unit at `0x15` makes a requester send the
  EM status request is not established beyond the candidate "energy manager"
  reading.
- The validated ZONE values (`0xFF` for the DHW and CC writes, `0x00` to
  `0x02` for the zone heating writes; Sections 4.1 and 7) are not reconciled
  with the candidate correspondence ZONE = module index.
- The B524 OP04 aggregate-day numbering (8 = Saturday-Sunday,
  9 = Monday-Friday) is documented as a **Hypothesis** in the
  [B524 timer section](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules).
  Physical acceptance, support and persistence remain **Unknown**.
- Other installations of the VRC720 family have not been observed for any
  candidate statement in this document.
