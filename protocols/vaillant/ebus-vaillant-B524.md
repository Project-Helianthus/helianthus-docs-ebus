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
is a profile-specific inference, not a universal B524 wire contract or proof of
live writability.

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

`0x7FFFFFFF` is a candidate no-data value in integer replies. Preserve it raw
and keep any no-data treatment profile-qualified until a correlated public
capture establishes the behavior.

### 2.5 Asymmetric read/write paths

Some B524 control registers use different GG/RR addresses for reading vs writing. The **write address** (used in `OT=0x01` frames) can differ from the **read address** (used in `OT=0x00` frames). This is a controller implementation pattern, not a general B524 feature.

**Historical asymmetric-path hypothesis -- System Quick Mode:**

The historical role labels below remain unqualified. The current register names
alone do not demonstrate that these selectors form one control path.

| Operation | Path | Register |
|-----------|------|----------|
| Read active flag | `OP=0x02, GG=0x00, RR=0x0016` | `system_ventilation_operating_mode` (dormant when no mode active) |
| Read mode value | `OP=0x02, GG=0x00, RR=0x0074` | `system_quick_mode` (dormant when no mode active) |
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
| `u16` | Little-endian uint16 | 2 bytes | Primary integer type. ebusd may decode only low byte for some enums |
| `u32` | Little-endian uint32 | 4 bytes | Energy counters, pump hours/starts |
| `f32` | IEEE 754 float32 (see note below) | 4 bytes | Primary numeric type for temperatures, pressures, percentages |

> **Profile-dependent f32 byte order:** The characterized BASV2 controller uses little-endian float32. A heat-pump HMU profile may use big-endian float32; qualify that codec independently before reversing bytes. The BASV2 survey does not establish the HMU layout, and a destination address alone never selects byte order.
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
| `0x02` | Local controller selector family | `GG=0x00..0x05`, `GG=0x08`, `GG=0x09`, `GG=0x0A` | Observed local selector sets; the role, physical identity and topology of OP02/GG0A remain Unknown |
| `0x06` | Controller-mediated selector family | `GG=0x01`, `GG=0x02`, `GG=0x08`, `GG=0x09`, `GG=0x0A`, `GG=0x0C`, `GG=0x0E`, `GG=0x0F` | Opcode-scoped selector sets. `GG=0x01/0x02` heat-generator labels remain profile-qualified hypotheses; `GG=0x00` is uncharacterized. |

**Unqualified presentation candidate:** The operator-provided display designation
`OP=0x06, GG=0x0B` = **Functional Modules (VR70) FM3** is retained as a name only. It
is not included in the documented selector sets because this repository has no
published capture, bounds, liveness predicate, or schema for that route. The
separately documented `OP=0x06, GG=0x0C` presentation name is **Functional
Modules (VR71) FM5**; neither display name establishes a universal product-identity
rule.

### 3.3 OP02 family presentation-name catalog

The following operation-scoped labels are used by the scan planner, Browser,
HTML, and saved-artifact views. They retain the complete `(OP=0x02, GG)`
identity. A label does not add a selector route, instance range, register
layout, or physical-device claim.

| GG | Human label | Presentation semantic name | Qualification |
| --- | --- | --- | --- |
| 00 | System | `system` | Observed singleton local selector set. |
| 01 | Native Domestic Hot Water | `native_domestic_hot_water` | Observed singleton local selector set. |
| 02 | Circuits | `circuits` | Current profile: II01..08 heating candidates and II09 virtual native water. |
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
| 01 | Boiler | `boiler` | Hypothesis. The existing profile-qualified `primary_heating_source` route remains the documented route. |
| 02 | Heat Pump | `heat_pump` | Hypothesis. The existing profile-qualified `secondary_heating_source` route remains the documented route. |
| 03 | Air Recovery (VAR) recoVair | `air_recovery_recovair` | Hypothesis; no public OP06 route or bounds are documented. |
| 04 | unused | `unused` | Unknown. This recorded presentation state does not establish universal absence or reservation. |
| 05 | Wärmepumpe Zubehör Appliance Interface (VWZ-AI) | `heat_pump_accessory_vwz_ai` | Hypothesis; no public OP06 route or bounds are documented. |
| 06 | Pumpen Module - Solar (VPM-S) auroFLOW | `solar_pump_module_auroflow` | Hypothesis; no public OP06 route or bounds are documented. |
| 07 | Pumpen Module - Wasser (VPM-W) aguaFLOW | `water_pump_module_aguaflow` | Hypothesis; no public OP06 route or bounds are documented. |
| 08 | Modul Solar (VMS) auroSTEP | `solar_module_aurostep` | Hypothesis. It does not replace the separately documented profile-specific `buffer_solar_cylinder_2_remote` route. |
| 09 | Remote Control Regulators (VRC7xx, VRT38x) | `remote_control_regulator` | Hypothesis for the family name; the `regulator_slot` route and its profile qualification remain separate. |
| 0A | Remote Control Thermostats (VR9x) | `remote_control_thermostat` | Hypothesis for the family name; the `thermostat_slot` route and its profile qualification remain separate. |
| 0B | Functional Modules (VR70) FM3 | `functional_modules_vr70` | Hypothesis. No public slot schema, bounds, or `RR=0001` predicate is documented. |
| 0C | Functional Modules (VR71) FM5 | `functional_modules_vr71` | Hypothesis for the family/FM5 display name. The separately published slot schema remains profile-qualified to OP06/GG0C. |
| 0D | Relay Module (VR41) | `relay_module_vr41` | Hypothesis; no public OP06 route or bounds are documented. |
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
- `GG=0x01 + OP=0x06` = profile-qualified controller-side primary
  heating-source candidate. It does not establish any global rule for
  `GG=0x00`.
