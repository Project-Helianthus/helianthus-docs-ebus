# B555 Timer/Schedule Protocol Specification

**Protocol:** eBUS B555 (PB=0xB5, SB=0x55)
**Status:** Reverse-engineered, validated on live hardware
**Date:** 2026-03-08
**Revision:** 2.15
**Author:** Helianthus Project (Claude Code + operator)

## 1. Scope

This document specifies the eBUS B555 protocol used by **VRC720-family controllers only** for reading and writing weekly heating, DHW, and other timer/schedule programs.

> **CORRECTION (2026-04-14):** B555 is NOT used by VRC700. The original scope statement "VRC700/VRC720 series" was incorrect. VRC700 (device ID 70000, including Saunier Duval B7S00) uses [B524 opcodes 0x03/0x04](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules) for all timer operations. Both device families share eBUS slave address `0x15` but are different device classes with different timer transports. (Source: FINAL-B524-B555-B507-B508.md B1, CROSSCHECK-B555-misc.md; confidence HIGH.)

### 1.0 Timer Transport Device Binding

| Device class | Device IDs | Timer transport | Reference |
|---|---|---|---|
| VRC720 family | BASV0, BASV2, BASV3, CTLV0, CTLV2, CTLV3, CTLS2 | **B555** (this document) | Validated on BASV2 |
| VRC700 | 70000 (including Saunier Duval B7S00) | **B524 opcodes 0x03/0x04** | [B524 section 4.4](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules) |

A scanner or schedule writer that does not check device identity before choosing transport will send B555 to a VRC700 (no response or error) or send B524 timer frames to a BASV2 (empty response). Device identity can be determined from the eBUS device ID returned during identification.

### 1.1 Validation Environment

| Component | Detail |
|-----------|--------|
| Controller | BASV2 (VRC720f/2), HW 1704, SW 0507, address 0x15 |
| Boiler | BAI00 (ecoTEC exclusive), HW 7603, address 0x08 |
| Cloud Gateway | VR940/NETX3, HW 0404, address 0xF6 (bus source 0xF1) |
| eBUS Adapter | ebusd-esp via ENH protocol |
| Capture Tool | ebusd 23.x (Docker addon), telnet port 8888 |
| Reference | ebusd CSV: `15.720.csv` (Vaillant BASV2 definitions) |

### 1.2 Validation Methods

1. **Passive capture** of VR940 cloud gateway writes (myVaillant app)
2. **Active reads** via ebusd `hex` and `read` commands
3. **Active writes** via ebusd `hex -n` commands with read-back verification
4. **Multi-zone probing** across Z1/Z2 heating, DHW, CC, Silent timers
5. **Exhaustive test pass** (T01-T07): byte[0] correlation, temp broadcast,
   multi-slot timing, error code mapping, hour/minute boundary, inactive timer
   writes, partial write atomicity

## 2. Frame Structure

B555 uses the standard eBUS Master-Slave (MS) transaction format.

### 2.1 Master Frame

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

### 2.2 Slave Response

```
ACK NN <response[0..NN-1]> CRC ACK
```

| Field | Size | Description |
|-------|------|-------------|
| ACK | 1 | 0x00 = accepted |
| NN | 1 | Response data length |
| response | NN | Response payload |
| CRC | 1 | CRC-8 of NN..response |
| ACK | 1 | Master ACK |

### 2.3 Notation Conventions

This document uses two distinct notations for bus data:

1. **Full wire captures** (Section 12.1): show QQ, ZZ, PB, SB, NN and payload
   as seen on the physical bus, using the format `Master: QQ ZZ ... / NN data`.
   Example: `F1 15 B5 55 0C A6 ... / 01 00`.

2. **ebusd `hex` command output**: the ebusd telnet interface strips ACK bytes
   and CRCs. It returns only `NN <response_payload>` for slave responses.
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
  are intended for UI clients. The myVaillant app uses 10-minute resolution
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
  side-effecting the B524 setpoint. This is a client design choice — the
  protocol supports explicit temp writes, but they always update B524.

**Read-back is lossy:** reading a B555 DHW slot always returns the current
B524 setpoint. There is no way to distinguish between a slot that was written
with an explicit temperature and one that was written with 0xFFFF — both
read back as the B524 value.

**Wire-validated example:**

```
Master: 31 15 B5 55 03 A3 00 00
Slave:  09 00 0C 0A 05 01 0C 05 1E 00
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
Master: 31 15 B5 55 03 A4 00 00
Slave:  09 00 01 01 01 01 01 01 01 00
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
Master: 31 15 B5 55 05 A5 00 00 00 00
Slave:  07 00 00 00 18 00 E1 00

# Z1 Heating Sunday: 00:00-18:00 @ 22.5°C
Master: 31 15 B5 55 05 A5 00 00 06 00
Slave:  07 00 00 00 12 00 E1 00

# Z2 Heating Monday: 00:00-24:00 @ 20.0°C
Master: 31 15 B5 55 05 A5 01 00 00 00
Slave:  07 00 00 00 18 00 C8 00

# HWC Monday: 00:00-24:00 @ 61.0°C (DHW target)
Master: 31 15 B5 55 05 A5 00 02 00 00
Slave:  07 00 00 00 18 00 62 02

# HWC Saturday: 06:00-24:00 @ 61.0°C
Master: 31 15 B5 55 05 A5 00 02 05 00
Slave:  07 00 06 00 18 00 62 02

# CC Monday: 00:00-24:00 @ NONE
Master: 31 15 B5 55 05 A5 00 03 00 00
Slave:  07 00 00 00 18 00 FF FF
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
| 0x04 | Multi-slot write error | Observed once in early testing, not reproducible |
| 0x05 | Multi-slot write error | Observed once in early testing, not reproducible |
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
Master: F1 15 B5 55 0C A6 00 00 00 00 02 00 00 06 00 18 01
Slave:  01 00

# Monday slot 1/2: 06:00-23:50 @ 7.5°C
Master: F1 15 B5 55 0C A6 00 00 00 01 02 06 00 17 32 4B 00
Slave:  01 00

# Tuesday slot 0/1: 00:00-24:00 @ 22.5°C (single slot)
Master: F1 15 B5 55 0C A6 00 00 01 00 01 00 00 18 00 E1 00
Slave:  01 00

# Sunday slot 0/1: 00:00-18:00 @ 22.5°C (single slot)
Master: F1 15 B5 55 0C A6 00 00 06 00 01 00 00 12 00 E1 00
Slave:  01 00
```

**Write verified by read-back (ebusd `hex -n` command):**

