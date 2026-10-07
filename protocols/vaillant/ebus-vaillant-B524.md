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
- Research & working hypotheses: archived observations

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

`FLAGS` is an observed two-bit reply attribute. The following bit interpretation
comes from private static analysis and is a profile-specific inference; it is not
a universal B524 wire contract or proof of live writability.

| Bit | Inferred meaning | Limit |
|-----|------------------|-------|
| 0 | visibility/category discriminator | It does not establish volatile or stable behavior. |
| 1 | writable capability | A set bit does not authorize a write or establish that a target accepts one. |

The numeric value and the raw response must be retained. Do not assign public
`volatile`, `stable`, `technical`, or `user-facing` semantics from `FLAGS` alone.

Notes:
- `II` is not echoed in the response.
- **Short responses** (payload < 4 bytes) are **not** successful register reads. A single-byte `0x00` indicates wrong route, unsupported opcode, or group default -- ebusd reports `invalid position ... / 00`. Write operations may return short acknowledgements. Treat as not-a-register-value.
- Correlation must retain request context (`GG/II/RR/opcode`).
- Parameter descriptions retain their request identifier and full 16-bit register. The historical short `01 GG RR` probe is incomplete and must not provide input-validation authority.

### 2.3 Register response states

B524 register reads produce one of three distinct response states:

| State | Wire manifestation | Meaning |
|-------|-------------------|---------|
| **Value reply** | ACK + FLAGS+GG+RR+VALUE (4+ bytes) | A correlated value-shaped reply; its semantic validity still needs a qualified codec. |
| **Empty reply** | ACK + 0 bytes payload (NN=0) | An observed empty response. It may be feature-gated, unsupported, or otherwise profile-specific. |
| **Negative/timeout** | NACK, transport error, or timeout | No qualifying value reply; this does not prove global register absence. |

**NACK-or-CRC ambiguity:** When accessing B524 via transport-layer adapters (ebusd TCP `hex`, ENH), the adapter reports negative outcomes as a single error class. A true protocol-level NACK (the device explicitly rejected the request) and a CRC failure (corrupt frame on the wire) are indistinguishable in transport traces. Scanners and analysis tools should classify these uniformly as `nack_or_crc` rather than asserting either cause. Only direct bus-level observation (raw frame capture with CRC verification) can disambiguate. A scanner may use the outcome to bound a profile-local scan, but must retain it as non-qualification rather than proof of absence.

Some BASV2 observations correlate empty replies with a feature being inactive. They do not make an empty reply a universal feature-gated state:

- `GG=0x00, RR=0x0006` (manual cooling days): dormant when VRC720 cooling is not configured
- `GG=0x00, RR=0x0016` (system quick mode active flag): dormant when no system quick mode is engaged
- `GG=0x00, RR=0x0074` (system quick mode value): dormant when no system quick mode is engaged
- `GG=0x00, RR=0x00DA/0x00DB` (manual cooling dates): responsive with BCD defaults in one scan, dormant in another after configuration change

A reader must preserve empty replies separately from value replies and negative/timeout outcomes. A profile may label an empty reply `dormant` only where correlated evidence supports that interpretation.

### 2.4 Sentinel and no-data patterns

Four distinct "no real data" signaling mechanisms exist in B524 responses:

| Pattern | Wire bytes | When used | Detection |
|---------|-----------|-----------|-----------|
| **Empty reply** | ACK + 0 data bytes | Empty response; cause is profile-specific | `len(payload) < 4` |
| **NaN sentinel** | FLAGS+GG+RR+`00 00 C0 7F` | Float register where sensor is disconnected or reading unavailable | `math.isnan(f32_value)` |
| **0x7FFFFFFF sentinel** | FLAGS+GG+RR+`FF FF FF 7F` | Integer register with uninitialized or out-of-range value | `u32_value == 0x7FFFFFFF` |
| **Zero** | FLAGS+GG+RR+`00 00` | Legitimate value = 0 | Context-dependent; not a sentinel |

**Hypothesis:** independent protocol evidence is required for this interpretation.

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

