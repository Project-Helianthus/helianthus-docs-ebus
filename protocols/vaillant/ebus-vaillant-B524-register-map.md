# Vaillant B524 Extended Register Map

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This reference uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

> **Status:** Authoritative reference. Single source of truth for B524 register semantics.
>
> **Last updated:** 2026-10-14 (register names renamed to the register naming rules)
>
> **Controller families:** VRC700 and VRC720.

This is the register catalog for B524. For the protocol specification (wire format, opcodes, FLAGS encoding, response states), see [ebus-vaillant-B524.md](./ebus-vaillant-B524.md). Each unresolved mapping remains marked inline as **Hypothesis** or **Unknown**.

Result tables for the OP02 registers that are read and written are
kept beside this catalog: the
[register matrix by family](fixtures/b524-op02-requester-register-matrix.csv)
(candidate reply widths, types, units and enumerations), the
[write templates](fixtures/b524-op02-write-templates.csv), the
[write sequences](fixtures/b524-op02-write-sequences.csv) and the
[calendar and clock selectors](fixtures/b524-op02-calendar-clock-selectors.csv).
Their meaning is explained in the
[Register matrix by family](#register-matrix-by-family) section.

---

## Table Legend

| Column | Meaning |
|--------|---------|
| **RR** | Register address (hex) |
| **Name** | Descriptive semantic name |
| **Cat** | Documentation category: **S**=state, **C**=configuration candidate, **P**=property candidate, **E**=energy/counter candidate, **—**=unknown/unclassified. It is not derived from `FLAGS` alone and does not authorize a write. |
| **Wire** | On-wire encoding: `u8`, `u16`, `u32`, `f32`, `string`, `date`, `time`, `bytes`. All multi-byte integers are little-endian. **f32 byte order is profile-dependent:** the characterized VRC720 values are little-endian. A destination address alone does not select byte order; qualify other profiles independently — see [B524 protocol doc section 2.6](./ebus-vaillant-B524.md#26-wire-type-encoding) |
| **Decode** | Semantic interpretation: `bool`, `°C`, `K`, `bar`, `%`, `kWh`, `hrs`, `min`, `count`, `enum`, `text`, `date`, `time`, `state`, `raw`, `—` (unknown) |
| **ebusd** | ebusd community TSP name. `—` = not in TSP |
| **Constraint** | Historical short-probe range hint. It requires a matching complete OP01/OP07 description before validating edits. `—` = no catalog entry |
| **Values** | Enum mapping. Inline for ≤3 values, otherwise `→enum_name` referencing [Enum Reference](#enum-reference) |
| **Gates** | Condition for register to be present/meaningful. `—` = no gate documented here; presence remains family-qualified. |

**Source annotations** (in Notes):
- No annotation = confirmed by multiple independent sources (ebusd + live scan + value match)
- `†` = CSV value-matched only, not independently confirmed (false-positive risk)
- `ebusd: "..."` = ebusd community note about this register (e.g., special value meanings)

Historic row notes may contain labels such as `stable RO`, `volatile RO`,
`technical RW`, or `user RW`. Those labels are withdrawn as public B524
semantics: retain the printed `FLAGS` value as an observation, but treat the
labels as family-specific static interpretation until corroborated by public,
correlated evidence. They do not establish writability or authorize a write.

---

## Group Topology

The OP06 product-family labels in this table are **Hypotheses** from the
operation-scoped presentation catalog unless a separate row supplies its own
publishable identity evidence. They identify a candidate family for navigation;
they do not establish physical product identity, presence, or a device layout.
`unused` and the RR layout for GG04 and GG0D remain **Unknown**.

The family layout distinguishes singleton `OP=0x02, GG=0x00` system
selectors in VRC720 from the VRC700 ventilation selectors in the same group.
The register counts and raw observations below remain specific to VRC720.
See the [VRC700 ventilation reads](#gg0x00--system) for the separately scoped
selector encoding. Parameterized syntax establishes neither a supported
nonzero index nor an `II_MAX` for VRC700; those bounds remain open.

| Opcode | GG | Group label | Instanced | II_MAX | Observed scheduling RR ceiling | Instance gate | Regs (scan/doc) |
|--------|----|-------------|-----------|--------|-------------------------------|---------------|-----------------|
| 0x02 | 0x00 | System | No (VRC720 family) | 0x00 (VRC720 family) | 0xFF | VRC720-family singleton; VRC700 ventilation indexing differs, see below | 179 (0x0001–0x00FF) |
| 0x02 | 0x01 | Native Domestic Hot Water | No | 0x00 | 0x13 | RR0001 exact two-byte nonzero UIN; zero is not present | 17 (0x0001–0x0013) |
| 0x02 | 0x02 | Circuits | Yes | 0x09 | 0x25 | VRC720: RR0002 raw `0100`, FLAGS=03 at II00/II01 is active; raw `0000`, FLAGS=03 at II02 is inactive; II09 is virtual native water | profile candidate bound: II00..II08 heating + II09 virtual native-water; other or unknown families require separate qualification |
| 0x02 | 0x03 | Zones | Yes | 0x0A | 0x2E | `index != 0xFF` (RR=0x001C) | current profile interval II00..0A; presence probed separately |
| 0x02 | 0x04 | Solar Circuit | Yes (profile) | 0x01 | 0x0B | decodable, non-null RR0004 EXP value | current profile interval II00..01; presence probed separately |
| 0x02 | 0x05 | Solar Loaded Cylinder | Yes | 0x01 | 0x04 | SystemScheme + VR_71 config | 8 (4/inst, 2 inst) |
| 0x02 | 0x06 | Device | Unknown | — | — | no public selector/profile contract | Unknown |
| 0x02 | 0x07 | Generator | Unknown | — | — | no public selector/profile contract | Unknown |
| 0x02 | 0x08 | DeltaT (local) | Unknown | profile-dependent | 0x0007 | not qualified | 7 local |
| 0x02 | 0x09 | Ventilation | Unknown | profile-dependent | 0x000F | not qualified | 15 local |
| 0x02 | 0x0A | Unknown | Unknown | 0x0A | 0x004D | local selector evidence; physical topology Unknown | current profile interval II00..0A |
| 0x06 | 0x01 | Boiler | Yes | 0x08 | 0x002F | `device_connected` requires a concrete-II correlated Boolean | class-level evidence only |
| 0x06 | 0x02 | Heat Pump | Yes | 0x08 | 0x002F | `device_connected` requires a concrete-II correlated Boolean | class-level evidence only |
| 0x06 | 0x03 | Air Recovery (VAR) recoVair | Yes | 0x08 | 0x002F | `device_connected` candidate; concrete-II verification required | class-level evidence only |
| 0x06 | 0x04 | unused | Yes | 0x08 | — | Unknown | Unknown |
| 0x06 | 0x05 | Wärmepumpe Zubehör Appliance Interface (VWZ-AI) | Yes | 0x08 | 0x002F | `device_connected` candidate; concrete-II verification required | class-level evidence only |
| 0x06 | 0x06 | Pumpen Module – Solar (VPM-S) auroFLOW | Yes | 0x08 | 0x002F | `device_connected` candidate; concrete-II verification required | class-level evidence only |
| 0x06 | 0x07 | Pumpen Module – Wasser (VPM-W) aguaFLOW | Yes | 0x08 | 0x002F | `device_connected` candidate; concrete-II verification required | class-level evidence only |
| 0x06 | 0x08 | Modul Solar (VMS) auroSTEP | Yes | 0x08 | 0x002F | `device_connected` requires a concrete-II correlated Boolean | class-level evidence only |
| 0x06 | 0x09 | Remote Control Regulators (VRC7xx, VRT38x) | Yes | 0x08 | 0x35 | `device_connected` (RR=0x0001) | profile slot bound only |
| 0x06 | 0x0A | Remote Control Thermostats (VR9x) | Yes | 0x08 | 0x35 | `device_connected` (RR=0x0001) | profile slot bound only |
| 0x06 | 0x0B | Functional Modules (VR70) FM3 | Yes | 0x08 | 0x002F | `device_connected` candidate; concrete-II verification required | class-level evidence only |
| 0x06 | 0x0C | Functional Modules (VR71) FM5 | Yes | 0x08 | 0x2F | `device_connected` (RR=0x0001) | profile slot bound only |
| 0x06 | 0x0D | Relay Module (VR41) | Yes | 0x08 | — | `device_connected` RR0001 exact one-byte BOOL | RR maximum Unknown; availability-only |
| 0x06 | 0x0E | Clock Module | Yes | 0x08 | 0x0033 | `device_connected` requires a concrete-II correlated Boolean | class-level evidence only |
| 0x06 | 0x0F | Base Station | Yes | 0x08 | 0x0033 | `device_connected` requires a concrete-II correlated Boolean | class-level evidence only |

**GG values are opcode-scoped, not global:** for the VRC720 family,
`OP=0x02, GG=0x00` and `OP=0x02, GG=0x01` are the singleton local selector
sets for system/settings and DHW. The VRC700 ventilation case is scoped
separately above; it does not inherit the VRC720-family instance bound.
Separately, `OP=0x06, GG=0x01` and `OP=0x06, GG=0x02` are instanced
controller-side selector sets for primary and secondary heating sources
respectively. `GG=0x00` has no qualified heat-generator route; this does not
establish its universal absence under `OP=0x06`, populated slots, or other
models' limits.

The [OP06 family presentation-name catalog](ebus-vaillant-B524.md#34-op06-family-presentation-name-catalog)
records operator-provided human names and `snake_case` semantic names for GG01
through GG0F. Except where this map already supplies an explicitly qualified
route, they are hypotheses only. A corrected presentation name does not change
the selector's wire identity or layout, expand the scan, or establish that a
group is unused on all profiles.

**GG=0x08 — OP02 local DeltaT; OP06 Modul Solar (VMS)
auroSTEP:** The documented selector spaces are `OP=0x02, GG=0x08` for 7 local
registers and `OP=0x06, GG=0x08` through the observed scheduling ceiling
RR002F, over candidate slots II01..II08. The OP06 display name is a family
hypothesis from the catalog; the local OP02 presentation name is DeltaT. Naming
does not establish physical-device identity or change routing and register
layout. These namespaces must not be merged by `GG` alone.

**Characterized OP=0x06 device slot categories (0x09, 0x0A, 0x0C, 0x0E, 0x0F):**
`GG=0x09` = Remote Control Regulators (VRC7xx, VRT38x), `GG=0x0A` = Remote
Control Thermostats (VR9x), `GG=0x0C` = Functional Modules (VR71) FM5,
`GG=0x0E` = Clock Module, and `GG=0x0F` = Base Station. Connected-device discovery
uses family-qualified `device_connected` (RR=0x0001),
over II01..II08 for the characterized profile. `II=0x00`, `II=0x09`, and
`II=0x0A` are outside its current OP06 slot interval. Readable headers do not override
a false connection Boolean; retained inventory is distinct. See the
[qualified policy and bounds](ebus-vaillant-b524-profile-discovery-and-descriptions.md).
Instance `II` selects the slot.
`OP=0x02, GG=0x09/0x0A` identifies separate local selector sets;
remote device labels do not establish their physical identity or topology.

`OP=0x06, GG=0x0B` = **Functional
Modules (VR70) FM3** is a named OP06 family with an observed scheduling ceiling.
Its class-level observations do not transfer a concrete instance, identity, or
presence result to GG0C.

`OP=0x06, GG=0x0C` is presented as **Functional Modules (VR71) FM5** in the
documented map below. That presentation name does not turn the profile/lab
correlation into universal protocol identity.

**GG=0x0C — Functional Modules (VR71) FM5:** Responds only to opcode `0x06`. No local
config selector set is documented. Uses the same remote-device slot schema as
`GG=0x09/0x0A`.
In the current lab, `II=0x01` with
`device_class_address=0x26` correlates to the eBUS-identified `VR_71` hardware
at target address `0x26`, but that family identification comes from eBUS
identity correlation rather than from B524 alone.

**Discovery:** OP00 information identifiers are distinct from GG. The
[family-qualified mapping table](ebus-vaillant-b524-profile-discovery-and-descriptions.md#system-information-and-concrete-instances)
records family-qualified count interpretation. ID00 `circuit_count_maximum` and ID01
`zone_count_maximum` denote supported capacity under the bounded
profile contract, not configured or present-instance cardinality. They do not
identify, allocate, or make II slots contiguous: keep sparse II slots and apply
the group predicate to every candidate. II09 remains an independent virtual
native-water candidate. These counts do not establish a terminal instance interval. See [the corrected protocol contract](./ebus-vaillant-B524.md).

### Discovery Profiles

The following discovery intervals apply to the VRC720 family. “Observed scheduling ceiling” is the
highest RR in the current bounded scheduling evidence; it is not a terminal
maximum and does not exclude read-only state registers above it. A other
or unknown family requires separate qualification.

| Opcode | Group | Instance interval | Observed scheduling ceiling | Evidence scope | Notes |
|--------|-------|-------------------|-----------------------------|-------------------|-------|
| 0x02 | 0x00 System | 00 | 0x00FF | observed scope | Singleton |
| 0x02 | 0x01 Native Domestic Hot Water | 00 | 0x0013 | observed scope | RR0001 exact two-byte nonzero UIN predicate; OP01 RR0000..0013 independent |
| 0x02 | 0x02 Circuits | 00..09 | 0x0025 | VRC720-family scope | II00..08 heating candidates; II09 independent virtual native water |
| 0x02 | 0x03 Zones | 00..0A | 0x002E | observed scope | profile bound |
| 0x02 | 0x04 Solar Circuit | 00..01 | 0x000B | observed scope | profile bound |
| 0x02 | 0x05 Solar Loaded Cylinder | 00..01 | 0x0004 | observed scope | profile bound |
| 0x02 | 0x06 Device | Unknown | — | RR scope Unknown | layout Unknown |
| 0x02 | 0x07 Generator | Unknown | — | RR scope Unknown | layout Unknown |
| 0x02 | 0x08 DeltaT | profile-dependent | 0x0007 | observed scope | topology Unknown |
| 0x02 | 0x09 Ventilation | profile-dependent | 0x000F | observed scope | topology Unknown |
| 0x02 | 0x0A Unknown | 00..0A | 0x004D | observed scope | role and physical identity Unknown |
| 0x06 | 0x01 Boiler | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x02 Heat Pump | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x03 Air Recovery (VAR) recoVair | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x04 unused | 01..08 | — | RR scope Unknown | RR layout and predicate Unknown |
| 0x06 | 0x05 Wärmepumpe Zubehör Appliance Interface (VWZ-AI) | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x06 Pumpen Module – Solar (VPM-S) auroFLOW | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x07 Pumpen Module – Wasser (VPM-W) aguaFLOW | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x08 Modul Solar (VMS) auroSTEP | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x09 Remote Control Regulators (VRC7xx, VRT38x) | 01..08 | 0x0035 | observed scope | concrete-II predicate required |
| 0x06 | 0x0A Remote Control Thermostats (VR9x) | 01..08 | 0x0035 | observed scope | concrete-II predicate required |
| 0x06 | 0x0B Functional Modules (VR70) FM3 | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x0C Functional Modules (VR71) FM5 | 01..08 | 0x002F | observed scope | concrete-II predicate required |
| 0x06 | 0x0D Relay Module (VR41) | 01..08 | — | RR0001 predicate; other RR Unknown | `device_connected`: exact one-byte BOOL; RR maximum Unknown; availability-only |
| 0x06 | 0x0E Clock Module | 01..08 | 0x0033 | observed scope | concrete-II predicate required |
| 0x06 | 0x0F Base Station | 01..08 | 0x0033 | observed scope | concrete-II predicate required |

---

## Gate Conditions (Quick Reference)

Several registers are conditionally available based on system configuration. Gates are also annotated per-register in the group tables below.

| Gate | Source Register | Controls |
|------|----------------|----------|
| `hwc_enabled` | OP=0x02 GG=0x01 RR=0x0001 | Local DHW registers in `OP=0x02 GG=0x01`; HWC-related config in GG=0x00 |
| `fm5_config` | GG=0x00 RR=0x002F | Solar registers (GG=0x04, GG=0x05), `solar_flow_rate_quantity` |
| `circuit_type` | GG=0x02 RR=0x0002 | Per-circuit: heating regs (type=1), fixed_value regs (type=2), return_increase regs (type=4) |
| `cooling_enabled` | GG=0x02 RR=0x0006 | Cooling-related config in circuits and zones. Required for dew point functions (see below) |
| `room_temp_control_mode` | GG=0x02 RR=0x0015 | Dew point monitoring requires `cooling_enabled=true` AND `room_temp_control_mode != off` |
| `ext_hwc_active` | GG=0x02 RR=0x0018 | External HWC temp/mode |

**Rule:** Gated-off registers return no meaningful data. Readers should check gate conditions before interpreting values.

---

## OP=0x02 — Local Parameter Registers

The semantic names below form an operation-scoped naming
catalog ([issue #544](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/544)),
machine-checked against
[`fixtures/b524-op02-register-names.csv`](fixtures/b524-op02-register-names.csv).
The names follow the register naming rules of this repository
([issue #560](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/560)):
a name reads as a sentence of subject, predicate, object and circumstances,
and every token comes from the register name vocabulary. The catalog keeps the
earlier name of each register in its `previous_name` column; a provisional
name, whose meaning is not established, states the unresolved point in its
`open_question` column. The OP=0x06 and `OP=0x02, GG=0x0A` names of this
document follow the same rules; the earlier names that changed are listed in the
`previous_name` tables of their sections.
Naming does not independently qualify a codec, value range, write capability,
physical identity or scan bound. Existing raw observations and profile limits
remain separately qualified. Newly named entries without a characterized layout
are marked **Hypothesis**.

### Register name correspondence fixture

[`fixtures/b524-register-name-correspondence.csv`](fixtures/b524-register-name-correspondence.csv)
maps each `(opcode, group, register)` key to this catalog's canonical `name`
and, where known, a set of annotation columns:

| Column | Meaning |
| --- | --- |
| `name` | The canonical, presentation name from this catalog. Identical to `b524-op02-register-names.csv` for every OP02 key; this is the only column that names a register in this document. |
| `previous_name` | The earlier canonical name of the register, before the register naming rules applied; identical to the `previous_name` column of `b524-op02-register-names.csv`. It is a migration aid, not a name of the register. |
| `vaillant_friendly_name` | An observed Vaillant friendly name for the register. |
| `vaillant_name_vrc720` / `vaillant_name_vrc700` | Observed Vaillant names, where known, for the VRC720 and VRC700 regulator families respectively. An empty cell means no name has been observed for that family; it does not imply the register is absent on that family. |
| `myvaillant_name_vrc720` / `myvaillant_name_vrc700` | Observed myVaillant app/cloud names, where known, per family. |
| `ebusd_name` | The name used by the community `ebusd` configuration. May contain `{hc}` / `{zone}` placeholders for per-circuit or per-zone instances. |

Multiple observed values in one cell are separated by `` | ``. A cell lists
more than one value only when each of them is an observed name of that same
register for that column. Names of values that are merely derived from a
register (an activity or visibility flag, an aggregate over all instances, or
a composite field the register is one component of) are not names of the
register and are not listed. Each name is recorded once, in one spelling:
values that differ only in letter case, spacing or punctuation are the same
name, not separate values. `vaillant_friendly_name` is not split by
regulator family, so it carries two labels where the label differs between
families or releases. The multi-valued cells are GG=0x02 RR=0x0002 (both
Vaillant name columns: two names for the same value), GG=0x00 RR=0x008B and
GG=0x01 RR=0x0008 (friendly name). These
annotation columns are observed names only: they establish neither codec,
value range, nor write access, and they do not widen or narrow this
document's own register-level claims. Where a name has been observed for
only one regulator family, treat that as what was observed, not as proof
that the register is absent on the other family.

Candidate, unconfirmed on the wire: both Vaillant names `circuit_type` and `circuit_type_of_mixed_circuit_external` correspond to `OP=0x02, GG=0x02, RR=0x0002` and its value.

Candidate, unconfirmed on the wire: the myVaillant name `mixerCircuitTypeExternal` for this register denotes an enumeration string (see the
[mctype](#mctype--circuit-type) table), not the raw uint16.

**Column-level provenance:** `name` is this document's own canonical catalog
([`fixtures/b524-op02-register-names.csv`](fixtures/b524-op02-register-names.csv)).
`ebusd_name` is a name from the public `ebusd` configuration, as mapped onto
each `(group, register)` selector by this project; that mapping can itself
be wrong — two such mapping errors (`HwcParallelLoading` on GG=0x00 RR=0x0015,
and `Hc{hc}CircuitType` on GG=0x02 RR=0x0001) were found and removed in this
change. `vaillant_friendly_name`, `vaillant_name_vrc720`,
`vaillant_name_vrc700`, `myvaillant_name_vrc720`, and `myvaillant_name_vrc700`
are observed names whose source is not published with this fixture. None of
the six annotation columns (`vaillant_friendly_name`,
`vaillant_name_vrc720`, `vaillant_name_vrc700`, `myvaillant_name_vrc720`,
`myvaillant_name_vrc700`, and `ebusd_name`) is itself a wire observation;
each is at `Hypothesis` grade as an identification, and none establishes a
codec, a value range, or write access on its own. This document does not
invent a per-row source beyond what is stated here.

### GG=0x00 — System

The VRC720-family system selectors use opcode `0x02`, instance `0x00`.
For the VRC700 ventilation selectors RR0016, RR0042, RR0043 and RR00A4,
the instance domain remains unconfirmed. The notation
`II=<ventilation_index>` does not establish a supported index or range.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | dhw_outdoor_bivalence_temperature_limit | C | f32 | °C | — | profile-scoped: BASV0 -20..20 step 1 (retained description record; EXP decoding **Hypothesis**); BASV2 -20..50 step 1 (unqualified historical observation, **Hypothesis**) | — | — | FLAGS=0x02 (historical scan value, controller profile not recorded); BASV0 observes flags 03. See the DHW bivalence note in the [Constraint Catalog](#constraint-catalog) |
| 0x0002 | continuous_heating_outdoor_temperature_limit | C | f32 | °C | ContinuousHeating | -26..10 step 1 | — | — | FLAGS=0x03. ebusd: `-26=off` disables function |
| 0x0003 | frost_protection_delay_time | C | u16 | hrs | FrostOverRideTime | 0..12 step 1 | — | — | FLAGS=0x03 |
| 0x0004 | preheating_time_maximum | C | u16 | min | — | 0..300 step 10 | — | — | FLAGS=0x03. † |
| 0x0006 | manual_cooling_time | C | u16 | days | — | — | — | cooling_enabled? | **Dormant** when cooling not configured. Two-byte register where present. Vaillant name observed for the VRC700 family only; hardware confirmation pending. Candidate, unconfirmed on the wire: on the VRC700 family the count is written as `02 01 00 00 06 00 Vlo Vhi` (cancel `00 00`); the unit of the count is not established. † |
| 0x0007 | unknown_11 | C | u8 | bool | — | — | `0=off 1=on` | — | FLAGS=0x03 (user RW). System on/off switch, not a sensor reading. Provisional name: the polarity is unresolved between this value table and the candidate write (01 sets the switch-off) |
| 0x0008 | cooling_enabled_at_holiday | C | u8 | bool | — | — | — | — | † |
| 0x0009 | automatic_cooling_enabled | C | u8 | bool | — | — | `0=off 1=on` | — | FLAGS=0x02 (technical RW). Scan: 1 byte. † |
| 0x000A | cylinder_parallel_loading_enabled | C | u16 | bool | HwcParallelLoading | — | →onoff | — | ebusd confirmed at `@ext(0xa,0)` |
| 0x000B | solar_circuit_bleeding_time | — | u16 | — | — | — | — | — | Scan value: 0. Near boolean cluster |
| 0x000D | solar_frost_protection_limit | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000E | room_humidity_limit_maximum | C | u16 | % | MaxRoomHumidity | — | — | — | |
| 0x000F | hybrid_control_mode | — | u16 | — | HybridManager | — | — | — | Access: `ri/wi` (installer). Hybrid system manager (HP + boiler). Wire semantics pending live validation |
| 0x0010 | backup_heater_tariff | — | u16 | — | TariffAuxHeater | — | — | — | Access: `ri` (installer read). Tariff for auxiliary heater |
| 0x0011 | electricity_price_at_low_tariff | — | u16 | — | — | — | — | — | Scan value: 16. Possible temp threshold |
| 0x0012 | electricity_price_at_high_tariff | C | u16 | °C | — | — | — | — | Confirmed exact, value=20 |
| 0x0013 | backup_heater_type | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for both families, a two-byte `uint16 LE` value with the enumeration `0=Condensing; 1=NonCondensing; 2=Electrical`. |
| 0x0014 | adaptive_heating_curve_enabled | C | u8 | bool | AdaptHeatCurve | — | →yesno | — | FLAGS=0x03 (user RW). Scan validated 1-byte |
| 0x0015 | automatic_daylight_saving_time | — | u16 | — | — | — | — | — | False positive in CSV (was `parallel_tank_loading`; actual is at 0x000A) |
| 0x0016 | ventilation_operating_mode | S | u16 | enum | — | — | `1=AUTO 2=DAY 3=SET_BACK` | — | Candidate VRC700 uint16 interpretation: `1=Auto 2=Day 3=Setback`, unconfirmed on the wire. The VRC720-family ventilation-mode selector is OP02/GG09/RR0002; the VRC700 selector does not replace it. Other codes remain raw. This is distinct from OP02 GG09 RR0002. Behaviour without an active quick mode and the proposed GG09/RR0002 write correspondence remain open; see [Open questions](#open-questions--family-specific-register-interpretation). The write selector and the write encoding are not established. Candidate: present on the VRC700 family only. |
| 0x0017 | dhw_loading_time_maximum | C | u16 | min | MaxCylinderChargeTime | — | — | hwc_enabled | |
| 0x0018 | dhw_blocking_time | C | u16 | min | HwcLockTime | — | — | hwc_enabled | |
| 0x0019 | solar_flow_rate_setpoint | C | f32 | — | — | — | — | fm5_config≤2 | See [Mapping Conflicts](#mapping-conflicts) |
| 0x001B | dhw_pump_overrun_time | C | u16 | min | PumpAdditionalTime | — | — | — | |
| 0x001C | heat_generator_flow_temperature_limit_maximum | C | f32 | °C | — | — | — | — | † |
| 0x001E | automatic_sequence_reversal | — | u8 | — | — | — | — | — | Scan value: 1. Possible pump/flag |
| 0x0022 | heating_outdoor_alternative_temperature_limit | C | f32 | °C | — | — | — | — | -21..40 per TSP |
| 0x0023 | heating_outdoor_bivalence_temperature_limit | C | f32 | °C | — | — | — | — | -20..30 per TSP |
| 0x0024 | backup_heater_mode | C | u16 | enum | — | — | values unknown | — | See [Mapping Conflicts](#mapping-conflicts). Candidate, unconfirmed on the wire: the requester matrix gives, for both families, the enumeration `0=Disabled; 1=Heating; 2=DHW; 3=DHWandHeating`. |
| 0x0025 | temporary_backup_heater_mode | — | u16 | — | — | — | — | — | Scan value: 0 |
| 0x0026 | heating_flow_temperature_setpoint_maximum_at_heat_pump_fault | C | f32 | °C | — | — | — | — | 20..80 per TSP |
| 0x0027 | cylinder_loading_start_hysteresis | C | f32 | K | CylinderChargeHyst | — | — | hwc_enabled | 3..20 step 0.5 per TSP. Candidate, unconfirmed on the wire: written as `02 01 00 FF 27 00 <float32 LE>` (`OT=0x01, GG=0x00, II=0xFF`), identical on both families. Candidate, unconfirmed on the wire: a write of 1.0 K, a value below the range documented here, is a candidate write; whether the controller accepts, clamps or refuses 1.0 K is not established; the documented range is unchanged. |
| 0x0029 | cylinder_loading_offset | C | f32 | K | CylinderChargeOffset | — | — | hwc_enabled | 0..40 per TSP |
| 0x002A | dhw_legionella_protection_start_clock_time | C | time | time | — | — | — | hwc_enabled | HH:MM |
| 0x002B | dhw_legionella_protection_start_weekday | C | u16 | enum | — | — | `0=off 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun` | hwc_enabled | Day-of-week selector. 0=disabled. Candidate, unconfirmed on the wire: the requester matrix gives, for both families, the additional code `8=Daily`, outside the enumeration of this row. |
| 0x002C | maintenance_date | C | date | date | MaintenanceDate | — | — | — | FLAGS=0x03 (user-facing RW). HDA:3 encoding [DD,MM,YY]. Sentinel 2015-01-01 = factory default. Writable via B524 OT=0x01 |
| 0x002D | outdoor_temperature_offset | C | f32 | K | — | — | — | — | -3..3 step 0.5 per TSP |
| 0x002F | functional_module_configuration_code | P | u16 | count | — | — | — | — | 1..11 |
| 0x0031 | language | — | u16 | — | — | — | — | — | Scan value: 0 |
| 0x0034 | date | S | date | date | Date | — | — | — | BCD in the scalar observation. Candidate, unconfirmed on the wire: also written (time first, then date): `02 01 00 00 34 00 dd mm yy` with `yy` the year minus 2000, identical on both families, with no BCD step in that encoding; the codec the controller itself uses is not established. See [protocol section 4.7](./ebus-vaillant-B524.md#47-date-and-time-triples-and-system-clock). |
| 0x0035 | clock_time | S | time | time | Time | — | — | — | HH:MM:SS. Candidate, unconfirmed on the wire: written before the date: `02 01 00 00 35 00 hh mm ss` (hour in 24 h form, minute, second), identical on both families. |
| 0x0036 | hydraulic_scheme_code | P | u16 | count | HydraulicScheme | — | — | — | 1..16 |
| 0x0038 | cooling_start_temperature_limit | C | f32 | °C | — | — | — | — | 10..30 per TSP |
| 0x0039 | water_pressure | S | f32 | bar | WaterPressure | — | — | — | Read-only |
| 0x003A | hybrid_unknown_2 | C | f32 | K | — | — | — | — | -10..10 per TSP |
| 0x003C | solar_yield_total_reset_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x003D | solar_yield_total | E | u32 | kWh | SolarYieldTotal | — | — | fm5_config≤2 | |
| 0x003E | environmental_yield_total | E | u32 | kWh | YieldTotal | — | — | — | |
| 0x003F | environmental_yield_total_reset_command | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0040 | ventilation_volatile_organic_compound_sensor_1 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0041 | ventilation_volatile_organic_compound_sensor_2 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0042 | ventilation_fan_speed_limit_maximum_at_day | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for the VRC700 family, a two-byte `uint16 LE` value. |
| 0x0043 | ventilation_fan_speed_limit_maximum_at_night | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for the VRC700 family, a two-byte `uint16 LE` value. |
| 0x0044 | ventilation_heat_recovery | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0045 | utility_lockout_mode | C | u16 | enum | — | — | values unknown | — | Candidate, unconfirmed on the wire: the requester matrix gives, for both families, the enumeration `0=Disable heatpump; 1=Disable backup heater; 2=Disable Heatpump and Backup heater; 3=Disable heating; 4=Disable cooling; 5=Disable heating and cooling`. |
| 0x0046 | dhw_flow_temperature_setpoint_maximum | C | f32 | °C | HwcMaxFlowTempDesired | — | — | — | 15..80 per TSP |
| 0x0047 | emergency_operation_active | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0 |
| 0x0048 | energy_manager_state | S | u16 | enum | — | — | `0=standby 1=heating 2=cooling 3=dhw` | — | Single raw enum projected into multiple system-status views. `heating+cooling` is only a possible combined state presentation; its raw numeric encoding remains pending validation. |
| 0x0049 | electricity_consumption_total_reset_command | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x004A | settings_reset_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x004B | flow_temperature | S | f32 | °C | SystemFlowTemp | — | — | — | Read-only. Do not conflate with B509 boiler flow temperature or the controller-side `OP=0x06 GG=0x01 RR=0x0015` heat-source status selector |
| 0x004C | backup_heater_power_limit_maximum | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x004D | multifunction_output_2_mode | C | u16 | enum | MultiRelaySetting | — | →mamode | — | |
| 0x004E | heating_fuel_consumption_current_month | E | u32 | kWh | PrFuelSumHcThisMonth | — | — | — | |
| 0x004F | heating_electricity_consumption_current_month | E | u32 | kWh | PrEnergySumHcThisMonth | — | — | — | |
| 0x0050 | dhw_electricity_consumption_current_month | E | u32 | kWh | PrEnergySumHwcThisMonth | — | — | — | |
| 0x0051 | dhw_fuel_consumption_current_month | E | u32 | kWh | PrFuelSumHwcThisMonth | — | — | — | |
| 0x0052 | heating_fuel_consumption_previous_month | E | u32 | kWh | PrFuelSumHcLastMonth | — | — | — | |
| 0x0053 | heating_electricity_consumption_previous_month | E | u32 | kWh | PrEnergySumHcLastMonth | — | — | — | |
| 0x0054 | dhw_electricity_consumption_previous_month | E | u32 | kWh | PrEnergySumHwcLastMonth | — | — | — | |
| 0x0055 | dhw_fuel_consumption_previous_month | E | u32 | kWh | PrFuelSumHwcLastMonth | — | — | — | |
| 0x0056 | heating_fuel_consumption_total | E | u32 | kWh | PrFuelSumHc | — | — | — | |
| 0x0057 | heating_electricity_consumption_total | E | u32 | kWh | PrEnergySumHc | — | — | — | |
| 0x0058 | dhw_electricity_consumption_total | E | u32 | kWh | PrEnergySumHwc | — | — | — | |
| 0x0059 | dhw_fuel_consumption_total | E | u32 | kWh | PrFuelSumHwc | — | — | — | |
| 0x005C | electricity_consumption_1_total | E | u32 | kWh | PrEnergySum | — | — | — | |
| 0x005D | fuel_consumption_1_total | E | u32 | kWh | PrFuelSum | — | — | — | |
| 0x005E | heat_recovery_yield_total | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0. Near energy counters |
| 0x005F | actuator_sensor_test_device_code | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0060 | actuator_sensor_test_sensor_code | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 2 |
| 0x0061 | actuator_sensor_test_actuator_code | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0062 | ventilation_volatile_organic_compound_sensor_3 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0063 | ventilation_volatile_organic_compound_limit_maximum | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0065 | ventilation_fan_speed_setpoint | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x0066 | home_screen_unknown_6 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0067 | cylinder_bottom_temperature | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 1" |
| 0x0068 | cylinder_top_temperature | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 2" |
| 0x0069 | unknown_1 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for the VRC700 family, a two-byte `uint16 LE` value with the candidate labels `0=regulator; 1=Zone_1; 2=Zone_2; 3=Zone_3`. |
| 0x006A | multifunction_input_mode | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 1 |
| 0x006C | installer_name_prefix | C | string | text | Installer1 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x006D | installer_name_suffix | C | string | text | Installer2 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x006F | installer_phone_number_prefix | C | string | text | PhoneNumber1 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x0070 | installer_phone_number_suffix | C | string | text | PhoneNumber2 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x0071 | holiday_start_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: on the VRC700 family it is a three-byte date triple written in the system holiday sequence (set: after `RR=0x0082`; cancel: first step, `01 01 0F`); see [protocol section 4.8](./ebus-vaillant-B524.md#48-system-holiday-zone-holiday-and-cooling-for-days). |
| 0x0072 | holiday_end_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: read and written like `RR=0x0071` on the VRC700 family (last step; cancel `01 01 0F`). |
| 0x0073 | outdoor_temperature | S | f32 | °C | DisplayedOutsideTemp | — | — | — | Read-only |
| 0x0074 | special_function_mode | S | u8 | enum | — | — | — | — | **Dormant** when no system quick mode active. Mode enumeration and write path `OP=0x02, GG=0x09, RR=0x0001` remain hypotheses. See [Asymmetric Read/Write Paths](#asymmetric-readwrite-paths). Candidate, unconfirmed on the wire: on the VRC700 family this register is also written as a ventilation boost (`02 01 00 00 74 00 val`, 01 or 00); the relation of that write to the GG09 write path stays open. |
| 0x0075 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. Near installer_access_code cluster |
| 0x0076 | installer_access_code | C | u16 | count | KeyCodeforConfigMenu | — | — | — | FLAGS=0x02 (technical RW). Range 0..999. Writable via B524 OT=0x01 |
| 0x0077 | installation_assistant_ready | C | u8 | bool | — | — | — | — | FLAGS=0x03. Scan value: 1 |
| 0x0078 | home_screen_special_function | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0079 | heating_zone_time_program_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007A | cooling_zone_time_program_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007B | heating_zone_operating_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007C | cooling_zone_operating_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007D | home_screen_operating_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007E | unknown_3 | C | f32 | — | — | — | — | — | FLAGS=0x03. Scan value: 0.0 |
| 0x007F | screed_drying_time | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0080 | cylinder_loading_start_offset | C | f32 | — | — | — | — | — | FLAGS=0x03. Scan value: 0.0. Constraint: -10..10 step 1. Possibly PV offset |
| 0x0081 | cylinder_loading_stop_offset | P | f32 | K | — | — | — | — | † |
| 0x0082 | room_temperature_setpoint_at_holiday | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: on the VRC700 family a float32 is written here as the first step of the system holiday set sequence; the unit and any persistence in the controller are not established. |
| 0x0083 | bank_holiday_start_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0084 | bank_holiday_end_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0085 | actuator_sensor_test_sensor_reading | P | f32 | — | — | — | — | — | FLAGS=0x01. NaN |
| 0x0086 | backlight_on_time | — | u16 | — | — | — | — | — | Scan value: 60. PV/smart cluster |
| 0x0087 | drainback_start_time | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0088 | drainback_station | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0089 | solar_pump_kick_time | — | u16 | — | — | — | — | — | Scan value: 15. PV/smart cluster |
| 0x008A | solar_pump_kick_gradient_limit_minimum | — | f32 | — | — | — | — | — | Scan value: 1.0. PV/smart cluster |
| 0x008B | heat_pump_flow_temperature_setpoint_maximum | — | f32 | — | — | — | — | — | Scan value: 90.0. PV/smart cluster, possible max flow temp |
| 0x008C | boiler_remote_reset_available | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Near PV/smart cluster |
| 0x008D | display_test_pattern | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x008E | backlight_mode | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x008F | cylinder_type | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0090 | unknown_4 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0091 | left_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0092 | right_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0093 | encoder_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0094 | external_crystal_status | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0095 | outdoor_temperature_daily_average | S | f32 | °C | OutsideTempAvg | — | — | — | Rounded avg updated every 3h |
| 0x0096 | maintenance_active | S | u8 | bool | MaintenanceDue | — | →yesno | — | FLAGS=0x01 (stable RO). Scan validated 1-byte |
| 0x0097 | eeprom_update_active | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Near maintenance cluster |
| 0x0098 | boiler_reset_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0099 | rtc_crystal_ok | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x009A | unknown_5 | S | u16 | bool | — | — | — | — | |
| 0x009B | time_program_reset_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. Near unknown_5 |
| 0x009C | home_screen_headline | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x009D | dhw_cylinder_top_temperature | S | f32 | °C | HwcStorageTempTop | — | — | — | Read-only |
| 0x009E | dhw_cylinder_bottom_temperature | S | f32 | °C | HwcStorageTempBottom | — | — | — | Read-only |
| 0x009F | heating_cylinder_top_temperature | S | f32 | °C | HcStorageTempTop | — | — | — | Read-only |
| 0x00A0 | heating_cylinder_bottom_temperature | S | f32 | °C | HcStorageTempBottom | — | — | — | Read-only |
| 0x00A1 | pv_surplus_enabled | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Between cylinder temps and buffer_charge_offset |
| 0x00A2 | heating_cylinder_offset_at_pv_surplus | C | f32 | K | — | — | — | — | 0..15 per TSP. Candidate, unconfirmed on the wire: written as `02 01 00 FF A2 00 <float32 LE>` (`OT=0x01, GG=0x00, II=0xFF`), identical on both families: a float32 (unit not established; candidate K). Not established: the controller's reaction. Correspondence: `smartPhotovoltaicBufferOffset` (`myvaillant_name_vrc720` and `myvaillant_name_vrc700`). |
| 0x00A3 | ventilation_time_program_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A4 | ventilation_special_function_state | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for the VRC700 family, a two-byte `uint16 LE` value with the enumeration listed under [Enumerations that differ by family](#enumerations-that-differ-by-family). |
| 0x00A5 | cascade_client_sequence | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00A6 | menu_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A7 | confirm_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A8 | back_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A9 | up_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00AA | down_button_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00AB | isolation_switch_active | C | u8 | bool | — | — | — | — | FLAGS=0x02. Scan value: 1 |
| 0x00AF | cooling_electricity_consumption_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B0 | cooling_electricity_consumption_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B1 | cooling_electricity_consumption_total | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B2 | network_identifier | C | u16 | raw | — | — | — | — | FLAGS=0x02. Scan value: 0xBDA9 (48553). Semantics unknown |
| 0x00B3 | multifunction_output_1_mode | C | u8 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00B5 | outdoor_temperature_sensor_ok | P | u8 | bool | — | — | — | — | FLAGS=0x01. Scan value: 1 |
| 0x00B6 | external_energy_management_enabled | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. Candidate, unconfirmed on the wire: written as `02 01 00 FF B6 00 <u8>` (value 0 or 1). It is also read as `02 00 00 00 B6 00`; see [protocol section 4.11](./ebus-vaillant-B524.md#411-writes-with-iiff-dhw-cylinder-and-buffer-registers). Not established: the controller's reaction and the meaning of 0 and 1 on the controller. |
| 0x00B8 | solar_diverter_valve | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00B9 | cooling_electricity_consumption_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0. Energy/counter region start |
| 0x00BA | cooling_electricity_consumption_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00BB | dhw_electricity_consumption_current_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BC | dhw_electricity_consumption_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BD | heating_fuel_consumption_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BF | dhw_fuel_consumption_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00C0 | heating_electricity_consumption_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00C1 | heating_electricity_consumption_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Unknown sub-counter (slowly incrementing, value=7). No standard register equivalent |
| 0x00C2 | electricity_consumption_current_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x004F** (PrEnergySumHcThisMonth). Verified 2026-03-08 |
| 0x00C3 | electricity_consumption_previous_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0053** (PrEnergySumHcLastMonth). Verified 2026-03-08 |
| 0x00C4 | electricity_consumption_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Unknown sub-counter (slowly incrementing, value=7). Same as 0x00C1 |
| 0x00C5 | electricity_consumption_previous_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0058** (PrEnergySumHwc). Verified 2026-03-08 |
| 0x00C6 | electricity_consumption_total | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0057** (PrEnergySumHc). Verified 2026-03-08 |
| 0x00C7 | dhw_fuel_consumption_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0059** (PrFuelSumHwc). Verified 2026-03-08 |
| 0x00C8 | heating_fuel_consumption_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0056** (PrFuelSumHc). Verified 2026-03-08 |
| 0x00C9 | fuel_consumption_current_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Near-mirror of 0x004E** (PrFuelSumHcThisMonth). Off-by-1 delta |
| 0x00CA | fuel_consumption_previous_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Near-mirror of 0x0052** (PrFuelSumHcLastMonth). Off-by-1 delta |
| 0x00CB | fuel_consumption_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. gas.climate + gas.dhw (all-time). Verified 2026-03-08 |
| 0x00CC | fuel_consumption_previous_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Always 0 |
| 0x00CD | fuel_consumption_total | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Duplicate of 0x00CB. Verified 2026-03-08 |
| 0x00CE | heat_recovery_yield_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00CF | heat_recovery_yield_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D0 | heat_recovery_yield_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D1 | heat_recovery_yield_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D2 | solar_yield_previous_month | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D3 | solar_yield_current_month | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D4 | solar_yield_current_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D5 | solar_yield_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D6 | environmental_yield_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D7 | environmental_yield_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D8 | environmental_yield_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D9 | electricity_tariff_type | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00DA | manual_cooling_start_date | C | date | date | — | — | — | cooling_enabled? | FLAGS=0x02 observed. VRC700 manual cooling start-date interpretation and writability are **Hypotheses**; no correlated write evidence is published. BCD HDA:3. Default: 01.01.2013. **Dormant** when cooling not configured. Candidate, unconfirmed on the wire: on the VRC720 family this register is a three-byte date; for cooling for a number of days the start date is written here and the stop date to `RR=0x00DB` (cancel triple `01 01 13`; the start date is written before the stop date). The family scope of this register is unresolved: the VRC700-family interpretation above and the VRC720-family scope of the candidate read and write are both candidates (see Open questions). |
| 0x00DB | manual_cooling_end_date | C | date | date | — | — | — | cooling_enabled? | FLAGS=0x02 observed. VRC700 manual cooling end-date interpretation and writability are **Hypotheses**; no correlated write evidence is published. BCD HDA:3. Default: 01.01.2013. **Dormant** when cooling not configured. Candidate, unconfirmed on the wire: on the VRC720 family the stop date of cooling for a number of days is written here. The family scope of this register is unresolved: the VRC700-family interpretation above and the VRC720-family scope of the candidate read and write are both candidates (see Open questions). |
| 0x00DC | room_temperature_control_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: the requester matrix gives, for the VRC720 family, a one-byte `uint8` value with the enumeration `0=Two Point; 1=Analoge` (spelled as shown). |
| 0x00DD | screed_drying_profile_1_temperature_setpoint | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 10 bytes: [25,30,35,40,45,45,45,45,45,45] — hourly temp profile (°C/2) |
| 0x00DE | screed_drying_profile_2_temperature_setpoint | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 10 bytes: [45,45,40,35,30,25,10,10,10,10] — hourly temp profile continued |
| 0x00DF | screed_drying_profile_3_temperature_setpoint | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 9 bytes: [10,10,10,30,35,40,45,35,25] — hourly temp profile end. 29 values total across DD-DF |
| 0x00E0 | environmental_yield_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00E1 | circuit_control_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00E2 | automatic_control_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00E3 | up_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E4 | down_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E5 | help_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E6 | confirm_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E7 | menu_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E8 | back_button_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E9 | slider_button_1_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EA | slider_button_2_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EB | slider_button_3_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EC | slider_button_4_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00ED | slider_button_5_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EE | slider_button_6_level | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EF | continuous_heating_room_temperature_setpoint | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 20.0. Temperature setpoint |
| 0x00F0 | priority_error_code | P | u16 | — | — | — | — | — | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F1 | priority_maintenance_code | P | u16 | — | — | — | — | — | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F2 | holiday_start_date | C | date | date | — | — | — | — | System holiday start date (3-byte date). FLAGS=0x03. Scan: 01.01.2015 (BCD) |
| 0x00F3 | holiday_end_date | C | date | date | — | — | — | — | System holiday end date (3-byte date). FLAGS=0x03. Scan: 01.01.2015 (BCD). Candidate, unconfirmed on the wire: the VRC720-family set sequence writes a start time here; its cancel sequence writes the date-shaped `01 01 0F`. The disagreement is unresolved. |
| 0x00F4 | holiday_start_clock_time | C | time | time | — | — | — | — | System holiday start time (3-byte time), not a date. FLAGS=0x03. Scan: 00:00:00 (reset). Candidate, unconfirmed on the wire: the VRC720-family set sequence writes an end date here; its cancel sequence writes the time-shaped `00 00 00`. The disagreement is unresolved. |
| 0x00F5 | holiday_end_clock_time | C | time | time | — | — | — | — | System holiday end time (3-byte time), not a date. FLAGS=0x03. Scan: 00:00:00 (reset) |
| 0x00F6 | room_temperature_setpoint_at_holiday | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 10.0 |
| 0x00F7 | holiday_abort_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00F8 | manual_cooling_abort_command | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. ebusd TSP hinted 5-byte — scan sees 1 byte |
| 0x00F9 | ventilation_boost_active | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00FA | external_demand_input_mode | C | u8 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00FB | heat_pump_temperature_difference_limit_minimum | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 10.0 |
| 0x00FC | dhw_heat_pump_flow_temperature_setpoint_maximum | P | f32 | °C | — | — | — | — | FLAGS=0x01. Scan value: 90.0. Likely max flow temperature |
| 0x00FD | boiler_flow_temperature_setpoint_maximum | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00FE | (unknown_temp_config) | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 13.0 |
| 0x00FF | (unknown_temp_config) | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 25.0 |

**Note:** 100 new registers discovered in the 0x003C-0x00FF range by proof scan 2026-03-05. The 0x00C1-0x00CD cluster contains u32 energy counters (decode as u32, NOT f32 — the tiny float values like 6.586e-43 are mis-decoded u32 integers). The 0x00DD-0x00DF cluster contains packed hourly temperature schedule bytes. The 0x00E3-0x00EE cluster (13 consecutive f32=0.0 with FLAGS=0x01) may be per-month energy statistics. The 0x00F2-0x00F5 cluster contains the system holiday start/end dates (0x00F2/0x00F3) and start/end times (0x00F4/0x00F5).

---

### GG=0x01 — Native Domestic Hot Water

All registers use opcode `0x02`, instance `0x00`. `dhw_circuit_type`
(RR0001) is also the family-qualified discovery predicate only when its reply
is an exact two-byte UIN decoded nonzero; zero is `not_present`, and an empty,
wrong-width, NACK, decode-failed, or unmatched result is `unknown`. This is
independent of OP01 descriptions for RR0000..0013. All registers except
`dhw_special_function_state` (0x000F) are gated by `dhw_circuit_type` (0x0001).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | dhw_circuit_type | C | u16 | bool | — | 0..1 | `0=off 1=on` | — | Gate register for GG=0x01. Constraint tag u16, Scan verified 2-byte. The candidate raw LE16 interpretation `0=Deactivated`, `1=DHWCircuit` remains unconfirmed on the wire. The availability test and a circuit-type interpretation remain distinct. |
| 0x0002 | dhw_circulation_pump_active | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | Constraint tag u8 |
| 0x0003 | dhw_operating_mode | C | u16 | enum | HwcOpMode | 0..2 | →opmode | hwc_enabled | |
| 0x0004 | dhw_temperature_setpoint | C | f32 | °C | HwcTempDesired | 35..70 | — | hwc_enabled | Candidate, unconfirmed on the wire: written as `02 01 01 FF 04 00 <float32 LE>` (`OT=0x01, GG=0x01, II=0xFF`; a float32 little-endian value), identical on both families. Not established: the controller's reaction. |
| 0x0005 | dhw_temperature | S | f32 | °C | HwcStorageTemp | 0..99 | — | hwc_enabled | Read-only |
| 0x0006 | dhw_pump_active | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | Constraint tag u8 |
| 0x0007 | dhw_time_program_reset_command | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0008 | dhw_flow_temperature_setpoint | S | f32 | °C | HwcFlowTemp | — | — | hwc_enabled | Read-only |
| 0x0009 | dhw_holiday_start_date | C | date | date | HwcHolidayStartPeriod | — | — | hwc_enabled | |
| 0x000A | dhw_holiday_end_date | C | date | date | HwcHolidayEndPeriod | — | — | hwc_enabled | |
| 0x000B | dhw_bank_holiday_start_date | C | date | date | HwcBankHolidayStartPeriod | — | — | hwc_enabled | ebusd confirmed |
| 0x000C | dhw_bank_holiday_end_date | C | date | date | HwcBankHolidayEndPeriod | — | — | hwc_enabled | ebusd confirmed |
| 0x000D | dhw_special_function_mode | C | u8 | enum | HwcSFMode | — | →sfmode | hwc_enabled | FLAGS=0x03 (user RW). Scan validated 1-byte. Candidate, unconfirmed on the wire: written as `OP=0x02, OT=0x01, GG=0x01, II=0xFF, RR=0x000D` with one value byte, 6 = start a one-time DHW load and 0 = cancel it (bodies `02 01 01 FF 0D 00 06` and `02 01 01 FF 0D 00 00`), identical on both families. Reflected in (candidate): `GG=0x01, II=0x00, RR=0x000F`, where 9 denotes one-time tank loading (candidate). Not established: the controller's reaction to the write. |
| 0x000E | dhw_central_control_active | P | u8 | bool | — | — | — | — | FLAGS=0x01. Scan value: 1. Near hwc_status, possibly active flag |
| 0x000F | dhw_special_function_state | S | u16 | state | — | — | — | — | Not gated |
| 0x0010 | dhw_holiday_start_clock_time | C | time | time | — | — | — | hwc_enabled | |
| 0x0011 | dhw_holiday_end_clock_time | C | time | time | — | — | — | hwc_enabled | |
| 0x0012 | dhw_holiday_abort_command | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0013 | (unknown) | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0014 | dhw_preference | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0015 | dhw_recharge_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0019 | dhw_loading_efficiency_state | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |

---

<a id="gg0x02--heating-circuits-multi-instance"></a>
### GG=0x02 — Circuits

All registers use opcode `0x02`. The VRC720 family
admits II00..II08 as ordinary heating-circuit candidates and II09 as the virtual
native-water circuit. A other or unknown family requires separate
qualification. Active heating circuits are discovered by probing
`circuit_type` (RR=0x0002). In sanitized observations, II00 and
II01 return raw `0100` with FLAGS=03; II02 returns raw `0000` with FLAGS=03 and
is inactive. These are profile-scoped selector observations, not a global
indexing rule or a physical-topology claim. An empty/null response contains no
valid register value; it does not by itself distinguish absence, inactivity or
unsupported addressing.

`II=0x09` is retained as the virtual native-water circuit. Its selector does
not identify a physical heating circuit. The current public evidence supplies
no presence predicate for this virtual identity: RR0008 and RR0020 must not be
used to infer it from a temperature or status value. This leaves the inactive
handling of other `mctype=0` circuit slots unchanged. Community evidence:
[public register observations](https://github.com/Project-Helianthus/helianthus-vrc-explorer/discussions/53).

Historical scan records include II0A probes. They remain retained raw
observations, but do not extend the current profile's II00..09 coverage.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | hydraulic_circuit_type | — | u16 | — | — | 1..2 | — | — | CSV says `circuit_type` but commonly mapped to 0x0002. Purpose unverified. † |
| 0x0002 | circuit_type | P | u16 | enum | Hc{hc}CircuitType | 0..4 | →mctype | — | Discovery probe. Also `mixer_circuit_type_external` |
| 0x0003 | circuit_room_influence_mode | C | u8 | enum | Hc{hc}RoomInfluenceType | — | `0=inactive 1=active 2=extended` | — | Controls room sensor influence on heating curve. No value reply observed at II=0x00. See GetExtendedRegisters §4.2.5 for behavioral semantics |
| 0x0004 | circuit_return_temperature_setpoint | C | f32 | °C | Hc{hc}ReturnTempDesired | 15..80 | — | circuit_type=4 (return_increase) | Factory setting 30°C. Only meaningful for "Increase in return" circuits |
| 0x0005 | circuit_condensate_sensitive_emitter_available | C | u8 | bool | — | 0..1 | `0=off 1=on` | cooling_enabled | Constraint tag u8. ebusd onoff=UCH. † |
| 0x0006 | circuit_cooling_enabled | C | u8 | bool | Hc{hc}CoolingEnabled | 0..1 | `0=off 1=on` | — | Gate register. Constraint tag u8. ebusd onoff=UCH |
| 0x0007 | circuit_flow_temperature_setpoint | S | f32 | °C | Hc{hc}FlowTempDesired | — | — | — | Installer-field candidate; physical menu correspondence requires corroboration. |
| 0x0008 | circuit_flow_temperature | S | f32 | °C | Hc{hc}FlowTemp | — | — | — | Read-only. Circuit flow sensor VF[x], NOT boiler return temperature |
| 0x0009 | dhw_circuit_temperature_setpoint | C | f32 | °C | — | — | — | ext_hwc_active | † |
| 0x000A | circuit_unknown_7 | C | f32 | K | — | — | — | cooling_enabled | † |
| 0x000B | heating_circuit_flow_temperature_offset | C | f32 | K | Hc{hc}ExcessTemp | — | — | circuit_type=1 (heating) | Flow temp increased by this value to keep mixing valve in control range |
| 0x000C | circuit_flow_high_temperature_setpoint | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | Fixed-value circuit target flow temp. † |
| 0x000D | circuit_flow_low_temperature_setpoint | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | Fixed-value circuit setback temp. † |
| 0x000E | circuit_frost_protection_mode | C | u16 | enum | Hc{hc}SetbackMode | — | →offmode | circuit_type=1 (heating) | Installer-field candidate; do not infer a separate setback field from this label or physical menu correspondence. |
| 0x000F | circuit_heating_curve_factor | C | f32 | — | Hc{hc}HeatCurve | — | — | — | Dimensionless ratio |
| 0x0010 | heating_circuit_flow_temperature_setpoint_maximum | C | f32 | °C | Hc{hc}MaxFlowTempDesired | — | — | — | 15..80 per ebusd |
| 0x0011 | cooling_circuit_flow_temperature_setpoint_minimum | C | f32 | °C | Hc{hc}MinCoolingTempDesired | — | — | cooling_enabled | |
| 0x0012 | circuit_flow_temperature_setpoint_minimum | C | f32 | °C | Hc{hc}MinFlowTempDesired | — | — | — | |
| 0x0013 | dhw_circuit_operating_mode | C | u16 | enum | — | — | values unknown | ext_hwc_active | |
| 0x0014 | heating_circuit_outdoor_temperature_limit_maximum | C | f32 | °C | Hc{hc}SummerTempLimit | — | — | — | Installer-field candidate; the summer-cutoff interpretation requires physical corroboration. |
| 0x0015 | circuit_room_temperature_influence_mode | C | u16 | enum | Hc{hc}RoomTempSwitchOn | — | →rcmode | — | Gate for dew point |
| 0x0016 | circuit_screed_drying_time | C | u16 | count | Hc{hc}ScreedDryingDay | — | — | — | Screed drying program |
| 0x0017 | screed_drying_circuit_temperature_setpoint | S | f32 | °C | Hc{hc}ScreedDryingTempDesired | — | — | — | FLAGS=0x01 (stable RO) — computed setpoint, not user-configurable |
| 0x0018 | dhw_circuit_circulation_pump_active | S | u16 | bool | Hc{hc}ExternalHWCActive | — | — | — | Gate register for ext HWC. FLAGS=0x00 (volatile RO) — status, not config |
| 0x0019 | circuit_external_demand_input | S | u16 | state | Hc{hc}ExternalHeatDemand | — | — | — | External heat source. FLAGS=0x00 (volatile RO) — status, not config |
| 0x001A | circuit_mixer_movement | S | f32 | % | Hc{hc}MixerMovement | — | — | — | Signed float: `<0`=closing, `>0`=opening. Scan verified: -100.0 when fully closing. Read-only |
| 0x001B | circuit_pump_unknown_8 | S | u16 | raw | Hc{hc}Status | — | — | — | Pump status per observed Vaillant naming ("Status Pump"). Earlier documented here as carrying the circuit state enumeration (STANDBY/HEATING/COOLING/DHW), on the strength of a single 2026-03-08 idle observation and a name correlation; that observation is equally consistent with a pump status and does not discriminate between the two readings. See [Circuit State Enum](#circuit-state-enum) |
| 0x001C | circuit_adaptive_heating_curve_offset | S | f32 | — | Hc{hc}HeatCurveAdaption | — | — | — | Heat curve adaption factor. Dimensionless. Read-only |
| 0x001D | circuit_unknown_9 | C | f32 | °C | Hc{hc}FrostProtThreshold | — | — | — | FLAGS=0x02 (technical RW) — writable config, not property |
| 0x001E | circuit_state | S | u16 | enum | Hc{hc}PumpStatus | — | — | — | Hypothesis: carries the circuit state enumeration (0=STANDBY, 1=HEATING, 2=COOLING, 3=DHW), based on observed Vaillant naming ("Status circuit", myVaillant `circuitState`); hardware confirmation pending. Installer-field candidate, distinct from RR001B and RR0020. See [Circuit State Enum](#circuit-state-enum) |
| 0x001F | cooling_circuit_outdoor_temperature_limit_minimum | C | f32 | °C | Hc{hc}RoomSetpoint | — | — | — | |
| 0x0020 | circuit_unknown_10 | S | u8 | raw | Hc{hc}FlowTempCalc | — | — | — | Observed UCH one-byte raw status (`00`) at the relevant circuit selectors. It is not a temperature value; earlier f32 prose is unqualified. |
| 0x0021 | circuit_mixer_position | S | f32 | % | Hc{hc}MixerPosition | — | — | — | |
| 0x0022 | circuit_room_humidity | S | f32 | % | Hc{hc}Humidity | — | — | — | From room sensor |
| 0x0023 | circuit_dew_point_temperature | S | f32 | °C | Hc{hc}DewPointTemp | — | — | — | |
| 0x0024 | circuit_pump_operating_time_total | S | u32 | hrs | Hc{hc}PumpHours | — | — | — | |
| 0x0025 | circuit_pump_start_count_total | S | u32 | count | Hc{hc}PumpStarts | — | — | — | |

---

<a id="gg0x03--zones-multi-instance"></a>
### GG=0x03 — Zones

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones are
discovered by probing `zone_circuit_assignment` (RR=0x001C). In the VRC720
scoped observation, zone II00 maps to raw `00` and zone II01 to raw `01`; II02+
returns `FF`. These are native values, with no +1 remapping. They are
profile-scoped observations, not a universal zone/circuit contract.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | cooling_zone_operating_mode | C | u16 | enum | — | 0..2 | →opmode | cooling_enabled | Same enum as heating_operation_mode |
| 0x0002 | cooling_zone_room_temperature_setpoint | C | f32 | °C | Zone{z}CoolingTemp | 15..30 step 0.5 | — | cooling_enabled | |
| 0x0003 | zone_holiday_start_date | C | date | date | Zone{z}HolidayStartPeriod | — | — | — | |
| 0x0004 | zone_holiday_end_date | C | date | date | Zone{z}HolidayEndPeriod | — | — | — | |
| 0x0005 | zone_room_temperature_setpoint_at_holiday | C | f32 | °C | Zone{z}HolidayTemp | 5..30 | — | — | |
| 0x0006 | heating_zone_operating_mode | C | u16 | enum | Zone{z}OpMode | 0..2 | →opmode | — | Candidate, unconfirmed on the wire: VRC720-family labels 0 Off, 1 TimeControlled, 2 Manual; VRC700-family labels 0 Off, 1 Auto, 2 Day, 3 Setback; the VRC700-family value 3 lies outside the catalog range 0..2 of this row, and the conflict is unresolved. Candidate, unconfirmed on the wire: the room-control write on both families is `02 01 03 II 06 00 V0 V1` (a 16-bit little-endian mode code; candidate values 0 and 2), with no controller acceptance of the value known; whether the zone number denotes a circuit is not established. See [protocol section 4.10](./ebus-vaillant-B524.md#410-room-control-writes-and-zone-mapping-reads). |
| 0x0007 | heating_zone_room_comfort_temperature_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. Candidate, unconfirmed on the wire: on the VRC700 family it is a float32 (°C candidate); the room-control set point write is `02 01 03 II 07 00 V0 V1 V2 V3` (float32 little-endian). |
| 0x0008 | zone_room_temperature_setpoint_at_quick_veto | C | f32 | °C | Zone{z}QuickVetoTemp | — | — | — | Veto override target. Candidate, unconfirmed on the wire: written as `02 01 03 II 08 00 <float32>` as the first step of a quick veto set or modify; the unit is not established. See [protocol section 4.9](./ebus-vaillant-B524.md#49-quick-veto-away-mode-and-switching-back-to-time-control). |
| 0x0009 | heating_zone_room_setback_temperature_setpoint | C | f32 | °C | Zone{z}NightTemp | — | — | — | Night setpoint |
| 0x000A | heating_zone_operating_mode_at_teleswitch | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000B | cooling_zone_operating_mode_at_teleswitch | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000C | zone_bank_holiday_start_date | C | date | date | Zone{z}BankHolidayStartPeriod | — | — | — | ebusd confirmed |
| 0x000D | zone_bank_holiday_end_date | C | date | date | Zone{z}BankHolidayEndPeriod | — | — | — | ebusd confirmed |
| 0x000E | zone_special_function_mode | C | u8 | enum | Zone{z}SFMode | — | →sfmode | — | FLAGS=0x03 (user RW). Scan validated 1-byte. Writable to set quickveto/away. Candidate, unconfirmed on the wire: the values written are 03 to set a quick veto on the VRC700 family, 00 to cancel a quick veto or to switch back to time control, and 01 for a zone ventilation boost (`02 01 03 II 0E 00 xx`). |
| 0x000F | zone_room_temperature | S | f32 | °C | Zone{z}RoomTemp | — | — | — | FLAGS=0x01 (stable RO). From room sensor |
| 0x0010 | zone_time_program_reset_command | C | u16 | — | — | — | — | — | FLAGS=0x03 (user RW). Observed in a register survey, not in earlier catalogs |
| 0x0011 | zone_enabled | C | u16 | — | — | — | — | — | FLAGS=0x03 (user RW). Observed in a register survey, not in earlier catalogs |
| 0x0012 | zone_valve_position | S | u16 | bool | Zone{z}ValveStatus | — | `0=closed 1=open` | — | FLAGS=0x01 (stable RO). Used for hvac_action derivation |
| 0x0013 | zone_room_sensor_binding_mode | C | u16 | enum | Zone{z}RoomZoneMapping | — | →zmapping | — | Maps zone to room temperature sensor source. The raw numeric B524 enum (`0`, `1`, `2`, ...) is the authoritative value. Candidate, unconfirmed on the wire: the reply is two bytes (uint16 little-endian). Candidate labels beyond the `zmapping` table: VRC720 family 2..5 REMOTE_CONTROL1..4; VRC700 family 1 CENTRAL_CONTROL and 2..9 REMOTE_CONTROL1..8. |
| 0x0014 | heating_zone_room_effective_temperature_setpoint | S | f32 | °C | Zone{z}ActualRoomTempDesired | — | — | — | FLAGS=0x01 (stable RO) — computed output, not user-settable. Current setpoint considering all conditions |
| 0x0015 | cooling_zone_room_effective_temperature_setpoint | S | f32 | °C | — | — | — | cooling_enabled | FLAGS=0x01 (stable RO) — computed output, not user-settable |
| 0x0016 | zone_name | C | string | text | Zone{z}Shortname | — | — | — | maxLength 6 |
| 0x0017 | zone_name_prefix | C | string | text | Zone{z}Name1 | — | — | — | maxLength 5. Part 1 |
| 0x0018 | zone_name_suffix | C | string | text | Zone{z}Name2 | — | — | — | maxLength 5. Part 2 |
| 0x0019 | heating_zone_time_program_active | S | u16 | bool | — | — | `0=off 1=on` | — | Timer schedule flag |
| 0x001A | cooling_zone_time_program_active | S | u16 | bool | — | — | `0=off 1=on` | cooling_enabled | Timer schedule flag |
| 0x001B | zone_special_function_state | S | u16 | state | — | — | — | — | Raw zone status code. See the [unresolved response width](ebus-vaillant-B524.md#zone-special-function-response-width); retain this u16 catalog entry separately from the one-byte candidate format. |
| 0x001C | zone_circuit_assignment | P | bytes | raw | Zone{z}Index | — | — | — | Example VRC720 replies: II00=`00`, II01=`01`, II02+=`FF`; preserve raw index, no +1 remap. The signed int8 interpretation with `-1=notBound` remains unconfirmed; see [numeric formats](ebus-vaillant-B524.md#vaillant-numeric-formats) for profile ranges and the limit of that interpretation. Candidate, unconfirmed on the wire: the reply is one byte, a signed 8-bit value; it is not renumbered. |
| 0x001D | heating_zone_event_end_clock_time | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x001E | zone_quick_veto_end_clock_time | C | time | time | Zone{z}QuickVetoEndTime | — | — | — | FLAGS=0x03 (user RW) — writable, can extend/set veto end time |
| 0x0020 | zone_holiday_end_clock_time | C | time | time | — | — | — | — | |
| 0x0021 | zone_holiday_start_clock_time | C | time | time | — | — | — | — | |
| 0x0022 | heating_zone_room_manual_temperature_setpoint | C | f32 | °C | Zone{z}DayTemp | — | — | — | 15..30 step 0.5 per ebusd. Candidate, unconfirmed on the wire: the VRC720-family room-control set point write is `02 01 03 II 22 00 V0 V1 V2 V3` (float32 little-endian). |
| 0x0023 | cooling_zone_room_manual_temperature_setpoint | C | f32 | °C | — | — | — | cooling_enabled | |
| 0x0024 | zone_quick_veto_end_date | C | date | date | Zone{z}QuickVetoEndDate | — | — | — | FLAGS=0x03 (user RW) — writable, can extend/set veto end date |
| 0x0025 | zone_holiday_abort_command | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0026 | zone_quick_veto_time | C | f32 | hrs | Zone{z}QuickVetoDuration | — | — | — | 0.5..12 step 0.5. Writing enables quick veto mode. Candidate, unconfirmed on the wire: on the VRC720 family it is written as `02 01 03 II 26 00 <float32>` after the set point; the unit is not established. |
| 0x0027 | zone_manual_cooling_active | S | u16 | — | — | — | — | — | FLAGS=0x00 (volatile RO). Observed in a register survey |
| 0x0028 | zone_room_humidity | S | f32 | % | — | — | — | — | FLAGS=0x01 (stable RO). From room sensor |
| 0x0029 | zone_cooling_enabled | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002A | zone_summer_cutoff_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002B | zone_continuous_heating_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002C | zone_frost_protection_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002D | heating_zone_thermostat_cutoff_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002E | cooling_zone_thermostat_cutoff_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |

#### Zone Mode Derivation

The zone operating mode is typically derived from:
- `heating_zone_operating_mode` (0x0006): opmode enum (0=off, 1=auto, 2=manual)
- `zone_special_function_mode` (0x000E): sfmode enum (2=quickveto, 3/4=away)
- Associated circuit's `circuit_cooling_enabled` (GG=0x02 RR=0x0006): determines heat vs cool capability

---

### GG=0x04 — Solar Circuit

Entire group gated by `fm5_config ≤ 2`. All registers use opcode `0x02`, instance `0x00`.

**No ebusd coverage exists for GG=0x04** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | solar_pump_operating_time_total_reset_command | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | † |
| 0x0002 | solar_pump_kick_enabled | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | Not pump status (pump is at 0x0008). † |
| 0x0003 | solar_collector_temperature | S | f32 | °C | — | -40..155 | — | fm5_config≤2 | † |
| 0x0004 | solar_collector_temperature_limit_minimum | C | f32 | K | — | 0..99 | — | fm5_config≤2 | Not storage temp. † |
| 0x0005 | solar_circuit_protection_temperature_limit | C | f32 | °C | — | 110..150 | — | fm5_config≤2 | † |
| 0x0006 | solar_circuit_protection_stop_temperature_limit | C | f32 | °C | — | 75..115 | — | fm5_config≤2 | Not collector shutdown. † |
| 0x0007 | solar_yield_temperature | S | f32 | °C | — | — | — | fm5_config≤2 | † |
| 0x0008 | solar_pump_active | S | u8 | bool | — | — | `0=off 1=on` | fm5_config≤2 | † |
| 0x0009 | solar_circuit_flow_rate | S | f32 | raw | — | — | — | fm5_config≤2 | Current yield. † |
| 0x000A | solar_circuit_flow_rate_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000B | solar_pump_operating_time_total | S | u32 | hrs | — | — | — | fm5_config≤2 | Cumulative runtime. † |
| 0x000C | solar_pump_power_limit_minimum | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |

---

<a id="gg0x05--cylinders-multi-instance"></a>
### GG=0x05 — Solar Loaded Cylinder

Entire group gated by `fm5_config ≤ 2`. These are solar charging parameters per cylinder. General cylinder config (max temp, charge hysteresis) is in GG=0x00 system config.

**No ebusd coverage exists for GG=0x05** — all names are from value-matched CSV only (†) and carry false-positive risk.

Cylinder presence detection:
- Raw config registers alone do **not** imply cylinder presence.
- A cylinder instance should be considered present only when `RR=0x0004` (`solar_cylinder_bottom_temperature`) yields a live decodable value for that instance.
- Config-only responses (`RR=0x0001..0x0003`) without temperature evidence do not confirm a physical cylinder.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | solar_cylinder_temperature_limit_maximum | C | f32 | °C | — | 0..99 | — | fm5_config≤2 | † |
| 0x0002 | solar_cylinder_start_temperature_difference_limit | C | f32 | K | — | 2..25 | — | fm5_config≤2 | † |
| 0x0003 | solar_cylinder_stop_temperature_difference_limit | C | f32 | K | — | 1..20 | — | fm5_config≤2 | † |
| 0x0004 | solar_cylinder_bottom_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2 | † |

---

### GG=0x08 — DeltaT

7 named registers. The local II scope is observed and profile-dependent;
responses on multiple II selectors do not establish physical instance topology.
Historical II00..0A exploration is retained as evidence, not as a current
profile bound or a qualified device count.
OP06/GG08 remains a separate instanced selector set with its own RR limit.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | differential_control_temperature_limit_maximum | C | f32 | °C | — | 0..99 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 99.0 |
| 0x0002 | differential_control_temperature_limit_minimum | C | f32 | K | — | 0..99 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 0.0 |
| 0x0003 | differential_control_start_temperature_difference_limit | C | f32 | K | — | 2..25 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 12.0 |
| 0x0004 | differential_control_stop_temperature_difference_limit | C | f32 | K | — | 1..20 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 5.0 |
| 0x0005 | differential_control_sensor_1_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | FLAGS=0x01. NaN (no sensor) |
| 0x0006 | differential_control_sensor_2_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | FLAGS=0x01. NaN (no sensor) |
| 0x0007 | differential_control_output | S | u8 | — | — | — | — | — | FLAGS=0x00. Scan value: 0. Possibly pump status |

---

### GG=0x09 — Ventilation

OP02/GG09 is a local selector set. Its zero-instance passive observation does not establish a universal write-triggered or non-readable property. Any association between RR=0x0001..0x0004 and system quick-mode control remains a **Hypothesis** pending publishable correlated evidence.

The RR0002 and RR0004 labels below are operator-selected presentation
annotations. They are not independently native-verified and do not establish
target support or writability. Unknown values remain numeric/unknown.

The local II scope is profile-dependent. Repeated historical values do not
establish a template/default role or physical topology. Empty and failed reads
remain distinct observations, not confirmed absence.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | ventilation_special_function_mode | C | u16 | — | — | 0..255 | — | — | FLAGS=0x02. All instances: 0 |
| 0x0002 | ventilation_operating_mode | C | u16 | enum | — | 1..3 | `1=TIME_CONTROLLED 2=NORMAL 3=REDUCED` | — | FLAGS=0x02. All instances: 1. Operator-selected presentation annotation; not independently native-verified |
| 0x0003 | ventilation_time_program_active | S | u8 | bool | — | 0..1 | `0=off 1=on` | — | FLAGS=0x00. All instances: 1 |
| 0x0004 | ventilation_special_function_state | S | u16 | — | — | 0..10 | `0=REGULAR 1=BOOST 7=HOLIDAY 10=SYSTEM_OFF` | — | FLAGS=0x00. All instances: 0. Operator-selected presentation annotation; not independently native-verified |
| 0x0005 | ventilation_volatile_organic_compound_sensor_1 | S | u16 | — | — | 0..32768 | — | — | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0006 | ventilation_volatile_organic_compound_sensor_2 | S | u16 | — | — | 0..32768 | — | — | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0007 | ventilation_holiday_end_date | C | date | date | — | — | — | — | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x0008 | ventilation_holiday_end_clock_time | C | time | time | — | — | — | — | FLAGS=0x02. 00:00:00 |
| 0x0009 | ventilation_holiday_start_date | C | date | date | — | — | — | — | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x000A | ventilation_holiday_start_clock_time | C | time | time | — | — | — | — | FLAGS=0x02. 00:00:00 |
| 0x000B | ventilation_heat_recovery | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000C | ventilation_volatile_organic_compound_limit_maximum | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000D | ventilation_fan_speed_limit_maximum_at_day | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000E | ventilation_fan_speed_limit_maximum_at_night | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000F | ventilation_holiday_abort_command | C | u8 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |

---

### GG=0x09 — Ventilation / recoVair Candidates

The published OP00 interpretation includes ID0010h `ventilation_unit_count`. It does
not prove GG10h or device presence; the public reported samples all return zero.
The following corrected reconstruction is **Hypothesis** for a VRC720 controller
profile, awaiting publishable correlated replies. It does not replace other
GG09 meanings or establish writable capability. Keep `(OP02,GG09,II,RR)` and
profile provenance; no data from these rows is promoted into a universal mapping.

| RR | snake_case name | Candidate format |
| --- | --- | --- |
| 0002h | `ventilation_operating_mode` | enum; presentation values `1=TIME_CONTROLLED 2=NORMAL 3=REDUCED` |
| 0004h | `ventilation_special_function_state` | u16; presentation values `0=REGULAR 1=BOOST 7=HOLIDAY 10=SYSTEM_OFF` |
| 0007h / 0008h | `ventilation_holiday_end_date` / `ventilation_holiday_end_clock_time` | date / time; codec qualification pending |
| 0009h / 000Ah | `ventilation_holiday_start_date` / `ventilation_holiday_start_clock_time` | date / time; codec qualification pending |
| 000Dh / 000Eh | `ventilation_fan_speed_limit_maximum_at_day` / `ventilation_fan_speed_limit_maximum_at_night` | u16; range unknown |

These candidate names are shared with the OP02 scalar catalog. The status/availability of a local probe
and a decoded physical ventilation state are distinct. OP02/GG00/RR0016 (VRC700 family) is catalogued separately under the same name
`ventilation_operating_mode`; the equal name does not establish an
alias of OP02/GG09 or change the codec or meaning of its stored value.

---

### GG=0x0A — Local Parameters

`OP=0x02, GG=0x0A` is an observed local selector set, separate from
`OP=0x06, GG=0x0A`. Its physical-device identity, role and topology remain
**Unknown**. The namespace must not be labelled as a thermostat or a
controller template solely from the outer group name or repeated values.

Retained observations cover requested II=0x00..0x0A and contain repeated
register values across selectors. Repetition does not establish a physical
instance count, ignored II selectors, template/default purpose, or a per-VR92
relationship. Keep each native request identity and its reply independently.
Historical row names and short-probe constraints are unqualified annotations;
the row names are provisional, and their meanings are not established; the row
names do not establish writability, discovery predicates or device identity.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | sensor_mode | C | u8 | enum | — | 0..3 | — | — | FLAGS=0x03. All: 0 |
| 0x0002 | protocol_type | C | u8 | enum | — | 1..2 | — | — | FLAGS=0x03. All: 1 |
| 0x0003 | communication_mode | C | u8 | enum | — | 1..2 | — | — | FLAGS=0x03. All: 1 |
| 0x0005 | (unknown) | C | u8 | — | — | 0..3 | — | — | FLAGS=0x03. All: 1 |
| 0x0006 | sensor_enabled | C | u8 | bool | — | 0..1 | `0=off 1=on` | — | FLAGS=0x03. All: 0 |
| 0x0007 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x0008 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x000C | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x000D | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x000E | (unknown) | P | f32 | — | — | — | — | — | FLAGS=0x01. All: NaN |
| 0x000F | (unknown) | P | f32 | — | — | — | — | — | FLAGS=0x01. All: NaN |
| 0x0010-0x001A | (unknown, 8 regs) | P | f32 | — | — | — | — | — | FLAGS=0x01. All: NaN. Large NaN block |
| 0x001B | (unknown) | P | u8 | — | — | — | — | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean |
| 0x001D | serial_number_prefix | P | string | text | — | — | — | — | FLAGS=0x01. First 6 chars of VRC720 serial number (redacted in public docs) |
| 0x001E | serial_number_suffix | P | string | text | — | — | — | — | FLAGS=0x01. Chars 7-12 of VRC720 serial number (redacted in public docs) |
| 0x0020 | (unknown) | C | f32 | — | — | — | — | — | FLAGS=0x03. All: 0.0 |
| 0x0021 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x0022-0x003E | time_program_temperature_setpoint | C | u8 | °C/2 | — | — | — | — | FLAGS=0x03. 29 u8 values: hourly temperature profile. Pattern: 25→45 day, 45→10 night, 10→45→25 evening. Values are degrees × 2 (e.g. 45 = 22.5°C, 10 = 5°C) |
| 0x003F | (unknown) | P | u8 | — | — | — | — | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean |
| 0x0040 | (unknown) | P | time | time | — | — | — | — | FLAGS=0x01. All: 00:00:00 |
| 0x0042-0x004A | (unknown, 9 regs) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 0. Config block |
| 0x004B | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x004D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 0 |

The GG=0x0A names that changed under the register naming rules keep their
earlier names here:

| RR | Name | `previous_name` |
| --- | --- | --- |
| `0x001D` | `serial_number_prefix` | `vrc720_serial_part1` |
| `0x001E` | `serial_number_suffix` | `vrc720_serial_part2` |
| `0x0022-0x003E` | `time_program_temperature_setpoint` | `temperature_schedule` |

---


## OP=0x06 — Controller-Mediated Device Parameters

The following common register names apply to **every GG** under OP06,
independently of any local OP02 group with the same number:

| RR | Universal OP06 name |
| --- | --- |
| 0x0001 | device_connected |
| 0x0002 | device_class_address |
| 0x0003 | device_error_code |
| 0x0004 | device_firmware_version |

This is a naming rule. It does not establish register presence, a universal
value layout, slot identity or new discovery coverage. Group-specific raw
observations, codecs and qualification remain independent of the name.

The OP06 names below that changed under the register naming rules keep their
earlier names here:

| Selector | Name | `previous_name` |
| --- | --- | --- |
| `GG=0x01, RR=0x0012` | `heat_generator_error` | `heatgen_error` |
| `GG=0x01, RR=0x0015` | `heat_generator_status` | `heatgen_status` |
| `GG=0x09/0x0A, RR=0x0007` | `room_humidity` | `current_room_air_humidity` |
| `GG=0x09/0x0A, RR=0x000E` | `room_temperature_offset` | `room_temp_offset` |
| `GG=0x09/0x0A, RR=0x000F` | `room_temperature` | `current_room_temperature` |
| `GG=0x09/0x0A, RR=0x001E` | `device_pairing_active` | `device_paired` |
| `GG=0x09/0x0A, RR=0x001F` | `reception_level` | `reception_strength` |
| `GG=0x09/0x0A, RR=0x0030` | `time_program_day_period_count_maximum` | `max_time_periods_per_day` |


### GG=0x01 — Primary Heat Sources

All registers in this section use opcode `0x06`. `II` selects the heat-generator
slot, so the meaningful selector is `(0x06, 0x01, II, RR)`, not `GG=0x01`
alone. Slot availability/probing is a precondition for interpreting this
selector set: empty or unresolved slots must not be decoded as live primary
heat-source data.

The primary heat-source route is a family-qualified hypothesis. The selector
set is `(0x06, 0x01, II, RR)`; no published correlated reply qualifies a slot
matrix, availability predicate, or returned value layout. `GG=0x00` remains
uncharacterized rather than absent.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0012 | heat_generator_error | S | unknown | unknown | — | — | unknown | unknown | **Hypothesis.** Provisional name. The native reply layout, any Boolean convention, and error detail semantics are unqualified. Do not infer an enum or bitmask. |
| 0x0015 | heat_generator_status | S | unknown | unknown | — | — | unknown | unknown | **Hypothesis.** Provisional name; the reply layout and value class are not established. It is not a proven scalar flow-temperature mirror. |

---

### GG=0x02 — Secondary Heat Sources

All registers in this selector set use opcode `0x06`, with `II` selecting the
secondary heat-source slot. This selector set is documented separately from local DHW
(`OP=0x02, GG=0x01`). It is documented as an instanced controller-side
path for secondary sources such as solar-facing contributors.

Current canon status:

- selector-set identity is a family-qualified hypothesis
- populated slots and other models' limits are unqualified
- detailed register canon remains pending live validation
- no additional raw enum/bitmask semantics are inferred here

---

### GG=0x08 — Modul Solar (VMS) auroSTEP

Current profile slot interval: II01..II08. Historical II00..0A reads are
retained observations and do not expand this profile bound or prove presence.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | device_connected | S | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Status byte |
| 0x0002 | device_class_address | S | u8 | — | — | — | — | — | FLAGS=0x00. Scan value: 0 |
| 0x0003 | device_error_code | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN on all instances |
| 0x0004 | device_firmware_version | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN on all instances |

---

<a id="gg0x09--radio-sensors-vrc7xx-multi-instance-dual-opcode"></a>
### GG=0x09 — Remote Control Regulators (VRC7xx, VRT38x)

`OP=0x06, GG=0x09` is remote device data and is distinct from OP02/GG09 local configuration.



Characterized profile slot interval: II01..II08. Historical II00..0A reads
are separate observations; they do not establish a terminal instance bound. **Active
devices are identified by non-default values.** Empty slots have all
NaN/0xFF/0x8000.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | FLAGS=0x01. II=1: 1 (VRC720 paired) |
| 0x0002 | device_class_address | P | u8 | enum | — | — | `0x15=VRC720 0x35=VR92 0x26=VR71` | — | FLAGS=0x01. Canonical Vaillant eBUS address for device family |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | FLAGS=0x01. II=1: 0 (OK). Empty: 0xFF. 0=no error |
| 0x0004 | device_firmware_version | P | time | version | — | — | — | — | FLAGS=0x01. 3 bytes: major.minor.patch (byte-decimal, NOT BCD). II=1: 08.05.00 → VRC720 sw 08.05 |
| 0x0005 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0006 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0007 | room_humidity | S | f32 | % | — | — | — | — | FLAGS=0x01. II=1: 40.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". NaN if no sensor |
| 0x0008 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x0009 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000A | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. Empty: 0xFF, II=1: 0 |
| 0x000C | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x000E | room_temperature_offset | C | f32 | °C | — | — | — | — | FLAGS=0x03 (user RW). II=1: 0.0. Calibration offset for measured temperature |
| 0x000F | room_temperature | S | f32 | °C | — | — | — | — | FLAGS=0x01. II=1: 12.5°C. VR92f/3 manual: "Current room temperature in the zone". NaN if no sensor |
| 0x0010 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x0011 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | FLAGS=0x01. Empty: 0xFF, II=1: 0 (OK) |
| 0x0013 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00 |
| 0x0014 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x0015 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00 |
| 0x0016 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00 |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. Empty: 0xFF, II=1: 0 |
| 0x0019 | remote_control_address | S | u8 | count | — | — | — | — | FLAGS=0x01. VR92f/3 manual: "each remote control has a unique address starting at 1". VRC720=0 (initiator), VR92=1. Installer-settable per zone assignment |
| 0x001B | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x001E | device_pairing_active | P | u8 | bool | — | — | `0=no 1=yes` | — | FLAGS=0x01. II=1: 1. Confirms active pairing. Empty: 0xFF. Provisional name: whether 1 denotes an established pairing or a pairing in progress is not established |
| 0x001F | reception_level | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 7 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | P | u16 | raw | — | — | — | — | FLAGS=0x01. II=1: 0x1504. Byte 0 = device_class_address on VRC720 (0x15) |
| 0x0025 | zone_assignment | P | u8 | count | — | — | — | — | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x002F | (unknown) | P | u8 | — | — | — | — | — | FLAGS=0x01. All: 5 |
| 0x0030 | time_program_day_period_count_maximum | P | u8 | count | — | — | — | — | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |

---

<a id="gg0x0a--radio-sensors-vr92-multi-instance-dual-opcode"></a>
### GG=0x0A — Remote Control Thermostats (VR9x)

`OP=0x06, GG=0x0A` is remote device data and is distinct from the OP02/GG0A local selector set.



Characterized profile slot interval: II01..II08. Historical II00..0A reads
are separate observations; they do not establish a terminal instance bound. **Active VR92
devices are identified by non-default values.** Empty slots have NaN/0xFF.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | FLAGS=0x01. II=1: 1 (VR92f paired) |
| 0x0002 | device_class_address | S | u8 | enum | — | — | `0x15=VRC720 0x35=VR92 0x26=VR71` | — | FLAGS=0x01. Canonical Vaillant eBUS address for device family. II=1: 0x35 (53) |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 (OK) |
| 0x0004 | device_firmware_version | S | time | version | — | — | — | — | FLAGS=0x01. 3 bytes: major.minor.patch (byte-decimal, NOT BCD). II=1: 02.17.00 → VR92f sw 02.17 |
| 0x0006 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x01. II=1: 0.0, empty: NaN |
| 0x0007 | room_humidity | S | f32 | % | RoomHumidity | — | — | — | FLAGS=0x01. II=1: 39.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". ebusd confirmed. NaN if no sensor |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. II=empty: 0xFF, II=1: 0 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x000E | room_temperature_offset | C | f32 | °C | — | — | — | — | FLAGS=0x03 (user RW). II=1: 0.0, empty: NaN. Calibration offset for measured temperature |
| 0x000F | room_temperature | S | f32 | °C | RoomTemp | — | — | — | FLAGS=0x01. II=1: 13.625°C. VR92f/3 manual: "Current room temperature in the zone". ebusd confirmed. NaN if no sensor |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 (OK) |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0019 | remote_control_address | S | u8 | count | — | — | — | — | FLAGS=0x01. VR92f/3 manual: "each remote control has a unique address starting at 1". II=1: 1. Installer-settable per zone assignment |
| 0x001B | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00. All: NaN |
| 0x001E | device_pairing_active | S | u8 | bool | — | — | `0=no 1=yes` | — | FLAGS=0x01. II=1: 1. Empty: 0xFF. Provisional name: whether 1 denotes an established pairing or a pairing in progress is not established |
| 0x001F | reception_level | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 10 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | S | u16 | raw | — | — | — | — | FLAGS=0x01. II=1: 0x8201. Byte 0 = 0x82 (purpose unclear, does NOT match device_class_address 0x35) |
| 0x0025 | zone_assignment | S | u8 | count | — | — | — | — | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x0028-0x002E | (unknown, 7 regs) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0. User RW config block |
| 0x002F | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. All: 5 |
| 0x0030 | time_program_day_period_count_maximum | S | u8 | count | — | — | — | — | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |
| 0x0032 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0033 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean |
| 0x0035 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x02. All: 0 |

**Device slot observations:** The characterized OP06 profile uses II01..II08.
The [availability observations](ebus-vaillant-b524-profile-discovery-and-descriptions.md#availability-observations)
separate correlated concrete-II Boolean results from generic class descriptions
and unknown replies. This interval is family-specific, not a bound on the
one-byte instance field.

`device_connected=false` does not establish physical absence and must not suppress
retained inventory evidence. Identity and telemetry reads can include:
- `device_class_address` (0x0002) — resolve to a controller-ecosystem family hint; in a VRC720 observation, `0x26` correlates with the eBUS-identified `VR_71`
- `device_firmware_version` (0x0004) — byte-decimal triplet
- `reception_level` (0x001F) — 0-10 scale (4=acceptable, <4=unstable)
- `remote_control_address` (0x0019) — unique per remote (1..N), 0 for initiator
- `room_humidity` (0x0007) — f32 %, NaN if no sensor
- `room_temperature` (0x000F) — f32 °C, NaN if no sensor

**ebusd baseline:** The ebusd community definitions include only RR=0x0007 (RoomHumidity, EXP decode) and RR=0x000F (RoomTemp, EXP decode) for VR92 addresses 1-8, routed via `B524,06000a..`.

**ebusd decode note:** B524 remote responses carry a 4-byte header before the register value. When defining ebusd message templates, skip 4 bytes then decode the payload (e.g., for humidity: `B524,060009010700` → skip 4B → IEEE-754 LE float).

---

<a id="gg0x0c--remote-accessories-vr71fm5-multi-instance-remote-only"></a>
### GG=0x0C — Functional Modules (VR71) FM5

> **Verified 2026-03-05:** Responds only to opcode 0x06 (no local config selector set documented; opcode 0x02 returns 0 valid registers). 15 registers per instance, 165 total valid. Uses the same remote-device slot schema as GG=0x09/0x0A.
>
> In the current lab, the slot at **II=0x01** has `device_class_address=0x26` and firmware 01.00.00. This correlates with the eBUS-identified `VR_71` hardware at target address `0x26`. The family/product identification comes from eBUS identity, not from B524 alone.

#### Functional Modules (VR71) FM5 Data

Current profile slot interval: II01..II08. Uses the shared remote-device slot
schema. In the current lab, **II=0x01 has `device_class_address=0x26`**,
matching the eBUS-identified hardware at target address `0x26`, while
historical observations contain both `device_connected=0` and `1`.
Connection state and retained identity are distinct; neither observation is a
universal empty-slot or physical-liveness rule.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=not_connected 1=connected` | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean; false does not erase retained identity |
| 0x0002 | device_class_address | S | u8 | enum | — | — | `0x26` in current lab | — | FLAGS=0x00. II=1: 0x26 (38). In the current lab, this matches the eBUS-identified `VR_71` hardware at target address `0x26`; treat as correlation, not standalone B524 proof. |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | FLAGS=0x00. All empty: 0xFF |
| 0x0004 | device_firmware_version | S | time | version | — | — | — | — | FLAGS=0x00. II=1: 01.00.00 (byte-decimal). Empty: FF/FF/FF |
| 0x000A | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x02. All: 0 |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | FLAGS=0x00. All empty: 0xFF |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. All empty: 0xFF, II=1: 1 when type code present |
| 0x0028-0x002E | (unknown, 7 regs) | C | u8 | — | — | — | — | — | FLAGS=0x02. All: 0 |
| 0x002F | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. All: 5 |

**Current-lab VR_71 correlation:** B524 yields `device_class_address=0x26` at `II=0x01`. The conclusion that this slot corresponds to `VR_71` comes from correlating that hint with eBUS identity data, where target address `0x26` identifies itself as `VR_71`. Vaillant controller documentation then constrains the profile interpretation by describing `FM5` as "instead of VR 71". This is useful and strong for the current lab/profile, but it is not standalone protocol proof that `GG=0x0C` universally means `VR71/FM5`.


---

## Constraint Catalog

> Historical range hints from incomplete OP01 probes; not qualified input-validation metadata. Keep the returned selector independent from the intended request.

Source: VRC720 hardware constraint probe (`0x01` opcode).

**Record columns:** `Observed record word` is the value exactly as the
historical short probes returned it (kept as raw evidence). `Register (RR)` is
the little-endian register number of the same group (`RRlo | RRhi<<8`, the
register order used on the wire everywhere else on this page). The observed
word is the byte-swap of the register (register `0x0004` appears as
`0x0400`); earlier revisions of this page showed the swapped word in a single
`Record` column and read it as the register, which named a different register.
That reading was an error in this page, not a wire difference. Every register
in the second column is checked mechanically to be a register of the same group
in the OP=0x02 catalog above, and every observed word to be its byte-swap.

The historic short probes produced range-shaped samples, but the incomplete
selector and length/codec ambiguity prevent them from authoritatively mapping a
record to a register or from validating a value. Retain the rows as historical
hints only; a complete OP01/OP07 response with a qualified scalar codec is
required for validation.

| Group | Observed record word | Register (RR) | Type | Min | Max | Step |
|-------|----------------------|---------------|------|-----|-----|------|
| 0x00 | 0x0100 | 0x0001 | f32 | -20 | 50 (profile-scoped) | 1 |
| 0x00 | 0x0200 | 0x0002 | f32 | -26 | 10 | 1 |
| 0x00 | 0x0300 | 0x0003 | u16 | 0 | 12 | 1 |
| 0x00 | 0x0400 | 0x0004 | u16 | 0 | 300 | 10 |
| 0x00 | 0x8000 | 0x0080 | f32 | -10 | 10 | 1 |
| 0x01 | 0x0100 | 0x0001 | u16 | 0 | 1 | 1 |
| 0x01 | 0x0200 | 0x0002 | u8 | 0 | 1 | 1 |
| 0x01 | 0x0300 | 0x0003 | u16 | 0 | 2 | 1 |
| 0x01 | 0x0400 | 0x0004 | f32 | 35 | 70 | 1 |
| 0x01 | 0x0500 | 0x0005 | f32 | 0 | 99 | 1 |
| 0x01 | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |
| 0x02 | 0x0100 | 0x0001 | u16 | 1 | 2 | 1 |
| 0x02 | 0x0200 | 0x0002 | u16 | 0 | 4 | 1 |
| 0x02 | 0x0400 | 0x0004 | f32 | 15 | 80 | 1 |
| 0x02 | 0x0500 | 0x0005 | u8 | 0 | 1 | 1 |
| 0x02 | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |
| 0x03 | 0x0100 | 0x0001 | u16 | 0 | 2 | 1 |
| 0x03 | 0x0200 | 0x0002 | f32 | 15 | 30 | 0.5 |
| 0x03 | 0x0500 | 0x0005 | f32 | 5 | 30 | 1 |
| 0x03 | 0x0600 | 0x0006 | u16 | 0 | 2 | 1 |
| 0x04 | 0x0100 | 0x0001 | u8 | 0 | 1 | 1 |
| 0x04 | 0x0200 | 0x0002 | u8 | 0 | 1 | 1 |
| 0x04 | 0x0300 | 0x0003 | f32 | -40 | 155 | 1 |
| 0x04 | 0x0400 | 0x0004 | f32 | 0 | 99 | 1 |
| 0x04 | 0x0500 | 0x0005 | f32 | 110 | 150 | 1 |
| 0x04 | 0x0600 | 0x0006 | f32 | 75 | 115 | 1 |
| 0x05 | 0x0100 | 0x0001 | f32 | 0 | 99 | 1 |
| 0x05 | 0x0200 | 0x0002 | f32 | 2 | 25 | 1 |
| 0x05 | 0x0300 | 0x0003 | f32 | 1 | 20 | 1 |
| 0x05 | 0x0400 | 0x0004 | f32 | -10 | 110 | 1 |
| 0x08 | 0x0100 | 0x0001 | f32 | 0 | 99 | 1 |
| 0x08 | 0x0200 | 0x0002 | f32 | 0 | 99 | 1 |
| 0x08 | 0x0300 | 0x0003 | f32 | 2 | 25 | 1 |
| 0x08 | 0x0400 | 0x0004 | f32 | 1 | 20 | 1 |
| 0x08 | 0x0500 | 0x0005 | f32 | -10 | 110 | 1 |
| 0x08 | 0x0600 | 0x0006 | f32 | -10 | 110 | 1 |
| 0x09 | 0x0100 | 0x0001 | u16 | 0 | 255 | 1 |
| 0x09 | 0x0200 | 0x0002 | u16 | 1 | 3 | 1 |
| 0x09 | 0x0300 | 0x0003 | u8 | 0 | 1 | 1 |
| 0x09 | 0x0400 | 0x0004 | u16 | 0 | 10 | 1 |
| 0x09 | 0x0500 | 0x0005 | u16 | 0 | 32768 | 1 |
| 0x09 | 0x0600 | 0x0006 | u16 | 0 | 32768 | 1 |
| 0x0A | 0x0100 | 0x0001 | u8 | 0 | 3 | 1 |
| 0x0A | 0x0200 | 0x0002 | u8 | 1 | 2 | 1 |
| 0x0A | 0x0300 | 0x0003 | u8 | 1 | 2 | 1 |
| 0x0A | 0x0500 | 0x0005 | u8 | 0 | 3 | 1 |
| 0x0A | 0x0600 | 0x0006 | u8 | 0 | 1 | 1 |

**Notes:**
- Earlier revisions read the observed record words (for example `0x0100`..`0x0600`) as TSP-style registers `0x0100+`; that reading is withdrawn. TSP registers (`0x0100+`) remain outside standard B524 register reads (only `0x0001-0x00FF` work through them).
- **DHW bivalence row (GG=0x00, RR=0x0001), scoped per controller profile.** The `-20..50 step 1` range is a historical observation attributed to the BASV2 controller profile. It is a **Hypothesis** supported by corroborating implementation evidence: no description record is retained, and the API version and revision were not recorded, so the bound is unqualified. The BASV0 profile observes `-20..20 step 1` with access flags `03` for the same selector `(OP=0x02, GG=0x00, II=0x00, RR=0x0001)`, from a retained selector-qualified description record whose bytes are **Proven** and whose EXP decoding to this range is a **Hypothesis** (codec basis; see [issue #563](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/563) and the BASV0 profile page published by [#564](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/564)). Neither value is evidence for another software revision, hardware revision or installation configuration (**Unknown**). Consumers resolve bounds per controller profile (see the application contract), never from this unscoped table. The maximum shown in the table is the value of one profile only (the BASV2 observation above).
- GG=0x00 observed record word 0x8000 → RR=0x0080 is now confirmed responsive (FLAGS=0x03, f32=0.0, constraint: -10..10 step 1). Adjacent to `smart_photovoltaic_buffer_offset` (0x0081). Possibly PV-related offset config.

---

## Enum Reference

Enum definitions used by B524 registers. Where common usage differs from ebusd naming, both mappings are shown.

### opmode — Operation mode

Used by: GG=0x03 RR=0x0001, GG=0x03 RR=0x0006, GG=0x01 RR=0x0003

| Value | ebusd | Zones usage | DHW usage |
|-------|-------|-------------|-----------|
| 0 | off | off | off |
| 1 | auto | auto | auto |
| 2 | day | manual | heat |
| 3 | night | night | night |

Note: ebusd defines this as `UIN` with 4 values. Only 0-2 are commonly observed on VRC720. Value 3 is not observed in practice.

### sfmode — Special function

Used by: GG=0x03 RR=0x000E, GG=0x01 RR=0x000D

| Value | ebusd | Zones usage | DHW usage |
|-------|-------|-------------|-----------|
| 0 | auto | (none — normal operation) | (none — normal operation) |
| 1 | ventilation | ventilation | — |
| 2 | party | quickveto | — |
| 3 | veto | away | — |
| 4 | onedayaway | away | — |
| 5 | onedayathome | home | — |
| 6 | load | — | load |

Note: Values 3+4 are commonly collapsed into a single "away" preset. ebusd also defines `sfmodezone` (0=auto, 1=ventilation, 3=veto) and `sfmodehwc` (0=auto, 6=load) as restricted subsets.

Candidate, unconfirmed on the wire: the values written to `GG=0x01, RR=0x000D` are 0 and 6. On `GG=0x03, RR=0x000E` the values written are 03 (VRC700-family quick veto set), 00 (quick veto cancel and switching back to time control) and 01 (zone ventilation boost). The label of value 3 in the quick-veto set differs from the "Zones usage" column above; the difference is unresolved.

### mctype — Circuit type

Used by: GG=0x02 RR=0x0002

| Value | ebusd | Common name | Vaillant manual name | Description |
|-------|-------|-------------|---------------------|-------------|
| 0 | inactive | inactive | Inactive | Circuit unused |
| 1 | mixer | heating | Heating | Weather-compensated heating. Mixing or direct depending on basic system diagram. |
| 2 | fixed | fixed_value | Fixed value | Circuit held at a fixed target flow temperature. Applications: swimming pool heating, door air curtain heating. |
| 3 | hwc | dhw | DHW | Heating circuit used as DHW circuit for an additional cylinder. II09 remains a virtual native-water candidate; current public evidence provides no temperature-based predicate to infer this role when RR0002 is inactive. |
| 4 | returnincr | return_increase | Increase in return | Return temperature raise circuit. Target return temperature at RR=0x0004 (factory setting 30°C). |
| 5 | pool | pool | Pool | Observed Vaillant behavior on the VRC700 family only; hardware confirmation pending. Not within the VRC720-family constraint range (0..4) — see below. |

**Naming note:** ebusd templates label value 1 as "mixer" — this is a community naming convention; the Vaillant VRC720 operating & installation manual calls it "Heating" (Heizen). The mixing valve is an implementation detail of the hydraulic system, not the circuit type itself.

**Pool is a derived application, not a raw enum value.** The Vaillant manual describes "fixed value control" as suitable for "swimming pool heating" — so pool heating is an _application_ of `fixed_value` (mctype=2) when the system topology includes swimming pool hydraulics (sensor, circulation pump). It is NOT a separate enum value on VRC720-family controllers. Constraint catalog confirms range 0..4.

**ebusd extended enums:** ebusd `mctype` defines 0-5 (adding `pool=5`), and `mctype7` defines 0-6 (adding `circulation=6`; see ebusd-config issue #182 and PR #174). Value 5 is observed Vaillant behavior on the VRC700 family (hardware confirmation pending); value 6 remains unconfirmed on any family. Neither is within the VRC720-family constraint range (0..4).

**Label set (candidate).** Three label sets exist for this register: the catalog
labels of the table above (`inactive`, `heating`, `fixed_value`, `dhw`,
`return_increase`, `pool`), the candidate set below, and the candidate labels of
the [register matrix](#enumerations-that-differ-by-family) (`Deactivated`,
`HeatingCircuit`, `FixValueCircuit`, `DHWCircuit`, `BackFlowCircuit`, and
`PoolCircuit` for 5 on the VRC700 family); they differ. In the
candidate set, on the VRC720 family the labels are `OFF` for 0,
`HEATING` for 1, `FIX_VALUE` for 2, `DHW` for 3 and `BACK_FLOW` for 4; there is
no label for 5. Whether the VRC700-family value 5 (`pool`) occurs in replies of
this register is not established. The same register is read for
circuit indexes 0..8 (range used by a requester). This is a candidate interpretation, unconfirmed on the
wire.

**Zone capabilities** depend on (a) circuit type supporting heating, and (b) `cooling_enabled` flag (RR=0x0006) for cooling capability. Cooling is a separate function/mode, not derived from circuit type.

Sources: VRC720 operating & installation instructions (circuit type table, fixed value control description, abbreviations list for swimming pool); ebusd `_templates.tsp` mctype/mctype7 definitions; ebusd-config issue #182, PR #174 (translations: Heizen/Festwert/WW/Rückl.anh.).

### Circuit State Enum

Used by: GG=0x02 RR=0x001E (`circuit_state`, ebusd `Hc{hc}PumpStatus`)

**Hypothesis.** Assigning this enumeration to RR=0x001E rests on observed
Vaillant naming only: RR=0x001E's observed Vaillant friendly name is
"Status circuit" and its myVaillant name is `circuitState`, while RR=0x001B's
observed Vaillant friendly name is "Status Pump". No live observation has
been made against RR=0x001E itself; hardware confirmation is pending.

| Value | Common name | myPyllant | Evidence |
|-------|-------------|-----------|----------|
| 0 | standby | STANDBY | See the RR=0x001B observation below — it does not discriminate between RR=0x001B and RR=0x001E. |
| 1 | heating | HEATING | Inferred from the `CircuitState` enum correlation; physical corroboration remains required. |
| 2 | cooling | COOLING | Inferred from the `CircuitState` enum correlation; physical corroboration remains required. |
| 3 | dhw | — | Hypothesis: register-map correction (see RR001E above); physical corroboration remains required. |
| N | unknown_N | — | Safety fallback for unmapped values |

**The 2026-03-08 live observation was made on RR=0x001B, not RR=0x001E:**
three circuits simultaneously read value `0` on RR=0x001B, idle, pumps off,
flow setpoint=0. That observation supports "value 0 means idle/standby" on
whichever of RR=0x001B or RR=0x001E actually carries the circuit state
enumeration — it is equally consistent with RR=0x001B being a raw pump
status (pump off) and RR=0x001E carrying the state enum, or with RR=0x001B
itself carrying the enum. It does not discriminate between the two
readings. The naming evidence above (not this observation) is what is
being used to assign the enumeration to RR=0x001E.

**ebusd type:** Plain `UCH` — no enum type annotation in ebusd `Hc1PumpStatus` model (`15.700.tsp`).

**myPyllant:** `CircuitState` enum in `myPyllant/enums.py` defines `HEATING`, `COOLING`, `STANDBY` as string values; the fixture's own `myvaillant_name_vrc700` column names RR=0x001E `circuitState`. The cloud API performs the numeric-to-string conversion server-side. Test fixtures contain only HEATING and STANDBY observations, and do not themselves identify which register the cloud API reads.

**GG=0x02 RR=0x001B (`circuit_pump_unknown_8`, register selector `OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001B`)** is, per observed Vaillant naming ("Status Pump"), a raw pump-status register. It was earlier documented here as carrying the circuit state enumeration, on the strength of the single 2026-03-08 idle observation above plus a name correlation with myPyllant's `CircuitState`; that attribution has been moved to RR=0x001E as a Hypothesis, per the naming evidence above. The conflict between the two readings is not resolved by either the observation or the naming alone.

Sources: Live scan observation (2026-03-08, on RR=0x001B), myPyllant `enums.py` `CircuitState`, VRC720 register mapping.

### offmode — Auto-off behavior

Used by: GG=0x02 RR=0x000E

| Value | ebusd | Common name |
|-------|-------|-------------|
| 0 | eco | eco |
| 1 | night | night |

Note: Controls operation during lowering time. No influence if room temp modulation set to thermostat.

### rcmode — Room temperature control mode

Used by: GG=0x02 RR=0x0015

| Value | ebusd | Common name |
|-------|-------|-------------|
| 0 | off | off |
| 1 | modulating | modulating |
| 2 | thermostat | thermostat |

### onoff

Used by: GG=0x00 RR=0x000A (HwcParallelLoading), and various bool registers

| Value | ebusd | Boolean |
|-------|-------|---------|
| 0 | off | false |
| 1 | on | true |

Note: Commonly decoded as `bool`.

### yesno

Used by: GG=0x00 RR=0x0014 (AdaptHeatCurve), RR=0x0096 (MaintenanceDue)

| Value | ebusd | Boolean |
|-------|-------|---------|
| 0 | no | false |
| 1 | yes | true |

Note: Commonly decoded as `bool`.

### zmapping — Zone room temperature sensor mapping

Used by: GG=0x03 RR=0x0013 (`room_temperature_zone_mapping`)

| Numeric value | ebusd | Human alias only | Notes |
|-------------------------------|-------|------------------|-------|
| 0 | none | none | No room sensor assigned |
| 1 | VRC700 | regulator | Built-in sensor of the /f split regulator (wireless UI + base station). Same hardware class as VR91 with added UI capabilities |
| 2 | VR91_1 | thermostat_1 | External RF temperature/humidity sensor + UI endpoint |
| 3 | VR91_2 | thermostat_2 | Second VR91 sensor |
| 4 | VR91_3 | thermostat_3 | Third VR91 sensor |

Note: ebusd uses hardware model names (VRC700, VR91). User-facing labels such as `regulator` and `thermostat_*` are aliases for documentation/UI only. The authoritative value is the raw integer enum.

### mamode — Multi-relay setting

Used by: GG=0x00 RR=0x004D

| Value | ebusd | Common name |
|-------|-------|-------------|
| 0 | circulation | circulation |
| 1 | dryer | dryer |
| 2 | zone | zone |
| 3 | legiopump | legionella_pump |

---

## Mapping Conflicts

Three register mappings from the original myPyllant value-matching had errors, resolved using TSP:

| RR | myPyllant CSV leaf | TSP name | Resolution |
|----|-------------------|----------|------------|
| 0x0019 | heating_circuit_bivalence_point | SolarFlowRateQuantity | Coincidental 0.0 match (solar disabled). Real HcBivalencePoint at 0x0023. |
| 0x0026 | dhw_flow_setpoint_offset | HcEmergencyTemperature | 25.0 fits both semantics, TSP authoritative. |
| 0x0029 | max_flow_setpoint_hp_error | HwcStorageChargeOffset | 25.0 fits range, TSP authoritative. |

One resolved by ebusd verification:

| RR | CSV leaf | ebusd TSP | Resolution |
|----|----------|-----------|------------|
| 0x0015 | paralell_tank_loading_allowed | (not at this address) | CSV value-matching false positive. ebusd places HwcParallelLoading at 0x000A. 0x0015 purpose unknown. |

One pending:

| RR | myPyllant CSV leaf | TSP name | Status |
|----|-------------------|----------|--------|
| 0x0024 | hybrid_control_strategy (BIVALENCE_POINT) | BackupBoiler | Pending. TSP puts HybridManager at 0x000F (now named in GG=0x00 table). |

---

## Appendix: Semantic FSMs (Controller)

### `energy_manager_state` (OP=0x02, GG=0x00, RR=0x0048)

Register `OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0048` — system-level energy manager state. Wire type: `u16` enum.

| Value | State | myPyllant | Description |
|-------|-------|-----------|-------------|
| 0 | `standby` | `STANDBY` | No active demand; all circuits idle (live scan confirmed) |
| 1 | `heating` | `HEATING` | Heating demand active |
| 2 | `cooling` | `COOLING` | Cooling demand active (reversible HP only) |
| 3 | `dhw` | -- | DHW heating cycle (inferred from B524 architecture) |

**Transitions:** standby -> heating/dhw/cooling (demand). Active states -> standby (demand satisfied). heating <-> dhw (DHW priority override / DHW complete with pending heating demand).

**Related registers:** GG=0x02 RR=0x001E `circuit_state` (per-circuit sub-state aggregated here), GG=0x02 RR=0x001B `circuit_pump_unknown_8`, GG=0x00 RR=0x004B `flow_temperature`.

**Confidence:** MEDIUM for states 0-2 (live scan + myPyllant enum correlation); `dhw` remains a hypothesis pending correlated evidence.

### `circuit_state` (OP=0x02, GG=0x02, RR=0x001E)

Register `OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001E` — per-circuit state (`circuit_state`). Wire type: `u16` enum. **Hypothesis:** this enumeration's assignment to RR=0x001E rests on observed Vaillant naming (see [Circuit State Enum](#circuit-state-enum)), not on a live observation against RR=0x001E itself.

| Value | State | myPyllant | Description |
|-------|-------|-----------|-------------|
| 0 | `standby` | `STANDBY` | The 2026-03-08 live observation (3 circuits simultaneously idle, pumps off) was made on RR=0x001B, not RR=0x001E — see [Circuit State Enum](#circuit-state-enum). It is equally consistent with a pump status and does not discriminate between RR=0x001B and RR=0x001E. |
| 1 | `heating` | `HEATING` | Circuit active in heating mode |
| 2 | `cooling` | `COOLING` | Circuit active in cooling mode |
| 3 | `dhw` | — | Circuit active as a DHW circuit (Hypothesis: register-map correction; physical corroboration remains required) |

**Transitions:** standby -> heating (room temp below setpoint AND schedule slot active). heating -> standby (setpoint reached OR schedule inactive). standby -> cooling (room temp above cooling setpoint AND cooling enabled).

**Related registers:** GG=0x02 RR=0x001B (`circuit_pump_unknown_8`, register selector `OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001B`) is, per observed Vaillant naming, a distinct raw pump-status register; it was earlier documented as carrying this enumeration (see [Circuit State Enum](#circuit-state-enum) for why that attribution moved). GG=0x02 RR=0x001A is `mixer_movement`; GG=0x02 RR=0x0020 is an observed UCH one-byte raw status, not a calculated flow temperature.

**Confidence:** Hypothesis for 0/1/2 (naming-based assignment to RR=0x001E; the only live observation was made on RR=0x001B and does not discriminate between the two registers; myPyllant correlation for 1/2 remains uncorroborated); Hypothesis for 3 (DHW), pending physical corroboration.

### `special_function_mode` (OP=0x02, GG=0x00, RR=0x0016 + 0x0074)

<a id="asymmetric-readwrite-paths"></a>

#### Asymmetric read/write paths

- **Read ventilation operating mode:** `OP=0x02, OT=0x00, GG=0x00, II=<ventilation_index>, RR=0x0016`. The candidate VRC700 enum is listed in the [register entry](#gg0x00--system); the on-wire response remains unconfirmed.
- **Read mode value:** `OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0074` (u8 enum)
- **Write:** `OP=0x02, GG=0x09, RR=0x0001` (value) + `RR=0x0002` (active flag) -- asymmetric path

| Value (RR=0x0074) | State | Description |
|--------------------|-------|-------------|
| 0x00 | `dormant` | Historical interpretation: no quick mode active. The behaviour of VRC700 `OP=0x02, GG=0x00, II=<ventilation_index>, RR=0x0016` under that condition remains unresolved. |
| 0x01 | `ventilation` | Ventilation-only mode |
| 0x02 | `party` | Party mode -- enhanced heating |
| 0x03 | `away` | Away mode -- reduced heating |
| 0x04 | `one_day_at_home` | Single-day manual override |

**Transitions:** dormant -> any active (B524 write to GG=0x09). Active -> dormant (duration expires or explicit deactivation write).

**Related registers:** GG=0x09 RR=0x0001/0x0002 (write targets), GG=0x00 RR=0x0048 `energy_manager_state` (downstream effect: quick mode changes demand), B524 GG=0x03 zone schedules (quick mode overrides scheduled time programs).

**Confidence:** Hypothesis. The register addresses, asymmetric path, and exact enum labels require publishable correlated evidence.

---

## Register matrix by family

The [register matrix](fixtures/b524-op02-requester-register-matrix.csv) lists
candidate OP=0x02 selectors for VRC720-family and VRC700-family controllers, with
one fixture row per selector and family. All statements here are candidate interpretations, unconfirmed on the
wire. Every `name` is the catalog name of the same `(opcode, group, register)` key, and a name never qualifies a codec or an acceptance rule. The enumeration labels are Vaillant names.

- **Columns.** `candidate_reply_value_bytes` is the candidate value length of the
  reply; `candidate_value_type`, `candidate_unit` and
  `candidate_enumeration` are the candidate type, unit and enumeration for the
  family. `instance` is `00` (fixed) or
  `dynamic` (a zone or circuit number, or a ventilation index).
- **Groups and instances.** The matrix uses `GG=0x00`, `0x01`, `0x02`, `0x03` and,
  on the VRC720 family only, `GG=0x09`. The VRC700 family carries its ventilation
  items under `GG=0x00` with a dynamic instance (`RR=0x0016`, `0x0042`, `0x0043`,
  `0x00A4`). No selector of the matrix uses another group. Reads of `GG=0x00` and
  `GG=0x01` use `II=0x00`, except these VRC700-family ventilation reads under
  `GG=0x00`, which take the ventilation index; reads of `GG=0x02` and `GG=0x03` use a zone or circuit number (one byte; a requester uses the candidate range 0..8. For the VRC720 family the [discovery profiles](#discovery-profiles) give `II=0x00..0x09` for `GG=0x02`, a candidate bound with `II=0x09` a candidate virtual native-water instance, and `II=0x00..0x0A` for `GG=0x03`; for the VRC700 family they are not established); reads of `GG=0x09` use the ventilation index (0 only).
- **Floats and units.** Floats are float32 little-endian with an identity
  mapping. The `GG=0x00` floats are in °C, except kelvin for `RR=0x0027`,
  `RR=0x0029` and `RR=0x00A2` and bar for `RR=0x0039`. `RR=0x00EF`
  (continuous-heating room set point) is read on the VRC720 family only.
- **Widths.** The two zone special-function rows (`GG=0x03, RR=0x001B`) and the
  two rows of `GG=0x00, RR=0x000A` carry the unresolved width `1 or 2` and the
  type `uint8 or uint16 LE`: a one-byte and a two-byte candidate width,
  unresolved. For `RR=0x000A` the catalog gives `u16` while the write body is one
  byte. The same unresolved width and type are carried by the two rows of
  `GG=0x03, RR=0x0011` and by the VRC720-family rows of `GG=0x03, RR=0x0027` and
  `GG=0x03, RR=0x002C`; the catalog gives `u16` for all three, and the zone-enable
  write body for `RR=0x0011` is one byte.
- **Selectors outside the matrix, and paired zone reads.** The two OP=0x01 range
  requests (see the [protocol page](ebus-vaillant-B524.md#427-op01h-and-op07h-request-and-reply-layouts-candidate)),
  the VR70 module configuration (`OP=0x06, GG=0x0B, RR=0x0005`, II one-based) and
  the VRC700 radio-sensor humidity read (`OP=0x06, GG=0x09/0x0A, RR=0x0007`) have
  their own selectors and no matrix row. The zone name is read as two
  text-fragment registers `RR=0x0017` and `RR=0x0018` (no matrix row), and the zone mapping is the pair `RR=0x0013` and `RR=0x001C` (both in the matrix).

### Enumerations that differ by family

| Register | VRC720 family | VRC700 family |
| --- | --- | --- |
| `GG=0x01, RR=0x0003`, `GG=0x03, RR=0x0001`, `GG=0x03, RR=0x0006` (operation modes) | 0 Off, 1 TimeControlled, 2 Manual | 0 Off, 1 Auto, 2 Day; heating mode also 3 Setback |
| `GG=0x02, RR=0x0002` (circuit type) | 0 Deactivated, 1 HeatingCircuit, 2 FixValueCircuit, 3 DHWCircuit, 4 BackFlowCircuit | as the VRC720 family plus 5 PoolCircuit |
| `GG=0x03, RR=0x0013` (zone binding) | 0 Non, 1 CentralControl, 2..5 RemoteControl1..4 | 0 Non, 1 CentralControl, 2..9 RemoteControl1..8 |
| `GG=0x03, RR=0x001C` (circuit for zone, int8) | 0..8 Control_CC1..CC9, -1 notBound | 0..2 Control_CC1..CC3, -1 notBound |
| `GG=0x03, RR=0x001B` (zone special function) | 0 NoSpecialFunctionActive, 1 VentilationBoost, 4 QuickVeto, 7 Holiday, 10 SystemOff | 0 NoQuickMode, 1 VentilationBoost, 3 Party, 4 QuickVeto, 5 OneDayHoliday, 6 OneDayBankHoliday, 7 Holiday, 8 BankHoliday, 10 SystemOff |
| Ventilation mode | `GG=0x09, RR=0x0002`: 1 TimeControlled, 2 Normal, 3 Reduced | `GG=0x00, RR=0x0016`: 1 Auto, 2 Day, 3 Setback |
| Ventilation special function | `GG=0x09, RR=0x0004`: 0 NoSpecialFunctionActive, 1 VentilationBoost, 7 Holiday, 10 SystemOff (candidate labels) | `GG=0x00, RR=0x00A4`: 0 No special function active, 1 Ventilation boost, 3 Party, 5 One day holiday, 6 One day bank holiday, 7 Holiday, 8 BankHoliday, 10 SystemOff (candidate labels) |

A code with no candidate label is not shown to be invalid on the wire (for example
2 and 9 of the zone special function).

### Candidate write encodings

Candidate, unconfirmed on the wire: the registers below are written; the bodies are in the
[write templates](fixtures/b524-op02-write-templates.csv) and the multi-step
sequences in the [write sequences](fixtures/b524-op02-write-sequences.csv).
No ACK, response correlation or persistence is established for any of them, and
none is documented as safe to send (see the
[protocol page, section 4.3.2](ebus-vaillant-B524.md#432-write-encodings-candidate)).

The templates' `write_role` field classifies only the `write` label as a
canonical register name (`canonical`) or a descriptive phrase (`prose`), as
defined in that section; neither value qualifies native write behavior.

| Selector | Catalog name | Write |
| --- | --- | --- |
| `GG=0x00`, `RR=0x0001`, `0x0023`, `0x0026`, `0x0046` | `dhw_outdoor_bivalence_temperature_limit`, `heating_outdoor_bivalence_temperature_limit`, `heating_flow_temperature_setpoint_maximum_at_heat_pump_fault`, `dhw_flow_temperature_setpoint_maximum` | float32 little-endian |
| `GG=0x00`, `RR=0x0007`, `0x0009`, `0x000A`, `0x0014` | `unknown_11`, `automatic_cooling_enabled`, `cylinder_parallel_loading_enabled`, `adaptive_heating_curve_enabled` | one byte (system off: 01 set, 00 cancel; the others 00 or 01); the width of `RR=0x000A` is unresolved (one or two bytes) |
| `GG=0x00`, `RR=0x0036`, `0x002F` | `hydraulic_scheme_code`, `functional_module_configuration_code` | uint16 little-endian |
| `GG=0x00`, `RR=0x00F9` (VRC720 family), `RR=0x0074` (VRC700 family) | `ventilation_boost_active`, `special_function_mode` | one byte 01 or 00 (ventilation boost) |
| `GG=0x03`, `RR=0x0011` | `zone_enabled` | one byte 00 or 01 |
| `GG=0x02`, `RR=0x000E`, `RR=0x0002`, `RR=0x000F` (VRC720 family) | `circuit_frost_protection_mode`, `circuit_type`, `circuit_heating_curve_factor` | 00 or 01 followed by 00; enumeration low byte followed by 00; float32 |
| `GG=0x09`, `RR=0x0001` | `ventilation_special_function_mode` | bytes `01 00` |
| `GG=0x00`, `II=0xFF`, `RR=0x0103` | none in the catalog | bytes `01 00` (commissioning complete); the register is above the range documented here |

The label of value 3 in the quick-veto set and the position of `RR=0x0103`
relative to the documented register range are open (see the open questions
below).

## Open questions — family-specific register interpretation

- The VRC700 ventilation mode `OP=0x02, GG=0x00, II=<ventilation_index>, RR=0x0016` and its accepted setting
  values remain unconfirmed on the wire; its behaviour
  when no quick mode is engaged and the proposed asymmetric write selector
  remain unresolved.
- The raw circuit-type meaning of `OP=0x02, GG=0x01, II=0x00, RR=0x0001` is not
  confirmed on the wire. The same selector is used for
  an availability test; this does not make availability and circuit type
  interchangeable.
- Which of the two Vaillant names `circuit_type` and
  `circuit_type_of_mixed_circuit_external` describes the value of
  `OP=0x02, GG=0x02, RR=0x0002` is unresolved.
- The physical meaning of the signed value `-1` at
  `OP=0x02, GG=0x03, II=<zone>, RR=0x001C` remains unestablished;
  `notBound` remains a candidate interpretation.

- The supported instance domain for the VRC700 ventilation reads
  `OP=0x02, GG=0x00, II=<ventilation_index>, RR=0x0016/0x0042/0x0043/0x00A4`
  is not established. A variable instance field does not establish support for
  nonzero indices or multiple ventilation units.
- The write selector of the VRC700 ventilation mode is not established. A
  ventilation boost is written to `GG=0x00, RR=0x0074` (VRC700 family),
  `GG=0x00, RR=0x00F9` (VRC720 family) and `GG=0x09, RR=0x0001`; the relation of
  these writes to the proposed GG09 quick-mode write path is unresolved.
- The roles of `RR=0x00F3` and `RR=0x00F4` in the VRC720-family system holiday
  and away sequences (start time and end date in the set sequence; date-shaped and time-shaped cancel bodies) disagree with the rows of this
  catalog and are unresolved.
- The label of value 3 written to `GG=0x03, RR=0x000E` in the VRC700-family quick
  veto set differs from the "Zones usage" column of the `sfmode` table and is
  unresolved.
- The units of the system holiday set point (`RR=0x0082`, `RR=0x00F6`; this
  catalog lists °C for `RR=0x00F6`), of the zone holiday set point (`RR=0x0005`,
  candidate °C), of the cooling-for-days count
  (`RR=0x0006`; this catalog lists days) and of the quick-veto set point and
  duration (`GG=0x03, RR=0x0008` and `RR=0x0026`; this catalog lists °C and hrs)
  are not established.
- The year-byte codec of date triples (offset from 2000 in the triples; BCD in the
  scalar observations of this catalog) is unresolved per
  register and family. The year-byte values of the cancel triples `01 01 0F` and
  `01 01 13` are read under the same unresolved codec.
- Candidate, unconfirmed on the wire: `GG=0x00, RR=0x0103` (commissioning state and commissioning complete) is read and written; it lies above the register range documented in this catalog and has no catalog name. Whether that register is readable like the registers above it is not established.
- The enumeration values of the VR70 module configuration, the system scheme and
  the VR71 configuration are unknown, and the raw values of the DHW type
  (`GG=0x01, RR=0x0001`) have no established meaning.
- The reaction of the controller to the `II=FF` writes of B524 section 4.11
  (`GG=0x01, RR=0x0004`, `GG=0x00, RR=0x0027`, `0x00A2` and `0x00B6`, and
  `GG=0x01, RR=0x000D`), and the meaning and unit of the written values, are not
  established.
- The value width of `GG=0x03, RR=0x001B` (one or two bytes) is unresolved.
- The value width of `GG=0x00, RR=0x000A` (one or two bytes) is unresolved.
- The value widths of `GG=0x03, RR=0x0011` (both families), `GG=0x03, RR=0x0027`
  and `GG=0x03, RR=0x002C` (VRC720 family) are unresolved (one or two bytes);
  this catalog lists `u16` for all three, and the zone-enable write body for
  `RR=0x0011` is one byte.
- The family scope of `GG=0x00, RR=0x00DA` and `RR=0x00DB` is unresolved: the
  catalog rows give a VRC700-family manual cooling date interpretation as a
  **Hypothesis**, while the candidate read and write (calendar selector table,
  write templates, protocol section 4.8) are scoped to the VRC720 family; both
  scopes are candidates.

## Sources

- **Historical VRC720 short-probe catalog** — Range-shaped samples from incomplete
  `0x01` requests. It is unqualified historical evidence only: it does not
  authoritatively map a register, validate a value, or establish a scalar codec.
- **ebusd community definitions** — Community-maintained register-name correspondences. Published Vaillant specifications remain authoritative.
- **myVaillant register map** — Value-matched mapping against myPyllant cloud API. NOT a Vaillant-published source — carries false-positive risk where multiple registers share the same value (see [Mapping Conflicts](#mapping-conflicts)).
- **VRC Explorer full group scans** — FLAGS byte verification for all groups.
