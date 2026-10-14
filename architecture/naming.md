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

These rules describe the intended form of every canonical register name and every canonical name of a value field decoded from a register or telegram, documented in this repository. Structural, identity and provenance fields (identifiers, references, timestamps, hashes, envelope and API-schema keys) and the control bytes of a payload (selector, block-number, transmission-control, reply-status and reserved bytes) are outside these rules, as are method strings and the conditional-schema key `target`. A canonical name within this scope that cannot yet satisfy the rules is kept and tracked as non-compliant (see [Unknown meaning](#unknown-meaning)); it is not treated as a defect of the catalog. Until Project-Helianthus/helianthus-docs-ebus#560 is merged, canonical names on the eBUS surfaces that predate this section may not conform; that issue renames them. Canonical names on other surfaces that predate this section are renamed in later issues. Every canonical name added or changed from now on follows these rules wherever its meaning is established. Vendor, application and community names are correspondence annotations only; a canonical name never copies one of them.

### A name reads as a sentence

The value of a register reads as "[subject] [predicate] [object], [in these circumstances]", with attributes on the nouns. This is the reading order; the order of the words inside the name is given in [Order of the parts](#order-of-the-parts). `heating_flow_temperature_setpoint_maximum` reads as "for heating, the device's setpoint for the flow temperature, maximum".

| Part | Question | Content |
|---|---|---|
| Subject | About what? | The component, medium or sub-entity: `compressor`, `fan`, `pump`, `burner`, `valve`, `refrigerant`, `zone`, `circuit`, `cylinder`. Implicit when it is the device itself: a device never names itself, so no device class and no `system_` appear on a controller's own registers. An attached heat generator is a subject on a controller's registers: `heat_generator`, or its kind `boiler` or `heat_pump` when the register is specific to that kind. |
| Predicate | What is stated? | The value class, from the closed list in [Predicates](#predicates). A measured value has no predicate word. |
| Object | What is measured, counted, timed or regulated? | A quantity (`temperature`, `pressure`, `speed`, `power`, `energy`, `current`, `flow_rate`), an event (`start`, `switch`), an activity (`operating`, `on`, `off`), a point in time (`date`, `clock_time`, `weekday`) or what a text holds (`name`, `phone_number`). |
| Attribute | Which one? | Instance index (`fan_1`), kind (`external_pump`, `circulation_pump`, `environmental_power`), side (`low_pressure`, `high_pressure`; a side term that contains the object word supplies the object, as in `refrigerant_low_pressure`), bound (`minimum`, `maximum`; always in the bound slot at the end of the name), span boundary (`start`, `end`, before `date`, `clock_time` or `weekday`). |
| Circumstance | In which context? | Purpose (`heating`, `cooling`, `dhw`, `ventilation`, `solar`); place (`flow`, `return`, `inlet`, `outlet`, `room`, `outdoor`, `source`, `building`, `top`, `bottom`); period (`total`, `remaining`, `daily`, `current_month`, `previous_month`, `current_year`, `previous_year`); manner (`fine`, `average`); condition (`at_…`). |

### Order of the parts

`[purpose]_[attribute][subject][index]_[place]_[attribute][object]_[predicate]_[bound]_[period]_[manner]_[at_condition]`

- Parts that add no information are omitted.
- Bounds, periods and manner go at the end, in that order; a condition `at_…` closes the name, and only vocabulary terms may follow `at_`. Inside `at_…` a bound precedes its object (`at_maximum_flow_rate`).
- A word is one vocabulary term. A compound term is exactly a multi-token entry of the vocabulary file (`flow_rate`, `diverter_valve`, `current_month`), matched longest first; it and a whole `at_…` condition each count as one word. A name has at most six words.
- An index is an unpadded decimal number directly after the subject, or after the object when there is no subject; it does not count as a word. Elements of an array field are told apart by the field path, not by an index.
- A part of a date or a clock time (`year`, `month`, `day`, `hour`, `minute`, `second`) follows its object directly, before any predicate (`holiday_end_clock_time_hour`); so does a part of a text split across fields (`prefix`, `suffix`; `zone_name_prefix`).
- A name with the placeholder `unknown` follows the form given in [Unknown meaning](#unknown-meaning).
- A command name follows the form given in [Operations and commands](#operations-and-commands); its nested target counts as one word, and the six-word limit applies to the whole name.

| Name | Subject | Place | Attribute and object | Predicate | End |
|---|---|---|---|---|---|
| `heating_flow_temperature_setpoint_maximum` | (implicit) | `flow` | `temperature` | `setpoint` | `maximum` |
| `compressor_start_count_total` | `compressor` | | `start` | `count` | `total` |
| `compressor_on_time_minimum` | `compressor` | | `on` | `time` | `minimum` |
| `compressor_inlet_temperature` | `compressor` | `inlet` | `temperature` | (none) | |
| `environmental_power_fine` | (implicit) | | `environmental` `power` | (none) | `fine` |
| `source_temperature_limit_at_maximum_flow_rate` | (implicit) | `source` | `temperature` | `limit` | `at_maximum_flow_rate` |
| `heat_pump_flow_temperature_setpoint_maximum` | `heat_pump` | `flow` | `temperature` | `setpoint` | `maximum` |
| `outdoor_temperature_daily_average` | (implicit) | `outdoor` | `temperature` | (none) | `daily` `average` |
| `holiday_start_date` | (implicit) | | `holiday` `start` `date` | (none) | |

### Predicates

| Predicate | Value | Typically provided by |
|---|---|---|
| (none) | The measured or computed current value of a physical quantity. | the device |
| `setpoint` | The value the device regulates towards. | user, installer or controller |
| `limit` | A boundary the device enforces without regulating towards it. It takes a bound when its direction is established (`flow_temperature_limit_maximum`); `limit` alone states that the direction is not established. | configuration |
| `offset` | A value added to a reference. | configuration |
| `hysteresis` | A switching band. | configuration |
| `active` | Boolean: the subject performs its function now. | the device |
| `enabled` | Boolean: the function is permitted or configured on. | user or installer |
| `demand` | Boolean: the function is requested. | device or controller |
| `connected` | Boolean: the communication link to the subject is up. | the device |
| `ready` | Boolean: the subject can perform its function as soon as it is requested. | the device |
| `available` | Boolean: the function or component is present and usable in this installation; distinct from `enabled` (permitted) and from `status` (an enumeration). | the device |
| `ok`, `fault` | Health booleans; see [Booleans](#booleans). | the device |
| `state` | Closed enumeration: the position of the subject in its own operating sequence; it changes by itself. | the device |
| `status` | Enumeration of health or availability (for example ok, warning, fault, unavailable); distinct from `state`. | the device |
| `mode` | Enumeration: a choice among fixed alternatives, kept until it is changed. | user, installer or controller |
| `type` | Static enumeration: what kind of thing the subject is. | installation |
| `code` | A number whose meaning comes from an external code list (error codes, state numbers). | the device |
| `bitfield` | The value class, not the wire data type: several booleans in one value; each bit has its own boolean name in the per-bit description of the register. | the device |
| `count` | Number of occurrences of the object event. With a subject and no object, the number of such subjects (`boiler_count`); with the bound `maximum`, the supported number of them (`circuit_count_maximum`). | the device |
| `time` | After an activity, how long it lasts, accumulated or configured; after an event, the time between two occurrences; with the period `remaining`, the time until the next occurrence or the end (`service_time_remaining`). | device or configuration |
| `level`, `position`, `ratio`, `factor` | A graded amount without its own physical quantity; an actuator position; dimensionless quantities. | |
| `command` | Writing the register triggers the action named before it; see [Operations and commands](#operations-and-commands). | user, installer or controller |

The list is closed. A predicate is added to this table by explicit agreement before any name uses it.

A bound after `setpoint`, `time`, `count`, `offset` or `hysteresis` is the allowed range of that configured value, except that `maximum` after the count of a subject (`circuit_count_maximum`) is the supported number of such subjects. A bound after a measured value (no predicate word) is a measured extreme. Every lifetime accumulation (energy, a count, an accumulated time) carries the period `total`; a configured time or count does not.

### Booleans

Value 1 (true) always means the name is true. The predicate word is chosen from what the device sends: `…_ok` when 1 means normal, `…_fault` when 1 means a problem. A decoder never inverts a value to fit a preferred word. Encodings other than 0 and 1 are mapped by the codec; the name states what "true" means.

### Vocabulary

- `snake_case`, lowercase ASCII, English words, singular.
- Abbreviations only from a closed list of standard terms: `dhw` (domestic hot water), `pv` (photovoltaic), `rtc` (real-time clock) and `eeprom` (electrically erasable non-volatile memory). Additions require explicit agreement.
- Durations always use the noun `time`, with the kind of activity before it (`operating_time_total`, `on_time_minimum`).
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
| `time` | duration, hours (as a duration), interval |
| `external` | ext |

- A table entry names the general concept. A narrower meaning, once established, is kept through a purpose (`heating`, `dhw`, `solar`), an attribute (index, kind) or a place (`top`, `bottom`), never through the forbidden word. Where two registers of one device with different meanings would get the same name and no vocabulary term separates them, both names stay provisional (see [Unknown meaning](#unknown-meaning)) and each `open_question` states the narrower meaning.
- A calendar date is the object `date`, a time of day `clock_time` and a day of the week `weekday`; the start and end of a span are attributes before them (`holiday_start_date`, `holiday_end_clock_time`). When a date or a clock time is split across fields, each field adds its part after the object: `year`, `month`, `day`, `hour`, `minute` or `second` (`holiday_end_clock_time_hour`). These parts are components of a date or a time of day, not units.
- A text value is named by what it holds (`zone_name`, `installer_phone_number`) with no predicate word; that it is text is metadata. A text split across two fields adds `prefix` to the first and `suffix` to the second, after the object (`installer_name_prefix`, `installer_name_suffix`). An access code is the compound term `access_code` (`installer_access_code`), not the predicate `code`.
- An average is the manner `average` after its period (`outdoor_temperature_daily_average`); `daily` is a rolling period of 24 hours, and the calendar periods are `current_month`, `previous_month`, `current_year` and `previous_year`.
- No metadata in a name: unit, scale, data type, access, the device's own class, vendor, model, product name, service-menu code, operation, selector, API prefix. Units are documented outside the name, in the register documentation.
- No redundancy: nothing the purpose or subject already implies (`dhw_flow_rate`, not `dhw_water_flow_rate`).

### Unknown meaning

These naming rules describe the intended form of a name. They are guidance, not a contract enforced by review or CI: the decomposition gate (`scripts/check_register_names.py`) checks only the mechanical form of a name (vocabulary, order of the parts, word count). A name derived from the device maker's documented term for a register states a meaning that is documented; it is not a guess. When a name cannot yet follow the intended form because its meaning, polarity, value class, value table or the writability of the register is not established, the name derived from the documented term stays, the row is provisional, its `open_question` records what is open and the candidate reading, and the name is listed as non-compliant in the tracking issue (docs-ebus #560, or a dedicated non-compliance list) until evidence settles it. A name never encodes a guess of its own: where no documented term exists, nothing is invented. A provisional name still satisfies the format and vocabulary rules.

The placeholder `unknown` is used only when no documented term exists at all for the register or field, or when the documented readings of a register conflict and confirmation on the wire has not settled them. The eleven placeholders that predate the review of #560's first pull request (`unknown_1` to `unknown_11`, among them `circuit_pump_unknown_8` and `unknown_11`) are of these two kinds: the maker's annotation names a value or an effect rather than the register, or two documented readings give opposite polarities; each `open_question` says which. It stands for the missing object and predicate, with any established purpose, subject or place before it and an index after it when one device has several such registers or one telegram several such fields (`unknown_1`, `heating_unknown_2`). The index is assigned when the register or field is first documented, is never reused and is not the selector or the field position. The vocabulary file gives `unknown` the role placeholder, so these names pass the decomposition test.

### Identity and equal names

Identity consists of the parts below; a name never merges entries with different identities.

- the device class;
- the service (the primary and secondary command bytes `PB SB`);
- the operation and the selector, where the service has them; a telegram whose payload carries the values directly after `PB SB` (for example the `07 00` date and time broadcast) has neither;
- for a decoded value field, also its message role: the request part of a telegram, the reply part of the same telegram, a broadcast, or a separate telegram that answers an earlier one;
- for a decoded value field, also its position in the payload: the byte offset and, for a packed field, the bit position and width, or a field path that encodes all of them;
- where a conditional schema applies, the schema variant (its `target` and hardware-version bounds);
- where another field of the same telegram selects which quantity a field carries, the selecting value; each reading then carries the name of its own quantity.

The same quantity always has the same name across device classes and on alternative addresses. Variants that coexist on the same device get distinct names through an attribute or a circumstance; the manner `fine`, for example, marks a finer-resolution variant of a quantity (an illustrative pair, not an established one: `environmental_power` and `environmental_power_fine`).

### Operations and commands

A row that describes an operation rather than a value (for example a symbolic read or write) is named `[verb]_[object]` (`read_symbolic_address`, `write_symbolic_address`), like a method string, and is outside the value grammar. A register whose written value triggers an action (for example a reset or an abort) is named `[target]_[action]_command`: `[target]` is the canonical name of the value or function acted on and counts as one word, and `[action]` is a vocabulary verb such as `reset`, `abort`, `start` or `stop` (`compressor_start_count_total_reset_command`).

### Correspondence annotations

When correspondence annotations disagree on a meaning, confirmation on the wire prevails over all of them; among the annotations, a Vaillant name prevails over an application name, and an application name over a community name. A disagreement that confirmation on the wire does not settle keeps the name provisional, and its `open_question` records the disagreement. Each annotation keeps its source's spelling in its own correspondence column. A service-menu code (for example `d.40`) is an annotation in its own column, `service_menu_code`, and never part of a name.

### Migration and enforcement

Every renamed fixture carries a `previous_name` column with the earlier canonical name; consumers outside this repository migrate through it. A vocabulary file (token, every role the token may take, definition, forbidden synonyms) and a test that decomposes every canonical name within the scope of these rules into its parts, assigning each token its role from its position in the order of the parts, enforce their mechanical form (vocabulary, order of the parts, word count) and nothing more; the test fails on any token without a known role and on any forbidden synonym, and runs in `./scripts/ci_local.sh`. Both are added by Project-Helianthus/helianthus-docs-ebus#560. The test covers the eBUS surfaces that issue renames and widens to each further surface when a later issue renames it.

### Open questions

No questions are open. A change to these rules goes through explicit agreement and is recorded in Project-Helianthus/helianthus-docs-ebus#560.
