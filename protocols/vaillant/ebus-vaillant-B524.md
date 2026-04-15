# Vaillant GetExtendedRegisters (`0xB5 0x24`, B524)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document is the canonical wire-protocol reference for Vaillant `GetExtendedRegisters` (`PB=0xB5`, `SB=0x24`).

It is structured by:
- command families (opcode-based),
- shared selector/response data structures,
- discovery behavior and scanning guidance.

**Related documents:**
- Register catalog: [ebus-vaillant-B524-register-map.md](./ebus-vaillant-B524-register-map.md)
- Research & working hypotheses: [ebus-vaillant-b524-research.md](./ebus-vaillant-b524-research.md)

## 1. Scope and Framing

B524 is a selector-opcode multiplexed payload protocol carried inside a standard eBUS frame.

```text
eBUS telegram request body used with ebusd `hex`:
DST PB SB LEN DATA...

For B524:
PB=0xB5
SB=0x24
DATA... starts with B524 opcode family byte.
```

The full wire frame for a read request is:

```
QQ ZZ PB SB NN OC OT GG II RR_lo RR_hi
```

- `QQ` = source address
- `ZZ` = destination (e.g., `0x15` for BASV2)
- `PB` = `0xB5` (primary), `SB` = `0x24` (secondary)
- `NN` = payload length (6 for a read: OC + OT + GG + II + RR_lo + RR_hi)
- `OC` = opcode: `0x02` (local) or `0x06` (remote)
- `OT` = operation type: `0x00` (read), `0x01` (write)
- `GG` = group, `II` = instance
- `RR` = register address (16-bit little-endian)

When using ebusd TCP `hex`, the response line is typically prefixed with an eBUS response length byte (`LEN DATA...`). See `protocols/ebusd-tcp.md`.

## 2. Shared Data Structures

### 2.1 Request selectors

```text
GG      Group id (u8)
II      Instance id (u8)
RR      Register id (u16 little-endian)
SEL*    Timer selector bytes (u8)
WD      Weekday (u8, 0x00..0x06)
```

### 2.2 Common read-response header (`0x02` / `0x06`)

```text
FLAGS GG RR_LO RR_HI [value...]
```

`FLAGS` is an access/writability byte:

| FLAGS | Bit 1 (writable) | Bit 0 (sub-cat) | Access | Category | Description |
|-------|-------------------|------------------|--------|----------|-------------|
| `0x00` | 0 | 0 | RO | State (volatile) | Changes frequently -- external pushes, counters |
| `0x01` | 0 | 1 | RO | State (stable) | Computed outputs, sensor readings, properties |
| `0x02` | 1 | 0 | RW | Config (technical) | Offsets, thresholds, numeric ranges |
| `0x03` | 1 | 1 | RW | Config (user-facing) | Modes, schedules, names, setpoints |

**Opcode-specific behavior:** Opcode 0x06 remote read (`OC=0x06, OT=0x00`) is heavily RO -- across all groups, remote access exposes far fewer writable registers. When it does allow writes, they are always FLAGS=0x02 (technical), never 0x03 (user-facing). All user-configurable settings are exclusively on the opcode 0x02 local path.

Notes:
- `II` is not echoed in the response.
- **Short responses** (payload < 4 bytes) are **not** successful register reads. A single-byte `0x00` indicates wrong route, unsupported opcode, or group default -- ebusd reports `invalid position ... / 00`. Write operations may return short acknowledgements. Treat as not-a-register-value.
- Correlation must retain request context (`GG/II/RR/opcode`).
- Exception: the `0x01` constraint dictionary request is `01 GG RR` (no `II`), so correlation there is `GG/RR`.

### 2.3 Register response states

B524 register reads produce one of three distinct response states:

| State | Wire manifestation | Meaning |
|-------|-------------------|---------|
| **Active** | ACK + FLAGS+GG+RR+VALUE (4+ bytes) | Register is functional, value bytes contain valid data |
| **Dormant** | ACK + 0 bytes payload (NN=0) | Register exists on the device but is currently inactive -- the associated feature is not configured or not engaged |
| **Absent** | NACK or timeout | Register does not exist on this device |

