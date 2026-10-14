# Naming Conventions

This document describes naming patterns used in the current implementation.

## Packages

- Package names are lowercase and single-word (`protocol`, `transport`, `registry`, `schema`).
- Internal helpers live under `internal/` and are not exported outside their module.

## Data Types

- eBUS data types are represented with uppercase identifiers that reflect common eBUS terminology:
  `DATA1b`, `DATA2c`, `DATA2b`, `EXP`, `WORD`, `BCD`, `BITFIELD`.
- Replacement values are referred to explicitly as “replacement values” and are defined per type.

## Methods

- Vendor methods use snake_case strings (e.g., `get_status`, `set_target_temp`, `get_parameters`, `get_energy_stats`).
- Method names express intent rather than transport details. Method strings are outside the register and field naming rules below.

## Schemas and Fields

- Schema field names are snake_case and describe semantic values (`flow_temperature`, `room_temperature_setpoint`, `pump_active`). Canonical register names and the names of decoded value fields follow [Register and field names](#register-and-field-names); structural fields do not.
- Conditional schemas are described by `target` and optional hardware version bounds; the schema key `target` is outside the naming rules.

## Protocol Constants

- eBUS addresses and command bytes are referenced in hex (e.g., `0xB5`, `0x04`).
- Control symbols are named by their protocol role (`SymbolAck`, `SymbolNack`, `SymbolEscape`, `SymbolSyn`).

## Register and field names

These rules are normative for every canonical register name and every canonical name of a value field decoded from a register or telegram, documented in this repository. Structural, identity and provenance fields (identifiers, references, timestamps, hashes, envelope and API-schema keys) and the control bytes of a payload (selector, block-number, transmission-control, reply-status and reserved bytes) are outside these rules, as are method strings and the conditional-schema key `target`. A canonical name within this scope that does not satisfy the rules is a defect. Until Project-Helianthus/helianthus-docs-ebus#560 is merged, canonical names on the eBUS surfaces that predate this section may not conform; that issue renames them. Canonical names on other surfaces that predate this section are renamed in later issues. Every canonical name added or changed from now on conforms. Vendor, application and community names are correspondence annotations only; a canonical name never copies one of them.

### A name reads as a sentence

The value of a register reads as "[subject] [predicate] [object], [in these circumstances]", with attributes on the nouns. This is the reading order; the order of the words inside the name is given in [Order of the parts](#order-of-the-parts). `heating_flow_temperature_setpoint_maximum` reads as "for heating, the device's setpoint for the flow temperature, maximum".

| Part | Question | Content |
|---|---|---|
| Subject | About what? | The component, medium or sub-entity: `compressor`, `fan`, `pump`, `burner`, `valve`, `refrigerant`, `zone`, `circuit`, `cylinder`. Implicit when it is the device itself: a device never names itself, so no device class and no `system_` appear on a controller's own registers. |
| Predicate | What is stated? | The value class, from the closed list in [Predicates](#predicates). A measured value has no predicate word. |
| Object | What is measured, counted, timed or regulated? | A quantity (`temperature`, `pressure`, `speed`, `power`, `energy`, `current`, `flow_rate`), an event (`start`, `switch`) or an activity (`operating`, `on`, `off`). |
| Attribute | Which one? | Instance index (`fan_1`), kind (`external_pump`, `circulation_pump`, `environmental_power`), side (`low_pressure`, `high_pressure`; a side term that contains the object word supplies the object, as in `refrigerant_low_pressure`), bound (`minimum`, `maximum`; always in the bound slot at the end of the name). |
| Circumstance | In which context? | Purpose (`heating`, `cooling`, `dhw`, `ventilation`, `solar`); place (`flow`, `return`, `inlet`, `outlet`, `room`, `outdoor`, `source`, `building`, `top`, `bottom`); period (`total`, `remaining`, `current_month`, `previous_month`, `current_year`, `previous_year`); manner (`fine`); condition (`at_…`). |

### Order of the parts

`[purpose]_[attribute][subject][index]_[place]_[attribute][object]_[predicate]_[bound]_[period]_[manner]_[at_condition]`

- Parts that add no information are omitted.
- Bounds, periods and manner go at the end, in that order; a condition `at_…` closes the name, and only vocabulary terms may follow `at_`. Inside `at_…` a bound precedes its object (`at_maximum_flow_rate`).
- A word is one vocabulary term. A compound term is exactly a multi-token entry of the vocabulary file (`flow_rate`, `diverter_valve`, `current_month`), matched longest first; it and a whole `at_…` condition each count as one word. A name has at most six words.
- An index is an unpadded decimal number directly after the subject, or after the object when there is no subject; it does not count as a word. Elements of an array field are told apart by the field path, not by an index.
- A name with the placeholder `unknown` follows the form given in [Unknown meaning](#unknown-meaning).

| Name | Subject | Place | Attribute and object | Predicate | End |
|---|---|---|---|---|---|
| `heating_flow_temperature_setpoint_maximum` | (implicit) | `flow` | `temperature` | `setpoint` | `maximum` |
| `compressor_start_count` | `compressor` | | `start` | `count` | |
| `compressor_on_time_minimum` | `compressor` | | `on` | `time` | `minimum` |
| `compressor_inlet_temperature` | `compressor` | `inlet` | `temperature` | (none) | |
| `environmental_power_fine` | (implicit) | | `environmental` `power` | (none) | `fine` |
| `source_temperature_limit_at_maximum_flow_rate` | (implicit) | `source` | `temperature` | `limit` | `at_maximum_flow_rate` |

### Predicates

| Predicate | Value | Typically provided by |
|---|---|---|
| (none) | The measured or computed current value of a physical quantity. | the device |
| `setpoint` | The value the device regulates towards. | user, installer or controller |
| `limit` | A boundary the device enforces without regulating towards it. | configuration |
| `offset` | A value added to a reference. | configuration |
| `hysteresis` | A switching band. | configuration |
| `active` | Boolean: the subject performs its function now. | the device |
| `enabled` | Boolean: the function is permitted or configured on. | user or installer |
| `demand` | Boolean: the function is requested. | device or controller |
| `ok`, `fault` | Health booleans; see [Booleans](#booleans). | the device |
| `state` | Closed enumeration: the position of the subject in its own operating sequence; it changes by itself. | the device |
| `status` | Enumeration of health or availability (for example ok, warning, fault, unavailable); distinct from `state`. | the device |
| `mode` | Enumeration: a choice among fixed alternatives, kept until it is changed. | user, installer or controller |
| `type` | Static enumeration: what kind of thing the subject is. | installation |
| `code` | A number whose meaning comes from an external code list (error codes, state numbers). | the device |
| `bitfield` | The value class, not the wire data type: several booleans in one value; each bit has its own boolean name in the per-bit description of the register. | the device |
| `count` | Number of occurrences of the object event. | the device |
| `time` | How long the object activity lasts, accumulated or configured. | device or configuration |
| `level`, `position`, `ratio`, `factor` | A graded amount without its own physical quantity; an actuator position; dimensionless quantities. | |

The list is closed. A predicate is added to this table by explicit agreement before any name uses it.

### Booleans

Value 1 (true) always means the name is true. The predicate word is chosen from what the device sends: `…_ok` when 1 means normal, `…_fault` when 1 means a problem. A decoder never inverts a value to fit a preferred word. Encodings other than 0 and 1 are mapped by the codec; the name states what "true" means.

### Vocabulary

- `snake_case`, lowercase ASCII, English words, singular.
- Abbreviations only from a closed list of standard hydronic and HVAC terms: `dhw`. Additions require explicit agreement.
- Durations always use the noun `time`, with the kind of activity before it (`operating_time`, `on_time`).
- One concept, one word:

| Use | Never |
|---|---|
| `heating` | central heating, `ch` |
| `setpoint` | desired, target, set |
| `source` | brine |
| `defrost` | deicing |
| `diverter_valve` | three-way valve |
| `fuel` | `gas`, `oil` |
| `cylinder` | buffer, tank, storage |
| `operating_mode` | operation mode |
| `enabled` (permission), `active` (run time) | allowed, activation |
| `maximum`, `minimum` | max, min |
| `time` | duration, hours, interval |
| `external` | ext |

- A table entry names the general concept. A narrower meaning, once established, is kept through a purpose (`heating`, `dhw`, `solar`), an attribute (index, kind) or a place (`top`, `bottom`), never through the forbidden word. Where two registers of one device with different meanings would get the same name and no vocabulary term separates them, both names stay provisional (see [Unknown meaning](#unknown-meaning)) and each `open_question` states the narrower meaning.
- No metadata in a name: unit, scale, data type, access, device class, vendor, model, product name, service-menu code, operation, selector, API prefix. Units are documented outside the name, in the register documentation.
- No redundancy: nothing the purpose or subject already implies (`dhw_flow_rate`, not `dhw_water_flow_rate`).

### Unknown meaning

When the meaning of a register or field is not established, its name stays provisional and its `open_question` states what is unresolved. A name never encodes a guess; a name that cannot be decomposed into the parts above is provisional. A provisional name still satisfies the format and vocabulary rules. When nothing about the value is established, the name uses the placeholder `unknown` for the missing object and predicate, with any established purpose, subject or place before it and an index after it when one device has several such registers or one telegram several such fields (`unknown_1`, `heating_unknown_2`). The index is assigned when the register or field is first documented, is never reused and is not the selector or the field position. The vocabulary file gives `unknown` the role placeholder, so these names pass the decomposition test.

### Identity and equal names

Identity consists of the parts below; a name never merges entries with different identities.

- the device class;
- the service (the primary and secondary command bytes `PB SB`);
- the operation and the selector, where the service has them; a telegram whose payload carries the values directly after `PB SB` (for example the `07 00` date and time broadcast) has neither;
- for a decoded value field, also its message role: the request part of a telegram, the reply part of the same telegram, a broadcast, or a separate telegram that answers an earlier one;
- for a decoded value field, also its position in the payload: the byte offset and, for a packed field, the bit position and width, or a field path that encodes all of them;
- where a conditional schema applies, the schema variant (its `target` and hardware-version bounds).

The same quantity always has the same name across device classes and on alternative addresses. Variants that coexist on the same device get distinct names through an attribute or a circumstance; the manner `fine`, for example, marks a finer-resolution variant of a quantity (an illustrative pair, not an established one: `environmental_power` and `environmental_power_fine`).

### Migration and enforcement

Every renamed fixture carries a `previous_name` column with the earlier canonical name; consumers outside this repository migrate through it. A vocabulary file (token, every role the token may take, definition, forbidden synonyms) and a test that decomposes every canonical name within the scope of these rules into its parts, assigning each token its role from its position in the order of the parts, enforce them; the test fails on any token without a known role and on any forbidden synonym, and runs in `./scripts/ci_local.sh`. Both are added by Project-Helianthus/helianthus-docs-ebus#560. The test covers the eBUS surfaces that issue renames and widens to each further surface when a later issue renames it.

### Open questions

- Which further abbreviations are admitted, including candidates from outside hydronics such as `pv`, `rtc` and `eeprom`.
- Which correspondence annotation prevails when annotations disagree on a meaning.
- How rows that describe an operation rather than a register (for example a symbolic read or write), and registers whose written value triggers an action (for example a reset or an abort), are named; until this is resolved such names stay provisional.
- Whether service-menu codes get their own correspondence column.
- Which boolean predicates are added for conditions that are neither run time, permission, demand nor health, such as `connected`, `ready` and `available`.
- How clock and calendar values are named (a date, a clock time, a weekday, an hour or minute part); `time` stays reserved for durations and units stay out of names.
- How the time between two occurrences of an event and a countdown to the next occurrence are named.
- Whether `limit` always takes a bound, and whether a bound after `setpoint`, `time` or `count` names the allowed range of that value while a bound without a predicate names a measured extreme.
- How a field whose quantity is selected by another field of the same telegram is named, for example one entry per reading closed by an `at_…` condition on the selecting value.
- How text values and access codes are named; `code` denotes a number from an external code list.
- How averages over a rolling period are named (for example a 24-hour outdoor temperature average).
- Whether every lifetime count and accumulated time carries the period `total`, or only when another period of the same quantity exists.
- Whether the kind of an attached heat generator (for example a boiler or a heat pump) may appear as a subject on a controller's registers, given that no device class appears in a name, or whether such pairs stay provisional.