```
# Write Monday to 00:00-24:00 @ 22.5°C (SC=1)
hex -n 15b555a6000000000100001800e100
Response: 0100 (ACK)

# Read-back confirms:
read Z1HeatingTimer_Monday -> 00:00;24:00;22.5
```

## 6. Multi-Slot Write Protocol

### 6.1 Observed VR940 Behavior

When the myVaillant app modifies a schedule, the VR940 cloud gateway:

1. Writes **ALL 7 days** of the affected zone/HC, even if only 1 day changed
2. Sends one A6 frame per slot, per day, in sequence: Mon→Sun
3. Each A6 frame includes both SI (current slot index) and SC (total slot count)
4. Inter-frame interval: ~200ms
5. Cloud→eBUS delay: ~3 minutes from app commit to bus writes

### 6.2 Multi-Slot Write Window

When SC > 1, the controller processes slot SI=0 and allocates the
declared slot count. Subsequent slots (SI=1, SI=2, ...) must arrive
within a write window to populate the remaining positions.

#### 6.2.1 What the VR940 proves

The VR940 cloud gateway writes multi-slot schedules successfully with
inter-frame intervals of 190-300ms (Section 12.1). The captured frames
are non-interleaved (no other traffic between slots of the same day),
which is consistent with the VR940 holding the bus across the burst —
but the capture does not prove this directly. The VR940 may simply
win re-arbitration quickly due to its address priority (0xF1).

#### 6.2.2 What ebusd testing shows

All multi-slot write attempts through ebusd telnet produced the same
result: slot 0 persists, subsequent slots are silently discarded.

Observations:

1. **Slot 0 always commits.** Writing SI=0 with SC > 1 immediately
   persists slot 0's data AND sets the day's slot count to SC.

2. **Subsequent slots return 0x00 but don't persist.** The controller
   ACKs every slot with 0x00 regardless of timing. However, reading
   back slots 1+ returns copies of slot 0's data.

3. **No rollback.** A partial multi-slot write (only slot 0 delivered)
   does NOT roll back. The day keeps SC slots with slot 0's data in
   all positions.

4. **Error codes 0x04/0x05** were observed once in early testing with
   SC=3 but could not be reproduced in systematic retesting.

#### 6.2.3 Transport limitation vs protocol behavior

**The silent discard of slots 1+ cannot be attributed to the B555
protocol itself.** The ebusd telnet path requires re-arbitration for
each `hex -n` command, adding a minimum inter-frame gap of ~150-300ms
(command parsing + bus arbitration + frame TX + slave response). This
gap overlaps with the VR940's successful 190-300ms range, but the two
paths differ qualitatively:

- **VR940**: achieves 190-300ms inter-frame (may hold bus or win
  re-arbitration quickly — not directly observable from captures)
- **ebusd**: releases bus after each command, must re-arbitrate each time

Possible explanations for the ebusd silent discard:

1. The write window is shorter than ebusd's minimum achievable gap
2. Re-arbitration itself (not just timing) invalidates the write session
3. The controller's write session is keyed to the source address or
   some pairing state that ebusd (source 0x31) doesn't have

Without a transport that can control inter-frame timing independently
of bus arbitration, the root cause cannot be isolated.

#### 6.2.4 Implication for gateway implementation

Multi-slot writes require one of:

- **Bus burst mode**: send all slots for a day with minimal inter-frame
  gap (as the VR940 achieves, ~190-300ms)
- **SC=1 only**: limit to single-slot schedules (always reliable)

Using SC=1 per day covers the common case (one interval per day at a
single setpoint) and is the recommended initial approach.

### 6.3 Single-Slot Write (Reliable)

Single-slot writes (SC=1) are reliable from any source (ebusd 0x31,
VR940 0xF1) and work through standard bus arbitration with retries.
This covers the common case of one interval per day.

**Verified through both ebusd and VR940 captures:**
- ebusd: write + immediate read-back confirms persistence (Section 12.2)
- VR940: 84+21+21 frame captures, all persisted (Sections 12.10-12.11)

**Important:** The ebusd `hex -n` command format is `ZZPBSB` + DATA.
Do **not** include the NN length byte — ebusd calculates it automatically.
Including NN as a data byte produces a malformed frame (wrong opcode byte)
that the controller may ACK without persisting.

### 6.4 Writing to Unavailable Timers

Writing to a timer type with A3 config status=0x03 (unavailable) returns
error code 0x03. Validated for:

- Z1 Cooling (not enabled): response 0x03
- Z3 Heating (no zone 3 configured): response 0x03
- Silent (not configured): response 0x03

### 6.5 Time Validation

The controller enforces:

- **Hour range:** 0x00-0x18 (0-24). Hour values ≥ 0x19 (25) are rejected
  with error 0x01.
- **Minute range:** 0x00-0x3B (0-59). Validated; minute 59 accepted.
- **Inverted intervals (start > end):** ACCEPTED and persisted. The
  controller does not validate chronological ordering.
- **Zero-length intervals (start = end):** ACCEPTED and persisted.
- **Gapped intervals:** ACCEPTED. Slots need not be contiguous or
  cover the full day.

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

## 9. B524 Timer Read (Opcode 0x03) — VRC700 Only, Not Functional on VRC720 Family

The gateway's existing `read_timer` RPC method uses B524 (PB=0xB5, SB=0x24)
with opcode 0x03. Testing confirmed this returns **empty responses** on
BASV2/VRC720-family controllers. This is expected behavior: B524 timer opcodes
0x03/0x04 are a **VRC700-only** feature. VRC720-family controllers (BASV2,
BASV3, CTLV2, CTLV3, CTLS2) use B555 (this protocol) for all timer operations.

**Validated on BASV2:** `ebus.v1.rpc.invoke(address=21, plane=system, method=read_timer,
params={source:113, sel1:0, sel2:0, sel3:0, weekday:0})` returns
`value: null, valid: false`.