- `GG=0x02 + OP=0x06` = profile-qualified controller-side secondary
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
| 0000h | `circuit_count` | Legacy public name; profile-qualified supported circuit capacity for bounded OP=02h/GG=02h candidate guidance |
| 0001h | `zone_count` | Legacy public name; profile-qualified supported zone capacity for bounded OP=02h/GG=03h candidate guidance |
| 0002h | `solar_circuit_count` | Solar circuits; guides OP=02h/GG=04h discovery |
| 0003h | `solar_loaded_tank_count` | Solar-loaded tanks; guides OP=02h/GG=05h discovery |
| 0004h | `device_count` | Devices |
| 0005h | `generator_count` | Generators |
| 0006h | `api_version` | API version; not a count |
| 0007h | `api_revision` | API revision; not a count |
| 0008h / 0009h | `vr70_count` / `vr71_count` | Functional module counts |
| 000Ah | `remote_control_count` | Remote controls |
| 000Bh | `delta_t_count` | Guides OP=02h/GG=08h discovery; physical class remains unknown |
| 000Ch / 000Dh | `boiler_count` / `heat_pump_count` | Generator classes |
| 000Eh / 000Fh | `vpm_w_count` / `vpm_s_count` | Module classes |
| 0010h | `recovair_count` | recoVair ventilation units |
| 0011h | `cooling_heat_pump_count` | Cooling-capable heat pumps |

For ID=0000h `circuit_count` and ID=0001h `zone_count`, the retained legacy
public names denote supported capacity, not configured or present-instance
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

Read the parameter first. Acquisition includes all deduplicated, observed
writable candidates in the selected scope by default. An explicit caller budget
may limit acquisition. Candidates use the profile-scoped static
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
- `0x06` is a separate opcode-scoped controller-mediated selector family. It is
  used for several remote families. The primary and secondary heat-source
  labels (`GG=0x01` and `GG=0x02`) remain profile-qualified hypotheses.
- The selector meaning is always keyed on `(opcode, GG, II, RR)`, not on `GG`
  alone.

### 4.4 `0x03` / `0x04` Timer Schedules

`ReadTimer` and `WriteTimer` use the VRC700 schedule profile, identified by
`70000` or `B7S00`. Verify that identity before a live read. VRC720-family
controllers use the [B555 timer protocol](ebus-vaillant-b555-timer-protocol.md);
sharing a destination address does not qualify the B524 schedule profile.

```text
ReadTimer:  03 GG II ADDRESS WEEKDAY
WriteTimer: 04 GG II ADDRESS WEEKDAY START1 STOP1 START2 STOP2 START3 STOP3
Reply:      PARAM_CONFIG START1 STOP1 START2 STOP2 START3 STOP3
```

The read request is five bytes, the write request eleven bytes, and the read
reply seven bytes after transport normalization. These operations do not contain
an `RW` byte. `WEEKDAY=00..06` means Monday through Sunday. Retain
`PARAM_CONFIG` as a raw byte; do not infer writable access from it.

Time codes `00..90` represent ten-minute units. An unused slot is `90 90`.
A stop code `90` paired with a lower start code means 24:00. Retain unknown
codes as raw evidence; they do not become valid time values.

| GG | II | ADDRESS | Channel |
| --- | --- | --- | --- |
| 00 | 00 | 01 | Ventilation |
| 00 | 00 | 02 | Noise reduction |
| 00 | 00 | 03 | Tariff |
| 01 | 00 | 01 | Domestic hot water |
| 01 | 00 | 02 | Circulation |
| 03 | Selected zone | 01 | Zone cooling |
| 03 | Selected zone | 02 | Zone heating |

VRC Explorer exposes `b524 read-timer` and the offline-only
`b524 preview-write-timer`. Preview creates a payload without opening a
transport or writing to a regulator.

### 4.5 `0x09` / `0x0A` Events and `0x0B` / `0x0C` Event Setpoints

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

| Selected profile | GG | Permitted ADDRESS | Setpoint codec |
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
that every BASV2 or VRC700 implements them. Undocumented profile/address
combinations remain rejected rather than receiving an invented codec.

VRC Explorer provides live read-only `b524 read-event` and
`b524 read-event-setpoint`. `b524 preview-set-event` and
`b524 preview-set-event-setpoint` construct offline payloads only. No live
setter is exposed by these commands. Retries apply at the transport layer to
exact read requests; setters are excluded from automatic replay.

### 4.6 `0x08` ReadVR91

The VRC700 profile (`70000` or `B7S00`) uses a one-byte request `08` and an
eight-byte response:

```text
BINDING_ZONE SPECIAL_FUNCTION_STATUS HEATING_MODE COOLING_MODE
STATUS_INFO FROST_PROTECTION HEATING_TEMPERATURE_RAW COOLING_TEMPERATURE_RAW
```

These field names describe the response structure. Bit meanings, temperature
scaling and special-value semantics remain unqualified, so the Explorer retains
each byte without turning it into a physical measurement. `b524 read-vr91`
checks the controller identity before sending this request.

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

## 7. Open Items

Open protocol questions remain marked inline as **Hypothesis** or **Unknown**
until publishable correlated evidence qualifies them.
