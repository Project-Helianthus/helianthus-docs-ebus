# Vaillant GetExtendedRegisters (`0xB5 0x24`, B524)

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This reference uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document is the canonical wire-protocol reference for Vaillant `GetExtendedRegisters` (`PB=0xB5`, `SB=0x24`).

It is structured by:
- command families (opcode-based),
- shared selector/response data structures,
- discovery behavior and scanning guidance.

**Related documents:**
- Register catalog: [ebus-vaillant-B524-register-map.md](./ebus-vaillant-B524-register-map.md)
- Result tables (candidate interpretations, unconfirmed on the wire):
  [operations](fixtures/b524-operation-definitions.csv),
  [OP00 identifiers](fixtures/b524-op00-system-information-ids.csv),
  [OP06/OP07 system types](fixtures/b524-op06-op07-system-types.csv),
  [OP03/OP04 program selectors](fixtures/b524-op03-op04-program-selectors.csv),
  [event selectors](fixtures/b524-event-selector-candidates.csv),
  [calendar and clock selectors](fixtures/b524-op02-calendar-clock-selectors.csv),
  [write templates](fixtures/b524-op02-write-templates.csv),
  [write sequences](fixtures/b524-op02-write-sequences.csv),
  [register matrix by family](fixtures/b524-op02-requester-register-matrix.csv)

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
- `ZZ` = destination (e.g., `0x15` for VRC720)
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

The candidate aggregate day values 7..9 of OP=04h are described in
section 4.4.1.

### 2.2 Common read-response header (`0x02` / `0x06`)

The characterized VRC720 register catalog uses this value-reply layout;
it does not establish the reply layout of other controller families.

```text
FLAGS GG RR_LO RR_HI [value...]
```

`FLAGS` (the attribute byte) is an observed two-bit reply attribute. The following bit interpretation
is a family-specific inference, not a universal B524 wire contract or proof of
live writability.

| Bit | Inferred meaning | Limit |
|-----|------------------|-------|
| 0 | visibility/category discriminator | It does not establish volatile or stable behavior. |
| 1 | writable capability | A set bit does not authorize a write or establish that a target accepts one. |

The candidate bit names are `Visible` for bit 0 and `Read/Write` for bit 1
(`0=False`, `1=True`), with bits 2–7 reserved. These names do not establish
whether a particular target accepts writes. The candidate OP06 write-feedback
codes are `0=no error`, `1=read-only error`, `2=range error`; their on-wire
interpretation remains unconfirmed.

The numeric value and the raw response must be retained. Do not assign public
`volatile`, `stable`, `technical`, or `user-facing` semantics from `FLAGS` alone.

Notes:
- `II` is absent from this four-byte header. Retain it from the request;
  do not assume an unqualified controller profile uses this layout.
- **Short responses** (payload < 4 bytes) are **not** successful register reads. A single-byte `0x00` indicates wrong route, unsupported opcode, or group default -- ebusd reports `invalid position ... / 00`. Write operations may return short acknowledgements. Treat as not-a-register-value.
- Correlation must retain request context (`GG/II/RR/opcode`).
- Parameter descriptions retain their request identifier and full 16-bit register. The historical short `01 GG RR` probe is incomplete and must not provide input-validation authority.

### 2.3 Register response states

B524 register reads produce one of three distinct response states:

| State | Wire manifestation | Meaning |
|-------|-------------------|---------|
| **Value reply** | ACK + FLAGS+GG+RR+VALUE (4+ bytes) | A correlated value-shaped reply; its semantic validity still needs a qualified codec. |
| **Empty reply** | ACK + 0 bytes payload (NN=0) | An observed empty response. It may be feature-gated, unsupported, or otherwise family-specific. |
| **Negative/timeout** | NACK, transport error, or timeout | No qualifying value reply; this does not prove global register absence. |

**NACK-or-CRC ambiguity:** When accessing B524 via transport-layer adapters (ebusd TCP `hex`, ENH), the adapter reports negative outcomes as a single error class. A true protocol-level NACK (the device explicitly rejected the request) and a CRC failure (corrupt frame on the wire) are indistinguishable in transport traces. Scanners and analysis tools should classify these uniformly as `nack_or_crc` rather than asserting either cause. Only direct bus-level observation (raw frame capture with CRC verification) can disambiguate. A scanner may use the outcome to bound a profile-local scan, but must retain it as non-qualification rather than proof of absence.

Some VRC720 observations correlate empty replies with a feature being inactive. They do not make an empty reply a universal feature-gated state:

- `GG=0x00, RR=0x0006` (manual cooling days): dormant when VRC720 cooling is not configured
- `GG=0x00, RR=0x0074` (system quick mode value): dormant when no system quick mode is engaged
- `GG=0x00, RR=0x00DA/0x00DB` (manual cooling dates): responsive with BCD defaults in one scan, dormant in another after configuration change