**On a VRC700 system**, the same B524 opcode 0x03 query would return a valid
time-slot sequence. See [B524 section 4.4](./ebus-vaillant-B524.md#44-0x03--0x04-timer-schedules) for the VRC700 timer channel map
and device-binding details.

## 10. Observed Timer State (Test System, 2026-03-08)

### 10.1 Z1 Heating (Parter)

| Day | Start | End | Temp (C) | Slots |
|-----|-------|-----|----------|-------|
| Mon | 00:00 | 24:00 | 22.5 | 1 |
| Tue | 00:00 | 24:00 | 22.5 | 1 |
| Wed | 00:00 | 24:00 | 22.5 | 1 |
| Thu | 00:00 | 24:00 | 22.5 | 1 |
| Fri | 00:00 | 24:00 | 22.5 | 1 |
| Sat | 00:00 | 24:00 | 22.5 | 1 |
| Sun | 00:00 | 18:00 | 22.5 | 1 |

### 10.2 Z2 Heating (Etaj)

| Day | Start | End | Temp (C) | Slots |
|-----|-------|-----|----------|-------|
| All | 00:00 | 24:00 | 20.0 | 1 |

### 10.3 HWC (Domestic Hot Water)

| Day | Start | End | Temp (C) | Slots |
|-----|-------|-----|----------|-------|
| Mon-Fri | 00:00 | 24:00 | 61.0 | 1 |
| Sat-Sun | 06:00 | 24:00 | 61.0 | 1 |

### 10.4 CC (DHW Recirculation Pump Schedule)

All days: 00:00-24:00, no temperature (0xFFFF). 1 slot per day.

### 10.5 Silent

Not configured (0 slots per day).

### 10.6 Cooling

Not enabled on test system (ebusd: "element not found").

## 11. Implementation Notes

### 11.1 Gateway Integration Path

B555 is a separate PB/SB pair (0xB5/0x55) from B524 (0xB5/0x24). The
gateway requires:

1. **ebusreg:** New B555 plane provider with A3/A4/A5/A6 method templates
2. **ebusgateway:** B555-aware semantic poller for timer cache
3. **MCP:** New semantic plane `ebus.v1.semantic.schedules.get`
4. **HA integration:** Schedule entity with Home Assistant's calendar/schedule domain

### 11.2 Bus Contention

B555 reads are subject to the same bus arbitration as all eBUS traffic.
Observed error rate: ~30-40% of reads fail with `SYN received`,
`arbitration lost`, or `read timeout`. Retry logic is essential.

### 11.3 ebusd Coexistence

When ebusd and Helianthus share the same adapter-proxy, both compete
for bus arbitration. ebusd's periodic timer polling (B555 reads)
increases contention. Consider:

- Coordinating read schedules to avoid collision
- Using ebusd's `grab` cache instead of direct bus reads when possible
- Implementing backoff logic for arbitration failures

### 11.4 Source Address

- ebusd uses source address 0x31
- VR940 uses source address 0xF1
- Helianthus gateway uses source address 0x71 (initiator)
- Any valid eBUS master address can send B555 commands

## 12. Raw Wire Captures

### 12.1 VR940 Write Sequence (8 frames, ~2.5 seconds)

Captured 2026-03-08T17:28:23-17:28:25 EET. User modified Monday Z1
heating to 2 intervals: 00:00-06:00@28°C, 06:00-23:50@7.5°C.

```
17:28:23.849 f115b5550ca60000000002000006001801 / 0100  # Mon s0/2
17:28:24.047 f115b5550ca60000000102060017324b00 / 0100  # Mon s1/2
17:28:24.291 f115b5550ca6000001000100001800e100 / 0100  # Tue s0/1
17:28:24.595 f115b5550ca6000002000100001800e100 / 0100  # Wed s0/1
17:28:24.903 f115b5550ca6000003000100001800e100 / 0100  # Thu s0/1
17:28:25.092 f115b5550ca6000004000100001800e100 / 0100  # Fri s0/1
17:28:25.287 f115b5550ca6000005000100001800e100 / 0100  # Sat s0/1
17:28:25.483 f115b5550ca6000006000100001200e100 / 0100  # Sun s0/1
```

Inter-frame interval: 190-300ms. All responses: `01 00` (NN=1, data=0x00, ACK).

### 12.2 Single-Slot Write (Helianthus test)

```
# Write: Monday Z1 Heating, 00:00-24:00 @ 22.5°C
hex -n 15b555a6000000000100001800e100
Response: 0100

# Immediate read-back verification:
read Z1HeatingTimer_Monday -> 00:00;24:00;22.5
```

### 12.3 Temperature Boundary Enforcement (Helianthus test)

```
# Z1 Heating config: min_temp=5°C, max_temp=30°C

# 5.0°C (at minimum) — ACCEPTED
hex -n 15b555a60000010001000018003200
Response: 0100

# 4.5°C (below minimum) — REJECTED with error 0x06
hex -n 15b555a60000010001000018002d00
Response: 0106

# 30.0°C (at maximum) — ACCEPTED
hex -n 15b555a60000010001000018002c01
Response: 0100

# 30.5°C (above maximum) — REJECTED with error 0x06
hex -n 15b555a60000010001000018003101
Response: 0106
```

### 12.4 Time Resolution Non-Enforcement (Helianthus test)

```
# Config says time_resolution=10 min, min_duration=5 min
# Controller accepts ANY minute value and any duration:

# 00:00-06:05 (5-min boundary) — ACCEPTED
hex -n 15b555a6000001000100000605e100
Response: 0100

# 00:00-06:03 (3-min, non-boundary) — ACCEPTED
hex -n 15b555a6000001000100000603e100
Response: 0100

# 00:00-06:01 (1-min slot, below min_duration=5) — ACCEPTED
hex -n 15b555a6000001000100000601e100
Response: 0100

# Read-back confirms 1-minute time persisted:
hex 15b55505a500000100
Response: 070000000601e100  (00:00-06:01 @ 22.5°C)
```

### 12.5 Multi-Slot Write Behavior (Helianthus test)

**Typical behavior (SC=2, two separate nc calls):**

```
# Slot 0/2 — always succeeds:
hex -n 15b555a6000002000206000c00e100
Response: 0100

# Slot 1/2 — returns ACK but data doesn't persist:
hex -n 15b555a600000201020e001400c800
Response: 0100  (0x00 = ACK, but slot data silently discarded)

# A4 slot count shows 2 (allocated by slot 0 write):
hex 15b55503a40000
Response: 09000101020101010100  (Wed=2)

# Both slots read back as slot 0's data:
hex 15b55505a500000200  →  070006000c00e100  (06:00-12:00@22.5°C)
hex 15b55505a500000201  →  070006000c00e100  (same — slot 1 not written)
```

**Early observation (SC=3, not reproducible in later testing):**

```
# Slot 0/3: Response 0100
# Slot 1/3: Response 0105  (error 0x05)
# Slot 2/3: Response 0104  (error 0x04)
# Read-back showed original data (may have been rolled back)
```

These 0x04/0x05 errors could not be reproduced in systematic retesting.
All later multi-slot attempts returned 0x00 for every slot.

### 12.6 Unavailable Timer Write (Helianthus test)

```
# Write to Z1 Cooling (ZZ=00, HC=01, config status=0x03):
hex -n 15b555a6000001000100001800e100
Response: 0103  (error 0x03 — timer unavailable)

# Write to Z3 Heating (ZZ=02, HC=00, config status=0x03):
hex -n 15b555a6020000000100001800e100
Response: 0103

# Write to Silent (ZZ=00, HC=04, config status=0x03):
hex -n 15b555a6000004000100001800ffff
Response: 0103
```

### 12.7 Hour Boundary Validation (Helianthus test)

```
# Start hour 24 (0x18) — ACCEPTED:
hex -n 15b555a6000001000118001800e100
Response: 0100

# Start hour 25 (0x19) — REJECTED:
hex -n 15b555a6000001000119001800e100
Response: 0101  (error 0x01 — invalid time)

# End hour 25 (0x19) — REJECTED:
hex -n 15b555a6000001000100001900e100
Response: 0101

# End minute 59 (0x3B) — ACCEPTED:
hex -n 15b555a600000100010000063be100
Response: 0100
```

### 12.8 HWC Temperature Propagation (Helianthus test)

```
# HWC Monday: write 55.0°C (config [5]=1, temp_slots=1 → shared)
hex -n 15b555a60000020001000018002602
Response: 0100

# Read all 7 days — ALL show 55.0°C (propagated within B555 domain):
hex 15b55505a500020000  →  0700000018002602  (Mon: 55.0°C)
hex 15b55505a500020600  →  0700060018002602  (Sun: 55.0°C)

# Revert to 61.0°C:
hex -n 15b555a60000020001000018006202
Response: 0100
# All 7 days revert to 61.0°C
```

**Note:** This test validates B555 temperature broadcast for DHW (temp_slots=1).
Writing an explicit temperature to any DHW slot propagates it to all 7 days
**and updates the B524 setpoint** (tightly coupled — Section 12.13).
When VR940 writes 0xFFFF instead, the B524 setpoint is left unchanged and the
controller fills the read-back temp field with the current B524 value
(Section 12.11). This test used ZONE=0x00 (ebusd convention); VR940 uses
ZONE=0xFF — both are accepted (Section 7).

### 12.9 Per-Day Temperature Independence (Helianthus test)

Validates that Heating temp_slots=12 allows independent per-day temperatures
(no broadcast behavior). Wrote 7 distinct setpoints across Mon-Sun, verified
each persisted independently, then reverted.

```
# Write 7 distinct temperatures to Z1 Heating (HC=0x00), one per day, SC=1
# Byte layout: ZZ PB SB  A6 ZONE HC DD SI SC SH SM EH EM TL TH  (15 bytes)
# All commands are ebusd `hex -n` format — contiguous hex, copy-paste safe

# Monday: 5.0°C (raw 50 = 0x0032)
hex -n 15b555a60000000001000018003200
Response: 0100

# Tuesday: 10.0°C (raw 100 = 0x0064)
hex -n 15b555a60000010001000018006400
Response: 0100

# Wednesday: 15.0°C (raw 150 = 0x0096)
hex -n 15b555a60000020001000018009600
Response: 0100

# Thursday: 20.0°C (raw 200 = 0x00C8)
hex -n 15b555a6000003000100001800c800
Response: 0100

# Friday: 22.5°C (raw 225 = 0x00E1)
hex -n 15b555a6000004000100001800e100
Response: 0100

# Saturday: 25.0°C (raw 250 = 0x00FA)
hex -n 15b555a6000005000100001800fa00
Response: 0100

# Sunday: 30.0°C (raw 300 = 0x012C)
hex -n 15b555a60000060001000018002c01
Response: 0100

# Read-back verification — all 7 distinct temps persisted (ebusd hex output):
hex 15b55505a500000000  →  0700000018003200  (Mon:  5.0°C ✓)
hex 15b55505a500000100  →  0700000018006400  (Tue: 10.0°C ✓)
hex 15b55505a500000200  →  0700000018009600  (Wed: 15.0°C ✓)
hex 15b55505a500000300  →  070000001800c800  (Thu: 20.0°C ✓)
hex 15b55505a500000400  →  070000001800e100  (Fri: 22.5°C ✓)
hex 15b55505a500000500  →  070000001800fa00  (Sat: 25.0°C ✓)
hex 15b55505a500000600  →  0700000018002c01  (Sun: 30.0°C ✓)

# Revert Mon-Sat to 22.5°C / 00:00-24:00:
hex -n 15b555a6000000000100001800e100
hex -n 15b555a6000001000100001800e100
hex -n 15b555a6000002000100001800e100
hex -n 15b555a6000003000100001800e100
hex -n 15b555a6000004000100001800e100
hex -n 15b555a6000005000100001800e100

# Revert Sunday to 22.5°C / 00:00-18:00 (original baseline):
hex -n 15b555a6000006000100001200e100
```

**Result:** All 7 days retained their distinct temperatures. No broadcast
behavior observed for Heating timers (temp_slots=12). This proves at minimum
7 independent per-day temperature values. Full 12-slot intra-day independence
confirmed by VR940 capture (Section 12.10).

### 12.10 VR940 Z1 Heating 12-Slot Capture (84 frames)

VR940 wrote 12 slots × 7 days for Z1 Heating (HC=0x00, ZONE=0x00) with
12 distinct temperatures per day. Total: 84 frames, all ACKed.

```
# VR940 write pattern (captured via ebusd docker logs):
# Frame format: QQ ZZ PB SB NN  A6 ZONE HC DD SI SC SH SM EH EM TL TH
# Source: 0xF1 (VR940), target: 0x15 (BASV2), NN=0x0C (12 data bytes)
# SC=12 (0x0C) on all frames — matches max_slots from config

# Monday (DD=00), 12 slots — identical pattern repeats for Tue-Sun:
f115b5550ca6000000000c00000100e100  # SI=00 00:00-01:00 22.5°C  ACK
f115b5550ca6000000010c01000200c800  # SI=01 01:00-02:00 20.0°C  ACK
f115b5550ca6000000020c02000300b400  # SI=02 02:00-03:00 18.0°C  ACK
f115b5550ca6000000030c030004002c01  # SI=03 03:00-04:00 30.0°C  ACK
f115b5550ca6000000040c040005003200  # SI=04 04:00-05:00  5.0°C  ACK
f115b5550ca6000000050c05000600c800  # SI=05 05:00-06:00 20.0°C  ACK
f115b5550ca6000000060c060007008c00  # SI=06 06:00-07:00 14.0°C  ACK
f115b5550ca6000000070c070008000901  # SI=07 07:00-08:00 26.5°C  ACK
f115b5550ca6000000080c08000900a000  # SI=08 08:00-09:00 16.0°C  ACK
f115b5550ca6000000090c09000a00f500  # SI=09 09:00-10:00 24.5°C  ACK
f115b5550ca60000000a0c0a000b007300  # SI=10 10:00-11:00 11.5°C  ACK
f115b5550ca60000000b0c0b000c001301  # SI=11 11:00-12:00 27.5°C  ACK

# Timing: ~400-600ms inter-frame (intra-day), ~900ms at day boundaries
# All 84 responses: 01 00 (NN=1, ACK)
```

**Read-back verification (ebusd hex, 3 slots sampled):**

```
hex 15b55505a500000003  →  0700030004002c01  (Mon SI=03: 30.0°C ✓)
hex 15b55505a500000004  →  0700040005003200  (Mon SI=04:  5.0°C ✓)
hex 15b55505a50000000b  →  07000b000c001301  (Mon SI=11: 27.5°C ✓)
```

**Result:** 12 independent intra-day temperatures confirmed. temp_slots=12
is the per-slot temperature cardinality, matching max_slots.

### 12.11 VR940 DHW 21-Slot Capture + B524 Coupling

VR940 wrote 3 slots × 7 days for DHW (HC=0x02, ZONE=0xFF) with temp=0xFFFF.
All 21 frames ACKed. Read-back shows current B524 DHW temp (61.0°C) in all slots.

```
# VR940 DHW write pattern — all carry temp=FFFF:
f115b5550ca6ff020000030c000d00ffff  # Mon SI=0 12:00-13:00  ACK
f115b5550ca6ff020001030e000f00ffff  # Mon SI=1 14:00-15:00  ACK
f115b5550ca6ff0200020310001100ffff  # Mon SI=2 16:00-17:00  ACK
# ... (21 total, 3 per day, all ACK)

# Read-back: controller filled in current DHW temp (61.0°C):
hex 15b55505a5ff020000  →  07000c000d006202  (Mon SI=0: 61.0°C)

# B524→B555 coupling test:
# Changed DHW temp to 50°C via B524 (myVaillant UI, no B555 traffic)
hex 15b55505a5ff020000  →  07000c000d00f401  (Mon SI=0: 50.0°C — updated!)
hex 15b55505a5ff020400  →  070010001100f401  (Fri SI=0: 50.0°C — all updated!)
```

**Result:** When VR940 writes 0xFFFF for DHW temp, the B524 setpoint is
unchanged and the controller fills the read-back temp field with the current
B524 value. Changing B524 immediately updates all B555 read-backs (tightly
coupled — see Section 5.1.1). Writing an explicit temperature (not
0xFFFF) updates B524 to that value and broadcasts to all days (Section 12.13).
0xFFFF means "don't change the setpoint" — a temperature no-op. VR940 uses
0xFFFF to schedule time windows without side-effecting the B524 setpoint.

### 12.12 SC > max_slots Rejection (Helianthus test)

Tests write rejection when SC exceeds the config max_slots value.

```
# DHW max_slots=3, try SC=12:
hex -n 15b555a6ff0200000c000002005e01
Response: 0101  (error 0x01: parameter out of range)

# DHW max_slots=3, try SC=3 (same payload, valid SC):
hex -n 15b555a6ff02000003000002005e01
Response: 0100  (ACK)

# CC max_slots=3, try SC=12:
hex -n 15b555a6ff0300000c00000200ffff
Response: 0101  (error 0x01)

# CC max_slots=3, try SC=4 (max_slots+1):
hex -n 15b555a6ff0300000400000200ffff
Response: 0101  (error 0x01)

# DHW temp boundary: 34°C (below min=35):
hex -n 15b555a6ff02000003000002005401
Response: 0106  (error 0x06: temp out of range)

# DHW temp boundary: 66°C (above max=65):
hex -n 15b555a6ff02000003000002009402
Response: 0106  (error 0x06)

# DHW temp boundary: 35°C exact min:
hex -n 15b555a6ff02000003000002005e01
Response: 0100  (ACK — boundary accepted)

# DHW temp boundary: 65°C exact max:
hex -n 15b555a6ff02000003000002008a02
Response: 0100  (ACK — boundary accepted)
```

**Result:** Controller enforces max_slots, min_temp, and max_temp at write
time. Error 0x01 covers both invalid time values AND SC > max_slots. Error
0x06 is a validation failure that covers temperatures outside the [min, max]
range (boundary values are accepted) and other rejected write shapes
(Section 12.13).

### 12.13 B555→B524 DHW Temperature Coupling (Helianthus test)

Validates that writing an explicit temperature to a B555 DHW slot updates
the B524 DHW setpoint (proving they share state — writes propagate
bidirectionally).

```
# Initial state:
# B524 DHW target_temp_c = 61°C (via MCP semantic DHW read)
# B555 DHW Monday = 00:00-24:00 @ 61.0°C
hex -n 15b555a5ff020000
Response: 0700000018006202  (61.0°C)

# Write 52.0°C to Monday DHW (06:00-18:00, ZONE=0xFF):
hex -n 15b555a6ff02000001060012000802
Response: 0100  (ACK)

# Wait 30s, then read B524 via MCP:
# B524 DHW target_temp_c = 52°C — CHANGED from 61!
# B555 Monday: 06:00-18:00 @ 52.0°C (stored)
hex -n 15b555a5ff020000
Response: 0700060012000802  (52.0°C ✓)

# B555 Tuesday: broadcast updated
hex -n 15b555a5ff020100
Response: 0700000018000802  (52.0°C — propagated to all days)

# Write 61.0°C back to Monday DHW (06:00-18:00):
hex -n 15b555a6ff02000001060012006202
Response: 0100  (ACK)

# B524 DHW target_temp_c = 61°C — RESTORED
# B555 Tuesday: also restored to 61.0°C
hex -n 15b555a5ff020100
Response: 0700000018006202  (61.0°C — broadcast ✓)
```

**Result:** B555 DHW temp and B524 DHW setpoint are **tightly coupled** (shared
state or write-through). Writing an explicit temp via B555 updates B524 and broadcasts to all 7 days
(temp_slots=1). Writing 0xFFFF leaves B524 unchanged. Read-back always
returns the current B524 value — there is no way to distinguish a slot
written with explicit temp from one written with 0xFFFF.

**ZONE=0xFF full-day quirk (0x06):** Writing ZONE=0xFF with exact full-day
(SH=0x00 SM=0x00 EH=0x18 EM=0x00) and an explicit temp (not 0xFFFF)
consistently returns error 0x06, even when the temp is in range (35-65°C).
Quirk matrix (all DHW, temp=52.0°C in range):

| ZONE | Time | Temp | Result |
|------|------|------|--------|
| 0xFF | 00:00-24:00 | 52°C | **0x06** |
| 0x00 | 00:00-24:00 | 52°C | ACK |
| 0xFF | 00:00-23:50 | 52°C | ACK |
| 0xFF | 00:10-24:00 | 52°C | ACK |
| 0xFF | 06:00-18:00 | 52°C | ACK |
| 0xFF | 00:00-24:00 | 0xFFFF | ACK |

The failure is isolated to **exactly** ZONE=0xFF + SH=00 SM=00 EH=18 EM=00
+ explicit temp. The controller likely treats this combination as
"system-wide always-on" and requires 0xFFFF. This does not affect VR940
(which always writes 0xFFFF for DHW) or implementations using ZONE=0x00.

### 12.14 Heating 0xFFFF Rejection (Helianthus test)

Tests whether 0xFFFF is accepted for Heating timers (temp_slots=12).

```
# Z1 Heating Tuesday: write 06:00-18:00 @ 0xFFFF
hex -n 15b555a6000001000106001200ffff
Response: 0101  (error 0x01 — parameter out of range)

# Verify unchanged:
hex -n 15b555a500000100
Response: 070000001800e100  (still 00:00-24:00 @ 22.5°C)
```

**Result:** 0xFFFF is rejected for Heating (temp_slots=12) with error 0x01
(parameter out of range). Unlike DHW, Heating has no sentinel exemption for
0xFFFF — every slot must carry an explicit temperature within [min, max].
This confirms that the "don't change setpoint" semantics of 0xFFFF are
**DHW-specific** (temp_slots=1), not a generic has_temp=1 feature.

**Note (rev 2.12):** Prior to rev 2.12, this test used a malformed `hex -n`
command (16 bytes instead of 15) that shifted field positions and produced
error 0x06. The corrected command confirmed 0xFFFF is still rejected, but
with error 0x01 — the controller classifies it as an invalid parameter, not
a temperature range violation.

### 12.15 ZONE Alias Proof (Helianthus test)

Compares A3/A4/A5 read responses and paired A6 write behavior for DHW and
CC under ZONE=0x00 vs ZONE=0xFF.

**Read aliasing (A3/A4/A5):**

```
# A3 CONFIG_READ — DHW
hex -n 15b555a30002   →  0900030a0a0101234100
hex -n 15b555a3ff02   →  0900030a0a0101234100  (identical)

# A4 SLOTS_READ — DHW
hex -n 15b555a40002   →  09000101010101010100
hex -n 15b555a4ff02   →  09000101010101010100  (identical)

# A5 TIMER_READ — DHW Monday
hex -n 15b555a500020000  →  0700000018005802
hex -n 15b555a5ff020000  →  0700000018005802  (identical)

# A3 CONFIG_READ — CC
hex -n 15b555a30003   →  0900030a000000ffff00
hex -n 15b555a3ff03   →  0900030a000000ffff00  (identical)

# A4 SLOTS_READ — CC
hex -n 15b555a40003   →  09000101010101010100
hex -n 15b555a4ff03   →  09000101010101010100  (identical)

# A5 TIMER_READ — CC Monday
hex -n 15b555a500030000  →  070000001800ffff
hex -n 15b555a5ff030000  →  070000001800ffff  (identical)
```

**Write aliasing (A6 — paired same-payload writes):**

```
# DHW Monday: write 06:00-18:00 @ 52°C with ZONE=0x00, read back from both:
hex -n 15b555a60002000001060012000802  →  0100 (ACK)
hex -n 15b555a500020000  →  0700060012000802  (ZONE=0x00 read: 52°C ✓)
hex -n 15b555a5ff020000  →  0700060012000802  (ZONE=0xFF read: 52°C ✓)

# DHW Monday: write same payload with ZONE=0xFF, read back from both:
hex -n 15b555a6ff02000001060012000802  →  0100 (ACK)
hex -n 15b555a500020000  →  0700060012000802  (ZONE=0x00 read: 52°C ✓)
hex -n 15b555a5ff020000  →  0700060012000802  (ZONE=0xFF read: 52°C ✓)

# CC Monday: write 06:00-18:00 @ 0xFFFF with ZONE=0x00, read back from both:
hex -n 15b555a6000300000106001200ffff  →  0100 (ACK)
hex -n 15b555a500030000  →  070006001200ffff  (ZONE=0x00 read ✓)
hex -n 15b555a5ff030000  →  070006001200ffff  (ZONE=0xFF read ✓)

# CC Monday: write same payload with ZONE=0xFF, read back from both:
hex -n 15b555a6ff0300000106001200ffff  →  0100 (ACK)
hex -n 15b555a500030000  →  070006001200ffff  (ZONE=0x00 read ✓)
hex -n 15b555a5ff030000  →  070006001200ffff  (ZONE=0xFF read ✓)
```

**Result:** All read operations (A3, A4, A5) return identical responses for
ZONE=0x00 and ZONE=0xFF on both DHW and CC. Write operations are also
aliased: the same payload written via ZONE=0x00 and ZONE=0xFF produces
identical read-backs from both ZONE values, for both DHW and CC. The only
known divergence is the ZONE=0xFF + exact full-day + explicit DHW temp
quirk documented in Section 12.13.

## 13. Appendix: ebusd CSV Reference

The authoritative ebusd CSV definitions for B555 timers are in
`15.720.csv` (Vaillant BASV2/VRC720 profile). Key field types:

```csv
# Read format (ebusd labels byte[0] as "ign" — actually timer STATUS):
r,,,Z1HeatingTimer_Monday,...,b555,a500000000,ign,,IGN:1,,,,htm,,HTM,,,,htm_1,,HTM,,,,slottemp,,UIN,10,°C

# Write format:
w,,,Z1HeatingTimer_MondayWrite,...,b555,a600000000,slotindex,,UCH,...,slotcount,,UCH,...,htm,,HTM,...,htm_1,,HTM,...,slottemp,,UIN,10,°C

# Config format:
r,,,Z1HeatingTimer_Config,...,b555,a30000,value,,HEX:9,...

# Slots-per-weekday format (ebusd labels byte[0] as "ign" — actually timer STATUS):
r,,,Z1HeatingTimer_TimeSlotsPerWeekday,...,b555,a40000,ign,,IGN:1,...,slotcount,,UCH,...(x7)...,ign_1,,IGN:1
```

Note: ebusd CSV omits the temperature field from HWC timer reads, but
the wire response includes it (see Section 5.3 examples).

## 14. Revision History

| Rev | Date | Changes |
|-----|------|---------|
| 1.0 | 2026-03-08 | Initial specification from reverse-engineering sessions |
| 1.1 | 2026-03-08 | Full A3 config decode with boundary validation. Error code 0x06 discovered. Time resolution/min_duration confirmed advisory-only. |
| 2.0 | 2026-03-08 | Exhaustive validation pass (T01-T07). A4/A5 byte[0] reclassified from IGN to STATUS. Config byte[5] modeled as temp_slots (3-value: 0/1/12). New error codes: 0x01, 0x03. Hour boundary 0x18. Multi-slot: slot 0 persists, slots 1+ silently discarded through ebusd path. |
| 2.1 | 2026-03-08 | Adversarial review fixes (P1×2, P2×2). Added Section 2.3 notation conventions (wire vs ebusd output). Multi-slot write window rewritten to separate protocol behavior from transport limitation (Section 6.2.1-6.2.4). Byte[5] renamed temp_broadcast→temp_slots with 3-value model (Section 5.1.1). HWC/B524 independence claim weakened to "not validated". |
| 2.2 | 2026-03-08 | Adversarial review fixes (P1×1, P2×3). Cooling temp field changed from "No" to "Not observed (unavailable on test system)" — unavailable config ≠ protocol truth. CC description corrected to "DHW recirculation pump schedule". VR940 bus-hold claim weakened to inference with alternative explanations. Response code 0x00 relabeled from "Success" to "ACK — frame accepted" with persistence caveat. temp_slots=12 cardinality validated with 7-temp per-day independence test (Section 12.9). |
| 2.3 | 2026-03-08 | VR940 CC 21-slot capture: ZONE=0xFF documented as zone-agnostic for CC. Individual-slot write pattern confirmed (SI=N, SC=total per day). Silent timer evidence downgraded to unavailable (same caveat as Cooling). Section 12.9 hex commands made copy-paste safe (contiguous, no spaces). Remaining "success" labels replaced with "ACK". CC name fixed in Section 10.4. |
| 2.4 | 2026-03-08 | VR940 Z1 Heating 84-frame capture (12 slots/day × 7 days, 12 distinct temps): proves temp_slots=12 is intra-day per-slot independence. VR940 DHW 21-slot capture: ZONE=0xFF for DHW (same as CC). B524↔B555 DHW coupling validated: B524 is source of truth, B555 inherits immediately. SC > max_slots → error 0x01 (controller enforces). Error 0x01 reclassified as "parameter out of range" (covers hour ≥ 25 AND SC > max_slots). DHW temp boundary enforcement: 34°C → 0x06, 35°C → ACK, 65°C → ACK, 66°C → 0x06 (min/max inclusive). New wire capture sections: 12.10, 12.11, 12.12. |
| 2.5 | 2026-03-08 | **RETRACTED — superseded by 2.6.** False conclusions from malformed ebusd commands (NN byte included in `hex -n` data, producing wrong opcode on wire). All claims in this revision were incorrect: (1) 0xFFFF is NOT simply "no temperature", (2) ebusd writes DO persist when correctly formatted, (3) source-pairing model does NOT apply to B555. See 2.6 for corrections. |
| 2.6 | 2026-03-08 | **Format bug discovery and full revert of 2.5.** Root cause: ebusd `hex -n` expects `ZZPBSB` + DATA without NN byte (ebusd auto-calculates NN). Including NN as data byte shifted the opcode position — controller ACKed the malformed frame but did not persist. Confirmed by bus log: `3115b555 0d 0ca6...` (NN=0x0D, 0x0C treated as opcode instead of A6). **Corrections:** (1) 0xFFFF restored to context-dependent semantics: "no temperature" for has_temp=0, "inherit from B524" for has_temp=1. (2) DHW CAN store explicit temperature independently — validated by writing 45°C via ebusd (correct format), read-back confirmed 45°C (not B524 setpoint of 61°C). (3) temp_slots=1 broadcast re-confirmed — writing 45°C to Monday propagated to all 7 days. (4) ebusd single-slot writes confirmed reliable from any source. (5) All false caveats removed from Sections 12.2, 12.4, 12.5, 12.8, 12.9. Section 6.3 rewritten with format warning. |
| 2.7 | 2026-03-08 | **B555↔B524 DHW register identity proven.** Writing 52°C to DHW via B555 changed B524 `target_temp_c` from 61→52°C; writing 61°C restored it. They are the same register — B555 temp is not independent storage. 0xFFFF recharacterized from "inherit from B524" to "don't change setpoint" (temperature no-op). Read-back is lossy: no way to distinguish explicit temp from 0xFFFF after write. Section 7 ZONE contradiction fixed: ebusd CSV uses ZONE=0x00 for HWC/CC but VR940 uses 0xFF — both are accepted (aliased). ZONE=0xFF + 00:00-24:00 + explicit temp → error 0x06 documented as controller quirk (Section 12.13). myVaillant confirmed to use 10-minute resolution for all 4 visible schedule types. New test: Section 12.13. |
| 2.8 | 2026-03-08 | **Adversarial review fixes (P1×2, P2×1, P3×2) + 3 targeted tests.** (1) 0xFFFF narrowed from generic `has_temp=1` to DHW-specific — Heating rejects 0xFFFF with 0x06 (treated as 6553.5°C > max=30°C, no sentinel exemption; Section 12.14). (2) Error 0x06 broadened from "temp out of range" to "validation failure" — also fires on ZONE=0xFF + exact full-day + explicit DHW temp. (3) ZONE aliasing weakened from unconditional to conditional — reads fully aliased, writes diverge on one specific shape. (4) Stale "inherit from B524" wording fixed in temp_slots=1 row. (5) Section 7 citation fixed (12.10→12.11). (6) ZONE range in A5/A6 field tables updated to include 0xFF. (7) Full 0x06 quirk matrix (6 test points; Section 12.13). (8) ZONE alias proof: A3/A4/A5 identical for ZONE=0x00 vs 0xFF on DHW and CC (Section 12.15). New tests: Sections 12.14, 12.15. |
| 2.9 | 2026-03-08 | **Evidence hygiene pass (P2×2, P3×2).** (1) Spaced hex commands in Sections 12.14/12.15 made contiguous (copy-paste-safe). (2) CC A4/A5 alias test data added to Section 12.15 — now fully proves A3/A4/A5 aliasing for CC, not just A3. (3) Stale "temperatures strictly outside [min, max]" wording in Section 12.12 replaced with "validation failure" consistent with Section 5.4. (4) CC ZONE=0xFF write made self-contained in Section 7 — inline write+readback replaces "rev 2.3 notes" citation. |
| 2.10 | 2026-03-08 | **Claim calibration (P2×2, P3×1).** (1) "Same register" weakened to "tightly coupled (shared state or write-through)" across Sections 5.1.1, 12.13 — external observation cannot distinguish register identity from controller-side mirror/sync. (2) ZONE write aliasing now directly demonstrated: paired same-payload A6 writes with ZONE=0x00 and ZONE=0xFF produce identical read-backs for both DHW (06:00-18:00 @ 52°C) and CC (06:00-18:00 @ 0xFFFF). Section 12.15 expanded with write proof. (3) Section 7 citation fixed: "CC write verified in Section 12.15" → "inline below". |
| 2.11 | 2026-03-08 | **Wording hygiene (P2×1, P3×1) + file relocation.** (1) Three remaining "same register" / "same underlying register" instances replaced with "tightly coupled" in Sections 5.3, 12.8, and 12.11 — now consistent with the 2.10 calibration. (2) Section 12.11 intro changed from "Controller stored existing DHW temp" to "Read-back shows current B524 DHW temp" — matches the settled model that 0xFFFF is a write-time no-op and A5 materializes the current B524 value, not a literal stored representation. (3) File moved from `specs/` to `protocols/` alongside sibling protocol documents. |
| 2.12 | 2026-03-08 | **P1 hex command audit + error code correction.** Mechanical scrub of every `hex -n` example against declared opcode byte counts. (1) Three A6 commands (Sections 12.7, 12.14) had 16 bytes instead of 15 — extra `00` byte shifted field positions within the A6 frame (distinct from the 2.5 NN-inclusion bug which shifted the opcode itself). Fixed to 30 hex chars (15 bytes). (2) Eighteen A5 commands (Sections 7, 12.13, 12.14, 12.15) had trailing `00` byte(s) — controller ignored extra for reads but format was inconsistent. Fixed to 16 hex chars (8 bytes). (3) **Section 12.14 error code changed from 0x06 to 0x01**: re-running the Heating 0xFFFF test with correctly-formatted hex revealed the controller returns error 0x01 (parameter out of range), not 0x06. The conclusion (0xFFFF rejected) remains valid but the classification differs — 0x01 indicates the controller treats 0xFFFF as an invalid parameter, not a temperature range violation. Updated in Sections 5.3, 5.4, 8.2, 12.14. (4) Canonical filename normalized to `ebus-vaillant-b555-timer-protocol.md` for naming consistency. |
| 2.13 | 2026-03-08 | **Final wording pass (P2×1, P3×1).** (1) Section 5.1 min/max enforcement rule narrowed: numeric temp violations yield 0x06, but not all temp-field rejections use 0x06 — Heating 0xFFFF is rejected with 0x01 (Section 12.14). (2) Rev 2.12 changelog clarified: A6 field-shift bug described as "shifted field positions within the A6 frame" with explicit note distinguishing it from the 2.5 NN-inclusion bug that shifted the opcode itself. |
| 2.14 | 2026-03-08 | **Straggler hex audit (P2×1).** Two `hex` (with-NN) A5 commands in Section 12.5 had 6 data bytes after NN=0x05 (trailing `00`). ebusd used NN to bound the read so results were correct, but format was inconsistent. Fixed to 9 bytes (ZZ+PB+SB+NN+5 data). Full audit of all 19 `hex` commands now passes alongside the 76 `hex -n` commands. |
| 2.15 | 2026-04-14 | **Scope correction + enrichment integration.** (1) VRC700 removed from §1 scope -- B555 is VRC720-family only (BASV0/BASV2/BASV3/CTLV0/CTLV2/CTLV3/CTLS2). VRC700 uses B524 opcodes 0x03/0x04 for timers. New §1.0 device-binding table added. (2) HC=0x04 renamed from "Silent" to "NoiseReduction (Silent)" with dual-name note and B508 cross-reference. (3) §9 rewritten to explain B524 timer opcodes are VRC700-only (not "different subsystem"), with cross-reference to B524 §4.4 channel map. Source: FINAL-B524-B555-B507-B508.md, CROSSCHECK-B555-misc.md. |
| 2.16 | 2026-04-14 | **FSM appendix + cross-protocol gate.** Added Appendix A: noise_reduction FSM (B555 HC=0x04 -> B508 broadcast -> B509 EHP 0xA901) and B555<->B524 DHW temperature coupling gate. Source: GATES-semantic-fsms.md, GATES-protocol-level.md. |

---

## Appendix A: Semantic FSMs and Cross-Protocol Gates

> Source: `GATES-semantic-fsms.md` Section 1.7, `GATES-protocol-level.md` Sections 5-6.

### A.1 `noise_reduction` FSM (HC=0x04 -> B508 -> B509)

B555 schedule type HC=0x04 (NoiseReduction/Silent) triggers a cross-protocol broadcast chain:

1. B555 HC=0x04 timer slot starts on BASV2/VRC720
2. B508 broadcast emitted (ZZ=0xFE, ID=0x02, State1/State2 = on/off)
3. EHP00 (0x08) updates B509 registers: `0xA901` NoiseReduction (yesno) + `0x2401` NoiseReductionFactor (%)

**B509 register `0xA901` state table:**

| Value | State | Description |
|-------|-------|-------------|
| 0x00 | `off` | Noise reduction inactive; full-rated compressor/fan operation |
| 0x01 | `on` | Noise reduction active; compressor and fan speed capped per `NoiseReductionFactor` |

**Transitions:** off -> on (B508 broadcast State1=0x01, triggered by B555 HC=0x04 slot start). on -> off (B508 broadcast State1=0x00, slot end).

**Gate condition:** B509 registers `0xA901` and `0x2401` on EHP00 are only meaningful when HC=0x04 is configured and the timer is active.

**Confidence:** HIGH for register; MEDIUM-HIGH for B508 broadcast chain (wire format clear, no Helianthus live capture confirmation).

### A.2 B555 <-> B524 DHW Temperature Coupling

B555 timer temperature writes and B524 DHW setpoint share state. This creates a bidirectional gate:

| Write path | Effect |
|-----------|--------|
| B555 TIMER_WRITE with explicit temp (e.g., 52.0C to DHW Monday) | B524 `OP=0x02, GG=0x01, RR=0x0006` DHW target_temp_c changes immediately |
| B524 write to DHW setpoint register | All B555 DHW timer slots reflect the new value on read-back |
| B555 TIMER_WRITE with 0xFFFF (temp no-op) | B524 setpoint unchanged; slots read back current B524 value |

B555 DHW schedule reads are lossy -- no way to distinguish a slot written with an explicit temperature from one written with 0xFFFF. Both read back the current B524 setpoint.
