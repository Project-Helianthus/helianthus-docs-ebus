# B524 Research & Working Hypotheses

> **License:** CC0-1.0 (public domain). This documents protocol-level observations and hypotheses, not implementation-specific behavior.
>
> **Last updated:** 2026-04-06
>
> For the B524 protocol specification, see [ebus-vaillant-b524.md](./ebus-vaillant-b524.md).
> For the register catalog, see [ebus-vaillant-b524-register-map.md](./ebus-vaillant-b524-register-map.md).

This document collects protocol-level observations, working hypotheses, and open questions about B524 behavior that have not yet been resolved into confirmed protocol rules. Items graduate to the main protocol spec when sufficient evidence accumulates.

---

## 1. Directory Descriptor Analysis

### 1.1 Wire Format

The directory probe (`OP=0x00`) returns a 4-byte IEEE 754 float32 LE value per group. NaN (`0x7FC00000` or `0xFFFFFFFF`) terminates group enumeration. Only controller devices (BASV2/3) respond; boiler appliances (BAI00) do not implement OP=0x00.

### 1.2 Cross-Installation Data

Study corpus: 8 scans across 4 installations and 3 firmware versions.

Observed descriptor values (always clean non-negative integers encoded as float32): **{0, 1, 2, 3, 5, 6}**. Values 4 and 7 are never observed.

**Cross-installation comparison (`int(float)` value, 3-bit binary):**

| GG | FW 0507 (BASV2) | FW 0760 (BASV3) | FW 0217 (BASV0) |
|----|-----------------|-----------------|-----------------|
| 0x00 | 3 = 011 | 1 = 001 | 3 = 011 |
| 0x01 | 3 = 011 | 1 = 001 | 3 = 011 |
| 0x02 | 1 = 001 | 0 = 000 | 0 = 000 |
| 0x03 | 1 = 001 | 0 = 000 | 0 = 000 |
| 0x04 | 6 = 110 | 5 = 101 | 6 = 110 |
| 0x05 | 1 = 001 | 2 = 010 | 2 = 010 |
| 0x06 | 1 = 001 | 1 = 001 | 1 = 001 |
| 0x07 | 1 = 001 | 1 = 001 | 1 = 001 |
| 0x08 | 0 = 000 | (n/a) | (n/a) |
| 0x09 | 1 = 001 | (n/a) | 1 = 001 |
| 0x0A | 1 = 001 | (n/a) | (n/a) |
| 0x0C | 1 = 001 | (n/a) | (n/a) |

**Register quality per group (BASV2 FW 0507, exhaustive scan):**

| GG | Desc | NS 0x02 instances | NS 0x02 valid/total | NS 0x06 instances | NS 0x06 valid/total |
|----|------|-------------------|---------------------|-------------------|---------------------|
| 0x00 | 3 | 1 | 165/256 | 1 | 0/22 |
| 0x01 | 3 | 1 | 16/20 | 1 | 7/22 |
| 0x02 | 1 | 3 | 92/114 | 3 | 33/114 |
| 0x03 | 1 | 2 | 76/94 | 2 | 26/94 |
| 0x04 | 6 | 1 | 10/12 | 1 | 0/12 |
| 0x05 | 1 | 1 | 4/5 | 1 | 4/5 |
| 0x06 | 1 | 3 | 0/147 | 11 | 55/196 |
| 0x07 | 1 | 3 | 0/147 | 11 | 53/196 |
| **0x08** | **0** | 1 | **5/8** | 4 | **16/20** |
| 0x09 | 1 | 0 | 0/0 | 1 | 31/54 |
| 0x0A | 1 | 11 | 609/858 | 1 | 31/54 |
| **0x0B** | **0** | 3 | 0/51 | 11 | **24/68** |
| 0x0C | 1 | 1 | 0/48 | 1 | 14/48 |
| **0x0E** | **0** | 11 | 0/68 | 11 | **16/68** |
| **0x0F** | **0** | 11 | 0/68 | 11 | **15/68** |

### 1.3 Falsified Hypotheses

- ~~Instance count~~ — desc=3 for singleton groups (GG=0x00, ii_max=0)
- ~~Opcode count~~ — max 2 opcodes per group but values reach 6
- ~~Static firmware constant~~ — GG=0x04 changed from 5 to 6 on the **same device** (BASV2 FW 0507) between Feb and Apr 2026 scans, no firmware update
- ~~Simple revision counter~~ — 5->6 flips 2 bits simultaneously (XOR=011), not a monotonic increment
- ~~Direct bit-to-opcode mapping~~ — 5-8 mismatches against observed opcode presence data
- ~~Descriptor=0 means inactive~~ — GG=0x08 has desc=0 but contains 21 valid registers (5 on NS 0x02, 16 on NS 0x06); GG=0x02/0x03 have desc=0 on other installations but are core heating groups

### 1.4 Confirmed Invariants

- **Descriptor=0 groups CAN contain real register data.** Never skip scanning a group based on its descriptor value.
- **Value 1 is the default/fallback.** BASV0 FW 0217 returns 1 for all probed GG >= 0x12 (non-existent groups).
- **Deterministic per firmware build.** Two devices with identical firmware (same SW + HW version) return byte-identical descriptors.
- **Paired groups always match:** GG=0x00+0x01, GG=0x02+0x03, GG=0x06+0x07.
- **NaN terminator is the only reliable end-of-table signal.**
- **BASV0 FW 0217 NaN terminator bug:** never emits NaN, causing scanners to enumerate 249 groups. Defensive ceiling of ~0x20 recommended for unknown devices.