**NACK-or-CRC ambiguity:** When accessing B524 via transport-layer adapters (ebusd TCP `hex`, ENH), the adapter reports negative outcomes as a single error class. A true protocol-level NACK (the device explicitly rejected the request) and a CRC failure (corrupt frame on the wire) are indistinguishable in transport traces. Both present as "absent" in scan results. Scanners and analysis tools should classify these uniformly as `nack_or_crc` rather than asserting either cause. Only direct bus-level observation (raw frame capture with CRC verification) can disambiguate. For scanning purposes, the distinction is immaterial: the register is treated as absent regardless of the underlying cause.

The **dormant** state is feature-gated: the controller knows the register address but returns an empty payload because the prerequisite feature is off. Examples observed on BASV2:

- `GG=0x00, RR=0x0006` (manual cooling days): dormant when VRC720 cooling is not configured
- `GG=0x00, RR=0x0016` (system quick mode active flag): dormant when no system quick mode is engaged
- `GG=0x00, RR=0x0074` (system quick mode value): dormant when no system quick mode is engaged
- `GG=0x00, RR=0x00DA/0x00DB` (manual cooling dates): responsive with BCD defaults in one scan, dormant in another after configuration change

A compliant reader must distinguish dormant from absent: dormant registers may become active when the corresponding feature is enabled (e.g., activating a quick mode on the thermostat, configuring cooling). Scanners should classify 0-byte replies as `dormant`, not as hard errors.

### 2.4 Sentinel and no-data patterns

Four distinct "no real data" signaling mechanisms exist in B524 responses:

| Pattern | Wire bytes | When used | Detection |
|---------|-----------|-----------|-----------|
| **Empty reply** | ACK + 0 data bytes | Register dormant (feature inactive) | `len(payload) < 4` |
| **NaN sentinel** | FLAGS+GG+RR+`00 00 C0 7F` | Float register where sensor is disconnected or reading unavailable | `math.isnan(f32_value)` |
| **0x7FFFFFFF sentinel** | FLAGS+GG+RR+`FF FF FF 7F` | Integer register with uninitialized or out-of-range value | `u32_value == 0x7FFFFFFF` |
| **Zero** | FLAGS+GG+RR+`00 00` | Legitimate value = 0 | Context-dependent; not a sentinel |

The `0x7FFFFFFF` sentinel was confirmed via ISC Smartconnect KNX analysis: when the ISC gateway reads this value from a B524 register, it skips updating the corresponding output. Implementations should treat `0x7FFFFFFF` in integer registers as "value not available" rather than as the literal number 2,147,483,647.

### 2.5 Asymmetric read/write paths

Some B524 control registers use different GG/RR addresses for reading vs writing. The **write address** (used in `OT=0x01` frames) can differ from the **read address** (used in `OT=0x00` frames). This is a controller implementation pattern, not a general B524 feature.

**Known asymmetric path -- System Quick Mode:**

| Operation | Path | Register |
|-----------|------|----------|
| Read active flag | `OP=0x02, GG=0x00, RR=0x0016` | `system_quick_mode_active` (dormant when no mode active) |
| Read mode value | `OP=0x02, GG=0x00, RR=0x0074` | `system_quick_mode_value` (dormant when no mode active) |
| Write mode value | `OP=0x02, GG=0x09, RR=0x0001` | Write target for mode activation |
| Write active flag | `OP=0x02, GG=0x09, RR=0x0002` | Write target for mode on/off |
| Read-back from write group | `OP=0x02, GG=0x09, RR=0x0004` | Mirrors the written mode value |

The GG=0x09 local namespace shows zero instances on passive scan because these are **write-triggered registers** -- they only become meaningfully readable after a value has been written. This pattern cannot be discovered through read-only scanning; it requires third-party device analysis (e.g., ISC Smartconnect KNX) or write experimentation.

### 2.6 Wire type encoding

| Wire | Encoding | Size | Notes |
|------|----------|------|-------|
| `u8` | Unsigned byte | 1 byte | Boolean-range values and small enums. ebusd `onoff`/`yesno` (UCH) |
| `u16` | Little-endian uint16 | 2 bytes | Primary integer type. ebusd may decode only low byte for some enums |
| `u32` | Little-endian uint32 | 4 bytes | Energy counters, pump hours/starts |
| `f32` | IEEE 754 float32 (see note below) | 4 bytes | Primary numeric type for temperatures, pressures, percentages |