The VRC700 ventilation-mode selector is separate from these VRC720
observations; see the [register-map entry](ebus-vaillant-B524-register-map.md#gg0x00--system)
for its candidate enum and profile scope. It does not establish a VRC720
empty reply or the selector's behaviour when no system quick mode is engaged.

A reader must preserve empty replies separately from value replies and negative/timeout outcomes. A profile may label an empty reply `dormant` only where correlated evidence supports that interpretation.

### 2.4 Sentinel and no-data patterns

Four distinct "no real data" signaling mechanisms exist in B524 responses:

| Pattern | Wire bytes | When used | Detection |
|---------|-----------|-----------|-----------|
| **Empty reply** | ACK + 0 data bytes | Empty response; cause is family-specific | `len(payload) < 4` |
| **NaN sentinel** | FLAGS+GG+RR+`00 00 C0 7F` | Float register where sensor is disconnected or reading unavailable | `math.isnan(f32_value)` |
| **0x7FFFFFFF sentinel** | FLAGS+GG+RR+`FF FF FF 7F` | Integer register with uninitialized or out-of-range value | `u32_value == 0x7FFFFFFF` |
| **Zero** | FLAGS+GG+RR+`00 00` | Legitimate value = 0 | Context-dependent; not a sentinel |

`0x7FFFFFFF` is a candidate no-data value in integer replies. Preserve it raw
and keep any no-data treatment family-qualified until a correlated public
capture establishes the behavior.

### 2.5 Asymmetric read/write paths

Some B524 control registers use different GG/RR addresses for reading vs writing. The **write address** (used in `OT=0x01` frames) can differ from the **read address** (used in `OT=0x00` frames). This is a controller implementation pattern, not a general B524 feature.

**Historical asymmetric-path hypothesis -- System Quick Mode:**

The historical role labels below remain unqualified. The current register names
alone do not demonstrate that these selectors form one control path.

| Operation | Path | Register |
|-----------|------|----------|
| Read operating mode | `OP=0x02, OT=0x00, GG=0x00, II=<ventilation_index>, RR=0x0016` | `ventilation_operating_mode` (enum, see register map) |
| Read mode value | `OP=0x02, GG=0x00, RR=0x0074` | `special_function_mode` (dormant when no mode active) |
| Write mode value | `OP=0x02, GG=0x09, RR=0x0001` | Write target for mode activation |
| Write active flag | `OP=0x02, GG=0x09, RR=0x0002` | Write target for mode on/off |
| Read-back from write group | `OP=0x02, GG=0x09, RR=0x0004` | Mirrors the written mode value |

On the controller/profile behind this reconstruction, the local GG=0x09 path
returned no instances in a passive scan and the historical reconstruction associates
these selectors with the asymmetric quick-mode path. That observation does not
make all OP=02h/GG=09h registers write-triggered, unavailable to passive reads,
or irrelevant to another profile; ventilation candidates remain separately
profile-scoped and capture-required.

### 2.6 Wire type encoding

| Wire | Encoding | Size | Notes |
|------|----------|------|-------|
| `u8` | Unsigned byte | 1 byte | Boolean-range values and small enums. ebusd `onoff`/`yesno` (UCH) |
| `i8` | Signed 8-bit integer | 1 byte | Profile-specific index values; see the Vaillant decoder notes below. |
| `u16` | Little-endian uint16 | 2 bytes | Primary integer type. ebusd may decode only low byte for some enums |
| `u32` | Little-endian uint32 | 4 bytes | Energy counters, pump hours/starts |
| `f32` | IEEE 754 float32 (see note below) | 4 bytes | Primary numeric type for temperatures, pressures, percentages |
| `string` | Null-terminated C string | Variable | Zone names, installer info |
| `bytes` | Raw byte sequence | Variable | Opaque payload, not decoded as numeric |
| `date` | Profile-qualified date codec | Variable | BCD `DD MM YY` is observed for some scalar fields; it does not follow from a description-response length. The year byte of date triples is a candidate offset from 2000 (section 4.7); which codec applies to which register is not established. |
| `time` | Profile-qualified time codec (candidate BCD `HH MM [SS]`) | 2-3 bytes | 2 bytes (HH:MM) for timers, 3 bytes (HH:MM:SS) for system clock. The system-clock triple is a candidate of plain hour, minute and second bytes with no BCD step (section 4.7); the codec the controller uses is not established. |

> **Profile-dependent f32 byte order:** The characterized VRC720 controller uses little-endian float32. A heat-pump HMU profile may use big-endian float32; qualify that codec independently before reversing bytes. The VRC720 survey does not establish the HMU layout, and a destination address alone never selects byte order.

#### Vaillant numeric formats

The following additional numeric interpretations remain unconfirmed on the
wire for the stated controller families.

- Float format: IEEE-754 binary32, little-endian, with an identity mapping
  (no wire scale or offset). `Precision 1` denotes presentation precision,
  not a multiplier.
- Unit metadata: °C has factor 1 and SI offset 273.15, K has offset 0, and
  bar has factor 100000. These unit conversions do not change the numeric
  value transmitted in the register's own unit.
- Float bounds: finite binary32 extrema, with no reserved bit pattern
  established. The NaN example in section 2.4 is one binary32 NaN
  representation; handling of other NaN encodings and infinity remains open.

For `OP=0x02, GG=0x03, II=<zone>, RR=0x001C` (`zone_circuit_assignment`),
the candidate signed-byte interpretation is `-1=notBound`, with `0..8` for
the VRC720 family and `0..2` for the VRC700 family. It does not establish which
zone instances are present. Preserve the existing VRC720 raw values in the
register map; the physical meaning of `FF` remains unconfirmed.

#### Zone special-function response width

For `OP=0x02, GG=0x03, II=<zone>, RR=0x001B`
(`zone_special_function_state`), a one-byte format remains a candidate
alongside the two-byte catalog entry. The response width remains unconfirmed
for the VRC700 and VRC720 families. The ordinary read request contains six selector
bytes and does not request a value width. The
[register matrix](fixtures/b524-op02-requester-register-matrix.csv) therefore
carries the width as `1 or 2` and the type as `uint8 or uint16 LE` for this
register.

### 2.7 System-information identifiers

OP=00h is `ReadSystemInformation`. Its 16-bit identifier selects a system
quantity; it is independent of the `GG` used by OP=02h or OP=06h. For example,
ID=0000h describes circuits, while OP=02h/GG=00h contains system parameters.
This 16-bit system-information identifier is distinct from the one-byte `II`
selector byte, which this document also calls the identifier in OP=01h,
OP=03h/04h, OP=06h and OP=07h requests.
The earlier interpretation of finite results as opaque group-descriptor classes
is superseded by the [published identifier interpretation](https://github.com/Project-Helianthus/helianthus-vrc-explorer/discussions/53#discussioncomment-18748372).

Keep the raw float and its interpreted count separate. Accept a count only when
it is finite, non-negative, integral, within the profile's bound, and the identifier
has a documented count meaning. API version/revision are not instance counts.
NaN was an enumeration terminator in the VRC720 observations;
this is not a universal rule for every product or identifier range. Implementations
continue only through their configured bounded identifier set and retain NaN as
an observation rather than using it as an unbounded scan-control signal.

### 2.8 Reply layouts

Candidate interpretations, unconfirmed on the wire. In sections 2.8, 3.6, 4.1.1,
4.2.7, 4.3.1, 4.3.2, 4.4.1, 4.5.1 and 4.7 to 4.11, and for the candidate
positions in section 4.6, a layout marked candidate, unconfirmed on the wire, is
**Hypothesis**; a value marked not established is **Unknown**; nothing in these
sections is **Proven**.

- **Opcode echo (unresolved).** One candidate layout has an OP=0x02 or OP=0x06
  reply begin with an echo of the request opcode. This conflicts with the
  register reply layout `FLAGS GG RR_LO RR_HI [value...]` of sections 2.2 and
  4.3, which has no opcode echo, and which of the two applies is unresolved (see
  Open questions). The two OP=0x06 replies in
  [`fixtures/b524-op06-observed-windows-v1.json`](fixtures/b524-op06-observed-windows-v1.json)
  begin with the flags byte, without an opcode echo. The field order after any opcode echo, attribute byte, `GG`,
  `RR`, value bytes, is the same in both. Whether OP=0x01 and OP=0x08 replies
  begin with an opcode echo is also unresolved; the OP=0x07 replies in the same
  fixture begin with `GG`, without one.
- **OP=0x02 reply layout.** The reply carries the attribute byte, `GG`, `RR`
  (16-bit little-endian) and then `n = length - 4` value bytes, where `length`
  counts the bytes from the attribute byte on (an opcode echo, if present, is not
  counted); candidate reply lengths are 4 to 33 (`n` up to 29). The instance
  byte is not echoed. The value width follows the field: float32 `n=4`, uint16
  enumeration `n=2`, date or time triple `n=3`, uint8 `n=1`.
- **OP=0x06 reply layout.** The same split applies (attribute byte, `GG`, `RR`,
  `n = length - 4`). The VR70 module-configuration reply carries `GG=0x0B`,
  `RR=0x0005` and `n=2`. The radio-sensor humidity reply has attribute bit 0 set,
  the requested `GG` returned (`0x09` or `0x0A`), `RR=0x0007` and `n` of at least
  4 (the first four bytes are a float32). The instance byte is not echoed.
- **Reply matching.** In the candidate layout with an opcode echo, the first
  reply body byte equals the request opcode, for OP=0x02 and OP=0x06 replies
  alike. In the layout of section 2.2 a reply is matched through the retained
  request context.
- **Attribute byte.** Bit 0 of the attribute byte (candidate meaning Visible,
  section 2.2) is evaluated by a requester on specific reads: the zone-active
  read (`GG=0x03, RR=0x0011`), the visibility-qualified float members of the
  VRC720 family, the VRC700 ventilation mode (`GG=0x00, RR=0x0016`) and the
  humidity read. Bit 1 has the candidate meaning Read/Write (`0=False`,
  `1=True`; section 2.2); whether it reflects writability on a target is not
  established. No user level, configuration or state class is established for
  the byte.
- **NaN class.** A float register may reply with a NaN, which marks the value as
  unavailable (candidate). No meaning is established for infinity.
- **Enumerations.** Enumerations are 16-bit little-endian codes (one byte for
  uint8 items). A code with no candidate label is not shown to be an invalid wire value.
- **Write reply.** An OP=02h/06h register write reply is longer than one byte (the OP=04h timer write reply is one feedback byte, section 4.4.1) and carries a
  status byte (after the opcode echo, in the candidate layout that has one);
  status 0 is the candidate success value. The
  candidate write status values are `0` no error, `1` read-only and `2` out of
  range (section 2.2 states them for the OP=06h write feedback; unconfirmed on
  the wire). Whether they apply to an OP=02h write reply, and the meaning of
  other status values, are not established.
- **Roles.** No mapping from the reply attribute bits to user roles is known
  (**Unknown**).

## 3. Opcode Family Map

These are descriptive operation names from the public discussion, with spelling
normalized for `GetParameter` and `GetDeviceParameter`. They are not proprietary
service identifiers. A listed operation is not proof that every target supports it.

| OP / OT | Descriptive name | Selector / purpose |
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
corrected reconstruction adopted for family-qualified implementations. The
identifier byte is retained as `II` in this notation; its exact meaning
and any special identifier (including FFh) must be qualified per profile.
Physical support and response codecs require correlated target evidence.

OP=03h/04h timer support remains product-specific: VRC700 uses this family;
VRC720-family controllers use B555. All write variants are mutative and excluded
from discovery and read-only scans.

No layout of OP=05h is known (**Unknown**). The request prefixes of the
operations 00, 01, 02, 03, 04, 06, 07, 08, 09, 0A, 0B and 0C are given in the
[operation table](fixtures/b524-operation-definitions.csv) in wire order, with
the length byte `NN` between the service bytes `B5 24` and the operation bytes;
each row carries the status `candidate, unconfirmed on the wire`. No B524 operation
that is available only on PeBUS is known; PeBUS carries a subset of the eBUS
services (candidate interpretation, unconfirmed on the wire). The VRC700-family
PeBUS profile carries neither OP=03h nor OP=04h (candidate interpretation,
unconfirmed on the wire); whether those operations are available on that profile
is unresolved (see Open questions).

### 3.1 Selector semantics are opcode-scoped

B524 selectors are **opcode-dependent**. The semantic meaning of a register read
is determined by the full tuple:

```text
(opcode, GG, II, RR)
```

`II=0x00` may be omitted as shorthand for singleton groups, but the canonical
selector remains `(opcode, GG, II, RR)`. A group's singleton status must be
qualified for the controller profile; `GG` alone does not establish it.

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
| `0x02` | Local controller selector family | `GG=0x00..0x05`, `GG=0x08`, `GG=0x09`, `GG=0x0A` | Observed local selector sets; the role, physical identity and topology of OP02/GG0A remain Unknown |
| `0x06` | Controller-mediated selector family | `GG=0x01`, `GG=0x02`, `GG=0x08`, `GG=0x09`, `GG=0x0A`, `GG=0x0C`, `GG=0x0E`, `GG=0x0F` | Opcode-scoped selector sets. `GG=0x01/0x02` heat-generator labels remain family-qualified hypotheses; `GG=0x00` is uncharacterized. |

**Unqualified presentation candidate:** The operator-provided display designation
`OP=0x06, GG=0x0B` = **Functional Modules (VR70) FM3** is retained as a name only. It
is not included in the documented selector sets. Candidate layouts for a read
and a write of `RR=0x0005` on that route are given in sections 2.8, 4.3.1 and
4.3.2 (candidate, unconfirmed on the wire); a published capture,
bounds and a liveness predicate for the route are not established. The
separately documented `OP=0x06, GG=0x0C` presentation name is **Functional
Modules (VR71) FM5**; neither display name establishes a universal product-identity
rule.

### 3.3 OP02 family presentation-name catalog

The following descriptive labels retain the complete `(OP=0x02, GG)`
identity. A label does not add a selector route, instance range, register
layout, or physical-device claim.

| GG | Human label | Presentation semantic name | Qualification |
| --- | --- | --- | --- |
| 00 | System | `system` | VRC720-family singleton local selector set; see the [register-map topology](ebus-vaillant-B524-register-map.md#group-topology) for the separately scoped VRC700 ventilation indexing. |
| 01 | Native Domestic Hot Water | `native_domestic_hot_water` | Observed singleton local selector set. |
| 02 | Circuits | `circuits` | VRC720 family: II00..08 heating candidates and independent II09 virtual native water; other or unknown families require separate qualification. |
| 03 | Zones | `zones` | Observed local selector set. |
| 04 | Solar Circuit | `solar_circuit` | Observed local selector set. |
| 05 | Solar Loaded Cylinder | `solar_loaded_cylinder` | Observed local selector set. |
| 06 | Device | `device` | Presentation only; no public selector/profile contract. |
| 07 | Generator | `generator` | Presentation only; no public selector/profile contract. |
| 08 | DeltaT | `delta_t` | Observed local selector set; II topology Unknown. |
| 09 | Ventilation | `ventilation` | Observed local selector set; II topology Unknown. |
| 0A | Local Parameters | `local_parameters` | Observed selector set; role, physical identity, and topology Unknown. |

### 3.4 OP06 family presentation-name catalog

The following is an operator-provided **hypothesis catalog** for the OP06 family.
It gives a stable human label and a `snake_case` presentation semantic name for
use only after the exact `(OP=0x06, GG)` selector has been retained. It does not
add a documented selector route, scan target, instance range, register layout,
identity rule, liveness predicate, or write capability. Promote an individual row
only with publishable correlated wire and identity evidence for that complete
selector.

| GG | Human label | Presentation semantic name | Public qualification |
| --- | --- | --- | --- |
| 01 | Boiler | `boiler` | Hypothesis. The existing family-qualified `primary_heating_source` route remains the documented route. |
| 02 | Heat Pump | `heat_pump` | Hypothesis. The existing family-qualified `secondary_heating_source` route remains the documented route. |
| 03 | Air Recovery (VAR) recoVair | `air_recovery_recovair` | Hypothesis for the family name; the characterized profile has a candidate route and II01..II08 bound. |
| 04 | unused | `unused` | Unknown. This recorded presentation state does not establish universal absence or reservation. |
| 05 | Wärmepumpe Zubehör Appliance Interface (VWZ-AI) | `heat_pump_accessory_vwz_ai` | Hypothesis for the family name; the characterized profile has a candidate route and II01..II08 bound. |
| 06 | Pumpen Module - Solar (VPM-S) auroFLOW | `solar_pump_module_auroflow` | Hypothesis for the family name; the characterized profile has a candidate route and II01..II08 bound. |
| 07 | Pumpen Module - Wasser (VPM-W) aguaFLOW | `water_pump_module_aguaflow` | Hypothesis for the family name; the characterized profile has a candidate route and II01..II08 bound. |
| 08 | Modul Solar (VMS) auroSTEP | `solar_module_aurostep` | Hypothesis. It does not replace the separately documented family-specific `buffer_solar_cylinder_2_remote` route. |
| 09 | Remote Control Regulators (VRC7xx, VRT38x) | `remote_control_regulator` | Hypothesis for the family name; the `regulator_slot` route and its profile qualification remain separate. |
| 0A | Remote Control Thermostats (VR9x) | `remote_control_thermostat` | Hypothesis for the family name; the `thermostat_slot` route and its profile qualification remain separate. |
| 0B | Functional Modules (VR70) FM3 | `functional_modules_vr70` | Hypothesis for the family name; the characterized profile has II01..II08 candidates and requires a concrete Boolean predicate. |
| 0C | Functional Modules (VR71) FM5 | `functional_modules_vr71` | Hypothesis for the family/FM5 display name. The separately published slot schema remains family-qualified to OP06/GG0C. |
| 0D | Relay Module (VR41) | `relay_module_vr41` | Hypothesis for the family name; the characterized profile bounds RR0001 to II01..II08 as availability-only, with `device_connected` BOOL and Unknown RR maximum. |
| 0E | Clock Module | `clock_module` | Hypothesis for the family name; the `clock_slot` route and its profile qualification remain separate. |
| 0F | Base Station | `base_station` | Hypothesis for the family name; the `base_station_slot` route and its profile qualification remain separate. |

The `unused` label for GG04 is deliberately not an exclusion rule. Likewise,
similar human names do not authorize inheritance from a sibling group: GG0B
must not receive GG0C's scan policy or `device_connected` predicate, and none of
these OP06 names changes OP02 semantics or its parameter-description boundary.

**Selector rule:** `GG` labels are local to the opcode-selected selector set. A
shared `GG` byte value across different opcodes has no standalone semantic
meaning by itself.

Explicit examples:

- `GG=0x00 + OP=0x02` = local system/settings selector set.
- `GG=0x01 + OP=0x02` = local DHW selector set.
- `GG=0x01 + OP=0x06` = family-qualified controller-side primary
  heating-source candidate. It does not establish any global rule for
  `GG=0x00`.
- `GG=0x02 + OP=0x06` = family-qualified controller-side secondary
  heating-source candidate.
- `OP=0x02, GG=0x08/0x09/0x0A` and `OP=0x06, GG=0x08/0x09/0x0A` are distinct
  documented selector spaces with different meanings and register layouts.

This rule also applies to `GG=0x00`: even where only one selector set is
currently documented on wire, `GG` still does not carry a single global meaning
outside its opcode context. Apply the same caution to other opcode/GG
combinations until they are fully mapped.

### 3.5 Common OP06 register names

For every GG under `OP=0x06`, the common names are:

| RR | Name |
| --- | --- |
| 0x0001 | `device_connected` |
| 0x0002 | `device_class_address` |
| 0x0003 | `device_error_code` |
| 0x0004 | `device_firmware_version` |

These names do not qualify a common codec, successful response, physical device
identity or scan range. OP02 names remain independently keyed by opcode.

### 3.6 Candidate system-type key values

The first selector byte of OP=01h, OP=03h/04h and OP=09h..0Ch is a system-type
key with the values 0..9 of the first table; for OP=06h and OP=07h the first
selector byte is a system-type key, and the second table gives candidate labels
for its values 1..13. The values `0x0E` and `0x0F` also occur as OP=06h
selectors (section 3.4); no label of the second table is known for them, and the
full key domain of OP=06h and OP=07h is not established.
Both tables are candidate interpretations, unconfirmed on the wire. The labels
are Vaillant names.

| Key | System type (OP=01h/03h/04h/09h..0Ch) | Key | System type (OP=06h/07h) |
| --- | --- | --- | --- |
| 0 | system | 1 | Boiler |
| 1 | DHW circuit | 2 | Heat Pump |
| 2 | mixer circuit | 3 | recoVair |
| 3 | zone | 4 | unused |
| 4 | solar circuit | 5 | VWZ-AI |
| 5 | solar loaded tank | 6 | VPM-S |
| 6 | device | 7 | VPM-W |
| 7 | generator | 8 | VMS |
| 8 | delta-T control | 9 | RC VR700 |
| 9 | ventilation circuit | 10 | Remot Control (Vaillant name, spelled as shown) |
| | | 11 | VR70 |
| | | 12 | VR71 |
| | | 13 | VR41 |

The keys 0..9 of the first table correspond (candidate) to the `GG` presentation
catalog in section 3.3. The keys 1..13 of the second table correspond
(candidate) to `GG=0x01..0x0D` of the catalog in section 3.4. Candidate
address labels are known only for the keys 0, 1 and 3, in both the timer
(section 4.4) and the event (section 4.5) operations; keys 2, 4 and 5 appear in
the event table with the range 0..255 and no label. The second table is also given as a
[result table](fixtures/b524-op06-op07-system-types.csv). The OP=00h
identifiers are a separate axis (section 4.1).

## 4. Family Details

### 4.1 `0x00` ReadSystemInformation

```text
Request payload:  00 IDlo IDhi
Response body:   four float32 little-endian bytes on the documented controller profile
```

The identifier table below describes the VRC720 family. It is not a global register-group
list or a claim that all counts are physically verified on every system.

| ID | snake_case semantic name | Meaning |
| --- | --- | --- |
| 0000h | `circuit_count_maximum` | Family-qualified supported circuit capacity for bounded OP=02h/GG=02h candidate guidance |
| 0001h | `zone_count_maximum` | Family-qualified supported zone capacity for bounded OP=02h/GG=03h candidate guidance |
| 0002h | `solar_circuit_count` | Solar circuits; guides OP=02h/GG=04h discovery |
| 0003h | `solar_cylinder_count` | Solar-loaded tanks; guides OP=02h/GG=05h discovery |
| 0004h | `device_count` | Devices |
| 0005h | `heat_generator_count` | Generators |
| 0006h | `interface_version` | API version; not a count |
| 0007h | `interface_revision` | API revision; not a count |
| 0008h / 0009h | `functional_module_1_count` / `functional_module_2_count` | Functional module counts (VR70 and VR71 modules); provisional names, the index only keeps the two apart |
| 000Ah | `remote_control_count` | Remote controls |
| 000Bh | `differential_control_count` | Guides OP=02h/GG=08h discovery; physical class remains unknown |
| 000Ch / 000Dh | `boiler_count` / `heat_pump_count` | Generator classes |
| 000Eh / 000Fh | `water_pump_module_count` / `solar_pump_module_count` | Module classes |
| 0010h | `ventilation_unit_count` | recoVair ventilation units |
| 0011h | `cooling_heat_pump_count` | Cooling-capable heat pumps |
| 0012h | (unknown) | no name known; meaning unknown |
| 0099h | (unknown) | Vaillant name `RTC Crystle` (spelled as shown); meaning unknown |

ID=0000h `circuit_count_maximum` and ID=0001h `zone_count_maximum`
denote supported capacity, not configured or present-instance
cardinality. The bounded profile supports exactly these combinations:

| VR70 count | VR71 count | Circuit capacity | Zone capacity |
| --- | --- | --- | --- |
| 0 | 0 | 1 | 1 |
| 1 | 0 | 2 | 2 |
| 0 | 1 | 3 | 3 |
| 1 | 1 | 5 | 5 |
| 2 | 1 | 7 | 7 |
| 3 | 1 | 8 | 8 |

This is not a global hardware-capacity model and must not be extrapolated to
another mix. Two configured or confirmed circuits with circuit capacity `3`,
and two configured or confirmed zones with zone capacity `3`, are normal and
are not mismatches.

Those capacities only recommend bounded candidate planning. They never create
instances, select identities, require contiguous II slots, or replace a concrete
presence predicate. Circuit II09 remains independently considered. A missing,
non-integral, non-finite, out-of-bound, or conflicting capacity falls back to
the concrete group predicate without itself making presence qualification
incomplete. Full and `research` scans retain the declared II range. Preserve
the raw value, capacity interpretation, concrete presence results, and any
unmet planning guidance separately.

Other OP00 count fields retain count-guided cardinality semantics. A valid
count guides candidate generation; a valid zero suppresses only derived default
candidates and never erases an explicit positive observation. A missing,
non-integral, non-finite, out-of-bound, or conflicting count falls back to its
group's qualified predicate and leaves count-guided coverage incomplete.

Only an explicit profile mapping connects an information identifier to `(OP,GG)`.
In particular, ID=0010h does not imply GG=10h. Known groups remain scan candidates
even when their same-numbered information identifier returns zero.

#### 4.1.1 Request and reply (candidate)

Candidate interpretations, unconfirmed on the wire.

- The request is `B5 24` with length byte `03` and payload `00 IDlo IDhi`. The
  [identifier table](fixtures/b524-op00-system-information-ids.csv) gives, for
  each identifier, the name used in section 4.1, the Vaillant name and the
  candidate meaning.
- The reply is one float32 little-endian value. No unit, scale, count
  convention or NaN rule is defined for it.
- Identifier 0 is an expected circuit count and identifier 1 an expected zone
  count, each a supported capacity, not an installed count (section 4.1); a requester uses the circuit and zone indexes 0..8 (candidate). For the
  VRC720 family the register map gives the profile intervals `II=0x00..0x09` for
  circuits (a candidate bound, with `II=0x09` a candidate virtual native-water
  instance) and `II=0x00..0x0A` for zones; for the VRC700 family they are not
  established. The expected count is not a physical installation count.
- Identifier 8 is the VR70 module count. Identifier 0x10 is a candidate
  indication that ventilation is present when its value is 1 (VRC720 family);
  the value does not prove `GG=0x10` or device presence. A nonzero value of identifier 0x11 is a candidate count of cooling-capable
  heat pumps; its relation to the circuit cooling-allowed register
  (`OP=0x02, GG=0x02, RR=0x0006`) is not established.
- Identifier 0x000D is `heat_pump_count` in the identifier table above. A
  competing candidate reading, unconfirmed on the wire, treats a reply above 1.0
  to identifier 0x000D as an indication that no supported heat pump is
  available; the two readings conflict for such values, and which reading
  applies to which controllers is unresolved (see Open questions).

### 4.2 `0x01` DescribeParameter and `0x07` DescribeDeviceParameter

```text
System parameter:  01 GG II RRlo RRhi
Device parameter:  07 GG II RRlo RRhi
```

The historical `01 GG RR` request omitted the identifier and high address byte.
Its changing/misaligned replies do not prove a sliding-window dictionary or a
VRC720 buffer bug. Preserve them as historical observations, with the returned
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

#### 4.2.2 Description applicability

OP01 and OP07 metadata are meaningful only with a correlated selector and a
matching parameter codec. The static `FLAGS & 0x02` interpretation can identify
a writable candidate, but neither proves live writability nor authorizes a
write. An unknown codec leaves the response raw and unqualified. Empty or
unsupported descriptions provide no replacement validation evidence.

#### 4.2.3 Value constraints

A qualified matching description can constrain type, width, minimum, maximum
and step for numeric and non-enum values as well as enumerations. Missing or
unqualified metadata leaves those constraints Unknown. Historical short probes
do not replace a complete correlated OP01/OP07 description.

#### 4.2.4 Circuit type interpretation (`GG=0x02 RR=0x02`)

`GG=0x02 RR=0x02` (`circuit_type` / `mctype`) is a configuration register with raw values 0..4 on the VRC720 family. See [`ebus-vaillant-B524-register-map.md` mctype](./ebus-vaillant-B524-register-map.md#mctype--circuit-type) for the authoritative enum definition.

**Raw register meaning (Vaillant VRC720 manual):**

```text
0 = Inactive       Circuit unused
1 = Heating         Weather-compensated heating (mixing or direct)
2 = Fixed value     Circuit held at fixed target flow temperature
3 = DHW             Heating circuit used as DHW for additional cylinder
4 = Increase in return   Return temperature raise circuit
```

On the VRC720 family these raw values are the complete wire-level meaning; no resolution or context inputs are needed to interpret them. On the VRC700 family a value 5 with the label `PoolCircuit` is a candidate, unconfirmed on the wire (see the register map's [family enumerations](./ebus-vaillant-B524-register-map.md#enumerations-that-differ-by-family)); whether it occurs in replies is not established.

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

#### 4.2.7 OP=01h and OP=07h request and reply layouts (candidate)

Candidate interpretations, unconfirmed on the wire.

- Two candidate OP=01h requests, each with length byte `05`, are
  `01 00 FF 27 00` (system type 0, identifier `FF`, address `0x0027`, the DHW
  start-loading hysteresis range) and `01 01 FF 04 00` (system type 1, identifier
  `FF`, address `0x0004`, the DHW tapping set point range).
- The request selectors are SystemType (u8), Identifier (u8, `FF` in both
  requests) and Address (16-bit little-endian). Counted from the first reply
  data byte and assuming no opcode echo precedes it (section 2.8), a positive
  response carries SystemType (byte 0), Address (bytes 1-2, little-endian) and
  then Min, Max and Step (the `GG RRlo RRhi MIN MAX STEP` order of section
  4.2.1); for a float32 parameter, such as the two requests above, the spans are
  float32 little-endian at bytes 3-6, 7-10 and 11-14. The identifier is
  not echoed.
- For a float32 parameter the candidate reply length is 15 bytes, counted from
  the SystemType byte (three-byte header, then three four-byte spans); the
  uint16 record below is nine bytes. The unit and scale of the spans and the
  meaning of the step span are not established.
- For OP=07h the request carries SystemType, Identifier and Address; the response
  begins with SystemType and Address. The candidate positions are SystemType
  (byte 4), Identifier (byte 5) and a 16-bit Address (bytes 6-7) in the request,
  counted from the `B5` byte of the wire request (`B5` byte 0, `24` byte 1, `NN`
  byte 2, the opcode byte 3), and SystemType (byte 0) and a 16-bit Address
  (bytes 1-2) in the response, counted from the first reply data byte and
  assuming no opcode echo precedes it, as in the OP=07h replies of the
  observed-windows fixture (candidate widths and positions). OP=07h requests with their replies appear in
  [`fixtures/b524-op06-observed-windows-v1.json`](fixtures/b524-op06-observed-windows-v1.json);
  the codec of the reply spans is not qualified for every sample there, and the
  layout beyond SystemType and Address is unresolved.
- Candidate layout, unconfirmed on the wire: where the described parameter is a
  uint16, the three spans are two bytes each and the record is nine bytes (the
  three-byte header, then three two-byte spans): `GG`, `RR` (16-bit
  little-endian), then minimum, maximum and step as uint16 little-endian values.
  For `GG=0x02, RR=0x0002` the candidate record is `02 02 00 0000 0400 0100`
  (minimum 0, maximum 4, step 1).

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
- `0x06` is a separate opcode-scoped controller-mediated selector family. It is
  used for several remote families. The primary and secondary heat-source
  labels (`GG=0x01` and `GG=0x02`) remain family-qualified hypotheses.
- The selector meaning is always keyed on `(opcode, GG, II, RR)`, not on `GG`
  alone.

#### 4.3.1 Request framing and instance numbering (candidate)

Candidate interpretations, unconfirmed on the wire.

- The length byte `NN` counts `OP`, `OT`, `GG`, `II` and `RR` (six bytes) plus
  the value bytes (candidate). For OP=00h it is 3 (`OP` plus a 16-bit
  identifier), for OP=01h it is 5 (candidate). An OP=02h read has `NN=6`, for
  example zone 0 special-function status `B5 24 06 02 00 03 00 1B 00`
  (candidate); an OP=02h write sets `OT=01` and
  `NN = 6 + value length` (candidate). A buffer-availability read of the system
  group is `B5 24 06 02 00 00 00 8F 00` (candidate).
- Selector integers are little-endian 16-bit: `RR` in OP=02h and OP=06h
  requests and replies, the identifier in OP=00h, and the address in OP=01h
  (candidate).
- The instance byte `II` of an OP=02h read: for `GG=0x02` and `GG=0x03`, `II` is the zone or circuit number (one byte; a requester uses the candidate range 0..8. For the VRC720 family the [register map](ebus-vaillant-B524-register-map.md) gives the profile intervals `II=0x00..0x09` for `GG=0x02`, a candidate bound with `II=0x09` a candidate virtual native-water instance, and `II=0x00..0x0A` for `GG=0x03`; for the VRC700 family they are not established); `GG=0x09` uses the ventilation index (0 only on the VRC720 family), and `GG=0x00` and `GG=0x01`
  use `0x00`, except the VRC700 ventilation reads under `GG=0x00`, which take the
  ventilation index (candidate). The reply does not echo `II` (candidate).
- The instance byte of an OP=06h request is one-based (candidate). The VR70
  module-configuration read is `06 00 0B II 05 00` (candidate). The VRC700-family
  radio-sensor humidity read is `06 00 09 01 07 00` for accessor 1 and
  `06 00 0A II 07 00` with `II = accessor - 1` for accessors 2..9 (candidate).
- A literal `II=0xFF` (not shown to be a broadcast) appears in the commissioning-complete write and the five writes of section 4.11 (candidate).
- OP=06h read requests carry the operation type byte (`OT/RW=0x00`), a system
  type, an identifier and an address; a positive read reply carries the
  attribute byte
  (bit 0 Visible, bit 1 Read/Write, bits 2-7 reserved), the system type and the
  address (candidate). A write request appends the data; its reply carries a
  feedback byte (candidate values `0` no error, `1` read-only error, `2` range
  error; section 2.2) and the system type (candidate).
- The same register number is a different parameter in every `(OP, GG)`
  (candidate). For example `RR=0x0015` is a DHW recharge tapping set point in
  `OP=0x02, GG=0x01` (candidate; its value type is not established, and the
  requester matrix gives a four-byte value for the VRC720 family), a zone
  cooling-related item in
  `OP=0x02, GG=0x03`, and a heat-generator status item in
  `OP=0x06, GG=0x01/0x02` (candidate).

#### 4.3.2 Write encodings (candidate)

The [write templates](fixtures/b524-op02-write-templates.csv) list each write
body, with its family where one is stated; the multi-step sequences are in the
[write sequences](fixtures/b524-op02-write-sequences.csv). Every row of both
tables carries the status `candidate, unconfirmed on the wire`.

No write template or write sequence on this page or in
`b524-op02-write-templates.csv` / `b524-op02-write-sequences.csv` is documented
as safe to send; an ACK does not show the resulting device state, and a
separately established safety procedure and target qualification are required.

- Float values are a float32 little-endian value.
- Integers are a uint16 little-endian value; booleans are one byte `00` or `01`;
  16-bit enumerations are the low byte followed by `00`; dates and times are three-byte
  triples (section 4.7); the one-time DHW load is the byte `06` (start) or `00`
  (cancel). The one-byte enumerations `GG=0x01, RR=0x000D` (one-time DHW load)
  and `GG=0x03, RR=0x000E` (zone mode command, section 4.9) are written as
  one byte without a following `00`.
- The system configuration floats `RR=0x0001`, `0x0023`, `0x0026` and `0x0046`
  of `GG=0x00` use the body `02 01 00 00 RRlo RRhi b0 b1 b2 b3`; the scalar
  bytes `RR=0x0007`, `0x0009`, `0x000A` and `0x0014` use
  `02 01 00 00 RRlo RRhi val`; the system scheme and the VR71 configuration
  (`RR=0x0036`, `0x002F`) use `02 01 00 00 RRlo RRhi Vlo Vhi`.
- The value width of `GG=0x00, RR=0x000A` is unresolved: the one-byte body above
  is a one-byte candidate (`uint8`), while the register catalog gives `u16`. The
  [register matrix](fixtures/b524-op02-requester-register-matrix.csv) therefore
  carries the width as `1 or 2` and the type as `uint8 or uint16 LE` for this
  register in both families (candidate, unconfirmed on the wire).
- The VR70 module configuration is read and written through OP=06h on the
  VRC720 family as `06 01 0B II 05 00 Vlo Vhi` (write) with `II` one-based.
- Writes whose request body is shown with `II=FF`, and the room-control writes,
  have their own sections (4.10 and 4.11).

### 4.4 `0x03` / `0x04` Timer Schedules

`ReadTimer` and `WriteTimer` use the VRC700 schedule profile, identified by
`70000` or `B7S00`. Verify that identity before a live read. The
[VRC700 crosswalk](ebus-vaillant-regulators.md#vrc700-operation-profile)
supplies model-row context but does not replace that command guard.
VRC720-family controllers use the [B555 timer protocol](ebus-vaillant-b555-timer-protocol.md);
sharing a destination address does not qualify the B524 schedule profile.

```text
ReadTimer:  03 GG II ADDRESS WEEKDAY
WriteTimer: 04 GG II ADDRESS WEEKDAY START1 STOP1 START2 STOP2 START3 STOP3
Reply:      PARAM_CONFIG START1 STOP1 START2 STOP2 START3 STOP3
```

The read request is five bytes, the write request eleven bytes, and the read
reply seven bytes after transport normalization. These operations do not contain
an `RW` byte. `WEEKDAY=00..06` means Monday through Sunday (the candidate
aggregate values 7..9 of OP=04h are in section 4.4.1). Retain
`PARAM_CONFIG` as a raw byte; do not infer writable access from it.

Time codes `00..90` represent ten-minute units. An unused slot is `90 90`.
A stop code `90` paired with a lower start code means 24:00. Retain unknown
codes as raw evidence; they do not become valid time values.

| GG | II | ADDRESS | Channel |
| --- | --- | --- | --- |
| 00 | 00 | 01 | Noise reduction |
| 00 | 00 | 02 | Ventilation |
| 00 | 00 | 03 | Tariff (electricity high-tariff period) |
| 01 | 00 | 01 | Domestic hot water |
| 01 | 00 | 02 | Circulation |
| 03 | Selected zone | 01 | Zone cooling |
| 03 | Selected zone | 02 | Zone heating |

**System row addressing (`GG=00`):** observed Vaillant addressing assigns
`0x01` to noise reduction and `0x02` to ventilation. This conflicts with the
VRC700 ebusd configuration (`15.700.csv`), which assigns the system timer
channel map the other way round — `0x01` ventilation, `0x02` noise
reduction. Both assignments are kept visible here; hardware confirmation by
VRC700 owners is pending. The DHW, circulation, and zone rows are unaffected
by this conflict.

#### 4.4.1 Requests, replies and selectors (candidate)

Candidate interpretations, unconfirmed on the wire.

- The read request for VRC700-family controllers is
  `QQ ZZ B5 24 05 | 03 GG II ADDRESS WEEKDAY` (length byte `05`) and the write
  request is
  `QQ ZZ B5 24 0B | 04 GG II ADDRESS WEEKDAY START1 STOP1 START2 STOP2 START3 STOP3`
  (length byte `0B`). `ZZ` is the controller address.
- The read reply payload is seven bytes: `PARAM_CONFIG`, then `START1`, `STOP1`,
  `START2`, `STOP2`, `START3`, `STOP3` as one-byte time codes. No meaning is
  established for the `PARAM_CONFIG` bits. The write reply is one feedback byte:
  0 is the candidate success value and a nonzero value a failure.
- A time code is minutes divided by 10, so `00..90` (0..144) span 00:00..24:00.
  A day carries at most three start/stop pairs in its six time bytes.
- The three selector bytes `GG`, `II` and `ADDRESS` are not an `RR` register
  selector; OP=03h/04h do not use the OP=02h/06h register selector. The program
  selectors are given in the
  [program selector table](fixtures/b524-op03-op04-program-selectors.csv):
  heating `(3, zone index, 2)`, cooling `(3, zone index, 1)`, DHW `(1, 0, 1)`,
  circulation pump `(1, 0, 2)` and ventilation `(0, 0, 2)` or `(0, 0, 1)` (the two
  system channel assignments above conflict; unresolved). The address values
  carry the Vaillant names given in the table in section 4.4; the keys for `GG`
  are in section 3.6. The ventilation program selector uses identifier 0 (candidate).

##### Weekday codes

| Operation | 0..6 | 7 | 8 | 9 |
| --- | --- | --- | --- | --- |
| OP=03h `WEEKDAY` | Monday..Sunday | not used (candidate) | not used (candidate) | not used (candidate) |
| OP=04h `WEEKDAY` | Monday..Sunday | Monday-Sunday | Saturday-Sunday | Monday-Friday |
| B555 `A6` (candidate; [B555 timer protocol](ebus-vaillant-b555-timer-protocol.md)) | Monday..Sunday | Monday-Sunday | Monday-Friday | Saturday-Sunday |

The aggregate values 7..9 of OP=04h are a candidate interpretation for the
VRC700 family, unconfirmed on the wire; OP=03h does not use them (candidate). The
B555 `A6` group-day values are candidates, unconfirmed on the wire. The
numbering of 8 and 9 differs between OP=04h and B555 `A6`. One request carries one weekday; a full program is seven requests
(candidate).

### 4.5 `0x09` / `0x0A` Events and `0x0B` / `0x0C` Event Setpoints

**Hypothesis — experimental schema:** The layouts below define the explicit
Event/EventSetPoint command schema. Native wire qualification remains Unknown
for a model/version until a sanitized, correlated request/reply observation
qualifies the selectors, response length, and byte interpretation. An
implementation or a deterministic fixture does not establish that qualification.
Retain the complete request context and raw reply when contributing an
observation; a successful value decode alone is insufficient.

These operations are separate from OP02/OP06 scalar register discovery.
`ADDRESS` is an event selector, not an RR16 scalar address.

```text
GetEvent:         09 GG II ADDRESS WEEKDAY_CODE
SetEvent:         0A GG II ADDRESS WEEKDAY_CODE VALUE1..VALUE7
GetEventSetPoint: 0B GG II ADDRESS WEEKDAY_CODE
SetEventSetPoint: 0C GG II ADDRESS WEEKDAY_CODE VALUE1..VALUE7
Read replies:    PARAM_CONFIG VALUE1..VALUE7
```

Each read request is five bytes, each setter request twelve bytes, and each
read reply eight bytes after transport normalization. Retain the weekday-code
byte exactly as requested; the Event profile does not assign it the ReadTimer
weekday interpretation. Neither `II` nor the request selector is echoed in
these replies, so correlation depends on the outstanding request context.

| Selected profile | GG | Candidate ADDRESS catalog | Candidate setpoint codec |
| --- | --- | --- | --- |
| `system` | 00 | 01, 02, 03 | Numeric code divided by two, degrees Celsius |
| `dhw` | 01 | 01, 02 | FD=enable, FE=disable, FF=replacement; other codes unknown |
| `zone` | 03 | 01, 02 | Numeric code divided by two, degrees Celsius |

For `GetEvent`, VALUE1 remains raw. VALUE2..VALUE7 codes `00..90` may be
interpreted as ten-minute units; larger codes remain raw and unqualified.
For `GetEventSetPoint`, decoding requires the explicitly selected profile above.
Always retain all seven original codes and the raw `PARAM_CONFIG` byte.
A successful decode does not establish installed equipment or authorize a write.

The Event families do not inherit the VRC700-only timer gate. Support is
qualified by each target's actual response; this specification does not claim
that every VRC720- or VRC700-family controller implements them. Undocumented profile/address
combinations remain rejected rather than receiving an invented codec.

Event-code semantics and supported selector ranges remain family-qualified.
A response of the expected length does not establish those semantics, physical
presence, writable behavior or support outside the observed selector. A read
retry must preserve the exact selector; write repetition has distinct effects
and cannot be inferred from read behavior.

#### 4.5.1 Event selector candidates

Candidate interpretation, unconfirmed on the wire. The event operations share one
selector layout: `GG` is byte 4, `II` byte 5, `ADDRESS` byte 6 (one 8-bit field)
and `WEEKDAY_CODE` byte 7, counted from the `B5` byte of the wire request (`B5`
byte 0, `24` byte 1, `NN` byte 2, the opcode byte 3). The [event selector table](fixtures/b524-event-selector-candidates.csv)
lists these rows:

| `GG` | Label | `ADDRESS` | Address label |
| --- | --- | --- | --- |
| 0x00 | system | 1 | noise-reduction period (conflicting assignment: ventilation; see section 4.4) |
| 0x00 | system | 2 | ventilation period (conflicting assignment: noise reduction; see section 4.4) |
| 0x00 | system | 3 | high-tariff period |
| 0x01 | DHW circuit | 1 | DHW period |
| 0x01 | DHW circuit | 2 | circulation-pump period |
| 0x02 | mixer circuit | 0..255 | no candidate name known |
| 0x03 | zone | 1 | cooling period |
| 0x03 | zone | 2 | heating period |
| 0x04 | solar circuit | 0..255 | no candidate name known |
| 0x05 | solar loaded tank | 0..255 | no candidate name known |
| 0x06 | device | **Unknown** | no candidate name known |
| 0x07 | generator | **Unknown** | no candidate name known |
| 0x08 | delta-T control | **Unknown** | no candidate name known |
| 0x09 | ventilation circuit | **Unknown** | no candidate name known |

Address labels follow the OP=03h/04h table in section 4.4, including its
conflict with the VRC700-family community configuration.

The physical meaning of the `PARAM_CONFIG` bits is not known.
The candidate value encodings are:

- `GetEvent` `VALUE1` is a one-byte value 0..255; `VALUE2..VALUE7` of `GetEvent` and
  of `SetEvent` use the time-code table 0..144 = 00:00..24:00 in
  ten-minute steps. One candidate reading also applies the time-code table to
  `SetEvent` `VALUE1`, while `GetEvent` `VALUE1` stays a raw byte; the encoding
  of `SetEvent` `VALUE1` is unresolved (see Open questions).
- `GetEventSetPoint` and `SetEventSetPoint` values are code divided by 2 in
  degrees Celsius for the `system` and `zone` profiles of section 4.5 and for a
  mixer-circuit profile (candidate). The mixer-circuit profile (`GG=0x02`) is
  outside the profile catalog of section 4.5, and no address label is known for
  `GG=0x02` in the table above (`ADDRESS` 0..255), so the mixer codec is not
  tied to a selector, unresolved. The DHW profile
  uses the text values 253 enable, 254 disable and 255 replacement, without a
  unit.

No request using OP=09h, OP=0Ah, OP=0Bh or OP=0Ch is known; OP=08h is the candidate request of section 4.6, and OP=07h requests with their replies appear in [`fixtures/b524-op06-observed-windows-v1.json`](fixtures/b524-op06-observed-windows-v1.json).
Whether a controller supports the event operations is not known. OP=08h is a candidate zone status read for a remote
control that includes the special-function status (section 4.6); the zone special-function status is also read with
`OP=0x02, OT=0x00, GG=0x03, RR=0x001B`.

### 4.6 `0x08` ReadVR91

The VRC700 profile (`70000` or `B7S00`) uses a one-byte request `08` and an
eight-byte response. The [VRC700 crosswalk](ebus-vaillant-regulators.md#vrc700-operation-profile)
adds model-row context without changing that command guard:

```text
BINDING_ZONE SPECIAL_FUNCTION_STATUS HEATING_MODE COOLING_MODE
STATUS_INFO FROST_PROTECTION HEATING_TEMPERATURE_RAW COOLING_TEMPERATURE_RAW
```

These field names describe the response structure. Bit meanings, temperature
scaling and special-value semantics remain unqualified. Raw bytes alone do not
establish a physical measurement or support on another controller profile.

Candidate positions (unconfirmed on the wire), counted from the first reply data
byte and assuming no opcode echo precedes them (section 2.8): byte 0 zone
binding, byte 1 special-function status, byte 2 heating operating mode, byte 3
cooling operating mode, byte 4 status information, byte 5 frost protection,
byte 6 heating temperature and byte 7 cooling temperature. Each field is one byte; the value scale is not established. The
candidate bits of the status byte are bit 0 system error, bit 1 maintenance,
bit 2 zone period heating, bit 3 zone period cooling, bit 4 cooling allowed and
bits 5-7 reserved.

### 4.7 Date and time triples and system clock

Candidate interpretations, unconfirmed on the wire. The
[calendar and clock selector table](fixtures/b524-op02-calendar-clock-selectors.csv)
lists a subset of the date and time selectors; each of its rows carries the
status `candidate, unconfirmed on the wire`. The other date and time selectors
are given in sections 4.8 and 4.9 and in the
[register matrix](fixtures/b524-op02-requester-register-matrix.csv).

- A date is a three-byte triple (day, month, year) and a time is a three-byte
  triple (hour, minute, second). The reply payload is three bytes (candidate,
  unconfirmed on the wire).
- A date triple is day 1..31, month 1..12 and, as a candidate reading, year as
  byte + 2000; the year-byte codec is unresolved (see below).
- The year byte of a written date triple is a candidate year minus 2000,
  unconfirmed on the wire. Time triples are hour, minute, second.
- The cancel bodies carry the date triple `01 01 0F` (cooling period: `01 01 13`)
  and the time triple `00 00 00` (candidate).
- The year byte of these triples is a candidate offset from 2000, with no BCD
  step. The scalar date observations in the register map (for example holiday and
  manual cooling defaults) are BCD-qualified. Which codec each register uses on
  each family is not established.
- **System clock reads** (both families): `OP=0x02, OT=0x00, GG=0x00, II=0x00`,
  `RR=0x0034` date (day, month, year bytes) and `RR=0x0035` time (hour, minute,
  second bytes). Candidate reply layout: an attribute byte of value 0, then `GG`, then the
  register echoed little-endian, then a three-byte payload (the position of the
  attribute byte relative to any opcode echo is described in section 2.8). Time and
  date are read by separate requests.
- **System clock write** (both families): `OP=0x02, OT=0x01, GG=0x00, II=0x00`,
  first the time, body `02 01 00 00 35 00 hh mm ss`, then the date, body
  `02 01 00 00 34 00 dd mm yy` with `yy` the year minus 2000 (length byte 9).

### 4.8 System holiday, zone holiday and cooling for days

Candidate interpretations, unconfirmed on the wire. The step lists are in the
[write sequences](fixtures/b524-op02-write-sequences.csv).
All writes below are `OP=0x02, OT=0x01`; the instance is `0x00` except where the text names a zone.

No write template or write sequence on this page or in
`b524-op02-write-templates.csv` / `b524-op02-write-sequences.csv` is documented
as safe to send; an ACK does not show the resulting device state, and a
separately established safety procedure and target qualification are required.

| Command | Family | Sequence |
| --- | --- | --- |
| System holiday set | VRC700 | `GG=0x00` `RR=0x0082` set point (float32), then `RR=0x0071` start date, then `RR=0x0072` end date, in that order |
| System holiday cancel | VRC700 | `RR=0x0071` then `RR=0x0072`, each `01 01 0F`, in that order |
| System holiday set | VRC720 | `GG=0x00` `RR=0x00F6` set point (float32), `RR=0x00F2` start date, `RR=0x00F3` start time, `RR=0x00F4` end date, `RR=0x00F5` end time, in that order |
| System holiday cancel | VRC720 | `RR=0x00F2` `01 01 0F`, `RR=0x00F4` `00 00 00`, `RR=0x00F3` `01 01 0F`, `RR=0x00F5` `00 00 00`, `RR=0x00F7` `01`, in that order |

- The register roles in the VRC720 set sequence (`RR=0x00F3` start time and
  `RR=0x00F4` end date) disagree with the catalog rows of the register map
  (`RR=0x00F3` system holiday end date and `RR=0x00F4` system holiday start
  time). The cancel sequence writes a date-shaped triple to `RR=0x00F2` and
  `RR=0x00F3` and a time-shaped triple to `RR=0x00F4` and `RR=0x00F5`. The disagreement is unresolved.
- The set point, the start and the end are carried by the request bodies
  (float32 for the set point). The unit of the
  set point (the register map lists °C for `RR=0x00F6`, unconfirmed on the wire)
  and any persistence in the controller are not established.
- Registers that reflect a system holiday (candidate), for the zone indexes 0..8 (range used by a requester). On the VRC720 family, per zone `GG=0x03` `RR=0x001B`, `RR=0x0014`, `RR=0x0020`, `RR=0x0004`, `RR=0x0021`, `RR=0x0003`, `RR=0x0005`; for DHW `GG=0x01, II=0x00` `RR=0x000F`, `RR=0x0009`, `RR=0x0010`, `RR=0x000A`, `RR=0x0011`; for ventilation `GG=0x09, II=0x00` `RR=0x0004`, `RR=0x0008`, `RR=0x0007`, `RR=0x000A`, `RR=0x0009`.
- Zone holiday reads on the VRC720 family (`OP=0x02, OT=0x00, GG=0x03`, `II` =
  zone): start date `RR=0x0003`, end date `RR=0x0004`, end time `RR=0x0020`,
  start time `RR=0x0021` (three bytes each) and holiday set point `RR=0x0005`
  (float32; candidate unit °C, as in the register map, unconfirmed on the wire; a
  NaN means unavailable). Ventilation holiday
  reads (`GG=0x09`): start date `RR=0x0009`, start time `RR=0x000A`, end date
  `RR=0x0007`, end time `RR=0x0008`. VRC700-family DHW holiday reads (`GG=0x01`,
  `II=0x00`): start `RR=0x0009`, end `RR=0x000A`; VRC700-family system holiday reads
  (`GG=0x00`, `II=0x00`): start `RR=0x0071`, end `RR=0x0072`, each a three-byte date
  triple. Date and
  time parts are read separately.
- **Cooling for a number of days.** On the VRC700 family the count is
  `GG=0x00, II=0x00, RR=0x0006` as a uint16 little-endian value (the reply
  payload is two bytes, candidate; the write cancels with `00 00`); the unit of
  the count is not established. On the VRC720 family the manual-cooling start date
  is `GG=0x00, II=0x00, RR=0x00DA` (three-byte date) and the stop date
  `RR=0x00DB`; the cancel triple is `01 01 13`, and the start date is written
  before the end date.
- **VRC700-family ventilation mode.** `OP=0x02, OT=0x00, GG=0x00, II=` ventilation index (one byte), `RR=0x0016`, uint16 little-endian: 1 AUTO, 2 DAY, 3 SET_BACK. The
  write selector and the write encoding are not established.

### 4.9 Quick veto, away mode and switching back to time control

Candidate interpretations, unconfirmed on the wire. All writes are
`OP=0x02, OT=0x01`. The statement on sending writes in section 4.8 applies to
every write in this section.

- **Quick veto** (both families, `GG=0x03`, `II` = zone number (one byte)):
  set point `RR=0x0008` as float32 (body `02 01 03 II 08 00 f32`), mode command
  `RR=0x000E` as one byte (body `02 01 03 II 0E 00 xx`) and, on the VRC720
  family, duration `RR=0x0026` as float32 (body `02 01 03 II 26 00 f32`). The
  units of temperature and duration are not established.
- VRC700 family: set writes `RR=0x0008` and then `RR=0x000E` = 03; modify writes
  `RR=0x0008` only; cancel writes `RR=0x000E` = 00. VRC720 family: set writes
  `RR=0x0008` and then `RR=0x0026`, in that order; a request carrying only
  `RR=0x0008` or only `RR=0x0026` is also a candidate form; cancel writes `RR=0x000E` = 00; no `RR=0x000E` = 03 write is known for this family.
- Registers that reflect the quick veto (candidate): the zone special function
  `RR=0x001B` (width unresolved, one or two bytes: a one-byte reply is read as
  uint8 and a two-byte reply as uint16 little-endian; the value, or the low byte
  of the two-byte form, is 4 QUICK_VETO or 0 none; 7 is the value associated
  with an away command) and the displayed set point `RR=0x0014` (float32). On the VRC720 family a quick veto in mode 4 also has the
  end time `RR=0x001E` and end date `RR=0x0024` (three bytes each, `GG=0x03`).
- **Away mode** (VRC720 family): set writes `GG=0x00, II=0x00` `RR=0x00F6` =
  float32 15.0 (bytes `00 00 70 41`), then for each zone `i` = 0..8 (range used by a requester) `GG=0x03,
  II=i`: `RR=0x0003` start date, `RR=0x0021` start time, `RR=0x0004` end date,
  `RR=0x0020` end time. After an away request, `GG=0x03, RR=0x001B` reads 7 (candidate). Cancel
  writes `GG=0x00` `RR=0x00F2` `01 01 0F`, `RR=0x00F4` `00 00 00`, `RR=0x00F3`
  `01 01 0F`, `RR=0x00F5` `00 00 00` and `RR=0x00F7` `01`. The candidate cancel
  sequence does not write the per-zone registers `RR=0x0003`, `RR=0x0021`,
  `RR=0x0004` and `RR=0x0020` of the set sequence; whether those are reset is
  not established.
- **Switching back to time control** (VRC720 family): `GG=0x03`, `II` = the zone number (one byte), `RR=0x000E` = 00. After the request, the special-function value at `RR=0x001B`, or the low byte of its two-byte form, is 0 (candidate).
- No ACK, response correlation or persistence is established for any of the
  holiday, away, quick-veto or clock writes. The setpoint unit, the duration
  unit, controller acceptance, calendar validity at the controller and the
  installed index domain are not established.

### 4.10 Room-control writes and zone-mapping reads

Candidate interpretations, unconfirmed on the wire. The templates are in the
[write templates](fixtures/b524-op02-write-templates.csv). The statement on
sending writes in section 4.8 applies to every write in this section.

- **Mode write** (both families): `QQ ZZ B5 24 08 02 01 03 II 06 00 V0 V1`, that
  is length byte `08`, OP=02h, OT=01h, `GG=0x03`, `II`, `RR=0x0006` and `V0 V1` a 16-bit little-endian mode code (candidate values 0 and 2).
- **Set point write.** VRC720 family: `QQ ZZ B5 24 0A 02 01 03 II 22 00 V0 V1 V2 V3`
  with `RR=0x0022` (zone room-temperature set point, manual) and `V0..V3` a
  float32. VRC700 family: the same layout with `RR=0x0007` (comfort
  room-temperature set point, heating).
- `ZZ` is the controller address (not an address of any wireless device) and the
  length byte `NN` is 6 plus the length of the value bytes. The bytes shown are
  a frame before the CRC (from `QQ` to the last value byte).
- `II` is the zone number (one byte). The mode is written first and the set point second, in that order. Nothing shows that a zone number denotes a circuit or that the controller accepted the value.
- Registers that reflect the room-control writes (candidate): `RR=0x0022` and `RR=0x0014`
  (VRC720 family), `RR=0x0007` and `RR=0x0014` (VRC700 family), `RR=0x0006` and
  `RR=0x0014`.
- **Zone-mapping reads.** The zone binding is read with
  `OP=0x02, OT=0x00, GG=0x03, II, RR=0x0013` (body `02 00 03 II 13 00`, `II` the zone number (one byte)); the candidate reply carries `GG=0x03`, `RR=0x0013`
  and two bytes, a uint16 little-endian value. The circuit index is read with
  `RR=0x001C`; the candidate reply is one byte, a signed 8-bit value. The physical
  meaning of the index, including -1, is not established.
- No instance echo and no timestamp in the replies are known (candidate). The
  zone numbers used by a requester are 0..8 (candidate). For the VRC720 family
  the register map gives the profile interval `II=0x00..0x0A` for zones, for the
  VRC700 family it is not established, and the installed zone cardinality is not
  established.
- Candidate binding labels: VRC720 family 0 NONE, 1 CENTRAL_CONTROL,
  2..5 REMOTE_CONTROL1..4; VRC700 family 0 NONE, 1 CENTRAL_CONTROL, 2..9
  REMOTE_CONTROL1..8.

### 4.11 Writes with II=FF (DHW, cylinder and buffer registers)

Candidate interpretations, unconfirmed on the wire. The same candidate bodies
apply to the VRC720 family and the VRC700 family; all use `OP=0x02, OT=0x01` and the
literal instance `II=FF`. The statement on sending writes in section 4.8 applies
to every write in this section:

| Write | Body | Value |
| --- | --- | --- |
| DHW tapping set point (`RR=0x0004`) | `02 01 01 FF 04 00 <f32 LE>` | float32 little-endian |
| Tank start-loading hysteresis (`RR=0x0027`) | `02 01 00 FF 27 00 <f32 LE>` | float32 little-endian |
| CH buffer offset (`RR=0x00A2`) | `02 01 00 FF A2 00 <f32 LE>` | float32 little-endian |
| `external_energy_management_enabled` (`RR=0x00B6`) | `02 01 00 FF B6 00 <u8 0\|1>` | one byte, 0 or 1 |
| One-time DHW load (`RR=0x000D`) | `02 01 01 FF 0D 00 06` / `02 01 01 FF 0D 00 00` | one byte, 6 start or 0 cancel |

- The units are not established (candidate: °C for the tapping set point, K for
  the hysteresis and offsets); the meaning of the written values and the
  controller's reaction to any of these writes are not established.
- The activation register is also read with `02 00 00 00 B6 00`.

## 5. Topology-Significant Registers

Two registers in `OP=0x02, GG=0x00` carry system-level topology information that constrains the interpretation of other groups:

| RR | Name | Wire | Semantics |
|----|------|------|-----------|
| `0x0036` | `hydraulic_scheme_code` | u16 | Hydraulic scheme number (1..16). Defines the physical piping topology of the heating system (number/type of heat sources, mixing circuits, buffer tanks, solar integration). Different scheme numbers imply different valid group/register combinations. |
| `0x002F` | `functional_module_configuration_code` | u16 | VR71 functional module configuration (1..11). Encodes which mixing/direct circuits the VR71 hardware module manages. Combined with `hydraulic_scheme_code`, determines circuit ownership and whether FM5-backed families (solar, cylinders) are structurally valid. |

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

## 7. Open Items

Open protocol questions remain marked inline as **Hypothesis** or **Unknown**
until publishable correlated evidence qualifies them.

### Open questions — numeric formats and reply attributes

- The reply layout and attribute interpretation outside the characterized
  VRC720 profile remain unconfirmed, including whether `II` is echoed.
- The value width of `OP=0x02, GG=0x03, II=<zone>, RR=0x001B` remains
  unresolved between the one-byte candidate format and two-byte catalog
  entry.
- The volatility, persistence and time-to-live of B524 parameters are not defined
  here; visibility and role information do not classify a parameter as configuration or state.
- No wire observation establishes `0x7FFFFFFF` as an inactive integer-style
  float pattern; the NaN example does not establish that interpretation.
- Which numeric and enum definitions apply to an installed controller remains
  open; controller families require separate qualification.
- The interpretation of OP00 replies containing NaN, infinity or out-of-range
  values is not established.

### Open questions — reply layouts and register interpretation

- The full key domain of the OP=06h and OP=07h system-type key, including labels
  for the values `0x0E` and `0x0F`, is not established.
- Whether identifier `0x000D` carries a heat pump count or, for replies above
  1.0, an indication that no supported heat pump is available, and whether the
  reading depends on the controller software, is unresolved.
- Apart from what the observed-windows fixture shows (OP=07h requests with
  replies, section 4.2.7, and two OP=06h reads of `GG=0x0E` and `GG=0x0F`,
  `II=0x01`, `RR=0x0033`, whose replies begin with the flags byte and carry
  neither an opcode echo nor the instance byte), no controller reply to the
  requests described in sections 2.8 and 4.1.1 to 4.2.7 is known on the wire.
  For the other requests the reply layout (position of the attribute byte),
  whether the instance byte is echoed and the meaning of the attribute byte are
  unconfirmed on the wire.
- The OP00 reply (one float32 little-endian value; no unit, scale, count
  convention or identifier echo) is unconfirmed on the wire.
- The OP01 positive response layout (SystemType, Address, then Min, Max and Step,
  as float32 little-endian for a float32 parameter and as uint16 little-endian
  for a uint16 parameter, no identifier echo) is unconfirmed on the wire.
- Whether a controller checks the OP=01h request length is unresolved.
- Whether the identifier byte of an OP=01h request changes the reply is
  unresolved.
- The OP02 reply split (attribute byte, `GG`, `RR`, `n = length - 4`, lengths 4
  to 33, instance byte not echoed) and the OP06 reply split with the VR70 and
  humidity replies are unconfirmed on the wire.
- Whether an OP=02h or OP=06h reply begins with an echo of the request opcode (a
  candidate layout in section 2.8) or begins with the attribute byte (section
  2.2) is unresolved beyond the two OP=06h replies of the observed-windows
  fixture, which begin with the flags byte without an opcode echo.
- Whether OP=01h and OP=08h replies begin with an opcode echo is unresolved;
  the candidate positions of sections 4.2.7 and 4.6 assume none.
- The meaning of the attribute byte on the wire is unresolved; the candidate
  meanings of bit 0 (Visible) and bit 1 (Read/Write) are unconfirmed, and no
  user level, configuration or state class or write permission is established.
- The candidate write status values (`0` no error, `1` read-only, `2` out of
  range) are unconfirmed on the wire, and whether they apply to an OP=02h write
  reply is not established.
- A zone special-function status reply (`OP=0x02, GG=0x03, RR=0x001B`) is
  candidate-shaped with 2 value bytes, a one-byte width is also a candidate; the
  width is unresolved.
- The value width of `GG=0x00, RR=0x000A` is unresolved (one byte `uint8` or two
  bytes `uint16`, in both families).
- The value widths of `GG=0x03, RR=0x0011` (both families), `GG=0x03, RR=0x0027`
  and `GG=0x03, RR=0x002C` (VRC720 family) are unresolved (one byte `uint8` or
  two bytes `uint16`): the register matrix carries `1 or 2`, the register map
  lists `u16`, and the candidate zone-enable write body for `RR=0x0011` is one
  byte.
- Which of the two Vaillant names `circuit_type` and
  `circuit_type_of_mixed_circuit_external` describes the value of
  `OP=0x02, GG=0x02, RR=0x0002` (section 4.2.4) is unresolved.
- The VRC700 ventilation mode (`GG=0x00, RR=0x0016`) as a 16-bit text table
  1 AUTO, 2 DAY, 3 SET_BACK is unconfirmed on the wire; the write selector is not
  established.
- The DHW circuit type (`OP=0x02, GG=0x01, II=0x00, RR=0x0001`) is a raw 16-bit
  value; no request for it as a type is known, and the
  raw values have no established meaning.
- The raw OP00 values 0, 1, 2, 3, 5, 6 and NaN have no established meaning, and the units of the OP01 spans and the meaning of the step span are not established.
- Which enumeration and unit table applies to an
  installed controller is not established; the enumerations given are candidates
  per family.
- OP=07h requests with their replies appear in the observed-windows fixture, but
  the codec and layout of their replies beyond SystemType and Address are
  unresolved; no request using OP=08h to OP=0Ch is established on the wire, and
  no layout of OP=05h is known (**Unknown**).
- That the PeBUS profile of the VRC700 family carries neither OP=03h nor OP=04h
  is a candidate, unconfirmed on the wire; whether those operations are
  available on that profile is unresolved.
- Several selectors in the
  [register matrix](fixtures/b524-op02-requester-register-matrix.csv) have no known decoder shape; the enumeration values of the VR70 module configuration, the system
  scheme and the VR71 configuration are unknown.
- The year-byte codec of B524 date triples (offset from 2000 in the triples,
  BCD in the scalar observations of the register map) is unresolved for each
  register and family.

### Open questions — periods, events, calendar and clock

- The OP03 reply payload (`PARAM_CONFIG` and six one-byte time codes) and the
  OP04 one-byte feedback (0 success, nonzero failure) are unconfirmed on the wire.
  The meaning of the `PARAM_CONFIG` bits is unknown.
- Whether controllers other than the VRC700 family accept OP=03h is unknown, and
  the OP04 aggregate day values 7..9 are unconfirmed on the wire.
- The ventilation program selector uses identifier 0 (candidate); no distinct
  wire instance for a non-zero index is established.
- The B555 `A6` group-day codes 7 to 9 and the OP=04h aggregate values 7 to 9
  are both unconfirmed on the wire; their numbering differs.
- The `PARAM_CONFIG` bit meaning, the Temp semantics beyond the candidate codes
  and controller support for OP=09h to OP=0Ch are unknown.
- The encoding of `SetEvent` `VALUE1` (a time code, or a raw one-byte value like
  `GetEvent` `VALUE1`) is unresolved.
- The mixer-circuit set point profile (`GG=0x02`) is outside the profile catalog
  of section 4.5, and no address label is known for it; its codec is not tied to
  a selector (unresolved).
- The set point unit of the system holiday (both families; the register map lists
  °C for `RR=0x00F6`), the set point unit of
  the zone holiday reads (candidate °C), the unit of the cooling-for-days count
  (the register map lists days for `GG=0x00, RR=0x0006`), and the units of
  the quick-veto set point and duration (the register map lists °C for
  `GG=0x03, RR=0x0008` and hrs for `GG=0x03, RR=0x0026`) are not established.
- Controller acceptance, calendar validity at the controller, persistence in the
  controller and the installed index domain are not established for the holiday,
  away, quick-veto and cooling writes. No ACK or response correlation is
  established for these writes.
- The clock write (time, then date) is unconfirmed on the wire; the controller's
  reply and acceptance are not established.
- The role of `RR=0x00F3` and `RR=0x00F4` in the VRC720-family system holiday and
  away sequences disagrees with the register-map rows and is unresolved.
- Whether the VRC720-family away cancel resets the per-zone registers written by
  the away set sequence (`GG=0x03, RR=0x0003`, `0x0021`, `0x0004`, `0x0020`) is
  not established; the candidate cancel sequence does not write them.

### Open questions — room-control writes, zone mapping and `II=FF` writes

- The room-control mode write (`RR=0x0006`, a 16-bit little-endian mode code)
  and set point writes (`RR=0x0022` on the VRC720 family, `RR=0x0007` on the
  VRC700 family) are unconfirmed on the wire; nothing shows that the zone numbers denote circuits or that the controller accepted a value.
- The physical meaning of the signed index at `RR=0x001C`, including -1, and the
  installed zone cardinality are not established.
- The controller's reaction to the five `II=FF` writes of section 4.11 and the meaning
  and unit of the written values are not established.
- No B524 register that carries valve demand, valve position, a room list or a
  wireless device identifier is known.