### 1.5 Active Hypotheses (Unverified)

**Hypothesis A — Register Schema Variant Identifier:**
The descriptor encodes a firmware-specific register schema variant for each group. The `int(float)` value, treated as a 3-bit field, indicates which register sub-schema the controller uses internally. bit2 (0x04) is exclusive to GG=0x04 across all devices. The 5->6 transition represents a schema mode switch (2 bits flip), not a simple increment. Evidence: deterministic per FW build, varies across FW versions non-monotonically (BASV3/newest has LOWER values for GG=0x00/0x01 than older FW).

**Hypothesis B — 3-bit bitmask (speculative bit assignment):**
- bit0 = standard/primary register namespace
- bit1 = extended/secondary register namespace
- bit2 = configuration/installer namespace (GG=0x04 only)

Problem: direct bit-to-namespace correlation has mismatches at GG=0x08-0x0C where descriptor=0 but real data exists on both namespaces.

**Hypothesis C — Firmware fingerprint vector:**
The vector `[desc_0x00, desc_0x01, ..., desc_0x11]` may serve as a firmware revision fingerprint. Observed vectors are unique per FW build. Potential use: cache invalidation (re-scan group when descriptor changes).

### 1.6 Open Questions

- Value 4 (100) and 7 (111) never observed — architectural constraint or insufficient sample?
- Could undiscovered opcodes (0x01 constraint is known; 0x03/0x04 timer is known; but 0x05, 0x07+ are unknown) correspond to descriptor bits?
- Why does BASV0 return 1 (not 0) for non-existent groups (0x12+)?
- What triggered the 5->6 change on GG=0x04 between Feb and Apr scans on the same device?

---

## 2. Register Discovery Notes

### 2.1 Dormant Registers

Certain registers return an empty payload (0 bytes after ACK) when their associated feature is not configured or not engaged. This "dormant" state is distinct from absent (NACK/timeout). See the protocol spec's "Register Response States" section for the wire-level definition.

Known dormant registers (BASV2, confirmed across 2 scan generations):

| GG | RR | Name | Dormant condition |
|----|----|------|-------------------|
| 0x00 | 0x0006 | manual_cooling_days | VRC720 cooling not configured |
| 0x00 | 0x0016 | system_quick_mode_active | No system quick mode engaged |
| 0x00 | 0x0074 | system_quick_mode_value | No system quick mode engaged |
| 0x00 | 0x00DA | manual_cooling_date_start | Cooling dates not set (was responsive in Feb 2026, dormant in Apr 2026) |
| 0x00 | 0x00DB | manual_cooling_date_end | Same as above |

Verification needed: activate quick mode (party/ventilation/away) on thermostat, then read 0x0016 and 0x0074 to confirm they become non-dormant.

### 2.2 Compound Register Observation (GG=0x00, RR=0x0048)

ISC KNX Smart analysis maps 5 communication objects to this register, each extracting different boolean sub-fields via application-level bitfield extraction (outdoor temp sensor OK, flow temp sensor OK, etc.). The standard B524 read returns 2 value bytes (u16=0, FLAGS=0x01 stable RO).

The ISC gateway's "compound" extraction is an application-layer abstraction (CSD/ControllerSpecificData class hierarchy), not a B524 protocol feature. The register contains a status bitmask; actual measurement values are read from dedicated registers (0x0073, 0x004B, 0x0039).

### 2.3 GG=0x09 Dual-Use Evidence

ISC KNX Smart analysis reveals GG=0x09 local config registers 1-4 are also used as system-level quick mode control registers:

| GG=0x09 Reg | ISC KNX Smart Use | Passive scan result |
|-------------|-------------------|---------------------|
| 0x0001 | System quick mode write target (mode value) | sensor_address (value=0) |
| 0x0002 | System quick mode active write target | sensor_type (value=1) |
| 0x0004 | System quick mode read-back | (unknown, value=0) |

The local namespace (opcode 0x02) shows zero instances on passive scan — these are write-triggered registers. The remote namespace (opcode 0x06) contains unrelated radio sensor data (54 registers per instance). This confirms absolute namespace isolation by opcode.

### 2.4 Asymmetric Read/Write Path Evidence

The system quick mode registers use different addresses for reading vs writing:
- **Read**: GG=0x00, Reg 0x0016 (active flag) + Reg 0x0074 (mode value) — dormant when no mode active
- **Write**: GG=0x09, Reg 0x0001 (mode value) + Reg 0x0002 (active flag)

This pattern cannot be discovered through read-only scanning.

---

## 3. Open Items / Validation Queue

- Finalize complete selector schema for opcode `0x0B` array/table read.
- Expand response exemplars per family (`0x01` and `0x0B` especially).
- Track descriptor-class transitions (e.g., GG=0x04 class 6 vs 5) against system topology changes.
- Probe system quick mode registers (0x0016/0x0074) during active quick mode to confirm non-dormant response.
- Probe undiscovered opcodes (0x05, 0x07+) on groups with bit2 set in descriptor.
- Investigate 0x7FFFFFFF sentinel in integer registers — confirm conditions under which it appears.