> **Device-dependent f32 byte order:** Controllers at address `0x15` (BASV2, CTLV2, VRC720 family) use **little-endian** f32 encoding. The HMU (Heat Management Unit) at address `0x08` on heat pump systems uses **big-endian** f32 encoding -- implementations reading f32 from HMU via B524 must reverse the 4 bytes before IEEE 754 decoding. This is confirmed by the OpenHAB community's use of the `reverseByteOrder` ebusd configuration flag for HMU B524 reads. All Helianthus scan data is from BASV2 (`0x15`) and is internally consistent little-endian. (Source: FINAL-B524-B555-B507-B508.md A1; confidence HIGH.)
| `string` | Null-terminated C string | Variable | Zone names, installer info |
| `bytes` | Raw byte sequence | Variable | Opaque payload, not decoded as numeric |
| `date` | BCD-encoded `DD MM YY` | 3 bytes | Year = 2000 + YY. See constraint type `0x0C` |
| `time` | BCD-encoded `HH MM [SS]` | 2-3 bytes | 2 bytes (HH:MM) for timers, 3 bytes (HH:MM:SS) for system clock |

### 2.7 Directory descriptor semantics

Directory probe returns a 4-byte `float32le` descriptor value per group. NaN terminates enumeration (observed on all tested VRC720-class targets). Descriptor values are small non-negative integers ({0, 1, 2, 3, 5, 6}) whose semantic meaning is not yet established.

Key confirmed facts:
- Descriptor=0 does NOT mean "group absent" -- groups with descriptor 0 can contain real register data.
- NaN is the only reliable end-of-table signal.
- Descriptor is deterministic per firmware build but varies across firmware versions.

For the full cross-installation analysis, falsified hypotheses, and active working hypotheses, see [ebus-vaillant-b524-research.md](./ebus-vaillant-b524-research.md).

## 3. Opcode Family Map

```text
Opcode  Name                 Request shape                     Status
0x00    Directory probe      00 <GG> 00                        Confirmed
0x01    Constraint dictionary 01 <GG> <RR>                     Confirmed
0x02    Local register I/O   02 <RW> <GG> <II> <RR_LO> <RR_HI> Confirmed
0x03    Timer read           03 <SEL1> <SEL2> <SEL3> <WD>      Non-functional on VRC720/BASV2 (VRC700 only)
0x04    Timer write          04 <SEL1> <SEL2> <SEL3> <WD> ...  Confirmed (VRC700 only)
0x06    Remote register I/O  06 <RW> <GG> <II> <RR_LO> <RR_HI> Confirmed
0x0B    Array/table read     Shape unresolved (non-scalar)     Observed/partial
```

