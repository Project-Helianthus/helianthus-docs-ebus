# Vaillant B524 Extended Register Map

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. This reference uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

> **Status:** Authoritative reference. Single source of truth for B524 register semantics.
>
> **Last updated:** 2026-10-07 (operation-scoped naming catalog)
>
> **Device:** BASV2 (VRC720-compatible, HW 1704)

This is the register catalog for B524. For the protocol specification (wire format, opcodes, FLAGS encoding, response states), see [ebus-vaillant-B524.md](./ebus-vaillant-B524.md). Each unresolved mapping remains marked inline as **Hypothesis** or **Unknown**.

---

## Table Legend

| Column | Meaning |
|--------|---------|
| **RR** | Register address (hex) |
| **Name** | Descriptive semantic name |
| **Cat** | Documentation category: **S**=state, **C**=configuration candidate, **P**=property candidate, **E**=energy/counter candidate, **—**=unknown/unclassified. It is not derived from `FLAGS` alone and does not authorize a write. |
| **Wire** | On-wire encoding: `u8`, `u16`, `u32`, `f32`, `string`, `date`, `time`, `bytes`. All multi-byte integers are little-endian. **f32 byte order is device-dependent:** all values in this map assume address `0x15` (BASV2/VRC720) = little-endian. HMU at `0x08` (heat pump systems) uses big-endian f32 -- see [B524 protocol doc section 2.6](./ebus-vaillant-B524.md#26-wire-type-encoding) |
| **Decode** | Semantic interpretation: `bool`, `°C`, `K`, `bar`, `%`, `kWh`, `hrs`, `min`, `count`, `enum`, `text`, `date`, `time`, `state`, `raw`, `—` (unknown) |
| **ebusd** | ebusd community TSP name. `—` = not in TSP |
| **Constraint** | Historical short-probe range hint. It requires a matching complete OP01/OP07 description before validating edits. `—` = no catalog entry |
| **Values** | Enum mapping. Inline for ≤3 values, otherwise `→enum_name` referencing [Enum Reference](#enum-reference) |
| **Gates** | Condition for register to be present/meaningful. `—` = always available |

**Source annotations** (in Notes):
- No annotation = confirmed by multiple independent sources (ebusd + live scan + value match)
- `†` = CSV value-matched only, not independently confirmed (false-positive risk)
- `ebusd: "..."` = ebusd community note about this register (e.g., special value meanings)

Historic row notes may contain labels such as `stable RO`, `volatile RO`,
`technical RW`, or `user RW`. Those labels are withdrawn as public B524
semantics: retain the printed `FLAGS` value as an observation, but treat the
labels as profile-specific static interpretation until corroborated by public,
correlated evidence. They do not establish writability or authorize a write.

---

## Group Topology

The OP06 product-family labels in this table are **Hypotheses** from the
operation-scoped presentation catalog unless a separate row supplies its own
publishable identity evidence. They identify a candidate family for navigation;
they do not establish physical product identity, presence, or a device layout.
`unused` and the RR layout for GG04 and GG0D remain **Unknown**.

| Opcode | GG | Group label | Instanced | II_MAX | Observed scheduling RR ceiling | Instance gate | Regs (scan/doc) |
|--------|----|-------------|-----------|--------|-------------------------------|---------------|-----------------|
| 0x02 | 0x00 | System | No | 0x00 | 0xFF | — | 179 (0x0001–0x00FF) |
| 0x02 | 0x01 | Native Domestic Hot Water | No | 0x00 | 0x13 | RR0001 exact two-byte nonzero UIN; zero is not present | 17 (0x0001–0x0013) |
| 0x02 | 0x02 | Circuits | Yes | 0x09 | 0x25 | Exact `BASV2/rawSW0507/HW1704/API1`: RR0002 raw `0100`, FLAGS=03 at II00/II01 is active; raw `0000`, FLAGS=03 at II02 is inactive; II09 is virtual native water | profile candidate bound: II00..II08 heating + II09 virtual native-water; nonmatching or unknown profiles require separate qualification |
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

**GG values are opcode-scoped, not global:** `OP=0x02, GG=0x00` and
`OP=0x02, GG=0x01` are the singleton local selector sets for system/settings
and DHW. Separately, `OP=0x06, GG=0x01` and `OP=0x06, GG=0x02` are instanced
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
uses profile-qualified `device_connected` (RR=0x0001),
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
[profile-qualified mapping table](ebus-vaillant-b524-profile-discovery-and-descriptions.md#system-information-and-concrete-instances)
records profile-qualified count interpretation. For ID00 `circuit_count` and ID01
`zone_count`, the legacy public names mean supported capacity under the bounded
profile contract, not configured or present-instance cardinality. They do not
identify, allocate, or make II slots contiguous: keep sparse II slots and apply
the group predicate to every candidate. II09 remains an independent virtual
native-water candidate. These counts do not establish a terminal instance interval. See [the corrected protocol contract](./ebus-vaillant-B524.md).

### Discovery Profiles

Source: sanitized observations and constraint-probe corpus for the exact
`BASV2/rawSW0507/HW1704/API1` profile. “Observed scheduling ceiling” is the
highest RR in the current bounded scheduling evidence; it is not a terminal
maximum and does not exclude read-only state registers above it. A nonmatching
or unknown profile requires separate qualification.

| Opcode | Group | Instance interval | Observed scheduling ceiling | Evidence scope | Notes |
|--------|-------|-------------------|-----------------------------|-------------------|-------|
| 0x02 | 0x00 System | 00 | 0x00FF | observed scope | Singleton |
| 0x02 | 0x01 Native Domestic Hot Water | 00 | 0x0013 | observed scope | RR0001 exact two-byte nonzero UIN predicate; OP01 RR0000..0013 independent |
| 0x02 | 0x02 Circuits | 00..09 | 0x0025 | exact BASV2/rawSW0507/HW1704/API1 scope | II00..08 heating candidates; II09 independent virtual native water |
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

The semantic names below form an operator-curated, operation-scoped naming
catalog ([issue #544](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/544)).
Naming does not independently qualify a codec, value range, write capability,
physical identity or scan bound. Existing raw observations and profile limits
remain separately qualified. Newly named entries without a characterized layout
are marked **Hypothesis**.

### GG=0x00 — System

All registers use opcode `0x02`, instance `0x00`.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | system_dhw_bivalence_point | C | f32 | °C | — | -20..50 step 1 | — | — | FLAGS=0x02 |
| 0x0002 | continuous_heating_limit | C | f32 | °C | ContinuousHeating | -26..10 step 1 | — | — | FLAGS=0x03. ebusd: `-26=off` disables function |
| 0x0003 | frost_protection_delay | C | u16 | hrs | FrostOverRideTime | 0..12 step 1 | — | — | FLAGS=0x03 |
| 0x0004 | max_preheating_time | C | u16 | min | — | 0..300 step 10 | — | — | FLAGS=0x03. † |
| 0x0006 | manual_cooling_days | C | u8 | days | — | — | — | cooling_enabled? | **Dormant** when cooling not configured. VRC720 manual cooling days count. † |
| 0x0007 | system_off | C | u8 | bool | — | — | `0=off 1=on` | — | FLAGS=0x03 (user RW). System on/off switch, not a sensor reading |
| 0x0008 | cooling_while_holiday | C | u8 | bool | — | — | — | — | † |
| 0x0009 | automatic_cooling_enabled | C | u8 | bool | — | — | `0=off 1=on` | — | FLAGS=0x02 (technical RW). Scan: 1 byte. † |
| 0x000A | system_cylinder_parallel_loading_allowed | C | u16 | bool | HwcParallelLoading | — | →onoff | — | ebusd confirmed at `@ext(0xa,0)` |
| 0x000B | system_solar_circuit_bleeding_time | — | u16 | — | — | — | — | — | Scan value: 0. Near boolean cluster |
| 0x000D | system_solar_frost_protection_limit | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000E | max_room_humidity | C | u16 | % | MaxRoomHumidity | — | — | — | |
| 0x000F | hybrid_control_strategy | — | u16 | — | HybridManager | — | — | — | Name confirmed by BASV3 TypeSpec (`burmistrzak/ebusd-configuration 15.basv3.tsp`). Access: `ri/wi` (installer). Hybrid system manager (HP + boiler). Wire semantics pending live validation |
| 0x0010 | backup_heater_tariff | — | u16 | — | TariffAuxHeater | — | — | — | Name confirmed by BASV3 TypeSpec (`burmistrzak/ebusd-configuration 15.basv3.tsp`). Access: `ri` (installer read). Tariff for auxiliary heater |
| 0x0011 | energy_rate_low_tariff | — | u16 | — | — | — | — | — | Scan value: 16. Possible temp threshold |
| 0x0012 | energy_rate_high_tariff | C | u16 | °C | — | — | — | — | Confirmed exact, value=20 |
| 0x0013 | backup_heater_type | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0014 | adaptive_heating_curve | C | u8 | bool | AdaptHeatCurve | — | →yesno | — | FLAGS=0x03 (user RW). Scan validated 1-byte |
| 0x0015 | automatic_daylight_saving_time | — | u16 | — | — | — | — | — | False positive in CSV (was `parallel_tank_loading`; actual is at 0x000A) |
| 0x0016 | system_ventilation_operating_mode | S | u8 | bool | — | — | `0=off 1=on` | — | **Dormant** when no system quick mode active. Write path is a hypothesis: `OP=0x02, GG=0x09, RR=0x0002`. See [Asymmetric Read/Write Paths](#asymmetric-readwrite-paths) |
| 0x0017 | system_dhw_max_loading_time | C | u16 | min | MaxCylinderChargeTime | — | — | hwc_enabled | |
| 0x0018 | system_dhw_blocking_time | C | u16 | min | HwcLockTime | — | — | hwc_enabled | |
| 0x0019 | system_solar_flow_rate_setpoint | C | f32 | — | — | — | — | fm5_config≤2 | See [Mapping Conflicts](#mapping-conflicts) |
| 0x001B | pump_overrun_time | C | u16 | min | PumpAdditionalTime | — | — | — | |
| 0x001C | generator_max_flow_temperature | C | f32 | °C | — | — | — | — | † |
| 0x001E | automatic_sequence_reversal | — | u8 | — | — | — | — | — | Scan value: 1. Possible pump/flag |
| 0x0022 | alternative_point_for_central_heating | C | f32 | °C | — | — | — | — | -21..40 per TSP |
| 0x0023 | heating_circuit_bivalence_point | C | f32 | °C | — | — | — | — | -20..30 per TSP |
| 0x0024 | backup_heater_allowed_for | C | u16 | enum | — | — | values unknown | — | See [Mapping Conflicts](#mapping-conflicts) |
| 0x0025 | backup_heater_allow_temporary | — | u16 | — | — | — | — | — | Scan value: 0 |
| 0x0026 | heating_circuit_emergency_temperature | C | f32 | °C | — | — | — | — | 20..80 per TSP |
| 0x0027 | system_cylinder_start_loading_hysteresis | C | f32 | K | CylinderChargeHyst | — | — | hwc_enabled | 3..20 step 0.5 per TSP |
| 0x0029 | system_cylinder_loading_offset | C | f32 | K | CylinderChargeOffset | — | — | hwc_enabled | 0..40 per TSP |
| 0x002A | system_cylinder_dhw_legionella_protection_start_time | C | time | time | — | — | — | hwc_enabled | HH:MM |
| 0x002B | system_cylinder_dhw_legionella_protection_start_weekday | C | u16 | enum | — | — | `0=off 1=Mon 2=Tue 3=Wed 4=Thu 5=Fri 6=Sat 7=Sun` | hwc_enabled | Day-of-week selector. 0=disabled |
| 0x002C | maintenance_date | C | date | date | MaintenanceDate | — | — | — | FLAGS=0x03 (user-facing RW). HDA:3 encoding [DD,MM,YY]. Sentinel 2015-01-01 = factory default. Writable via B524 OT=0x01 |
| 0x002D | outside_temperature_correction | C | f32 | K | — | — | — | — | -3..3 step 0.5 per TSP |
| 0x002F | module_configuration_vr71 | P | u16 | count | — | — | — | — | 1..11 |
| 0x0031 | language | — | u16 | — | — | — | — | — | Scan value: 0 |
| 0x0034 | system_date | S | date | date | Date | — | — | — | BCD |
| 0x0035 | system_time | S | time | time | Time | — | — | — | HH:MM:SS |
| 0x0036 | system_scheme | P | u16 | count | HydraulicScheme | — | — | — | 1..16 |
| 0x0038 | system_cooling_start_temperature | C | f32 | °C | — | — | — | — | 10..30 per TSP |
| 0x0039 | system_water_pressure | S | f32 | bar | WaterPressure | — | — | — | Read-only |
| 0x003A | tri_vai_calculation_result | C | f32 | K | — | — | — | — | -10..10 per TSP |
| 0x003C | system_yield_solar_reset | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x003D | system_yield_solar_total | E | u32 | kWh | SolarYieldTotal | — | — | fm5_config≤2 | |
| 0x003E | system_yield_environmental_total | E | u32 | kWh | YieldTotal | — | — | — | |
| 0x003F | system_yield_environmental_reset | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0040 | system_ventilation_voc_sensor_1 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0041 | system_ventilation_voc_sensor_2 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0042 | system_ventilation_day_max_fan_stage | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0043 | system_ventilation_night_max_fan_stage | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0044 | system_ventilation_heat_recovery | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0045 | power_cut_function_evu | C | u16 | enum | — | — | values unknown | — | |
| 0x0046 | system_cylinder_mss_dhw_max_flow_setpoint | C | f32 | °C | HwcMaxFlowTempDesired | — | — | — | 15..80 per TSP |
| 0x0047 | system_in_failure_mode | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0 |
| 0x0048 | energy_manager_state | S | u16 | enum | — | — | `0=standby 1=heating 2=cooling 3=dhw` | — | Single raw enum projected into multiple system-status views. `heating+cooling` is only a possible combined state presentation; its raw numeric encoding remains pending validation. |
| 0x0049 | system_consumption_electricity_reset | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x004A | reset_to_default | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x004B | system_flow_temperature | S | f32 | °C | SystemFlowTemp | — | — | — | Read-only. Do not conflate with B509 boiler flow temperature or the controller-side `OP=0x06 GG=0x01 RR=0x0015` heat-source status selector |
| 0x004C | vwz_ai_backup_heater_max_power | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x004D | vwz_ai_configuration_ma2 | C | u16 | enum | MultiRelaySetting | — | →mamode | — | |
| 0x004E | system_consumption_fuel_heating_current_month | E | u32 | kWh | PrFuelSumHcThisMonth | — | — | — | |
| 0x004F | system_consumption_electricity_heating_current_month | E | u32 | kWh | PrEnergySumHcThisMonth | — | — | — | |
| 0x0050 | system_consumption_electricity_dhw_current_month | E | u32 | kWh | PrEnergySumHwcThisMonth | — | — | — | |
| 0x0051 | system_consumption_fuel_dhw_current_month | E | u32 | kWh | PrFuelSumHwcThisMonth | — | — | — | |
| 0x0052 | system_consumption_fuel_heating_previous_month | E | u32 | kWh | PrFuelSumHcLastMonth | — | — | — | |
| 0x0053 | system_consumption_electricity_heating_previous_month | E | u32 | kWh | PrEnergySumHcLastMonth | — | — | — | |
| 0x0054 | system_consumption_electricity_dhw_previous_month | E | u32 | kWh | PrEnergySumHwcLastMonth | — | — | — | |
| 0x0055 | system_consumption_fuel_dhw_previous_month | E | u32 | kWh | PrFuelSumHwcLastMonth | — | — | — | |
| 0x0056 | system_consumption_fuel_heating_total | E | u32 | kWh | PrFuelSumHc | — | — | — | |
| 0x0057 | system_consumption_electricity_heating_total | E | u32 | kWh | PrEnergySumHc | — | — | — | |
| 0x0058 | system_consumption_electricity_dhw_total | E | u32 | kWh | PrEnergySumHwc | — | — | — | |
| 0x0059 | system_consumption_fuel_dhw_total | E | u32 | kWh | PrFuelSumHwc | — | — | — | |
| 0x005C | system_consumption_electricity_total | E | u32 | kWh | PrEnergySum | — | — | — | |
| 0x005D | system_consumption_fuel_total | E | u32 | kWh | PrFuelSum | — | — | — | |
| 0x005E | system_yield_heatrecovery_total | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0. Near energy counters |
| 0x005F | actor_sensor_test_device | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0060 | actor_sensor_test_sensor | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 2 |
| 0x0061 | actor_sensor_test_actor | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0062 | system_ventilation_voc_sensor_3 | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0063 | system_ventilation_max_voc | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0065 | system_ventilation_displayed_wish_fan_stage | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x0066 | home_screen_status | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0067 | system_cylinder_low_temperature | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 1" |
| 0x0068 | system_cylinder_top_temperature | S | f32 | — | — | — | — | — | FLAGS=0x00. NaN = no VR70 module. ebusd TSP: "VR70 Konfig 2" |
| 0x0069 | operation_mode_effect | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x006A | vwz_ai_configuration_me | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 1 |
| 0x006C | installer_name_1 | C | string | text | Installer1 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x006D | installer_name_2 | C | string | text | Installer2 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x006F | installer_phone_1 | C | string | text | PhoneNumber1 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x0070 | installer_phone_2 | C | string | text | PhoneNumber2 | — | — | — | FLAGS=0x03 (user-facing RW). CString, maxLength 6. Writable via B524 OT=0x01 |
| 0x0071 | system_holiday_start | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0072 | system_holiday_end | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0073 | outside_temperature | S | f32 | °C | DisplayedOutsideTemp | — | — | — | Read-only |
| 0x0074 | system_quick_mode | S | u8 | enum | — | — | — | — | **Dormant** when no system quick mode active. Mode enumeration and write path `OP=0x02, GG=0x09, RR=0x0001` remain hypotheses. See [Asymmetric Read/Write Paths](#asymmetric-readwrite-paths) |
| 0x0075 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. Near installer_menu_code cluster |
| 0x0076 | installer_menu_code | C | u16 | count | KeyCodeforConfigMenu | — | — | — | FLAGS=0x02 (technical RW). Range 0..999. Writable via B524 OT=0x01 |
| 0x0077 | install_assistant_ready | C | u8 | bool | — | — | — | — | FLAGS=0x03. Scan value: 1 |
| 0x0078 | home_screen_special_function | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0079 | status_zone_period_heating | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007A | status_zone_period_cooling | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007B | operating_mode_heating_for_zone | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007C | operating_mode_cooling_for_zone | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007D | home_screen_operation_mode | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x007E | fair_mode | C | f32 | — | — | — | — | — | FLAGS=0x03. Scan value: 0.0 |
| 0x007F | screed_drying_day | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0080 | system_cylinder_loading_start_offset | C | f32 | — | — | — | — | — | FLAGS=0x03. Scan value: 0.0. Constraint: -10..10 step 1. Possibly PV offset |
| 0x0081 | system_cylinder_loading_stop_offset | P | f32 | K | — | — | — | — | † |
| 0x0082 | room_temperature_setpoint_for_holiday | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0083 | bank_holiday_start_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0084 | bank_holiday_end_date | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0085 | actor_sensor_test_sensor_value | P | f32 | — | — | — | — | — | FLAGS=0x01. NaN |
| 0x0086 | backlight_switch_off_time | — | u16 | — | — | — | — | — | Scan value: 60. PV/smart cluster |
| 0x0087 | drainback_start_time | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0088 | drainback_station | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0089 | collector_pump_kick_time | — | u16 | — | — | — | — | — | Scan value: 15. PV/smart cluster |
| 0x008A | collector_min_kick_gradient | — | f32 | — | — | — | — | — | Scan value: 1.0. PV/smart cluster |
| 0x008B | heatpump_max_flow_setpoint | — | f32 | — | — | — | — | — | Scan value: 90.0. PV/smart cluster, possible max flow temp |
| 0x008C | boiler_with_remote_reset | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Near PV/smart cluster |
| 0x008D | display_test_pattern | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x008E | backlight_mode | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x008F | system_cylinder_available | C | u16 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0090 | plugged_in | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0091 | button_pressed_left | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0092 | button_pressed_right | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0093 | encoder_rotated | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0094 | external_crystal_state | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0095 | outside_temperature_average_24h | S | f32 | °C | OutsideTempAvg | — | — | — | Rounded avg updated every 3h |
| 0x0096 | maintenance_mode | S | u8 | bool | MaintenanceDue | — | →yesno | — | FLAGS=0x01 (stable RO). Scan validated 1-byte |
| 0x0097 | eeprom_update_in_progress | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Near maintenance cluster |
| 0x0098 | boiler_remote_reset | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x0099 | rtc_crystal_state | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x009A | green_iq | S | u16 | bool | — | — | — | — | |
| 0x009B | reset_to_default_time_program | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. Near green_iq |
| 0x009C | home_screen_headline | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x009D | system_cylinder_mss_dhw_top_temperature | S | f32 | °C | HwcStorageTempTop | — | — | — | Read-only |
| 0x009E | system_cylinder_mss_dhw_bottom_temperature | S | f32 | °C | HwcStorageTempBottom | — | — | — | Read-only |
| 0x009F | system_cylinder_mss_heating_top_temperature | S | f32 | °C | HcStorageTempTop | — | — | — | Read-only |
| 0x00A0 | system_cylinder_mss_heating_bottom_temperature | S | f32 | °C | HcStorageTempBottom | — | — | — | Read-only |
| 0x00A1 | smart_pv_activation | P | u8 | — | — | — | — | — | FLAGS=0x01. Scan value: 0. Between cylinder temps and buffer_charge_offset |
| 0x00A2 | system_cylinder_smart_pv_ch_offset | C | f32 | K | — | — | — | — | 0..15 per TSP |
| 0x00A3 | system_ventilation_status_period | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A4 | system_ventilation_special_function_status | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A5 | cascade_client_sequence | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00A6 | button_pressed_menu | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A7 | button_pressed_ok | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A8 | button_pressed_back | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00A9 | button_pressed_up | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00AA | button_pressed_down | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00AB | isolation_switch | C | u8 | bool | — | — | — | — | FLAGS=0x02. Scan value: 1 |
| 0x00AF | system_consumption_electricity_cooling_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B0 | system_consumption_electricity_cooling_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B1 | system_consumption_electricity_cooling_total | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00B2 | net_id | C | u16 | raw | — | — | — | — | FLAGS=0x02. Scan value: 0xBDA9 (48553). Semantics unknown |
| 0x00B3 | vwz_ai_configuration_ma1 | C | u8 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00B5 | outside_temperature_sensor_visibility | P | u8 | bool | — | — | — | — | FLAGS=0x01. Scan value: 1 |
| 0x00B6 | ext_energy_management_activation | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00B8 | system_solar_3wv | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00B9 | system_consumption_electricity_cooling_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0. Energy/counter region start |
| 0x00BA | system_consumption_electricity_cooling_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00BB | system_consumption_electricity_dhw_current_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BC | system_consumption_electricity_dhw_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BD | system_consumption_fuel_heating_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00BF | system_consumption_fuel_dhw_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00C0 | system_consumption_electricity_heating_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00C1 | system_consumption_electricity_heating_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Unknown sub-counter (slowly incrementing, value=7). No standard register equivalent |
| 0x00C2 | system_consumption_electricity_system_current_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x004F** (PrEnergySumHcThisMonth). Verified 2026-03-08 |
| 0x00C3 | system_consumption_electricity_system_previous_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0053** (PrEnergySumHcLastMonth). Verified 2026-03-08 |
| 0x00C4 | system_consumption_electricity_system_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Unknown sub-counter (slowly incrementing, value=7). Same as 0x00C1 |
| 0x00C5 | system_consumption_electricity_system_previous_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0058** (PrEnergySumHwc). Verified 2026-03-08 |
| 0x00C6 | system_consumption_electricity_system_total | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0057** (PrEnergySumHc). Verified 2026-03-08 |
| 0x00C7 | system_consumption_fuel_dhw_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0059** (PrFuelSumHwc). Verified 2026-03-08 |
| 0x00C8 | system_consumption_fuel_heating_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Mirror of 0x0056** (PrFuelSumHc). Verified 2026-03-08 |
| 0x00C9 | system_consumption_fuel_system_current_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Near-mirror of 0x004E** (PrFuelSumHcThisMonth). Off-by-1 delta |
| 0x00CA | system_consumption_fuel_system_previous_month | P | u32 | kWh | — | — | — | — | FLAGS=0x01. **Near-mirror of 0x0052** (PrFuelSumHcLastMonth). Off-by-1 delta |
| 0x00CB | system_consumption_fuel_system_current_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. gas.climate + gas.dhw (all-time). Verified 2026-03-08 |
| 0x00CC | system_consumption_fuel_system_previous_year | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Always 0 |
| 0x00CD | system_consumption_fuel_system_total | P | u32 | kWh | — | — | — | — | FLAGS=0x01. Duplicate of 0x00CB. Verified 2026-03-08 |
| 0x00CE | system_yield_heatrecovery_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00CF | system_yield_heatrecovery_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D0 | system_yield_heatrecovery_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D1 | system_yield_heatrecovery_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D2 | system_yield_solar_previous_month | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D3 | system_yield_solar_current_month | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D4 | system_yield_solar_current_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D5 | system_yield_solar_previous_year | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00D6 | system_yield_environmental_previous_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D7 | system_yield_environmental_previous_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D8 | system_yield_environmental_current_year | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00D9 | electricity_tariff_type | C | u16 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00DA | manual_cooling_date_start | C | date | date | — | — | — | cooling_enabled? | FLAGS=0x02 observed. VRC700 manual cooling start-date interpretation and writability are **Hypotheses**; no correlated write evidence is published. BCD HDA:3. Default: 01.01.2013. **Dormant** when cooling not configured. |
| 0x00DB | manual_cooling_date_end | C | date | date | — | — | — | cooling_enabled? | FLAGS=0x02 observed. VRC700 manual cooling end-date interpretation and writability are **Hypotheses**; no correlated write evidence is published. BCD HDA:3. Default: 01.01.2013. **Dormant** when cooling not configured. |
| 0x00DC | room_temperature_control_strategy_type | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00DD | screed_drying_profile_day_01_10 | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 10 bytes: [25,30,35,40,45,45,45,45,45,45] — hourly temp profile (°C/2) |
| 0x00DE | screed_drying_profile_day_11_20 | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 10 bytes: [45,45,40,35,30,25,10,10,10,10] — hourly temp profile continued |
| 0x00DF | screed_drying_profile_day_21_29 | C | bytes | schedule | — | — | — | — | FLAGS=0x03. 9 bytes: [10,10,10,30,35,40,45,35,25] — hourly temp profile end. 29 values total across DD-DF |
| 0x00E0 | system_yield_environmental_current_month | S | f32 | — | — | — | — | — | FLAGS=0x00. Scan value: 0.0 |
| 0x00E1 | circuit_control_strategy | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00E2 | automatic_mode_active | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00E3 | button_raw_value_up | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E4 | button_raw_value_down | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E5 | button_raw_value_question | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E6 | button_raw_value_ok | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E7 | button_raw_value_menu | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E8 | button_raw_value_back | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00E9 | button_raw_value_slider_1 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EA | button_raw_value_slider_2 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EB | button_raw_value_slider_3 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EC | button_raw_value_slider_4 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00ED | button_raw_value_slider_5 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EE | button_raw_value_slider_6 | P | f32 | — | — | — | — | — | FLAGS=0x01. Scan value: 0.0 |
| 0x00EF | continuous_heating_room_setpoint | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 20.0. Temperature setpoint |
| 0x00F0 | error_number_priority | P | u16 | — | — | — | — | — | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F1 | maintenance_number_priority | P | u16 | — | — | — | — | — | FLAGS=0x01. Scan value: 0xFFFF (65535) — sentinel/unset |
| 0x00F2 | system_holiday_start_date | C | date | date | — | — | — | — | FLAGS=0x03. Scan: 01.01.2015 (BCD) |
| 0x00F3 | system_holiday_end_date | C | date | date | — | — | — | — | FLAGS=0x03. Scan: 01.01.2015 (BCD) |
| 0x00F4 | system_holiday_start_time | C | date | date | — | — | — | — | FLAGS=0x03. Scan: 00.00.2000 (BCD reset) |
| 0x00F5 | system_holiday_end_time | C | date | date | — | — | — | — | FLAGS=0x03. Scan: 00.00.2000 (BCD reset) |
| 0x00F6 | room_temperature_setpoint_for_holiday | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 10.0 |
| 0x00F7 | system_holiday_abort | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00F8 | manual_cooling_abort | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0. ebusd TSP hinted 5-byte — scan sees 1 byte |
| 0x00F9 | system_ventilation_boost | C | u8 | — | — | — | — | — | FLAGS=0x03. Scan value: 0 |
| 0x00FA | external_heat_demand_input_configuration | C | u8 | — | — | — | — | — | FLAGS=0x02. Scan value: 0 |
| 0x00FB | heatpump_mss_min_difference | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 10.0 |
| 0x00FC | heatpump_max_flow_dhw_setpoint | P | f32 | °C | — | — | — | — | FLAGS=0x01. Scan value: 90.0. Likely max flow temperature |
| 0x00FD | boiler_max_flow_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x00FE | (unknown_temp_config) | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 13.0 |
| 0x00FF | (unknown_temp_config) | C | f32 | °C | — | — | — | — | FLAGS=0x03. Scan value: 25.0 |

**Note:** 100 new registers discovered in the 0x003C-0x00FF range by proof scan 2026-03-05. The 0x00C1-0x00CD cluster contains u32 energy counters (decode as u32, NOT f32 — the tiny float values like 6.586e-43 are mis-decoded u32 integers). The 0x00DD-0x00DF cluster contains packed hourly temperature schedule bytes. The 0x00E3-0x00EE cluster (13 consecutive f32=0.0 with FLAGS=0x01) may be per-month energy statistics. The 0x00F2-0x00F5 cluster contains holiday date pairs.

---

### GG=0x01 — Native Domestic Hot Water

All registers use opcode `0x02`, instance `0x00`. `native_dhw_circuit_type`
(RR0001) is also the profile-qualified discovery predicate only when its reply
is an exact two-byte UIN decoded nonzero; zero is `not_present`, and an empty,
wrong-width, NACK, decode-failed, or unmatched result is `unknown`. This is
independent of OP01 descriptions for RR0000..0013. All registers except
`native_dhw_status` (0x000F) are gated by `native_dhw_circuit_type` (0x0001).

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | native_dhw_circuit_type | C | u16 | bool | — | 0..1 | `0=off 1=on` | — | Gate register for GG=0x01. Constraint tag u16, Scan verified 2-byte |
| 0x0002 | native_dhw_circulation_pump_status | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | Constraint tag u8 |
| 0x0003 | native_dhw_operation_mode | C | u16 | enum | HwcOpMode | 0..2 | →opmode | hwc_enabled | |
| 0x0004 | native_dhw_tapping_temperature_setpoint | C | f32 | °C | HwcTempDesired | 35..70 | — | hwc_enabled | |
| 0x0005 | native_dhw_current_temperature | S | f32 | °C | HwcStorageTemp | 0..99 | — | hwc_enabled | Read-only |
| 0x0006 | native_dhw_pump_status | S | u8 | bool | — | 0..1 | `0=off 1=on` | hwc_enabled | Constraint tag u8 |
| 0x0007 | native_dhw_program_reset_to_default | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0008 | native_dhw_current_target_flow_temperature | S | f32 | °C | HwcFlowTemp | — | — | hwc_enabled | Read-only |
| 0x0009 | native_dhw_holiday_start_date | C | date | date | HwcHolidayStartPeriod | — | — | hwc_enabled | |
| 0x000A | native_dhw_holiday_end_date | C | date | date | HwcHolidayEndPeriod | — | — | hwc_enabled | |
| 0x000B | native_dhw_bank_holiday_start | C | date | date | HwcBankHolidayStartPeriod | — | — | hwc_enabled | ebusd confirmed |
| 0x000C | native_dhw_bank_holiday_end | C | date | date | HwcBankHolidayEndPeriod | — | — | hwc_enabled | ebusd confirmed |
| 0x000D | native_dhw_special_function_mode | C | u8 | enum | HwcSFMode | — | →sfmode | hwc_enabled | FLAGS=0x03 (user RW). Scan validated 1-byte |
| 0x000E | native_dhw_controlled_by_system | P | u8 | bool | — | — | — | — | FLAGS=0x01. Scan value: 1. Near hwc_status, possibly active flag |
| 0x000F | native_dhw_status | S | u16 | state | — | — | — | — | Not gated |
| 0x0010 | native_dhw_holiday_start_time | C | time | time | — | — | — | hwc_enabled | |
| 0x0011 | native_dhw_holiday_end_time | C | time | time | — | — | — | hwc_enabled | |
| 0x0012 | native_dhw_holiday_abort | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0013 | (unknown) | C | u8 | — | — | — | — | hwc_enabled | FLAGS=0x03. Scan value: 0 |
| 0x0014 | native_dhw_preference | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0015 | native_dhw_recharge_tapping_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0019 | native_dhw_loading_efficiency_state | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |

---

<a id="gg0x02--heating-circuits-multi-instance"></a>
### GG=0x02 — Circuits

All registers use opcode `0x02`. The exact `BASV2/rawSW0507/HW1704/API1` profile
admits II00..II08 as ordinary heating-circuit candidates and II09 as the virtual
native-water circuit. A nonmatching or unknown profile requires separate
qualification. Active heating circuits are discovered by probing
`circuit_mixer_type_external` (RR=0x0002). In sanitized observations, II00 and
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
| 0x0001 | circuit_circuit_type | — | u16 | — | — | 1..2 | — | — | CSV says `circuit_mixer_type_external` but commonly mapped to 0x0002. Purpose unverified. † |
| 0x0002 | circuit_mixer_type_external | P | u16 | enum | Hc{hc}CircuitType | 0..4 | →mctype | — | Discovery probe. Also `mixer_circuit_type_external` |
| 0x0003 | circuit_influence_type | C | u8 | enum | Hc{hc}RoomInfluenceType | — | `0=inactive 1=active 2=extended` | — | Controls room sensor influence on heating curve. No value reply observed at II=0x00. See GetExtendedRegisters §4.2.5 for behavioral semantics |
| 0x0004 | circuit_backflow_temperature_setpoint | C | f32 | °C | Hc{hc}ReturnTempDesired | 15..80 | — | circuit_type=4 (return_increase) | Factory setting 30°C. jonesPD CTLV2 confirmed. Only meaningful for "Increase in return" circuits |
| 0x0005 | circuit_condensate_sensitive_emitter | C | u8 | bool | — | 0..1 | `0=off 1=on` | cooling_enabled | Constraint tag u8. ebusd onoff=UCH. † |
| 0x0006 | circuit_cooling_allowed | C | u8 | bool | Hc{hc}CoolingEnabled | 0..1 | `0=off 1=on` | — | Gate register. Constraint tag u8. ebusd onoff=UCH |
| 0x0007 | circuit_current_target_flow_temperature | S | f32 | °C | Hc{hc}FlowTempDesired | — | — | — | Installer-field candidate; physical menu correspondence requires corroboration. |
| 0x0008 | circuit_current_flow_temperature | S | f32 | °C | Hc{hc}FlowTemp | — | — | — | Read-only. Circuit flow sensor VF[x], NOT boiler return temperature |
| 0x0009 | circuit_dhw_tapping_setpoint | C | f32 | °C | — | — | — | ext_hwc_active | † |
| 0x000A | circuit_epsilon | C | f32 | K | — | — | — | cooling_enabled | † |
| 0x000B | circuit_flow_temperature_setpoint_correction_heating | C | f32 | K | Hc{hc}ExcessTemp | — | — | circuit_type=1 (heating) | Flow temp increased by this value to keep mixing valve in control range |
| 0x000C | circuit_flow_temperature_setpoint_high | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | Fixed-value circuit target flow temp. † |
| 0x000D | circuit_flow_temperature_setpoint_low | C | f32 | °C | — | — | — | circuit_type=2 (fixed_value) | Fixed-value circuit setback temp. † |
| 0x000E | circuit_frost_protection_mode | C | u16 | enum | Hc{hc}SetbackMode | — | →offmode | circuit_type=1 (heating) | Installer-field candidate; do not infer a separate setback field from this label or physical menu correspondence. |
| 0x000F | circuit_heating_curve | C | f32 | — | Hc{hc}HeatCurve | — | — | — | Dimensionless ratio |
| 0x0010 | circuit_heating_flow_temperature_max_setpoint | C | f32 | °C | Hc{hc}MaxFlowTempDesired | — | — | — | 15..80 per ebusd |
| 0x0011 | circuit_cooling_flow_temperature_min_setpoint | C | f32 | °C | Hc{hc}MinCoolingTempDesired | — | — | cooling_enabled | |
| 0x0012 | circuit_flow_temperature_min_setpoint | C | f32 | °C | Hc{hc}MinFlowTempDesired | — | — | — | |
| 0x0013 | circuit_dhw_operating_mode | C | u16 | enum | — | — | values unknown | ext_hwc_active | |
| 0x0014 | circuit_maximum_outside_temperature_heating | C | f32 | °C | Hc{hc}SummerTempLimit | — | — | — | Installer-field candidate; the summer-cutoff interpretation requires physical corroboration. |
| 0x0015 | circuit_room_temperature_influence | C | u16 | enum | Hc{hc}RoomTempSwitchOn | — | →rcmode | — | Gate for dew point |
| 0x0016 | circuit_screed_drying_day | C | u16 | count | Hc{hc}ScreedDryingDay | — | — | — | Screed drying program |
| 0x0017 | circuit_screed_drying_setpoint | S | f32 | °C | Hc{hc}ScreedDryingTempDesired | — | — | — | FLAGS=0x01 (stable RO) — computed setpoint, not user-configurable |
| 0x0018 | circuit_dhw_circulation_pump_status | S | u16 | bool | Hc{hc}ExternalHWCActive | — | — | — | Gate register for ext HWC. FLAGS=0x00 (volatile RO) — status, not config |
| 0x0019 | circuit_external_heat_demand | S | u16 | state | Hc{hc}ExternalHeatDemand | — | — | — | External heat source. FLAGS=0x00 (volatile RO) — status, not config |
| 0x001A | circuit_status_heating_circuit_mixer | S | f32 | % | Hc{hc}MixerMovement | — | — | — | Signed float: `<0`=closing, `>0`=opening. Scan verified: -100.0 when fully closing. Read-only |
| 0x001B | circuit_pump_status | S | u16 | enum | Hc{hc}Status | — | — | — | Enum: 0=STANDBY, 1=HEATING, 2=COOLING. See [Circuit State Enum](#circuit-state-enum) |
| 0x001C | circuit_adaptive_heating_curve_offset | S | f32 | — | Hc{hc}HeatCurveAdaption | — | — | — | Heat curve adaption factor. Dimensionless. Read-only |
| 0x001D | circuit_dhw_quick_mode | C | f32 | °C | Hc{hc}FrostProtThreshold | — | — | — | FLAGS=0x02 (technical RW) — writable config, not property |
| 0x001E | circuit_status_circuit | S | u16 | raw | Hc{hc}PumpStatus | — | — | — | Installer-field candidate, distinct from RR001B and RR0020; its semantic status interpretation needs separate physical corroboration. |
| 0x001F | circuit_minimum_outside_temperature_cooling | C | f32 | °C | Hc{hc}RoomSetpoint | — | — | — | |
| 0x0020 | circuit_status_automatic_heating_cooling | S | u8 | raw | Hc{hc}FlowTempCalc | — | — | — | Observed UCH one-byte raw status (`00`) at the relevant circuit selectors. It is not a temperature value; earlier f32 prose is unqualified. |
| 0x0021 | circuit_mixer_position_percentage | S | f32 | % | Hc{hc}MixerPosition | — | — | — | |
| 0x0022 | circuit_current_room_humidity | S | f32 | % | Hc{hc}Humidity | — | — | — | From room sensor |
| 0x0023 | circuit_dew_point_temperature | S | f32 | °C | Hc{hc}DewPointTemp | — | — | — | |
| 0x0024 | circuit_pump_operating_hours | S | u32 | hrs | Hc{hc}PumpHours | — | — | — | |
| 0x0025 | circuit_pump_starts_count | S | u32 | count | Hc{hc}PumpStarts | — | — | — | |

---

<a id="gg0x03--zones-multi-instance"></a>
### GG=0x03 — Zones

All registers use opcode `0x02`. Instances 0x00-0x0A; active zones are
discovered by probing `zone_circuit_for_zone` (RR=0x001C). In the BASV2/SW0507
scoped observation, zone II00 maps to raw `00` and zone II01 to raw `01`; II02+
returns `FF`. These are native values, with no +1 remapping. They are
profile-scoped observations, not a universal zone/circuit contract.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | zone_cooling_operation_mode | C | u16 | enum | — | 0..2 | →opmode | cooling_enabled | Same enum as heating_operation_mode |
| 0x0002 | zone_room_temperature_setpoint_cooling | C | f32 | °C | Zone{z}CoolingTemp | 15..30 step 0.5 | — | cooling_enabled | |
| 0x0003 | zone_holiday_start_date | C | date | date | Zone{z}HolidayStartPeriod | — | — | — | |
| 0x0004 | zone_holiday_end_date | C | date | date | Zone{z}HolidayEndPeriod | — | — | — | |
| 0x0005 | zone_holiday_setpoint | C | f32 | °C | Zone{z}HolidayTemp | 5..30 | — | — | |
| 0x0006 | zone_heating_operation_mode | C | u16 | enum | Zone{z}OpMode | 0..2 | →opmode | — | |
| 0x0007 | zone_comfort_room_temperature_setpoint_heating | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0008 | zone_quick_veto_setpoint | C | f32 | °C | Zone{z}QuickVetoTemp | — | — | — | Veto override target |
| 0x0009 | zone_setback_room_temperature_setpoint_heating | C | f32 | °C | Zone{z}NightTemp | — | — | — | Night setpoint |
| 0x000A | zone_operating_mode_heating_teleswitch | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000B | zone_operating_mode_cooling_teleswitch | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000C | zone_bank_holiday_start | C | date | date | Zone{z}BankHolidayStartPeriod | — | — | — | ebusd confirmed |
| 0x000D | zone_bank_holiday_end | C | date | date | Zone{z}BankHolidayEndPeriod | — | — | — | ebusd confirmed |
| 0x000E | zone_quick_mode | C | u8 | enum | Zone{z}SFMode | — | →sfmode | — | FLAGS=0x03 (user RW). Scan validated 1-byte. Writable to set quickveto/away |
| 0x000F | zone_current_measured_temperature | S | f32 | °C | Zone{z}RoomTemp | — | — | — | FLAGS=0x01 (stable RO). From room sensor |
| 0x0010 | zone_schedule_reset_to_default | C | u16 | — | — | — | — | — | FLAGS=0x03 (user RW). Observed in a register survey, not in earlier catalogs |
| 0x0011 | zone_is_active | C | u16 | — | — | — | — | — | FLAGS=0x03 (user RW). Observed in a register survey, not in earlier catalogs |
| 0x0012 | zone_valve_status | S | u16 | bool | Zone{z}ValveStatus | — | `0=closed 1=open` | — | FLAGS=0x01 (stable RO). Used for hvac_action derivation |
| 0x0013 | zone_binding_of_zone | C | u16 | enum | Zone{z}RoomZoneMapping | — | →zmapping | — | Maps zone to room temperature sensor source. The raw numeric B524 enum (`0`, `1`, `2`, ...) is the authoritative value |
| 0x0014 | zone_heating_setpoint | S | f32 | °C | Zone{z}ActualRoomTempDesired | — | — | — | FLAGS=0x01 (stable RO) — computed output, not user-settable. Current setpoint considering all conditions |
| 0x0015 | zone_cooling_setpoint | S | f32 | °C | — | — | — | cooling_enabled | FLAGS=0x01 (stable RO) — computed output, not user-settable |
| 0x0016 | zone_name | C | string | text | Zone{z}Shortname | — | — | — | maxLength 6 |
| 0x0017 | zone_name_prefix | C | string | text | Zone{z}Name1 | — | — | — | maxLength 5. Part 1 |
| 0x0018 | zone_name_suffix | C | string | text | Zone{z}Name2 | — | — | — | maxLength 5. Part 2 |
| 0x0019 | zone_heating_schedule_status | S | u16 | bool | — | — | `0=off 1=on` | — | Timer schedule flag |
| 0x001A | zone_cooling_schedule_status | S | u16 | bool | — | — | `0=off 1=on` | cooling_enabled | Timer schedule flag |
| 0x001B | zone_special_function_status | S | u16 | state | — | — | — | — | Raw zone status code |
| 0x001C | zone_circuit_for_zone | P | bytes | raw | Zone{z}Index | — | — | — | BASV2/SW0507: II00=`00`, II01=`01`, II02+=`FF`; preserve raw index, no +1 remap. |
| 0x001D | zone_heating_event_end_time | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x001E | zone_quick_veto_end_time | C | time | time | Zone{z}QuickVetoEndTime | — | — | — | FLAGS=0x03 (user RW) — writable, can extend/set veto end time |
| 0x0020 | zone_holiday_end_time | C | time | time | — | — | — | — | |
| 0x0021 | zone_holiday_start_time | C | time | time | — | — | — | — | |
| 0x0022 | zone_heating_manual_setpoint | C | f32 | °C | Zone{z}DayTemp | — | — | — | 15..30 step 0.5 per ebusd |
| 0x0023 | zone_cooling_manual_setpoint | C | f32 | °C | — | — | — | cooling_enabled | |
| 0x0024 | zone_quick_veto_end_date | C | date | date | Zone{z}QuickVetoEndDate | — | — | — | FLAGS=0x03 (user RW) — writable, can extend/set veto end date |
| 0x0025 | zone_holiday_abort | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x0026 | zone_quick_veto_duration | C | f32 | hrs | Zone{z}QuickVetoDuration | — | — | — | 0.5..12 step 0.5. Writing enables quick veto mode. |
| 0x0027 | zone_manual_cooling_is_active_for_zone | S | u16 | — | — | — | — | — | FLAGS=0x00 (volatile RO). Observed in a register survey |
| 0x0028 | zone_current_humidity | S | f32 | % | — | — | — | — | FLAGS=0x01 (stable RO). From room sensor |
| 0x0029 | zone_cooling_allowed | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002A | zone_summer_cutoff_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002B | zone_continuous_heating_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002C | zone_frost_protection_active | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002D | zone_heating_roomthermostat_status | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |
| 0x002E | zone_cooling_roomthermostat_status | S | u16 | — | — | — | — | — | FLAGS=0x01 (stable RO). Observed in a register survey |

#### Zone Mode Derivation

The zone operating mode is typically derived from:
- `zone_heating_operation_mode` (0x0006): opmode enum (0=off, 1=auto, 2=manual)
- `zone_quick_mode` (0x000E): sfmode enum (2=quickveto, 3/4=away)
- Associated circuit's `circuit_cooling_allowed` (GG=0x02 RR=0x0006): determines heat vs cool capability

---

### GG=0x04 — Solar Circuit

Entire group gated by `fm5_config ≤ 2`. All registers use opcode `0x02`, instance `0x00`.

**No ebusd coverage exists for GG=0x04** — all names are from value-matched CSV only (†) and carry false-positive risk.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0001 | solar_collector_runtime_reset | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | † |
| 0x0002 | solar_collector_kick_function | C | u8 | bool | — | 0..1 | `0=off 1=on` | fm5_config≤2 | Not pump status (pump is at 0x0008). † |
| 0x0003 | solar_collector_temperature | S | f32 | °C | — | -40..155 | — | fm5_config≤2 | † |
| 0x0004 | solar_collector_min_temperature | C | f32 | K | — | 0..99 | — | fm5_config≤2 | Not storage temp. † |
| 0x0005 | solar_circuit_protection_function | C | f32 | °C | — | 110..150 | — | fm5_config≤2 | † |
| 0x0006 | solar_circuit_protection_function_setpoint | C | f32 | °C | — | 75..115 | — | fm5_config≤2 | Not collector shutdown. † |
| 0x0007 | yield_solar_temperature | S | f32 | °C | — | — | — | fm5_config≤2 | † |
| 0x0008 | solar_pump_active | S | u8 | bool | — | — | `0=off 1=on` | fm5_config≤2 | † |
| 0x0009 | solar_flow_rate_current | S | f32 | raw | — | — | — | fm5_config≤2 | Current yield. † |
| 0x000A | solar_flow_rate_setpoint | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |
| 0x000B | solar_pump_hours | S | u32 | hrs | — | — | — | fm5_config≤2 | Cumulative runtime. † |
| 0x000C | solar_pump_min_power | — | unknown | — | — | — | — | — | **Hypothesis:** operator-provided semantic name; representation and applicability require independent qualification. |

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
| 0x0001 | solar_cylinder_max_temperature_setpoint | C | f32 | °C | — | 0..99 | — | fm5_config≤2 | † |
| 0x0002 | solar_cylinder_start_temperature_difference | C | f32 | K | — | 2..25 | — | fm5_config≤2 | † |
| 0x0003 | solar_cylinder_stop_temperature_difference | C | f32 | K | — | 1..20 | — | fm5_config≤2 | † |
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
| 0x0001 | delta_temperature_control_max_temperature | C | f32 | °C | — | 0..99 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 99.0 |
| 0x0002 | delta_temperature_control_min_temperature | C | f32 | K | — | 0..99 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 0.0 |
| 0x0003 | delta_temperature_control_start_temperature_difference | C | f32 | K | — | 2..25 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 12.0 |
| 0x0004 | delta_temperature_control_stop_temperature_difference | C | f32 | K | — | 1..20 | — | fm5_config≤2? | FLAGS=0x03. Scan value: 5.0 |
| 0x0005 | delta_temperature_td1_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | FLAGS=0x01. NaN (no sensor) |
| 0x0006 | delta_temperature_td2_temperature | S | f32 | °C | — | -10..110 | — | fm5_config≤2? | FLAGS=0x01. NaN (no sensor) |
| 0x0007 | delta_temperature_td_output | S | u8 | — | — | — | — | — | FLAGS=0x00. Scan value: 0. Possibly pump status |

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
| 0x0001 | ventilation_quick_mode | C | u16 | — | — | 0..255 | — | — | FLAGS=0x02. All instances: 0 |
| 0x0002 | ventilation_operating_mode | C | u16 | enum | — | 1..3 | `1=TIME_CONTROLLED 2=NORMAL 3=REDUCED` | — | FLAGS=0x02. All instances: 1. Operator-selected presentation annotation; not independently native-verified |
| 0x0003 | ventilation_status_period | S | u8 | bool | — | 0..1 | `0=off 1=on` | — | FLAGS=0x00. All instances: 1 |
| 0x0004 | ventilation_status_special_operating_mode | S | u16 | — | — | 0..10 | `0=REGULAR 1=BOOST 7=HOLIDAY 10=SYSTEM_OFF` | — | FLAGS=0x00. All instances: 0. Operator-selected presentation annotation; not independently native-verified |
| 0x0005 | ventilation_voc_sensor_1 | S | u16 | — | — | 0..32768 | — | — | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0006 | ventilation_voc_sensor_2 | S | u16 | — | — | 0..32768 | — | — | FLAGS=0x00. All instances: 0x8000 (32768) |
| 0x0007 | ventilation_holiday_end | C | date | date | — | — | — | — | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x0008 | ventilation_holiday_end_time | C | time | time | — | — | — | — | FLAGS=0x02. 00:00:00 |
| 0x0009 | ventilation_holiday_start | C | date | date | — | — | — | — | FLAGS=0x02. 01.01.2015 (BCD default) |
| 0x000A | ventilation_holiday_start_time | C | time | time | — | — | — | — | FLAGS=0x02. 00:00:00 |
| 0x000B | ventilation_heat_recovery_ventilation | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000C | ventilation_max_voc | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000D | ventilation_day_max_fan_stage | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000E | ventilation_night_max_fan_stage | C | u16 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |
| 0x000F | ventilation_holiday_abort | C | u8 | — | — | — | — | — | FLAGS=0x02. All instances: 0 |

---

### GG=0x09 — Ventilation / recoVair Candidates

The published OP00 interpretation includes ID0010h `recovair_count`. It does
not prove GG10h or device presence; the public reported samples all return zero.
The following corrected reconstruction is **Hypothesis** for a VRC720 controller
profile, awaiting publishable correlated replies. It does not replace other
GG09 meanings or establish writable capability. Keep `(OP02,GG09,II,RR)` and
profile provenance; no data from these rows is promoted into a universal mapping.

| RR | snake_case name | Candidate format |
| --- | --- | --- |
| 0002h | `ventilation_operating_mode` | enum; presentation values `1=TIME_CONTROLLED 2=NORMAL 3=REDUCED` |
| 0004h | `ventilation_status_special_operating_mode` | u16; presentation values `0=REGULAR 1=BOOST 7=HOLIDAY 10=SYSTEM_OFF` |
| 0007h / 0008h | `ventilation_holiday_end` / `ventilation_holiday_end_time` | date / time; codec qualification pending |
| 0009h / 000Ah | `ventilation_holiday_start` / `ventilation_holiday_start_time` | date / time; codec qualification pending |
| 000Dh / 000Eh | `ventilation_day_max_fan_stage` / `ventilation_night_max_fan_stage` | u16; range unknown |

These candidate names are shared with the OP02 scalar catalog. The status/availability of a local probe
and a decoded physical ventilation state are distinct. OP02/GG00/RR0016 is catalogued separately as
`system_ventilation_operating_mode`; shared vocabulary does not establish an
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
they do not establish writability, discovery predicates or device identity.

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
| 0x001D | basv2_serial_part1 | P | string | text | — | — | — | — | FLAGS=0x01. First 6 chars of BASV2 serial number (redacted in public docs) |
| 0x001E | basv2_serial_part2 | P | string | text | — | — | — | — | FLAGS=0x01. Chars 7-12 of BASV2 serial number (redacted in public docs) |
| 0x0020 | (unknown) | C | f32 | — | — | — | — | — | FLAGS=0x03. All: 0.0 |
| 0x0021 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x0022-0x003E | temperature_schedule | C | u8 | °C/2 | — | — | — | — | FLAGS=0x03. 29 u8 values: hourly temperature profile. Pattern: 25→45 day, 45→10 night, 10→45→25 evening. Values are degrees × 2 (e.g. 45 = 22.5°C, 10 = 5°C) |
| 0x003F | (unknown) | P | u8 | — | — | — | — | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean |
| 0x0040 | (unknown) | P | time | time | — | — | — | — | FLAGS=0x01. All: 00:00:00 |
| 0x0042-0x004A | (unknown, 9 regs) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 0. Config block |
| 0x004B | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0 |
| 0x004D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 0 |

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


### GG=0x01 — Primary Heat Sources

All registers in this section use opcode `0x06`. `II` selects the heat-generator
slot, so the meaningful selector is `(0x06, 0x01, II, RR)`, not `GG=0x01`
alone. Slot availability/probing is a precondition for interpreting this
selector set: empty or unresolved slots must not be decoded as live primary
heat-source data.

The primary heat-source route is a profile-qualified hypothesis. The selector
set is `(0x06, 0x01, II, RR)`; no published correlated reply qualifies a slot
matrix, availability predicate, or returned value layout. `GG=0x00` remains
uncharacterized rather than absent.

| RR | Name | Cat | Wire | Decode | ebusd | Constraint | Values | Gates | Notes |
|----|------|-----|------|--------|-------|------------|--------|-------|-------|
| 0x0012 | heatgen_error | S | unknown | unknown | — | — | unknown | unknown | **Hypothesis.** The native reply layout, any Boolean convention, and error detail semantics are unqualified. Do not infer an enum or bitmask. |
| 0x0015 | heatgen_status | S | unknown | unknown | — | — | unknown | unknown | **Hypothesis.** It is not a proven scalar flow-temperature mirror. |

---

### GG=0x02 — Secondary Heat Sources

All registers in this selector set use opcode `0x06`, with `II` selecting the
secondary heat-source slot. This selector set is documented separately from local DHW
(`OP=0x02, GG=0x01`). It is documented as an instanced controller-side
path for secondary sources such as solar-facing contributors.

Current canon status:

- selector-set identity is a profile-qualified hypothesis
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
| 0x0001 | device_connected | P | u8 | bool | — | — | `0=empty 1=paired` | — | FLAGS=0x01. II=1: 1 (VRC720f/2 paired) |
| 0x0002 | device_class_address | P | u8 | enum | — | — | `0x15=VRC720 0x35=VR92 0x26=VR71` | — | FLAGS=0x01. Canonical Vaillant eBUS address for device family (ebusd: 0x15→CTLV2, 0x35→VR_92, 0x26→VR_71) |
| 0x0003 | device_error_code | S | u8 | — | — | — | — | — | FLAGS=0x01. II=1: 0 (OK). Empty: 0xFF. 0=no error |
| 0x0004 | device_firmware_version | P | time | version | — | — | — | — | FLAGS=0x01. 3 bytes: major.minor.patch (byte-decimal, NOT BCD). II=1: 08.05.00 → VRC720f/2 sw 08.05 |
| 0x0005 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0006 | (unknown) | S | u16 | — | — | — | — | — | FLAGS=0x00. II=empty: 0x8000, II=1: 0 |
| 0x0007 | current_room_air_humidity | S | f32 | % | — | — | — | — | FLAGS=0x01. II=1: 40.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". NaN if no sensor |
| 0x0008 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x0009 | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000A | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. Empty: 0xFF, II=1: 0 |
| 0x000C | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x000E | room_temp_offset | C | f32 | °C | — | — | — | — | FLAGS=0x03 (user RW). II=1: 0.0. Calibration offset for measured temperature |
| 0x000F | current_room_temperature | S | f32 | °C | — | — | — | — | FLAGS=0x01. II=1: 12.5°C. VR92f/3 manual: "Current room temperature in the zone". NaN if no sensor |
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
| 0x001E | device_paired | P | u8 | bool | — | — | `0=no 1=yes` | — | FLAGS=0x01. II=1: 1. Confirms active pairing. Empty: 0xFF |
| 0x001F | reception_strength | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 7 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | P | u16 | raw | — | — | — | — | FLAGS=0x01. II=1: 0x1504. Byte 0 = device_class_address on VRC720 (0x15) |
| 0x0025 | zone_assignment | P | u8 | count | — | — | — | — | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x002F | (unknown) | P | u8 | — | — | — | — | — | FLAGS=0x01. All: 5 |
| 0x0030 | max_time_periods_per_day | P | u8 | count | — | — | — | — | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |

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
| 0x0007 | current_room_air_humidity | S | f32 | % | RoomHumidity | — | — | — | FLAGS=0x01. II=1: 39.0%. VR92f/3 manual: "Current room air humidity, measured using the installed humidity sensor". ebusd confirmed. NaN if no sensor |
| 0x000B | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x00. II=empty: 0xFF, II=1: 0 |
| 0x000D | (unknown) | C | u16 | — | — | — | — | — | FLAGS=0x03. All: 1 |
| 0x000E | room_temp_offset | C | f32 | °C | — | — | — | — | FLAGS=0x03 (user RW). II=1: 0.0, empty: NaN. Calibration offset for measured temperature |
| 0x000F | current_room_temperature | S | f32 | °C | RoomTemp | — | — | — | FLAGS=0x01. II=1: 13.625°C. VR92f/3 manual: "Current room temperature in the zone". ebusd confirmed. NaN if no sensor |
| 0x0012 | device_status | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 (OK) |
| 0x0017 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0019 | remote_control_address | S | u8 | count | — | — | — | — | FLAGS=0x01. VR92f/3 manual: "each remote control has a unique address starting at 1". II=1: 1. Installer-settable per zone assignment |
| 0x001B | (unknown) | S | f32 | — | — | — | — | — | FLAGS=0x00. All: NaN |
| 0x001E | device_paired | S | u8 | bool | — | — | `0=no 1=yes` | — | FLAGS=0x01. II=1: 1. Empty: 0xFF |
| 0x001F | reception_strength | P | u8 | count | — | — | `4=acceptable <4=unstable 10=max` | — | FLAGS=0x01. VR92f/3 manual: "System control reception strength". Scale 0-10: 4=acceptable, <4=not stable, 10=highly stable. II=1: 10 |
| 0x0020 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 3 |
| 0x0023 | hardware_identifier | S | u16 | raw | — | — | — | — | FLAGS=0x01. II=1: 0x8201. Byte 0 = 0x82 (purpose unclear, does NOT match device_class_address 0x35) |
| 0x0025 | zone_assignment | S | u8 | count | — | — | — | — | FLAGS=0x01. II=1: 2 |
| 0x0026 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x03. II=1: 10. May be reception strength ceiling (constant) |
| 0x0028-0x002E | (unknown, 7 regs) | C | u8 | — | — | — | — | — | FLAGS=0x03. All: 0. User RW config block |
| 0x002F | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. All: 5 |
| 0x0030 | max_time_periods_per_day | S | u8 | count | — | — | — | — | FLAGS=0x01. All: 12 (constant). VR92f/3 manual: "Up to 12 time periods can be set per day". Schema capability constant |
| 0x0032 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. II=empty: 0xFF, II=1: 0 |
| 0x0033 | (unknown) | S | u8 | — | — | — | — | — | FLAGS=0x01. Historical connection state varies; preserve raw Boolean |
| 0x0035 | (unknown) | C | u8 | — | — | — | — | — | FLAGS=0x02. All: 0 |

**Device slot observations:** The characterized OP06 profile uses II01..II08.
The [availability observations](ebus-vaillant-b524-profile-discovery-and-descriptions.md#availability-observations)
separate correlated concrete-II Boolean results from generic class descriptions
and unknown replies. This interval is profile-specific, not a bound on the
one-byte instance field.

`device_connected=false` does not establish physical absence and must not suppress
retained inventory evidence. Identity and telemetry reads can include:
- `device_class_address` (0x0002) — resolve to a controller-ecosystem family hint; in a BASV2 observation, `0x26` correlates with the eBUS-identified `VR_71`
- `device_firmware_version` (0x0004) — byte-decimal triplet
- `reception_strength` (0x001F) — 0-10 scale (4=acceptable, <4=unstable)
- `remote_control_address` (0x0019) — unique per remote (1..N), 0 for initiator
- `current_room_air_humidity` (0x0007) — f32 %, NaN if no sensor
- `current_room_temperature` (0x000F) — f32 °C, NaN if no sensor

**ebusd baseline:** ebusd `15.ctlv2.csv` defines only RR=0x0007 (RoomHumidity, EXP decode) and RR=0x000F (RoomTemp, EXP decode) for VR92 addresses 1-8, routed via `B524,06000a..`.

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

Source: BASV2 hardware constraint probe (`0x01` opcode).

The historic short probes produced range-shaped samples, but the incomplete
selector and length/codec ambiguity prevent them from authoritatively mapping a
record to a register or from validating a value. Retain the rows as historical
hints only; a complete OP01/OP07 response with a qualified scalar codec is
required for validation.

| Group | Record | → RR | Type | Min | Max | Step |
|-------|--------|------|------|-----|-----|------|
| 0x00 | 0x0100 | 0x0001 | f32 | -20 | 50 | 1 |
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
- TSP-style registers (`0x0100+`) are listed in the constraint catalog but are NOT accessible via standard B524 read operations — only standard registers (`0x0001-0x00FF`) work through B524 register reads.
- GG=0x00 Record 0x8000 → RR=0x0080 is now confirmed responsive (FLAGS=0x03, f32=0.0, constraint: -10..10 step 1). Adjacent to `smart_photovoltaic_buffer_offset` (0x0081). Possibly PV-related offset config.

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

### mctype — Circuit type

Used by: GG=0x02 RR=0x0002

| Value | ebusd | Common name | Vaillant manual name | Description |
|-------|-------|-------------|---------------------|-------------|
| 0 | inactive | inactive | Inactive | Circuit unused |
| 1 | mixer | heating | Heating | Weather-compensated heating. Mixing or direct depending on basic system diagram. |
| 2 | fixed | fixed_value | Fixed value | Circuit held at a fixed target flow temperature. Applications: swimming pool heating, door air curtain heating. |
| 3 | hwc | dhw | DHW | Heating circuit used as DHW circuit for an additional cylinder. II09 remains a virtual native-water candidate; current public evidence provides no temperature-based predicate to infer this role when RR0002 is inactive. |
| 4 | returnincr | return_increase | Increase in return | Return temperature raise circuit. Target return temperature at RR=0x0004 (factory setting 30°C). |

**Naming note:** ebusd templates label value 1 as "mixer" — this is a community naming convention; the Vaillant VRC720 operating & installation manual calls it "Heating" (Heizen). The mixing valve is an implementation detail of the hydraulic system, not the circuit type itself.

**Pool is a derived application, not a raw enum value.** The Vaillant manual describes "fixed value control" as suitable for "swimming pool heating" — so pool heating is an _application_ of `fixed_value` (mctype=2) when the system topology includes swimming pool hydraulics (sensor, circulation pump). It is NOT a separate enum value on VRC720/CTLV2/BASV2 systems. Constraint catalog confirms range 0..4.

**ebusd extended enums:** ebusd `mctype` defines 0-5 (adding `pool=5`), and `mctype7` defines 0-6 (adding `circulation=6`; see ebusd-config issue #182 and PR #174). Neither value 5 nor 6 is within the BASV2 constraint range (0..4). These values may be valid on other Vaillant controller platforms.

**Zone capabilities** depend on (a) circuit type supporting heating, and (b) `cooling_enabled` flag (RR=0x0006) for cooling capability. Cooling is a separate function/mode, not derived from circuit type.

Sources: VRC720 operating & installation instructions (circuit type table, fixed value control description, abbreviations list for swimming pool); ebusd `_templates.tsp` mctype/mctype7 definitions; ebusd-config issue #182, PR #174 (translations: Heizen/Festwert/WW/Rückl.anh.).

### Circuit State Enum

Used by: GG=0x02 RR=0x001B (`circuit_state`, ebusd `Hc{hc}Status`)

| Value | Common name | myPyllant | Evidence |
|-------|-------------|-----------|----------|
| 0 | standby | STANDBY | Live scan confirmed: 3 circuits idle, pumps off, flow setpoint=0 |
| 1 | heating | HEATING | Inferred from the `CircuitState` enum correlation; physical corroboration remains required. |
| 2 | cooling | COOLING | Inferred from the `CircuitState` enum correlation; physical corroboration remains required. |
| N | unknown_N | — | Safety fallback for unmapped values |

**ebusd type:** Plain `UCH` — no enum type annotation in ebusd `Hc1Status` model (`15.700.tsp`).

**myPyllant:** `CircuitState` enum in `myPyllant/enums.py` defines `HEATING`, `COOLING`, `STANDBY` as string values. The cloud API performs the numeric-to-string conversion server-side. Test fixtures contain only HEATING and STANDBY observations.

Sources: Live scan observation (2026-03-08), myPyllant `enums.py` `CircuitState`, VRC720 register mapping.

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

**Related registers:** GG=0x02 RR=0x001B `circuit_state` (per-circuit sub-state aggregated here), GG=0x02 RR=0x001E `pump_status`, GG=0x00 RR=0x004B `system_flow_temperature`.

**Confidence:** MEDIUM for states 0-2 (live scan + myPyllant enum correlation); `dhw` remains a hypothesis pending correlated evidence.

### `circuit_state` (OP=0x02, GG=0x02, RR=0x001B)

Register `OP=0x02, OT=0x00, GG=0x02, II=<circuit>, RR=0x001B` — per-circuit state. Wire type: `u16` enum.

| Value | State | myPyllant | Description |
|-------|-------|-----------|-------------|
| 0 | `standby` | `STANDBY` | Circuit idle (live confirmed: 3 circuits simultaneously standby) |
| 1 | `heating` | `HEATING` | Circuit active in heating mode |
| 2 | `cooling` | `COOLING` | Circuit active in cooling mode |

**Transitions:** standby -> heating (room temp below setpoint AND schedule slot active). heating -> standby (setpoint reached OR schedule inactive). standby -> cooling (room temp above cooling setpoint AND cooling enabled).

**Related registers:** GG=0x02 RR=0x001E is an installer-field candidate with unknown semantic status interpretation; GG=0x02 RR=0x001A is `mixer_movement`; GG=0x02 RR=0x0020 is an observed UCH one-byte raw status, not a calculated flow temperature.

**Confidence:** HIGH for 0/1 (live confirmed + myPyllant); MEDIUM for 2 (no cooling hardware in lab).

### `system_quick_mode` (OP=0x02, GG=0x00, RR=0x0016 + 0x0074)

<a id="asymmetric-readwrite-paths"></a>

#### Asymmetric read/write paths

- **Read active flag:** `OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0016` (u8 bool)
- **Read mode value:** `OP=0x02, OT=0x00, GG=0x00, II=0x00, RR=0x0074` (u8 enum)
- **Write:** `OP=0x02, GG=0x09, RR=0x0001` (value) + `RR=0x0002` (active flag) -- asymmetric path

| Value (RR=0x0074) | State | Description |
|--------------------|-------|-------------|
| 0x00 | `dormant` | No quick mode active; RR=0x0016 returns `off` or dormant |
| 0x01 | `ventilation` | Ventilation-only mode |
| 0x02 | `party` | Party mode -- enhanced heating |
| 0x03 | `away` | Away mode -- reduced heating |
| 0x04 | `one_day_at_home` | Single-day manual override |

**Transitions:** dormant -> any active (B524 write to GG=0x09). Active -> dormant (duration expires or explicit deactivation write).

**Related registers:** GG=0x09 RR=0x0001/0x0002 (write targets), GG=0x00 RR=0x0048 `energy_manager_state` (downstream effect: quick mode changes demand), B524 GG=0x03 zone schedules (quick mode overrides scheduled time programs).

**Confidence:** Hypothesis. The register addresses, asymmetric path, and exact enum labels require publishable correlated evidence.

---

## Sources

- **Historical BASV2 short-probe catalog** — Range-shaped samples from incomplete
  `0x01` requests. It is unqualified historical evidence only: it does not
  authoritatively map a register, validate a value, or establish a scalar codec.
- **ebusd community TSP** (`15.ctlv2.tsp`) — Community-maintained register definitions. Highest authority for register-to-name mapping where coverage exists.
- **myVaillant register map** — Value-matched mapping against myPyllant cloud API. NOT a Vaillant-published source — carries false-positive risk where multiple registers share the same value (see [Mapping Conflicts](#mapping-conflicts)).
- **VRC Explorer full group scans** — FLAGS byte verification for all groups.
