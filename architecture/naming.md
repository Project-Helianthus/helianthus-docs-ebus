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

- GraphQL object, input, enum and type names, enum tokens, roots, arguments and payload field names are snake_case and describe semantic values (`zone_room_temperature`, `zone_room_humidity`, `pump_active`). Canonical register names and the names of decoded value fields follow [Register and field names](#register-and-field-names); structural fields do not.
- Conditional schemas are described by `target` and optional hardware version bounds; the schema key `target` is outside the naming rules.

## Protocol Constants

- eBUS addresses and command bytes are referenced in hex (e.g., `0xB5`, `0x04`).
- Control symbols are named by their protocol role (`SymbolAck`, `SymbolNack`, `SymbolEscape`, `SymbolSyn`).

## Documentation page file names

Page file names, and so the published URLs, are lowercase kebab-case: lowercase
letters and digits joined by single hyphens, with the `.md` extension.
snake_case stays for API, register and code names. A rename changes neither the
directory, the headings and their anchors, nor the status that a page states for
itself, and it leaves no redirect page or alias behind.

The repository control files `README.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`CHANGELOG.md` and `SECURITY.md` are tooling entrypoints, not published page
names. They keep their conventional spelling wherever they occur.

The [page status table](page-status.json) lists every page renamed to this
form. Each row gives the page, its earlier file name, one status from the
closed set below and the sentence of the page that carries that status. The
earlier file name is documentary only; nothing reads it as a fallback.

| Status | Meaning |
|---|---|
| `implemented` | The page states that the behavior it describes is implemented. |
| `accepted contract` | The page states a documentation, wire or software contract and does not grade its own subject as Hypothesis, candidate or proposed. |
| `candidate` | The page grades its subject, or the native layout it depends on, as Hypothesis, candidate, proposed or unconfirmed. Contract wording on such a page does not promote it. |
| `historical` | The page states that it is superseded or kept as history. |
| `unknown` | The page makes no page-level status statement in its opening section. |

`python3 scripts/check_page_names.py` enforces the table: one-to-one
destinations without collisions, the exact spelling of each directory entry, no
earlier file name left in the repository, the links and anchors into the
renamed pages, and the tree indexes. Two kinds of text keep an earlier file
name: pinned provenance that pairs a path with a fixed owner commit, and the
link text on an existing References line, where only the link target follows
the rename. Each tree index ([api](../api/index.md),
[architecture](index.md), [deployment](../deployment/index.md),
[development](../development/index.md), [protocols](../protocols/index.md)) is
linked from `README.md` and lists every publishable page of its tree.
Each tree index links every page of its tree except pages that publication policy keeps out of navigation, which the status table identifies by a digest prefix of their path.

Names outside this bounded set are not converted yet: the remaining snake_case
pages under `architecture/`, the `ebus_standard` directory name, the
version-numbered directories under `docs/platform/live/` and upper-case
evidence report names. Their conversion, the work-item prefixes that the
renamed pages keep, and any further directory taxonomy remain open.

## Register and field names

These rules are a binding contract for canonical register and decoded-value
field names on every eBUS service page and fixture, then Modbus, CAN and eeBUS,
and for the corresponding value fields in GraphQL, MCP, Home Assistant, Portal
and SemReg member names. The same value has the same spelling on every surface.
Adoption is eBUS first; extending protocol vocabularies requires explicit Board
agreement. This scope is a requirement, not a claim of ecosystem compliance.

Structural, identity and provenance keys (IDs, references, timestamps, hashes,
envelope and API-schema keys), payload control bytes, method strings and MCP
tool names remain outside the register grammar. They must still use snake_case.
The conditional-schema key `target` is structural. A name whose meaning remains
open is retained and recorded as non-compliant, as described below. This contract
does not rename existing registers, fields, metrics or consumer APIs.

### A name reads as a sentence

The value of a register reads as "[subject] [predicate] [object], [in these circumstances]", with attributes on the nouns. This is the reading order; the order of the words inside the name is given in [Order of the parts](#order-of-the-parts). `heating_flow_temperature_setpoint_maximum` reads as "for heating, the device's setpoint for the flow temperature, maximum".

| Part | Question | Content |
|---|---|---|
| Subject | About what? | The component, medium or sub-entity: `compressor`, `fan`, `pump`, `burner`, `valve`, `refrigerant`, `zone`, `circuit`, `cylinder`. Implicit when it is the device itself: a device never names itself, so no device class and no `system_` appear on a controller's own registers. An attached heat generator is a subject on a controller's registers: `heat_generator`, or its kind `boiler` or `heat_pump` when the register is specific to that kind. |
| Predicate | What is stated? | The value class, from the closed list in [Predicates](#predicates). A measured value has no predicate word. |
| Feature | Which maker-defined function? | A documented maker vocabulary term when a generic term does not describe the function. It is described only as an observed Vaillant definition, not an inferred native meaning. The value-class predicate follows the feature. |
| Object | What is measured, counted, timed or regulated? | A quantity (`temperature`, `pressure`, `speed`, `power`, `energy`, `current`, `flow_rate`), an event (`start`, `switch`), an activity (`operating`, `on`, `off`), a point in time (`date`, `clock_time`, `weekday`) or what a text holds (`name`, `phone_number`). |
| Attribute | Which one? | Instance index (`fan_1`), kind (`external_pump`, `circulation_pump`, `environmental_power`), side (`low_pressure`, `high_pressure`; a side term that contains the object word supplies the object, as in `refrigerant_low_pressure`), bound (`minimum`, `maximum`; always in the bound slot at the end of the name), span boundary (`start`, `end`, before `date`, `clock_time` or `weekday`). |
| Circumstance | In which context? | Purpose (`heating`, `cooling`, `dhw`, `ventilation`, `solar`); place (`flow`, `return`, `inlet`, `outlet`, `room`, `outdoor`, `source`, `building`, `top`, `bottom`); period (`total`, `remaining`, `daily`, `current_month`, `previous_month`, `current_year`, `previous_year`); manner (`fine`, `average`); condition (`at_…`). |

### Order of the parts

`[purpose]_[attribute][subject][index]_[place]_[attribute][object]_[feature]_[predicate]_[bound]_[period]_[manner]_[at_condition]`

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

The rules are a contract enforced by review and blocking mechanical checks.
Mechanical acceptance does not establish semantic correctness. A maker-derived
name with unresolved meaning, polarity, value class, value table or writability
stays provisional, with its exact spelling and `open_question`. It is listed as
non-compliant in [the provisional-name follow-up](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/573).
No invented replacement or placeholder replaces a documented maker term.
Existing mechanical debt is recorded separately with the violated rule and a
follow-up. Neither category permits debt growth or waives pre-release cleanup.
A provisional spelling is retained even when it cannot yet be decomposed; this
is explicit non-compliance, not proof of qualification. `Proven`, `Hypothesis`
and `Unknown` describe evidence status independently of naming compliance or
native write qualification. Native protocol facts require the owning public
wire contract first. Nothing here infers writable behavior or hidden meaning.

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

### Correspondence and enforcement

The `previous_name` column records documentary correspondence with the earlier
canonical spelling. It is not a runtime alias, fallback key, or migration step.

The vocabulary remains in [register-name-vocabulary.csv](fixtures/register-name-vocabulary.csv).
A future shared vocabulary home requires an explicit decision; no relocation is
claimed here. Rule changes require explicit Board agreement. The existing
[surface parser](../scripts/check_register_names.py) continues its mechanical
checks. The blocking [decomposition guard](../scripts/check_name_decomposition.py)
checks the B524 map's primary register tables and the checked example tables on
this page against [maintained decompositions](../scripts/name-decomposition.json).
It reconstructs spellings from ordered vocabulary roles, verifies the predicate
against the value class and rejects inventory drift, duplicate selectors and
unknown acceptance entries. Existing debt retains its exact spelling, violated
rule or documented open question and follow-up; acceptance is never generated
from current names during CI. Unknown provisional names retain their questions.

The Docs Checks local gate ([`scripts/ci_local.sh`](../scripts/ci_local.sh))
always runs the guard and its independent mutation tests, both in Docs CI and
locally. Coverage of other native pages and fixtures, and enforcement by each
consuming repository remain follow-up work. F52 remains open until these are covered.
The [eBUS adoption follow-up](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1151)
covers native-page adoption. Existing eBUS MCP behavior and GraphQL parity remain
unchanged. Failed admission must preserve partial last-known-good state; naming
validation grants no permission to admit unqualified values.

### Metrics

Metric vocabulary follows the same naming rules under one prefix, `helianthus`.
The unit belongs in a constant `unit` label wherever labels are possible, with
one unit per metric name. Unit suffixes are allowed only where labels cannot be
used: expvar values, library-emitted names (including `process_*` and `go_*`), or
automatic OpenTelemetry to Prometheus translation that cannot be configured
without suffixes. Each exception records why a label is unavailable; configure
translation without suffixes wherever possible. Library-owned spellings and
prefixes are documented exceptions, but the decomposition guard inventories only
`helianthus`-prefixed metrics; library-prefixed names such as `process_*` and
`go_*` are not checked by it until an enforcement child covers them. Counter `_total` and the predicate `_ratio`
remain. The [emitted metric contract](../deployment/prometheus-semantic-coverage.md)
records constant units, preserved numeric scales and measured library exceptions.
Incomplete naming coverage remains tracked in the
[metric follow-up](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1153).

### Checked examples

These synthetic examples establish spelling, not device qualification.
`special_function` names an observed Vaillant definition in the
[public B524 catalog](../protocols/vaillant/ebus-vaillant-b524-register-map.md);
a generic mode term does not distinguish this function. The `mode` predicate
states the candidate value class; native behavior remains subject to the
catalog's evidence status and open questions.
Metric examples use a constant `unit` label except the documented library case.

| Checked spelling | Kind and context |
|---|---|
| `dhw_special_function_mode` | Value; maker feature, mode enumeration |
| `circuit_unknown_9` | Provisional value; meaning and polarity remain Unknown; no replacement invented |
| `source_id` | Structural identity key |
| `observed_at` | Structural provenance key |
| `get_status` | Method string |
| `helianthus_compressor_start_count_total` | Counter; constant unit label `count` |
| `helianthus_compressor_operating_time_seconds_total` | Library-emitted counter; library cannot attach a constant unit label; seconds suffix retained |
| `helianthus_pump_ratio` | Dimensionless metric; constant unit label `ratio` |

### Open questions

Provisional register questions remain tracked in the non-compliance follow-up
above. The shared vocabulary home and all-surface enforcement remain open;
this bounded gate establishes neither whole-ecosystem compliance nor closure of
F52. Native row changes and per-repository gates require separate children.

GraphQL built-in scalars and protocol introspection identifiers retain their protocol spelling. Reflected SemReg envelopes recursively retain their snake_case JSON tags. Historical correspondence is documentary only and supplies no runtime fallback. Provisional value names retain an explicit open question; syntax compliance alone establishes no native meaning or qualification.