> **Note on opcodes 0x03/0x04:** These timer opcodes are functional on **VRC700 (device ID 70000) only**. VRC720-family controllers (BASV2/BASV3/CTLV2/CTLV3/CTLS2) return empty responses to these opcodes and use B555 for timer operations instead. See [Section 4.4](#44-0x03--0x04-timer-schedules) for the full device-binding note and channel map.

`RW` is `0x00` for read and `0x01` for write.

### 3.1 Selector semantics are opcode-scoped

B524 selectors are **opcode-dependent**. The semantic meaning of a register read
is determined by the full tuple:

```text
(opcode, GG, II, RR)
```

`II=0x00` may be omitted as shorthand for singleton groups, but the canonical
selector remains `(opcode, GG, II, RR)`.

Rules:

- Do **not** interpret `GG` in isolation.
- **OP=0x02 groups and OP=0x06 groups are independent entities.** The same GG
  byte value in different opcodes identifies completely unrelated register sets
  with different semantics, different instance counts, and different register
  layouts. There is no inheritance, aliasing, or structural relationship between
  them. For example, `OP=0x02, GG=0x09` contains local control/write-path
  registers while `OP=0x06, GG=0x09` contains radio device inventory/status
  registers -- these share nothing beyond the coincidental GG byte value.
- `RR` meanings are local to the full opcode-selected selector set.
- The correct way to correlate a read is always `(opcode, GG, II, RR)`, not
  `GG` or `RR` alone.

### 3.2 Opcode routing

| Opcode | Selector family | Documented selector sets | Notes |
|--------|-----------------|-------------------------------|-------|
| `0x02` | Local controller selector family | `GG=0x00..0x05`, `GG=0x08`, `GG=0x09`, `GG=0x0A` | Controller-local registers and per-slot configuration |
| `0x06` | Controller-mediated selector family | `GG=0x01`, `GG=0x02`, `GG=0x08`, `GG=0x09`, `GG=0x0A`, `GG=0x0C`, `GG=0x0E`, `GG=0x0F` | Opcode-scoped selector sets used for live remote data, controller-mediated slot data, and instanced heat-source paths corroborated by analiza ISC Smartconnect KNX. `GG=0x00` does not exist under OP=0x06 |

**Selector rule:** `GG` labels are local to the opcode-selected selector set. A
shared `GG` byte value across different opcodes has no standalone semantic
meaning by itself.

Explicit examples:

- `GG=0x00 + OP=0x02` = local system/settings selector set.
- `GG=0x01 + OP=0x02` = local DHW selector set.
- `GG=0x01 + OP=0x06` = controller-side primary heating source slots
  (gas burners, heat pumps, and similar primary generators), corroborated by
  analiza ISC Smartconnect KNX. Note: `GG=0x00 + OP=0x06` does not exist.
- `GG=0x02 + OP=0x06` = controller-side secondary heating source slots
  (for example solar-facing secondary sources), corroborated by analiza ISC
  Smartconnect KNX.
- `OP=0x02, GG=0x08/0x09/0x0A` and `OP=0x06, GG=0x08/0x09/0x0A` are distinct
  documented selector spaces with different meanings and register layouts.

This rule also applies to `GG=0x00`: even where only one selector set is
currently documented on wire, `GG` still does not carry a single global meaning
outside its opcode context. Apply the same caution to other opcode/GG
combinations until they are fully mapped.

## 4. Family Details

### 4.1 `0x00` Directory Probe

The directory probe (`0x00`) enumerates group availability. It is distinct from the register I/O opcodes: OP=0x02 (instance directory / local register I/O) reads or writes individual registers within a group, while OP=0x06 (register directory / remote register I/O) accesses a separate opcode-scoped selector family. The directory probe itself is opcode-independent -- it discovers groups that may then be accessed via either OP=0x02 or OP=0x06 depending on the group's documented opcode binding.

```text
Request payload (3 bytes):
  0: 0x00
  1: GG
  2: 0x00

Response payload (4 bytes):
  0..3: descriptor float32le
```

Discovery rules:
- Iterate GG upward.
- Treat only 4-byte responses as candidate directory descriptors.
- For transport-level compatibility detection, any valid 4-byte directory
  response is sufficient evidence that B524 directory probing is supported
  on that address, even if the descriptor value is `0.0`.
- NaN terminates enumeration (observed on all tested devices).
- Do not suppress known groups solely because `descriptor == 0.0`.
- Core structural groups `GG=0x02` (circuits) and `GG=0x03` (zones)
  remain scan candidates even when the descriptor is `0.0`.
- For unknown groups, the descriptor may be used only as a conservative hint,
  never as a universal proof of absence.
- Treat transport/timeouts as non-terminating errors.

Rationale:

- B524 is the controller-side aggregation surface for system structure.
- The current evidence does not justify treating descriptor class `0.0`
  as equivalent to "group absent".
- Single-circuit/no-functional-module installations are a known counterexample.

### 4.2 `0x01` Constraint Dictionary (min/max/step)

This family exposes an undocumented constraint dictionary for configuration parameters.

Canonical request form:

```text
Request payload (3 bytes):
  0: 0x01
  1: GG
  2: RR
```

**Note:** RR is u8 here (low byte only), unlike register read where RR is u16 LE.

Example ebusd `hex` command for `GG=0x03`, `RR=0x01`:

```text
hex 15B52403010301
```

#### 4.2.1 Type tags and decoding

The first byte of the constraint response is a **type tag (TT)** (distinct from the FLAGS byte in register read responses) that defines the constraint value encoding. Constraint decoding is TT-driven: the TT byte fully determines the wire format of the min/max/step triplet that follows.

```text
0x06: u8 range
  06 GG RR 00 MIN MAX STEP

0x09: u16le range
  09 GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are u16 little-endian

0x0F: float32le range
  0F GG RR 00 MIN MAX STEP
  where MIN/MAX/STEP are IEEE754 float32 little-endian

0x0C: date range (HDA3-like)
  0C GG RR 00 MIN(d,m,y) MAX(d,m,y) STEP(u16le) 00
  year is interpreted as 2000 + y
```

#### 4.2.2 Discovery method (practical)

To discover constraints for a group:

1. For each discovered group, iterate `RR=0x00..min(rr_max,0xFF)`.
2. Probe optional shared IDs above the window (e.g., `RR=0x80`).
3. Send `15 b5 24 03 01 GG RR`.
4. Keep responses where:
   - type tag `in {0x06,0x09,0x0C,0x0F}`
   - response echoes request `GG RR`.
5. Filter stdout noise/non-hex lines before decode.

#### 4.2.3 Constraint catalog

For the full decoded constraint catalog with register names, types, enum values, and ebusd cross-references, see [`ebus-vaillant-B524-register-map.md` Constraint Catalog](./ebus-vaillant-B524-register-map.md#constraint-catalog-ebusreg).

#### 4.2.4 Circuit type interpretation (`GG=0x02 RR=0x02`)

`GG=0x02 RR=0x02` (`heating_circuit_type` / `mctype`) is a configuration register with raw values 0..4. See [`ebus-vaillant-B524-register-map.md` mctype](./ebus-vaillant-B524-register-map.md#mctype--circuit-type) for the authoritative enum definition.

**Raw register meaning (Vaillant VRC720 manual):**

```text
0 = Inactive       Circuit unused
1 = Heating         Weather-compensated heating (mixing or direct)
2 = Fixed value     Circuit held at fixed target flow temperature
3 = DHW             Heating circuit used as DHW for additional cylinder
4 = Increase in return   Return temperature raise circuit
```

These raw values are the complete wire-level meaning. No resolution or context inputs are needed to interpret them.

Higher-level semantic projections (e.g., cooling capability, pool heating, cylinder charging) may combine the raw circuit type with other registers and system topology. Such projections are implementation-specific and are not part of the B524 wire protocol; they are documented separately.

#### 4.2.5 Room influence type behavior (`GG=0x02 RR=0x0003`)

This register controls how the room temperature sensor influences the heating curve. See [`ebus-vaillant-B524-register-map.md` GG=0x02](./ebus-vaillant-B524-register-map.md#gg0x02--heating-circuits-multi-instance) for the register definition.

Behavioral semantics (`enum_u8`, default `0`):

- `0 = INACTIVE` -- pure weather compensation. Flow temperature derived from outdoor temp + heating curve. Room controller acts as display/setpoint input only. Controller placement in technical room is acceptable.
- `1 = ACTIVE` -- weather compensation + room-temperature modulation. Flow temperature adjusted from room deviation vs setpoint. Heating may continue outside time windows at reduced temperature. Controller should be in representative living space. Practical: if room is `0.5C` below setpoint, flow setpoint is increased proportionally.
- `2 = EXTENDED` -- weather compensation + modulation + thermostat-like on/off gating. Zone deactivates when `room_temp > setpoint + 0.125C` (`2/16 K`), activates when `room_temp < setpoint - 0.1875C` (`3/16 K`). Hysteresis bandwidth is `0.3125C` (`5/16 K`). Caution: tight hysteresis can increase heat-pump cycling risk.

Practical guidance:

- `INACTIVE`: useful with external room controllers or radiator valves
- `ACTIVE`: commonly preferred for slower floor-heating systems
- `EXTENDED`: commonly preferred for faster radiator systems; disabled during absence mode

#### 4.2.6 Register catalogs

All register definitions (names, categories, types, constraints, enum values, gates) are maintained exclusively in [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md). This document covers only B524 wire protocol methods and their logic.

### 4.3 `0x02` / `0x06` Register Read/Write

```text
Read request payload (6 bytes):
  0: opcode  (0x02 local / 0x06 remote)
  1: RW      (0x00)
  2: GG
  3: II
  4: RR_LO
  5: RR_HI

Write request payload (6+ bytes):
  0: opcode  (0x02 local / 0x06 remote)
  1: RW      (0x01)
  2: GG
  3: II
  4: RR_LO
  5: RR_HI
  6..: value bytes
```

Read response:
- Successful: `FLAGS GG RR_LO RR_HI [value...]`
- Short responses (< 4 bytes) are not successful reads. See section 2.2.

Addressing notes:
- `0x02` is the local controller selector family.
- `0x06` is a separate opcode-scoped controller-mediated selector family. It is used
  for several remote families, including device slot data, controller-side
  primary heating source slots (`GG=0x01`), and controller-side secondary
  heating source slots (`GG=0x02`), corroborated by analiza ISC Smartconnect KNX.
- The selector meaning is always keyed on `(opcode, GG, II, RR)`, not on `GG`
  alone.

### 4.4 `0x03` / `0x04` Timer Schedules

> **Device binding:** Opcodes 0x03/0x04 are available on **VRC700 (device ID 70000, including Saunier Duval B7S00) only**. VRC720-family controllers (BASV2, BASV3, CTLV2, CTLV3, CTLS2, CTLV0, BASV0) do NOT respond to B524 timer opcodes -- they use the [B555 protocol](./ebus-vaillant-b555-timer-protocol.md) for all timer/schedule operations. Both device families share eBUS target address `0x15` but are different device classes. A scanner or schedule writer that does not check device identity before choosing transport will send the wrong protocol. (Source: FINAL-B524-B555-B507-B508.md A2/A3; confidence HIGH.)

```text
Timer read request (5 bytes):
  0: 0x03
  1: SEL1
  2: SEL2
  3: SEL3
  4: WD (0x00..0x06)

Timer write request (5+ bytes):
  0: 0x04
  1: SEL1
  2: SEL2
  3: SEL3
  4: WD
  5..: timer blocks (model-specific)
```

These families do not use `RW` byte.

#### 4.4.1 Timer channel map (SEL1/SEL2/SEL3)

The three selector bytes address a specific timer channel. The complete channel map from VRC700 ebusd CSV (`15.700.csv`):

| SEL1 | SEL2 | SEL3 | Channel |
|------|------|------|---------|
| `0x00` | `0x00` | `0x01` | Ventilation timer |
| `0x00` | `0x00` | `0x02` | Noise reduction timer |
| `0x00` | `0x00` | `0x03` | Tariff timer |
| `0x01` | `0x00` | `0x01` | DHW (HWC) timer |
| `0x01` | `0x00` | `0x02` | Circulation pump timer |
| `0x03` | `0x00` | `0x01` | Zone cooling timer |
| `0x03` | `0x00` | `0x02` | Zone heating timer |

The WD byte (0x00-0x06 = Monday-Sunday) selects the weekday within the addressed channel.

**Response format:** ebusd reports `slotCountWeek` / `slotCountDay` time-pair sequences. Full per-opcode wire layout is pending complete documentation from community sources.

**Channel mapping correspondence:** The SEL-addressed channels correspond to the B555 HC-addressed channels on VRC720-family devices. For example, B524 SEL1=`0x01`/SEL2=`0x00`/SEL3=`0x01` (DHW timer) on VRC700 is functionally equivalent to B555 HC=`0x02` (HWC) on BASV2.

(Source: FINAL-B524-B555-B507-B508.md A2; confidence HIGH.)

### 4.5 `0x0B` Array/Table Read (Schedules)

`0x0B` is observed for schedule/program-style groups (`GG=0x06`, `GG=0x07`) where simple register loops are insufficient.

Current status:
- family observed on wire
- full selector/body schema still under consolidation
- practical recommendation: treat as array/table transport, not scalar RR scan

Implication:
- sparse `0x01` constraints do not imply scalar coverage for schedule groups.

## 5. Topology-Significant Registers

Two registers in `OP=0x02, GG=0x00` carry system-level topology information that constrains the interpretation of other groups:

| RR | Name | Wire | Semantics |
|----|------|------|-----------|
| `0x0036` | `system_scheme` | u16 | Hydraulic scheme number (1..16). Defines the physical piping topology of the heating system (number/type of heat sources, mixing circuits, buffer tanks, solar integration). Different scheme numbers imply different valid group/register combinations. |
| `0x002F` | `module_configuration_vr71` | u16 | VR71 functional module configuration (1..11). Encodes which mixing/direct circuits the VR71 hardware module manages. Combined with `system_scheme`, determines circuit ownership and whether FM5-backed families (solar, cylinders) are structurally valid. |

These are property registers (FLAGS=0x01, read-only, stable). Their values are set during system commissioning and do not change during normal operation. They are the primary structural inputs for determining which semantic families and circuit assignments are valid on a given installation.

For the full register catalog including per-register constraints and enum values, see [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md).

## 6. Group Taxonomy and Descriptor Classes

For the authoritative group topology (names, instance ranges, opcodes), see [`ebus-vaillant-B524-register-map.md` Group Topology](./ebus-vaillant-B524-register-map.md#group-topology).

Directory probe descriptor values observed on VRC720-class targets:

```text
GG   Descriptor(s)  Typical opcode  Notes
0x00 3.0            0x02            singleton local system selector set; OP=0x06 GG=0x00 does NOT exist
0x01 3.0            0x02            singleton local DHW selector set; OP=0x06 GG=0x01 is primary heating sources (ISC KNX)
0x02 1.0            0x02            instanced
0x03 1.0            0x02            instanced
0x04 6.0 / 5.0      0x02            model-dependent
0x05 1.0 / absent   0x02            model-/system-dependent
0x06 (varies)       0x0B            program/timetable domain
0x07 (varies)       0x0B            program/timetable domain
0x08 1.0 / absent   0x02 / 0x06    OP=0x02 GG=0x08 = local singleton config; OP=0x06 GG=0x08 = remote instanced data
0x09 1.0            0x02 / 0x06    OP=0x02 GG=0x09 = local slot config; OP=0x06 GG=0x09 = remote live radio data
0x0A 1.0            0x02 / 0x06    OP=0x02 GG=0x0A = local slot config; OP=0x06 GG=0x0A = remote live radio data
0x0C 1.0 / absent   0x06           model-/system-dependent controller-mediated slot selector set
```

Descriptor class values behave like coarse enum tags, not physical numeric quantities.

## 7. Discovery and Scan Strategy

### 7.1 Phase A: group discovery

- probe `0x00` directory sequentially
- stop on first `NaN` (observed as reliable end-of-table on all tested devices)
- record unknown groups and unknown descriptor classes for follow-up

### 7.2 Phase B: constraint dictionary sampling (`0x01`)

- probe `0x01 GG RR` over bounded per-group RR windows
- decode and persist `min/max/step` domains (`u8`, `u16le`, `f32le`, `date`)
- constraints are advisory metadata (they provide value ranges but do not define register presence)

### 7.3 Phase C: instance detection (instanced groups)

- evaluate all `II=0x00..II_max` (no early stop on holes)
- `II_max` comes from static profile and observed valid instances, not from `0x01`.
- mark present slots based on group-specific heuristics

### 7.4 Phase D: register scan

- scan selected groups/instances/ranges
- for unknown groups, scanners may probe both `0x02` and `0x06` and keep best response

### 7.5 Static fallback profile (when dynamic evidence is missing)

```text
GG   Opcode  InstanceMax  RegisterMax
0x02 0x02    0x0A         0x0025
0x03 0x02    0x0A         0x002F
0x09 0x06    0x0A         0x0030
0x0A 0x06    0x0A         0x003F
0x0C 0x06    0x0A         0x003F
```

This profile is a baseline planner bound source; dynamic evidence (`0x01` constraints and successful read probes) should be persisted as advisory metadata to refine scan ranges over time.

## 8. ebusd TCP Interop Notes

For `hex` command integration (`protocols/ebusd-tcp.md`):
- send `DST PB SB LEN DATA...`
- parse first valid hex response line
- strip leading ebusd length prefix when present
- accept short status-only payloads
- ignore trailing noisy lines after a valid parsed payload

## 9. Open Items

Open protocol questions and validation items are tracked in [ebus-vaillant-b524-research.md](./ebus-vaillant-b524-research.md).
