# Kromschroeder/Weishaupt eBUS Protocols (MF=0x50/0xC5)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

> **Confidence:** LOW -- TypeSpec-only source (`aghulas/ebusd-configuration`), no eBUS wire data, no live validation. Archive-quality research document; no Helianthus action items arise from this protocol family.
>
> **Source fork:** `aghulas/ebusd-configuration` (commit `90c509d`, last push 2026-03-13)
> **Source files:** `src/kromschroeder/*.tsp` (TypeSpec source), `tsp-output/@ebusd/ebus-typespec/` (compiled CSV)

---

## Table of Contents

- [1. Manufacturer Overview](#1-manufacturer-overview)
- [2. TypeSpec Toolchain](#2-typespec-toolchain)
- [3. RAM/EEPROM Access (5000/5001)](#3-rameeprom-access-50005001)
  - [3.1 Architecture](#31-architecture)
  - [3.2 Addressing Scheme (CRC-Obfuscated)](#32-addressing-scheme-crc-obfuscated)
  - [3.3 Wire Format](#33-wire-format)
  - [3.4 Device Address Table](#34-device-address-table)
  - [3.5 Selected RAM Registers](#35-selected-ram-registers)
- [4. Secondary Channel (0902/0903)](#4-secondary-channel-09020903)
- [5. PBSB 500A (Unknown Role)](#5-pbsb-500a-unknown-role)
- [6. PB=0x50 Disambiguation](#6-pb0x50-disambiguation)
- [7. Helianthus Relevance](#7-helianthus-relevance)

---

## 1. Manufacturer Overview

| Field | Value |
|-------|-------|
| Kromschroeder manufacturer ID | `0x50` |
| Weishaupt manufacturer ID | `0xC5` |
| Product range | Industrial/commercial burner management (BCSi, BCU series); Weishaupt residential/commercial burners |
| Total registers (aghulas fork) | **20,973** across 56 device files |
| Relationship | Separate companies sharing the same eBUS burner management firmware family. Weishaupt is a Honeywell brand. |

Kromschroeder (MF=0x50) and Weishaupt (MF=0xC5) are covered under a unified TypeSpec model in the aghulas fork -- the largest single-manufacturer eBUS dataset found in the fork survey.

**Cross-reference:** For Weishaupt solar controller protocols, see [`weishaupt-wrsol.md`](./weishaupt-wrsol.md) in this directory (sourced from official Weishaupt documentation, not the aghulas fork).

---

## 2. TypeSpec Toolchain

The aghulas fork uses ebusd's TypeSpec compiler (`.tsp` source files compiled to CSV), not hand-written CSV. This is the most technically sophisticated ebusd contribution in the fork survey and represents the correct model for any future large-scale manufacturer support in ebusd-configuration.

| Component | Path |
|-----------|------|
| Source files | `src/kromschroeder/*.tsp` |
| Compiled output | `tsp-output/@ebusd/ebus-typespec/` |
| Weishaupt output | `tsp-output/@ebusd/ebus-typespec/weishaupt/` |

---

## 3. RAM/EEPROM Access (5000/5001)

The dominant protocol. Direct byte-level access to the burner management controller's RAM and EEPROM address space.

### 3.1 Architecture

- **PB=0x50** = Kromschroeder manufacturer/device primary byte
- **SB=0x00** = memory read request (PBSB 5000)
- **SB=0x01** = memory read response / write (PBSB 5001)

### 3.2 Addressing Scheme (CRC-Obfuscated)

IDs are 3 bytes with obfuscated addressing:

```
ID: [B0] [B1] [B2]
     |    |    |
     |    |    address low byte
     |    address high nibble (encodes page)
     CRC/obfuscation byte derived from address
```

B1 encodes the high nibble of a 12-bit address:
- `0x01xx` = RAM page 1 (most operational registers)
- `0x02xx` = Konstanten/factory constants

B0 is an 8-bit checksum or nibble-swap obfuscation; the specific algorithm is embedded in the TypeSpec source and not recoverable from the compiled CSV alone.

#### Observed Examples

| ID hex | Address | Register name |
|--------|---------|---------------|
| `580104` | 0x0004 | Divi |
| `590105` | 0x0005 | Aufruf_von |
| `7C0120` | 0x0020 | BYTE_20 |
| `DC0180` | 0x0080 | IRAEPKANF |
| `6802D0` | 0x00D0 | (Konstanten region) |

### 3.3 Wire Format

```
Read request  (5000): [id_B0:1B] [id_B1:1B] [id_B2:1B]                (3-byte ID)
Read response (5001): [value:1-2B]
Write         (5001): [id_B0:1B] [id_B1:1B] [id_B2:1B] [value:1-2B]
```

### 3.4 Device Address Table

9 device addresses confirmed across the aghulas fork:

| File | Device ID | eBUS Address | Type |
|------|-----------|-------------|------|
| `08..bc1.tsp` | bc1 | `0x08` | Burner controller 1 (BCSi-series) |
| `18..bc2.tsp` | bc2 | `0x18` | Burner controller 2 |
| `15..ka.tsp` | ka | `0x15` | Kessel-Automat (boiler automation controller) |
| `35..fs1.tsp` | fs1 | `0x35` | Flame sensor module 1 |
| `50..em1.tsp` | em1 | `0x50` | Extension module 1 |
| `51..em2.tsp` | em2 | `0x51` | Extension module 2 |
| `52..em3.tsp` | em3 | `0x52` | Extension module 3 |
| `f5..fs2.tsp` | fs2 | `0xF5` | Flame sensor module 2 |
| `f6..sc.tsp` | sc | `0xF6` | System controller (Weishaupt-side) |

**Evidence:** [aghulas, 08..bc1.tsp](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/src/kromschroeder/08..bc1.tsp); address table confirmed via F-aghulas.md lines 454--470.

**Note:** Weishaupt-branded output `tsp-output/@ebusd/ebus-typespec/weishaupt/f6..sc.csv` (558 rows) uses the same 5000/5001 space for the `sc` device at 0xF6. Weishaupt model-numbered files (`WH00928.tsp`, `WH01928.tsp`, etc.) have no fixed eBUS address -- matched by model/version at runtime.

**Address conflicts with Vaillant:**
- `0x08` (bc1) = Vaillant BAI00 burner controller
- `0x15` (ka) = Vaillant BASV2/CTLV2
- `0x50` (em1) = Vaillant solar module address

Physically impossible to co-exist on a Vaillant eBUS installation.

### 3.5 Selected RAM Registers

Representative subset from `0000360.tsp` (the shared register include file). Full register set contains thousands of entries.

> **Naming note:** Tables use ebusd CSV / TypeSpec parameter names in their original German. snake_case canonical names pending normalization.

#### Operational Registers (RAM Page 1)

| Address | Name | Description |
|---------|------|-------------|
| `0x0004` | Divi | Divider value |
| `0x0005` | Aufruf_von | State machine caller |
| `0x0006` | Bezeichnung_INr | Designation / internal number |
| `0x0007` | Drehzahl | Fan/blower RPM |
| `0x0023` | ERR_MERK | Error marker |
| `0x0026` | EBUS_BITS | eBUS status bits |
| `0x0055` | ICL20SEC | 20-second interval clock |
| `0x0056` | ICL1HRS | 1-hour interval clock |

#### Temperature Registers

| Address | Name | Description |
|---------|------|-------------|
| `0x005C` | TVISTAD | Flow temperature actual (damped) |
| `0x005D` | TWWISTAD | DHW temperature actual (damped) |
| `0x005E` | TAUSSEN | Outside temperature |
| `0x005F` | TABGAS | Exhaust gas temperature |
| `0x0068` | TVIST | Flow temperature instant |
| `0x006A` | TWWIST | DHW temperature instant |
| `0x006E` | TVSOLL | Flow temperature setpoint |
| `0x006F` | TWWSOLL_HS | DHW setpoint (heat exchanger side) |

#### Actuator / Control Registers

| Address | Name | Description |
|---------|------|-------------|
| `0x0060` | IONIST | Ionisation current actual |
| `0x0061` | PWMGPV | PWM pump output |
| `0x0070` | NGSOLL | Fan speed setpoint |
| `0x0071` | NGIST | Fan speed actual |
| `0x0072` | HZZUSTBM | Heating circuit state bitmap |
| `0x0074` | WWZUSTBM | DHW circuit state bitmap |

#### Configuration / Tuning Registers

| Address | Name | Description |
|---------|------|-------------|
| `0x0081` | HZ_HYS | Heating hysteresis |
| `0x0082` | TBRMINOFF | Minimum off-time |
| `0x0083` | HZ_KP | Heating PID proportional gain |
| `0x0084` | HZ_KTND | Heating PID derivative |
| `0x0085` | NG_KESSEL_MIN | Min fan speed |
| `0x0087` | NG_HZ_MAX | Max fan speed (heating) |
| `0x008B` | WW_HYS | DHW hysteresis |
| `0x008D` | NG_WW_MAX | Max fan speed (DHW) |
| `0x0094` | NG_START_PWM | Start PWM value |
| `0x009B` | HK_S | Heating curve slope |
| `0x009D` | NG_KESSEL_MAX | Max fan speed (global) |

**Evidence:** aghulas -> `src/kromschroeder/0000360.tsp` [lines 19--3500+](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/src/kromschroeder/0000360.tsp)

**Falsifiable claims:**

- TVIST (`0x0068`) and TVISTAD (`0x005C`) should converge during steady-state operation; a persistent large delta indicates the damping constant is incorrect or addresses are wrong.
- IONIST (`0x0060`) should be 0 when the burner is off and non-zero during active combustion. A non-zero value in standby suggests the address maps to a different register in this firmware version.
- EBUS_BITS (`0x0026`) should change when bus traffic state changes (initiator/target election). Stable value under varying bus load indicates it is a different register.

---

## 4. Secondary Channel (0902/0903)

- **PB=0x09**, SB=0x02 (read) and SB=0x03 (write)
- Defined in `reg09_inc.tsp` (read, 297 registers) and `reg0903_inc.tsp` (write, 297 registers)
- Same register count as the main 5000/5001 include files (`reg_inc.tsp` / `reg50_inc.tsp`), indicating the same register set exposed on a secondary access channel

**Inference:** bc1/bc2 burner controllers at 0x08/0x18 may use 0902/0903 while controller modules (ka at 0x15, em1--em3 at 0x50--0x52) use 5000/5001. Alternatively, 0902/0903 may be a diagnostic access channel vs the operational 5000/5001.

**Evidence:** File existence of `reg0903_inc.tsp` and `reg09_inc.tsp` in aghulas fork with matching 297-register counts; [aghulas fork root](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/)

---

## 5. PBSB 500A (Unknown Role)

- **PB=0x50**, SB=0x0A
- Listed as a new PBSB in the aghulas fork but no row-level data was extractable -- it appears only in include files or device files whose rows were truncated during fork analysis
- Candidate roles: EEPROM erase, block-level read, firmware initialization sequence, or a diagnostic command
- **Evidence:** Listed in new-PBSB inventory for aghulas fork; no further decoding possible from available data

---

## 6. PB=0x50 Disambiguation

PB=0x50 is shared between Wolf (MF=0x19) and Kromschroeder (MF=0x50). The opcode spaces are non-overlapping:

| PBSB | Manufacturer | Role | Protocol Class |
|------|-------------|------|----------------|
| 5000 | Kromschroeder | Memory read request | RAM/EEPROM direct access |
| 5001 | Kromschroeder | Memory read response / write | RAM/EEPROM direct access |
| 500A | Kromschroeder | Unknown (block/erase?) | Third opcode |
| 5014 | Wolf | Solar status + mixer setpoint | Solar broadcast |
| 5017 | Wolf | Solar pump + temperatures | Solar broadcast |
| 5018 | Wolf | Solar power/yield | Solar broadcast |
| 5022 | Wolf | Service parameter read | Indexed param access |
| 5023 | Wolf | Service parameter write | Indexed param access |

**Key disambiguation rules:**

1. **No physical overlap in practice.** Wolf's solar MC at 0x50 and Kromschroeder's em1 at 0x50 cannot co-exist on the same eBUS ring. ebusd disambiguates by ident (PBSB 0704) manufacturer byte.
2. **Opcode space is non-overlapping.** Wolf uses SB=0x14/0x17/0x18/0x22/0x23; Kromschroeder uses SB=0x00/0x01/0x0A. No collisions.
3. **Access model is fundamentally different.** Kromschroeder 5000/5001 = raw memory map (address-based, CRC-obfuscated, 20K+ registers). Wolf 5022/5023 = named parameter table (25 indexed service registers). A gateway parsing one as the other will get garbage.

See also: [`wolf-protocols.md`](../wolf/wolf-protocols.md) for the Wolf side of this disambiguation.

---

## 7. Helianthus Relevance

**Architectural feasibility: theoretical. Near-term priority: none.**

- Kromschroeder produces industrial/commercial burner management systems. Weishaupt produces residential and commercial burners. Neither is the residential HVAC gateway target.
- The 5000/5001 RAM access protocol with 20K+ registers is powerful but device-specific: register semantics differ per firmware version and are obfuscated behind a CRC ID scheme whose algorithm is not publicly documented.
- Multiple address conflicts with Vaillant devices (0x08, 0x15, 0x50) make physical co-existence impossible on a Vaillant installation.
- The TypeSpec toolchain used by aghulas is the most technically sophisticated ebusd contribution in the fork survey -- it is the correct model for any future large-scale manufacturer support.
- **Recommendation:** No action. Note TypeSpec approach as a reference if Helianthus ever contributes back to the ebusd-configuration upstream.

---

## Appendix: Evidence Index

| Finding | Fork | File | Line(s) | URL |
|---------|------|------|---------|-----|
| 5000/5001 RAM access + registers | aghulas | 0000360.tsp | 19--3500+ | [link](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/src/kromschroeder/0000360.tsp) |
| Device addresses bc1/bc2/ka/fs1/em1-em3/sc | aghulas | 08..bc1.tsp etc. | -- | [link](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/src/kromschroeder/08..bc1.tsp) |
| 0902/0903 include files (297 regs each) | aghulas | reg0903_inc.tsp | -- | [link](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/) |
| Weishaupt f6..sc.csv (558 rows) | aghulas | f6..sc.csv | 1+ | [link](https://github.com/aghulas/ebusd-configuration/blob/90c509ddbd494f8efab546a609bc195aba8ed991/src/kromschroeder/tsp-output/%40ebusd/ebus-typespec/weishaupt/f6..sc.csv) |