On the controller/profile behind this reconstruction, the local GG=0x09 path
returned no instances in a passive scan and the cited static analysis associates
these selectors with the asymmetric quick-mode path. That observation does not
make all OP=02h/GG=09h registers write-triggered, unavailable to passive reads,
or irrelevant to another profile; ventilation candidates remain separately
profile-scoped and capture-required.

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
| `date` | Profile-qualified date codec | Variable | BCD `DD MM YY` is observed for some scalar fields; it does not follow from a description-response length. |
| `time` | BCD-encoded `HH MM [SS]` | 2-3 bytes | 2 bytes (HH:MM) for timers, 3 bytes (HH:MM:SS) for system clock |

### 2.7 System-information identifiers

OP=00h is `ReadSystemInformation`. Its 16-bit identifier selects a system
quantity; it is independent of the `GG` used by OP=02h or OP=06h. For example,
ID=0000h describes circuits, while OP=02h/GG=00h contains system parameters.
The earlier interpretation of finite results as opaque group-descriptor classes
is superseded by the [published identifier interpretation](https://github.com/Project-Helianthus/helianthus-vrc-explorer/discussions/53#discussioncomment-18748372).

Keep the raw float and its interpreted count separate. Accept a count only when
it is finite, non-negative, integral, within the profile's bound, and the identifier
has a documented count meaning. API version/revision are not instance counts.
NaN was an enumeration terminator in the published BASV2/BASV3 observations;
this is not a universal rule for every product or identifier range. Implementations
continue only through their configured bounded identifier set and retain NaN as
an observation rather than using it as an unbounded scan-control signal.

## 3. Opcode Family Map

These are Helianthus operation names from the public discussion, with spelling
normalized for `GetParameter` and `GetDeviceParameter`. They are not proprietary
service identifiers. A listed operation is not proof that every target supports it.

| OP / OT | Helianthus name | Selector / purpose |
| --- | --- | --- |
| 00h | `ReadSystemInformation` | `00 IDlo IDhi` |
| 01h | `DescribeParameter` | `01 GG II RRlo RRhi`; describes a system parameter |
| 02h / 00h | `GetParameter` | `02 00 GG II RRlo RRhi` |
| 02h / 01h | `SetParameter` | `02 01 GG II RRlo RRhi VALUE...` |
| 03h | `ReadTimer` | VRC700 timer selectors |
| 04h | `WriteTimer` | VRC700 timer selectors and values |
| 06h / 00h | `GetDeviceParameter` | `06 00 GG II RRlo RRhi` |
| 06h / 01h | `SetDeviceParameter` | `06 01 GG II RRlo RRhi VALUE...` |
| 07h | `DescribeDeviceParameter` | `07 GG II RRlo RRhi`; device parameter description |
| 08h | `ReadVR91` | VRC700 zone status for an assigned VR91 |
| 09h / 0Ah | `GetEvent` / `SetEvent` | Event selectors / values |
| 0Bh / 0Ch | `GetEventSetPoint` / `SetEventSetPoint` | Event-setpoint selectors / values |

OP=01h and OP=07h use separate selector domains. Their complete forms are the
corrected reconstruction adopted for profile-qualified implementations. The
identifier byte is retained as `II` in Helianthus terminology; its exact meaning
and any special identifier (including FFh) must be qualified per profile.
Physical support and response codecs require correlated target evidence.

OP=03h/04h timer support remains product-specific: VRC700 uses this family;
VRC720-family controllers use B555. All write variants are mutative and excluded
from discovery and read-only scans.

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
| `0x06` | Controller-mediated selector family | `GG=0x01`, `GG=0x02`, `GG=0x08`, `GG=0x09`, `GG=0x0A`, `GG=0x0C`, `GG=0x0E`, `GG=0x0F` | **Hypothesis:** independent protocol evidence is required for this interpretation. |

**Unqualified presentation candidate:** The operator-provided display designation
`OP=0x06, GG=0x0B` = **Functional Modules (VR70)** is retained as a name only. It
is not included in the documented selector sets because this repository has no
published capture, bounds, liveness predicate, or schema for that route. The
separately documented `OP=0x06, GG=0x0C` presentation name is **Functional
Modules (VR71)**; neither display name establishes a universal product-identity
rule.

**Selector rule:** `GG` labels are local to the opcode-selected selector set. A
shared `GG` byte value across different opcodes has no standalone semantic
meaning by itself.

Explicit examples:

- `GG=0x00 + OP=0x02` = local system/settings selector set.
- `GG=0x01 + OP=0x02` = local DHW selector set.
- **Hypothesis:** independent protocol evidence is required for this interpretation.
- **Hypothesis:** independent protocol evidence is required for this interpretation.
- `OP=0x02, GG=0x08/0x09/0x0A` and `OP=0x06, GG=0x08/0x09/0x0A` are distinct
  documented selector spaces with different meanings and register layouts.

This rule also applies to `GG=0x00`: even where only one selector set is
currently documented on wire, `GG` still does not carry a single global meaning
outside its opcode context. Apply the same caution to other opcode/GG
combinations until they are fully mapped.

## 4. Family Details

### 4.1 `0x00` ReadSystemInformation

```text
Request payload:  00 IDlo IDhi
Response body:   four float32 little-endian bytes on the documented controller profile
```

The identifier table below follows the public BASV2/SW0507, BASV3/SW0760 and
BASV0/SW0217 report. It is a profile interpretation, not a global register-group
list or a claim that all counts are physically verified on every system.

| ID | snake_case semantic name | Meaning |
| --- | --- | --- |
| 0000h | `circuit_count` | Circuits; guides OP=02h/GG=02h instance discovery |
| 0001h | `zone_count` | Zones; guides OP=02h/GG=03h instance discovery |
| 0002h | `solar_circuit_count` | Solar circuits |
| 0003h | `solar_loaded_tank_count` | Solar-loaded tanks |
| 0004h | `device_count` | Devices |
| 0005h | `generator_count` | Generators |
| 0006h | `api_version` | API version; not a count |
| 0007h | `api_revision` | API revision; not a count |
| 0008h / 0009h | `vr70_count` / `vr71_count` | Functional module counts |
| 000Ah | `remote_control_count` | Remote controls |
| 000Bh | `delta_t_count` | Published deltaT label; physical class remains unknown |
| 000Ch / 000Dh | `boiler_count` / `heat_pump_count` | Generator classes |
| 000Eh / 000Fh | `vpm_w_count` / `vpm_s_count` | Module classes |
| 0010h | `recovair_count` | recoVair ventilation units |
| 0011h | `cooling_heat_pump_count` | Cooling-capable heat pumps |

A count selects how many active instances are expected, not their identities.
In non-exhaustive scans, probe profile-bounded II slots in order until the expected
number of present instances is found. Do not assume the first N slots are occupied.
A missing, non-integral, non-finite, out-of-bound or conflicting count falls back
to bounded presence discovery. A zero count is retained as evidence and does not
silently delete independently observed instances. Record expected and observed
counts and their mismatch. `research` scans keep the full configured II range.

Only an explicit profile mapping connects an information identifier to `(OP,GG)`.
In particular, ID=0010h does not imply GG=10h. Known groups remain scan candidates
even when their same-numbered information identifier returns zero.

### 4.2 `0x01` DescribeParameter and `0x07` DescribeDeviceParameter

```text
System parameter:  01 GG II RRlo RRhi
Device parameter:  07 GG II RRlo RRhi
```

The historical `01 GG RR` request omitted the identifier and high address byte.
Its changing/misaligned replies do not prove a sliding-window dictionary or a
BASV2 buffer bug. Preserve them as historical observations, with the returned
selector independent from the intended selector. See the
[original public short-probe report](https://github.com/Project-Helianthus/helianthus-vrc-explorer/discussions/53#discussioncomment-15839146).

Descriptions apply to numeric ranges, booleans, enum domains and other supported
writable parameter formats. They are not restricted to enums and do not establish
register presence, instance count, permission to write, or persistence.

#### 4.2.1 Description response and validation

After transport normalization, a description reply has this shape:

```text
GG RRlo RRhi MIN MAX STEP
```

The bytes formerly labelled `TT` (`06`, `09`, and `0F` in the observed samples)
are eBUS response lengths, not datatype tags. The three spans have equal width;
the observed scalar codec determines whether their values are unsigned, signed,
float, date, or another format. A response length alone does not qualify that
codec. Malformed length, mismatched `GG`/`RR16`, unequal spans, an unknown scalar
codec, or inconsistent/non-finite limits remain unqualified. Retain request
context because `II` is not echoed. Never assign a description across OP=02h/06h
or across instances merely because `GG`/`RR` match.

#### 4.2.2 Targeted acquisition

Read the parameter first. Recommended/custom acquisition contains at most 256
deduplicated, observed writable candidates for which the profile-scoped static
`FLAGS & 0x02` inference is present, including candidates whose scalar codec is
not yet known. An unknown codec is retained raw and remains unqualified; it is
not a reason to omit an otherwise eligible description request. That inference
selects candidates only: it neither proves live writability nor authorizes a
write. For each selected candidate, send its complete
profile-qualified description selector: OP=01h for the system family and OP=07h
for the device family. Keep the raw request and reply, decoder revision and
qualification outcome in the artifact. Unsupported descriptions are explicit
missing data; no short-probe fallback is allowed. The implementation records
`eligible`, `attempted`, `matched`, `unavailable`, `unqualified`, and
`budget_skipped` counters per description family.

#### 4.2.3 Offline value changes

A matching qualified description validates encoding/type/width, min/max and step
for every edit, including non-enum numeric values. A contradicted value is rejected.
When no qualified description is available, VRC Explorer warns that the edit is
unvalidated and permits its existing explicit confirmation. Offline editing does
not send a device write. Historical static ranges remain hints, not validation
authority. See the [historical constraint catalog](./ebus-vaillant-B524-register-map.md#constraint-catalog-ebusreg).

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
- **Hypothesis:** independent protocol evidence is required for this interpretation.
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

### 4.5 `0x0B` GetEventSetPoint

The public operation name is `GetEventSetPoint`, paired with mutative
`SetEventSetPoint` (OP=0Ch). The previous generic Array/Table Read label and the
claim that GG=06h/07h prove timetable domains are withdrawn. Preserve event
selectors and setpoint data independently from scalar register I/O. A correlated
request/reply and product-specific codec are required before promoting an event
setpoint to a decoded schedule. OP=09h/0Ah similarly form the separate GetEvent /
SetEvent pair. These families are not included in scalar discovery.

## 5. Topology-Significant Registers

Two registers in `OP=0x02, GG=0x00` carry system-level topology information that constrains the interpretation of other groups:

| RR | Name | Wire | Semantics |
|----|------|------|-----------|
| `0x0036` | `system_scheme` | u16 | Hydraulic scheme number (1..16). Defines the physical piping topology of the heating system (number/type of heat sources, mixing circuits, buffer tanks, solar integration). Different scheme numbers imply different valid group/register combinations. |
| `0x002F` | `module_configuration_vr71` | u16 | VR71 functional module configuration (1..11). Encodes which mixing/direct circuits the VR71 hardware module manages. Combined with `system_scheme`, determines circuit ownership and whether FM5-backed families (solar, cylinders) are structurally valid. |

These are candidate topology inputs. Their observed values and the inferred
`FLAGS` attributes do not by themselves prove read-only, stable, commissioning,
or universal installation semantics. A qualified profile may use them when its
source evidence supports the mapping.

For the full register catalog including per-register constraints and enum values, see [`ebus-vaillant-B524-register-map.md`](./ebus-vaillant-B524-register-map.md).

## 6. Group Taxonomy and System Information

The [register map](./ebus-vaillant-B524-register-map.md#group-topology) owns
operation-scoped group names and bounds. OP=00h identifiers are a separate axis;
their numerical values must not be joined to same-numbered groups. Keep an explicit
profile mapping for count-guided discovery, initially ID0→OP02/GG02 and
ID1→OP02/GG03. Other mappings require their own evidence.

## 7. Discovery and Scan Strategy

The four scan presets and JSON planning interface below are VRC Explorer
scanner-policy contracts. They constrain the planned implementation; they are
not universal B524 wire proof, a product support matrix, or authorization to
write a device.

1. Read bounded, known OP00 information identifiers and retain each raw result.
2. Select groups from operation-scoped profiles, not from successful OP00 IDs.
3. In `recommended`, use a valid mapped count to guide bounded presence probes.
   Keep sparse slots, zero/conflicting observations and mismatches visible.
   `full` audits every declared II slot regardless of OP00 counts; `research`
   is expanded but bounded rather than exhaustive; `custom` selections take
   precedence.
4. Read selected registers and acquire descriptions only for observed parameters
   that are eligible under the profile. Full/research plan all eligible descriptions
   within finite logical and actual-send budgets.
5. Persist complete operation-aware identities, profile/provenance, raw replies,
   expected/observed counts and description qualification.

Timeout, NACK, CRC/transport failure, empty response, malformed description and
unsupported operation are distinct evidence states. None alone proves that a
register is absent from every product. A failed description keeps the successful
value observation and any independently qualified earlier description.

### 7.1 Deterministic plans, budgets, and description scheduling

The same pure candidate-policy/planner serves the UI and CLI. The planned CLI
form is `--scan-plan <path.json>`. Its version-1 document has this shape:

```json
{
  "schema_version": 1,
  "groups": [
    {"opcode": "0x02", "group": "0x00", "instances": [0], "registers": [0, 1]}
  ]
}
```

`groups` is a list; selectors are explicit, with the mandatory OP02/GG02/II0A
addition described below. `instances` and `registers`
contain explicit values or bounded ranges expanded by the planner. The parser
accepts only OP=02h and OP=06h read selectors and enforces the applicable wire
bounds. It rejects a plan above 100000 planned scalar requests before a queue is
created. A UI and CLI custom scan pass the same normalized plan to the same pure
planner, so neither surface presence-prunes explicitly selected selectors.

#### Version-1 JSON grammar and normalization

- The root contains exactly `schema_version` and `groups`. The version is the
  integer `1` or string `"1"`; `groups` is a non-empty array of objects.
- Every group row contains exactly `opcode`, `group`, `instances`, and
  `registers`. Unknown or missing fields are rejected. `opcode` is only 2 or 6;
  `group` is an unsigned 8-bit value.
- Scalar values are JSON integers, decimal strings, `0x`-prefixed hexadecimal
  strings, or bare hexadecimal strings containing A-F. Digit-only strings are
  decimal: `"10"` is ten and `"0x10"` is sixteen. Booleans and floating-point
  numbers are rejected, even if numerically integral.
- `instances` and `registers` are non-empty arrays. Each element is one scalar
  or one string range `start..end` or `start-end`, using the scalar token syntax.
  Both endpoints are included. Reversed endpoints are reordered. For example,
  `"0x0004..0x0002"` expands to 2, 3, 4. Commas inside one element are rejected;
  use separate array elements.
- Every expanded instance is in `0..255`; every expanded register is in
  `0..65535`. Negative or out-of-bound values are rejected. Each list is
  deduplicated and sorted ascending before planning.
- Rows are keyed by `(opcode, group)`. Identical normalized duplicate rows
  collapse into one row; differing selectors for a duplicate key are rejected.
- The scalar request count is the sum of
  `len(unique_instances) * len(unique_registers)` over unique rows. Exactly
  100000 is accepted; 100001 or more is rejected before queuing. Discovery,
  descriptions and retries are additional sends governed by the send budget.

[Synthetic accepted/rejected contract vectors](../../tests/fixtures/b524_scan_plan_v1_cases.json)
include equivalent selector representations and the 100000/100002 boundary.
They are parser fixtures, not device or wire qualification evidence.

Description acquisition is a second phase. `--description-budget` is finite and
defaults to 256 for recommended/custom and 100000 for full/research. Extended
profiles therefore plan every eligible description within the actual-send cap.
Half of its slots are initially reserved for each family
(OP01h/OP02h and OP07h/OP06h); unused slots may be borrowed by the other family.
Within a family it schedules eligible `(GG,II)` candidates round-robin. The
artifact retains the six counters listed in section 4.2.2, including candidates
skipped by budget.

`--request-budget` is an optional finite cap on actual B524 sends, including
retries. Full and research default to 10000 sends. Budget exhaustion emits a partial
artifact marked `incomplete`; it is not converted into an absence claim.

### 7.2 Profile-qualified release contract

[Device discovery and bundled descriptions](b524-profile-discovery-and-descriptions.md)
defines mandatory OP02/GG02/II0A coverage, OP06 first-instance and connection
predicates, calendar/time STEP unknowns, extended description acquisition, and
profile-scoped offline baselines. The scalar request limit applies **after** the
mandatory II0A addition and deduplication, including custom plans.

## 8. ebusd TCP Interop Notes

For `hex` command integration (`protocols/ebusd-tcp.md`):
- send `DST PB SB LEN DATA...`
- parse first valid hex response line
- strip leading ebusd length prefix when present
- accept short status-only payloads
- ignore trailing noisy lines after a valid parsed payload

## 9. Open Items

Open protocol questions and validation items are tracked in archived observations.
