# Wolf eBUS Protocols (MF=0x19)

> **Confidence:** MEDIUM -- single fork (`ulda/ebusd-configuration`), no live validation against a Wolf device on the Helianthus bus. All findings are candidate mappings derived from ebusd CSV configuration files, not verified protocol specifications.
>
> **Source fork:** `ulda/ebusd-configuration` (commit `6ef5eb6`, last push 2026-04-13)
> **Source files:** `ebusd-22.4.x/de/wolf/all.csv`, `ebusd-22.4.x/de/wolf/_templates.csv`

---

## Table of Contents

- [1. Manufacturer Overview](#1-manufacturer-overview)
- [2. Broadcast Protocols](#2-broadcast-protocols)
  - [2.1 PBSB 0503 -- Burner Controller Status](#21-pbsb-0503----burner-controller-status)
  - [2.2 PBSB 0504 -- Modulation Actual](#22-pbsb-0504----modulation-actual)
  - [2.3 PBSB 0507 -- Heat Request Status (10-State FSM)](#23-pbsb-0507----heat-request-status-10-state-fsm)
  - [2.4 PBSB 0800 -- Boiler Setpoint Transfer](#24-pbsb-0800----boiler-setpoint-transfer)
- [3. Register Access (5022/5023)](#3-register-access-50225023)
  - [3.1 Wire Format](#31-wire-format)
  - [3.2 Register Table](#32-register-table)
- [4. Solar Extensions (5014, 5017, 5018)](#4-solar-extensions-5014-5017-5018)
  - [4.1 PBSB 5014 -- Solar Status + Mixer Setpoint](#41-pbsb-5014----solar-status--mixer-setpoint)
  - [4.2 PBSB 5017 -- Solar Pump + Temperatures](#42-pbsb-5017----solar-pump--temperatures)
  - [4.3 PBSB 5018 -- Solar Power / Yield](#43-pbsb-5018----solar-power--yield)
- [5. PB=0x50 Disambiguation](#5-pb0x50-disambiguation)
- [6. Helianthus Relevance](#6-helianthus-relevance)

---

## 1. Manufacturer Overview

| Field | Value |
|-------|-------|
| Manufacturer ID | `0x19` |
| Boiler eBUS address | `0x08` (primary burner controller) |
| Solar module eBUS address | `0x50` |
| Product range | Residential / light-commercial boilers (Germany/Austria) |
| eBUS address slots | Same as Vaillant (0x08 boiler, 0x50 solar) -- physically incompatible on the same bus |

Wolf boilers occupy address `0x08` (burner controller) and Wolf solar modules
occupy address `0x50`. Separately, Wolf CSVs also use manufacturer-specific
primary command `PB=0x50`; that command byte has the same numeric value as the
solar module address but is a different frame field. Neither value is a second
manufacturer ID; Wolf identity still comes from `0x07 0x04` manufacturer byte
`0x19`.

All Wolf CSV material lives in `ebusd-22.4.x/de/wolf/all.csv` and `ebusd-22.4.x/de/wolf/_templates.csv` of the ulda fork.

---

## 2. Broadcast Protocols

The `0x05 xx` and `0x08 xx` PBSBs below are **standard eBUS
Application Layer command allocations**, not Wolf-proprietary command numbers.
Wolf implements these standard service slots with Wolf-specific payload
profiles derived from the ulda CSV files.

Cross-reference:
- `0x05 0x03`: standard Burner Control, operational data from burner to
  controller; see [`../ebus-services/ebus-service-05h.md`](../ebus-services/ebus-service-05h.md).
- `0x05 0x04`: standard Burner Control, control-stop response allocation; the
  Wolf CSV maps it to a modulation payload, so treat the payload as
  Wolf-specific until live traces prove spec parity.
- `0x05 0x07`: standard Burner Control, channel-B operational data from
  controller to burner; Wolf extends the request-state enum with additional
  composite values.
- `0x08 0x00`: standard Controller-to-Controller target-values allocation; Wolf
  uses a shorter boiler-setpoint transfer profile than the generic service table.

Do not infer proprietary status from absence in john30 Vaillant-oriented CSVs.
The proprietary part here is the Wolf payload/profile, not the PBSB allocation.

### 2.1 PBSB 0503 -- Burner Controller Status

**Feuerungsautomatstatus (Burner Controller Status)**

- **Type:** `b` (broadcast) and `w` (write)
- **ID:** `01`

#### Wire Format

```
QQ ZZ 05 03 NN [block_number:0x01] [status:UCH:1B] [stellgrad:UCH:1B] [kesseltemp:1B...] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 0 | block_number | UCH (1B) | Constant `0x01`; matches standard `0x05 0x03` block-1 framing |
| 1 | status | UCH (1B) | Burner automaton state, transmitted as raw hex |
| 2 | stellgrad | UCH (1B) | Boiler output modulation; Wolf thermae send `0xFF` (dummy -- "Gastherme Ersatzwert: FF") |
| 3+ | kesseltemp | 1B+ | Boiler supply temperature |

**Evidence:** ulda -> `ebusd-22.4.x/de/wolf/all.csv` [line 3](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L3) (broadcast), [line 10](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L10) (write)

**Standard-service note:** PBSB `0503` is the standard Burner Control
operational-data slot for burner-to-controller data. The Wolf CSV `ID=01`
corresponds to the block-1 selector in the standard payload.

**Falsifiable:** Wolf gas thermae should always transmit `0xFF` in byte 2 of PBSB 0503. A non-`0xFF` value indicates a different Wolf device variant (e.g., oil boiler with real modulation).

---

### 2.2 PBSB 0504 -- Modulation Actual

**Stellgrad Ist (Modulation Actual)**

- **Type:** `w` (write/broadcast)
- **ID:** none (`-`)

#### Wire Format

```
QQ ZZ 05 04 NN [stellgradist:percent0:1B] [stellgradmax:percent0:1B] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1 | stellgradist | percent0 (1B) | Actual modulation percentage |
| 2 | stellgradmax | percent0 (1B) | Maximum modulation percentage |

**Evidence:** ulda -> all.csv [line 11](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L11)

**Standard-service note:** PBSB `0504` is allocated by the standard Burner
Control service as the control-stop response. The Wolf CSV names and shapes it
as `Stellgrad Ist` with two percent bytes, so the safe interpretation is
"standard PBSB allocation, Wolf-specific modulation payload" rather than
"Wolf-proprietary PBSB".

**Falsifiable:** Both bytes should be in range 0--100 (percent0 encoding). Values above 100 indicate decode error or a different wire type.

---

### 2.3 PBSB 0507 -- Heat Request Status (10-State FSM)

**Statuswaermeanforderung (Heat Request Status, Regulator -> Burner)**

This is the heat demand message from the Wolf regulator/sender at address
`0x50` to the burner controller at address `0x08`. The 10-state enum is
substantially richer than a standard binary heat-request signal.

- **Type:** `w` (write)
- **ID:** none (`-`)

#### Wire Format

```
QQ ZZ 05 07 NN [status:UCH:1B] [kesselsolltemp:1B] [solldruck:...] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1 | status | UCH (1B) | Heat request state (see FSM table below) |
| 2 | kesselsolltemp | 1B | Boiler setpoint temperature |
| 3+ | solldruck | variable | Target pressure / additional parameters |

#### Heat Request FSM -- 10 Named States

| Value | Name (German) | Meaning |
|-------|---------------|---------|
| `0x00` | aus | Off |
| `0x01` | keine | No demand |
| `0x44` | Reglerstop_stufig | Stepped regulator stop |
| `0x55` | Brauchwasser | DHW demand |
| `0x66` | Brauchwasser_Reglerstop | DHW + regulator stop |
| `0xAA` | Heizen | Heating demand |
| `0xBB` | Brauchwasser_Heizen | DHW + heating |
| `0xCC` | Emissionskontrolle | Emission test mode |
| `0xDD` | TUeV | Inspection mode (TUeV) |
| `0xEE` | Reglerstop | Regulator stop |

**Evidence:** ulda -> all.csv [line 13](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L13)

**Standard-service note:** PBSB `0507` is the standard Burner Control channel-B
operational-data slot for controller-to-burner data. Wolf reuses the standard
first-byte heat-request position but extends the enum beyond the generic
standard values with composite states such as `0x66` and `0xBB`.

**Falsifiable:** Status byte value should always be one of the 10 listed hex values. Any other value (e.g. `0x11`, `0x33`) indicates an undocumented state or parsing error.

---

### 2.4 PBSB 0800 -- Boiler Setpoint Transfer

**Kesselsollwert (Boiler Setpoint Transfer)**

- **Type:** `b` (broadcast) and `w;b` (write + broadcast)
- **ID:** none (`-`)

#### Wire Format

```
QQ ZZ 08 00 NN [kesselsolltemp:temp2:2B LE] [leistungszwang:1B] [status:1B] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1--2 | kesselsolltemp | temp2 (2B LE) | Boiler setpoint; temp2 = degrees C x 16, signed 16-bit little-endian (e.g. `0x0280` = 40.0 degrees C) |
| 3 | leistungszwang | UCH (1B) | Forced output / power demand byte |
| 4 | status | UCH (1B) | Status byte |

**Evidence:** ulda -> all.csv [line 4](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L4) (broadcast), [line 27](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L27) (write+broadcast)

**Standard-service note:** PBSB `0800` is the standard
Controller-to-Controller target-values allocation. The Wolf profile documented
here is shorter than the generic standard payload and should be decoded as a
Wolf-specific profile of that standard command, not as a manufacturer-specific
PB family.

**Falsifiable:** kesselsolltemp decoded as temp2 (divide by 16) should yield a plausible boiler setpoint, typically 40--90 degrees C. Raw value outside `0x0280`--`0x05A0` would indicate a different encoding.

---

## 3. Register Access (5022/5023)

Service parameter read/write using 3-byte CRC-addressed IDs. Distinct from
Kromschroeder's `5000`/`5001` use of the same manufacturer-specific primary
command byte (`PB=0x50`) with different secondary opcodes.

### 3.1 Wire Format

```
Read request  (5022): [id_lo:1B] [id_hi:1B] [param_idx:1B]
Read response (5022): [value:UIN:2B] or [value:UIN/10:2B]
Write command (5023): [id_lo:1B] [id_hi:1B] [value:UIN or UIN/10] [HEX:4]
```

The write ID is the **first 2 bytes** of the 5022 read ID; the third byte (param_idx) is omitted on writes. The 2-byte ID prefix appears to be a CRC over the parameter index -- the specific algorithm is not recoverable from the CSV alone (requires Wolf firmware source).

### 3.2 Register Table

25 readable registers, 14 writable. Writable registers are marked **W** in the Mode column.

> **Naming note:** Tables use ebusd CSV / TypeSpec parameter names in their original German. snake_case canonical names pending normalization.

| ID bytes | Mode | Name | Type | Range / Notes | Evidence (all.csv line) |
|----------|------|------|------|---------------|-------------------------|
| `842200` | R+W | hg01 hysterese_vorlauf | UIN/10 | 5--30 K -- flow hysteresis | 41/42 |
| `295a01` | R+W | hg02 gebl_unten | UIN | 25--100% -- blower minimum RPM | 43 |
| `cd5901` | R | hg03 gebl_oben_ww | UIN | 25--100% -- blower max DHW | 44 |
| `1d3f01` | R | hg04 gebl_oben_hz | UIN | 1--100% -- blower max heating | 45 |
| `254101` | R+W | hg06 betriebsart | UIN | 0--2 -- pump mode | 46/47 |
| `c14201` | R+W | hg07 pumpen_nachlauf | UIN | 0--30 min -- pump rundown | 48/49 |
| `de8402` | R+W | hg08 max_vorlauf_temp | UIN/10 | 40--90 degrees C -- max flow setpoint | 50/51 |
| `9d4301` | R+W | hg09 taktsperre | UIN | 1--30 min -- anti-cycling time | 52/53 |
| `ad7801` | R | hg10 ebus_addr | UIN | eBUS bus address | 54 |
| `794001` | R+W | hg15 hysterese_speicher | UIN/10 | 1--30 K -- storage hysteresis | 57/58 |
| `b95501` | R+W | hg16 pumpenleistung_hk_min | UIN | 20--100% -- HC pump min | 59/60 |
| `5d5601` | R+W | hg17 pumpenleistung_hk_max | UIN | 20--100% -- HC pump max | 61 |
| `201f00` | R+W | hg21 kessel_min | UIN/10 | Boiler minimum temperature | 63/64 |
| `f42700` | R+W | hg22 kessel_max | UIN/10 | Boiler maximum temperature | 65/66 |
| `f57001` | R | hg73 io_istwert | UIN | IO current value | 67 |
| `d5f601` | R | hg74 gebl_drehzahl | UIN | Blower RPM actual | 68 |
| `316c01` | R | hg75 ww_durchsatz | UIN | DHW flow rate | 69 |
| `662802` | R | hours_hg9x betriebsstunden_netz | UIN | Mains operating hours | 70 |
| `de2a02` | R | hours_hg90 betriebsstunden_brenner | UIN | Burner operating hours | 71 |
| `aa2602` | R | starts_hg91 brennerstarts | UIN | Burner start count | 72 |
| `b80200` | R | temp_vorlauf_soll | UIN/10 | Flow temperature setpoint | 73 |
| `280d00` | R | temp_vorlauf_ist | UIN/10 | Flow temperature actual | 74 |
| `241600` | R | temp_ruecklauf_ist | UIN/10 | Return temperature actual | 75 |
| `e40300` | R | temp_warmwasser_soll | UIN/10 | DHW setpoint | 76 |
| `cc0e00` | R | temp_warmwasser_ist | UIN/10 | DHW temperature actual | 77 |
| `6d6d01` | R | status_pwm_pumpe | UIN | PWM pump status | 78 |

**Evidence (all registers):** ulda -> `ebusd-22.4.x/de/wolf/all.csv` [lines 41--78](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv)

**Falsifiable claims:**

- hg10 ebus_addr should return the device's own eBUS address (`0x08` for the primary burner). A value outside 0--254 indicates decode error.
- hg74 gebl_drehzahl is raw RPM (UIN, no divisor). A value above 6000 is plausible for a Wolf blower; above 10000 suggests a wrong type (UIN/10 would need to be applied).
- hg75 ww_durchsatz (DHW flow rate) should correlate to zero when DHW is not active. Persistent non-zero value during standby = different encoding.
- Write round-trip test: write hg06 betriebsart = 1, then read back -- should return 1.

---

## 4. Solar Extensions (5014, 5017, 5018)

All three PBSBs use manufacturer-specific `PB=0x50` and type `w`
(write/broadcast from the Wolf solar module to the bus). They carry real-time
solar operational data. The sender address is also commonly `0x50`, but that is
separate from the `PB=0x50` command byte.

### 4.1 PBSB 5014 -- Solar Status + Mixer Setpoint

**StatusSolar + Mischersolltemp**

#### Wire Format

```
QQ ZZ 50 14 NN [status:HEX:1B] [IGN:1B] [mischersolltemp:...] [raumtemp:...] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1 | status | HEX (1B) | Solar status raw hex byte |
| 2 | IGN | 1B | Ignored byte (padding) |
| 3+ | mischersolltemp | variable | Mixer setpoint temperature |
| -- | raumtemp | variable | Room temperature |

**Evidence:** ulda -> all.csv [line 35](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L35)

**Falsifiable:** The `IGN` byte should be constant regardless of solar state changes. If it varies, it carries information and is not padding.

---

### 4.2 PBSB 5017 -- Solar Pump + Temperatures

**SolarPumpe + Temperaturen**

#### Wire Format

```
QQ ZZ 50 17 NN [pumpe:UCH:1B] [IGN:1B] [kollektortemp:...] [wwsolartemp:...] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1 | pumpe | UCH (1B) | Pump state: `0xBC` = off, `0xBD` = on (not a standard boolean) |
| 2 | IGN | 1B | Ignored byte |
| 3+ | kollektortemp | variable | Solar collector temperature |
| -- | wwsolartemp | variable | Solar DHW storage temperature |

**Evidence:** ulda -> all.csv [line 36](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L36)

**Falsifiable:** Pump byte should only ever be `0xBC` or `0xBD`. Any other value (e.g. `0x00`, `0x01`) indicates a different pump encoding convention on that Wolf variant.

---

### 4.3 PBSB 5018 -- Solar Power / Yield

**Solarleistung (Solar Power / Yield)**

#### Wire Format

```
QQ ZZ 50 18 NN [leistung:D2B:2B signed] [ertraghigh:1B] [ertragsummelow:1B] CRC
```

| Byte | Field | Type | Description |
|------|-------|------|-------------|
| 1--2 | leistung | D2B (2B signed) | Solar power output; D2B = signed 16-bit / 256 (1/256 W precision) |
| 3 | ertraghigh | UCH (1B) | Daily yield accumulator high byte |
| 4 | ertragsummelow | UCH (1B) | Cumulative yield sum low byte |

**Evidence:** ulda -> all.csv [line 37](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L37)

**Falsifiable:** leistung decoded as D2B should be negative at night (heat loss from collector) and positive during solar gain. A perpetually positive value suggests D2C (divide by 16) was used instead of D2B (divide by 256).

---

## 5. PB=0x50 Disambiguation

`PB=0x50` is a manufacturer-specific primary command byte used by multiple
vendor profiles. It is not itself a manufacturer ID. Wolf devices are identified
by the standard `0x07 0x04` manufacturer byte `0x19`; Kromschroeder material
uses different identity metadata while also defining `PB=0x50` opcodes. The
opcode spaces are non-overlapping:

| PBSB | Manufacturer | Role |
|------|-------------|------|
| 5000 | Kromschroeder | Memory read request |
| 5001 | Kromschroeder | Memory read response / write |
| 500A | Kromschroeder | Unknown (block/erase?) |
| 5014 | Wolf | Solar status + mixer setpoint |
| 5017 | Wolf | Solar pump + temperatures |
| 5018 | Wolf | Solar power/yield |
| 5022 | Wolf | Service parameter read |
| 5023 | Wolf | Service parameter write |

No physical overlap is possible in practice: Wolf's solar MC at address `0x50`
and Kromschroeder's em1 at address `0x50` cannot co-exist on the same eBUS
ring. ebusd disambiguates profiles through the standard identification service
(`PBSB 0704`) manufacturer byte and device ID, not by treating `PB=0x50` as a
manufacturer ID.

See also: [`kromschroeder-5000.md`](../weishaupt/kromschroeder-5000.md) for the Kromschroeder side of this disambiguation.

---

## 6. Helianthus Relevance

**Architectural feasibility: yes. Near-term priority: no.**

- Wolf boilers occupy the same eBUS address slots as Vaillant (0x08, 0x50) -- physically incompatible on the same bus.
- The 5022/5023 service parameter set (25 reads, 14 writes) covers the same operational surface as Helianthus reads from Vaillant via B524/B555: temperatures, pump states, blower RPM, flow rate, burner hours/starts. This is the closest non-Vaillant analogue to the Helianthus semantic adapter.
- The `0503`/`0504`/`0507` messages use standard eBUS Burner Control PBSB
  allocations with Wolf-specific payload profiles and provide real-time burner
  status equivalent to the Vaillant BAI00 broadcasts.
- **Blocker:** Wolf MF=0x19 requires a separate semantic adapter. No code path is shared with Vaillant MF=0xB5.
- **Recommendation:** Document as "manufacturer expansion track candidate." No issues to open now.

---

## Appendix: Data Type Reference

| Type | Description |
|------|-------------|
| UCH | Unsigned 8-bit integer (0--255) |
| UIN | Unsigned 16-bit integer (little-endian) |
| UIN/10 | UIN divided by 10 to get physical value |
| HEX | Raw hex byte |
| D2B | Signed 16-bit fixed-point, resolution 1/256 |
| temp2 | Signed 16-bit, value = raw / 16 (degrees C) |
| percent0 | Unsigned 8-bit, 0--100% |
| IGN | Ignored / padding byte |

## Appendix: Evidence Index

| Finding | File | Line(s) | URL |
|---------|------|---------|-----|
| PBSB 0503 burner status | all.csv | 3, 10 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L3) |
| PBSB 0504 modulation | all.csv | 11 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L11) |
| PBSB 0507 heat request FSM | all.csv | 13 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L13) |
| PBSB 0800 boiler setpoint | all.csv | 4, 27 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L4) |
| PBSB 5014 solar status | all.csv | 35 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L35) |
| PBSB 5017 solar pump | all.csv | 36 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L36) |
| PBSB 5018 solar power | all.csv | 37 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv#L37) |
| 5022/5023 registers (25R/14W) | all.csv | 41--78 | [link](https://github.com/ulda/ebusd-configuration/blob/6ef5eb6cd12548f7b0e33386bef56838594e0037/ebusd-22.4.x/de/wolf/all.csv) |
