# B510 OP00 operating defaults: finite representation contract

This architecture contract is a partial child of #736 (Refs #916). Nothing is
stable before Helianthus 1.0. It describes the merged AL13 catalog prerequisite,
not a native profile or an actuator. No cross-repository runtime import is added.

Read the [public native B510 contract](../protocols/vaillant/ebus-vaillant-B510.md)
first. Its OP00 layouts are candidate evidence. The finite defaults below are
Hypothesis metadata from the supplied AL14 contract and the AL13 catalog, not
additional observed wire facts. Do not transplant numeric modes or positions
from a different layout into these symbolic roles.

The companion implementation is in
[the AL13 catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab48_b510_operating_defaults.go),
with [its public data](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab48_b510_operating_defaults.json)
and [its checks](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab48_b510_operating_defaults_test.go).
These are implementation corroboration, not proof of native effects. AL13 must
merge before this page; provisioning identifies that prerequisite as merged.

## API and identity

`Ab48Entries() (json.RawMessage, error)` validates the complete source array and
returns it in independent memory. `Ab48Lookup(Ab48Key) (json.RawMessage, bool,
error)` validates the complete source before looking up one exact whole row.
Successful lookup returns independent returned memory: mutating a returned
array or row must not alter the catalog or later results. The JSON key names
below correspond to exported `Ab48Key` fields with an `Ab48` prefix.

| Key axis | Go field suffix | Type | Representative value |
|---|---|---|---|
| family | Family | string | vaillant |
| variant | Variant | string | B510 |
| primary | Primary | uint8 | 181 |
| secondary | Secondary | *uint8 | 16 |
| operation | Operation | *uint8 | 0 |
| direction | Direction | string | request |
| field | Field | string | loading_pump |
| alternative | Alternative | string | none |
| group | Group | *uint8 | null |
| instance_scope | InstanceScope | string | none |
| register | Register | *uint16 | null |

All eleven axes participate in exact identity. Optional pointer axes distinguish
absent/null from explicit zero; neither is a wildcard. Required strings must
be nonempty; use `none` for non-applicable strings. Required primary must be
present even if zero. Unknown key members, malformed JSON, non-array/null
sources, missing required axes, invalid types/ranges, empty required strings,
and duplicate identities are errors. Grade and width are row metadata, not
identity axes. Changing them cannot disambiguate a duplicate key.

Absence returns `(nil, false, nil)`; invalid source returns `(nil, false, error)`
from lookup and `(nil, error)` from entries. An invalid later row prevents an
earlier match from being admitted. This is structural validation, not a semantic
proof or qualification gate. Preserve raw bytes and independent useful fields
on partial interpretation failure. A consumer may retain partial last-known-good
state with its uncertainty, but must fail closed on new admission; no cache
policy is specified here.

## Finite claims

The companion has six entries, eleven identity axes, and three symbolic forced
contexts. The examples contain one representative key and a small scenario set,
not a second dictionary. Each row below is an independently checked declaration.

| Declaration | Value | Grade |
|---|---|---|
| catalog_entries | 6 | Proven |
| identity_axes | 11 | Proven |
| forced_contexts | 3 | Proven |
| mode_default | forced-heating | Hypothesis |
| numeric_mode_code | null | Unknown |
| modulation_default | 67 | Hypothesis |
| option_bit_defaults | 1,0,0,0,0,0,0,0 | Hypothesis |
| option_bit2 | CH_setpoint: heating -> cooling; raw unchanged | Hypothesis |
| loading_pump_domain | 0..127.5 percent; unsigned u8 / 2 | Hypothesis |
| loading_pump_default | 255.0; conflicting literal, not a byte | Hypothesis |
| raw_FF_arithmetic | FF / 2 = 127.5 | Proven |
| forced_mode_dependency | loading_pump meaning and pump_activation | Hypothesis |
| zero_degrees | stop / pump-stop | Hypothesis |
| zero_to_positive | candidate minimum 300 seconds | Hypothesis |
| execution_guarantee | false | Unknown |
| transition_enforcement | Unknown | Unknown |

The loading-pump default is not the modulation default. Keep the conflicting
literal 255.0 separate from raw FF and its arithmetic result 127.5; do not clamp
to 100, narrow the default, or truncate 255.0 into a byte. Other scalar bounds
and defaults, byte positions, mode encodings, peer acceptance and effects are
Unknown. Forced-heating, forced-DHW and forced-off are symbolic contexts only;
loading-pump meaning and pump activation within each remain Unknown.

The declared 0 -> 1 transition is one zero-to-positive example with candidate
minimum 300 seconds (five minutes). The 1 -> 2 scenario is distinct and has no
invented interval. Varying the start and end independently also gives 1 -> 1,
0 -> 0 and 0 -> 2 controls. No real timer runs. This is candidate behavior
metadata, not a timing guarantee or actuator implementation.

Hypothesis interpretation is independent of physical qualification, presence,
freshness and execution, each Unknown. Proven synthetic arithmetic and
implementation shape do not promote these dimensions. Raw bytes remain useful
when semantic interpretation is Unknown.

## Bounded examples and verification

[The synthetic examples](fixtures/al14_b510_operating_defaults.json) preserve raw
FF, separate defaults, option-bit2 context at unchanged setpoint raw values,
transition controls, and all three forced contexts. The scoped standard-library
[test](../tests/test_al14_b510_operating_defaults.py) checks declarations and
examples with independent expected values. It does not import or execute the
companion implementation, prove its lookup behavior, or establish full parity.
The companion's own checks remain necessary before claiming code results.

No eBUS MCP or GraphQL surface changes here; compatibility and parity remain
requirements for any later integration, not results of this document check.
No transmit route, polling default, automatic native qualification or write
admission is introduced. Existing OP02..06 enum tables, disable-bit rules,
local capability cache policies and full-family coverage are outside scope.
Navigation and runtime integration are carried separately. Full repository CI,
independent committed-change review and publication checks remain later gates.
