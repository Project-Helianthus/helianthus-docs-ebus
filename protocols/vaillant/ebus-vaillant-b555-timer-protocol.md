# B555 Timer/Schedule Protocol Specification

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This document uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

**Protocol:** eBUS B555 (PB=0xB5, SB=0x55)
**Status:** Reverse-engineered, validated on live hardware
**Date:** 2026-03-08
**Revision:** 2.15

## 1. Scope

This document specifies the eBUS B555 protocol used by **VRC720-family controllers only** for reading and writing weekly heating, DHW, and other timer/schedule programs.

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

## 3. Opcodes

The first byte of the data field is the opcode.

| Opcode | Name | Direction | NN | Description |
|--------|------|-----------|-------|-------------|
| 0xA3 | CONFIG_READ | Read | 3 | Read timer configuration |
| 0xA4 | SLOTS_READ | Read | 3 | Read slots-per-weekday counts |
| 0xA5 | TIMER_READ | Read | 5 | Read one day/slot timer entry |
| 0xA6 | TIMER_WRITE | Write | 12 (0x0C) | Write one day/slot timer entry |

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

### 4.2 HC (Schedule Type / Heating Circuit Type)

| Value | Type | Temperature Field |
|-------|------|-------------------|
| 0x00 | Heating | Yes (target setpoint) |
| 0x01 | Cooling | Not observed (unavailable on test system) |
| 0x02 | HWC (Domestic Hot Water) | Yes (DHW target temp) |
| 0x03 | CC (DHW recirculation pump schedule) | No — time-only schedule, temp field carries 0xFFFF |
| 0x04 | NoiseReduction (Silent) | Not observed (unavailable on test system). VRC720 CSV uses `Silent`; BASV2 CSV uses `NoiseReduction`. Both describe the same function: a quiet-hours schedule. Name aligns with B508 broadcast field `NoiseReduction`. See also [B524 section 4.4.1](./ebus-vaillant-B524.md#441-timer-channel-map-sel1sel2sel3) SEL=0x00/0x00/0x02 (VRC700 equivalent). |

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
[status] [max_slots] [time_res] [min_dur] [has_temp] [temp_slots] [min_temp] [max_temp] [pad]
```

| Byte | Name | Type | Description |
|------|------|------|-------------|
| [0] | status | UCH | 0x00 = available, 0x03 = unavailable |
| [1] | max_slots | UCH | Maximum time slots per day |
| [2] | time_resolution | UCH | Suggested time resolution in minutes (advisory) |
| [3] | min_duration | UCH | Suggested minimum slot duration in minutes (advisory) |
| [4] | has_temperature | UCH | 0x01 = slots carry a temperature setpoint, 0x00 = no |
| [5] | temp_slots | UCH | Number of independent temperature values. See Section 5.1.1. |
| [6] | min_temp_c | UCH | Minimum temperature in whole °C (0xFF = N/A). **Enforced.** |
| [7] | max_temp_c | UCH | Maximum temperature in whole °C (0xFF = N/A). **Enforced.** |
| [8] | padding | UCH | Always 0x00 |

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
- `time_resolution` and `min_duration` are **advisory only**. The controller
  accepts any minute value (0-59) regardless of these fields. These constraints
  are advisory timing metadata
  for all 4 visible schedule types (Heating Z1, Heating Z2, DHW, CC/circulation
  pump), matching the config `time_resolution=10` value.

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

#### 5.1.1 Byte [5] (temp_slots) — temperature cardinality

This field indicates how many independent temperature setpoints can exist
across the timer's slots. Three distinct values are observed:

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
[status] [Mon] [Tue] [Wed] [Thu] [Fri] [Sat] [Sun] [pad]
```

| Field | Size | Description |
|-------|------|-------------|
| status | 1 | Timer status: 0x00 = active, 0x03 = unavailable (matches A3 byte[0]). See A5 status for comparison. |
| Mon..Sun | 7 | Slot count per day (UCH, 0x00-0x0C) |
| pad | 1 | Trailing padding (always 0x00) |

> **Cross-reference:** The first byte of A4 (status/slot-count context) and A5 (status/timer-entry context) responses share the same byte position but have different semantics. A4 byte[0] gates the validity of the per-weekday slot counts; A5 byte[0] gates the validity of a single timer slot entry. See the respective section for details.

**Wire-validated example (Z1 Heating, all single-slot):**

```
Initiator: 31 15 B5 55 03 A4 00 00
Target:  09 00 01 01 01 01 01 01 01 00
```

### 5.3 TIMER_READ (0xA5)

Reads a single timer slot for a specific day.

**Request data (5 bytes):**

```
A5 [ZONE] [HC] [DD] [SS]
```

| Field | Size | Description |
|-------|------|-------------|
| ZONE | 1 | Zone index (0x00-0x02, or 0xFF for system-wide schedules — see Section 7) |
| HC | 1 | Schedule type (0x00-0x04) |
| DD | 1 | Day of week (0x00-0x06) |
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
- Value = raw / 10.0 (unit: degrees Celsius)
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

### 5.4 TIMER_WRITE (0xA6)

Writes a single timer slot for a specific day.

**Request data (12 bytes, NN=0x0C):**

```
A6 [ZONE] [HC] [DD] [SI] [SC] [Sh] [Sm] [Eh] [Em] [Tlo] [Thi]
```

| Field | Size | Encoding | Description |
|-------|------|----------|-------------|
| ZONE | 1 | UCH | Zone index (0x00-0x02, or 0xFF for system-wide schedules — see Section 7) |
| HC | 1 | UCH | Schedule type (0x00-0x04) |
| DD | 1 | UCH | Day of week (0x00-0x06) |
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

For temperature fields: physical value = raw / 10.0, unit = degrees Celsius.

Special value: `0xFFFF` (65535) = context-dependent. For `has_temp=0`
types (CC, Silent): no temperature. For DHW (`has_temp=1`, `temp_slots=1`):
"don't change setpoint" (temperature no-op; read-back returns current B524
value). For Heating (`has_temp=1`, `temp_slots=12`): **rejected** with error
0x01 (Section 12.14).

### 8.3 UCH (Unsigned Character)

Single byte, 0x00-0xFF. Used for slot counts, indices, hours, minutes.

## 9. B524 timer relation

B524 opcodes `0x03` and `0x04` are a distinct timer transport for VRC700-family controllers. B555 is the documented timer transport for the VRC720-family controllers listed in [Timer Transport Device Binding](#10-timer-transport-device-binding). The same eBUS target address does not establish interchangeability.
