# Heat-pump B509 codec dictionary boundaries

Start with the public native [B509 register-access contract](../protocols/vaillant/ebus-vaillant-B509.md)
and [heat-pump register map](../protocols/vaillant/ebus-vaillant-B509-heatpump-register-map.md).
Those pages establish the public candidate context and wire-order spelling;
software metadata below supplies no additional native proof. Only the finite
associations in this page are in scope. The [synthetic example package](fixtures/am14_b509_heatpump_codec_dictionary.json)
and [focused contract test](../tests/test_am14_b509_heatpump_codec_dictionary.py)
exercise a local example seam, without importing a production implementation.
AM13 is the registry prerequisite; its implementation is not verified here.

## Grades and limits

The finite codec-declaration associations are **Hypothesis**. Exact lookup,
validation, detached ownership and fail-closed metadata admission are **Proven**
software requirements of this contract. A passing synthetic example demonstrates
those local requirements only. Native support, physical qualification, presence,
freshness, execution, effects, persistence and delivery remain **Unknown**.
Unknown native properties are independent of invocation and qualification.
Calling the accessor does not promote a row's Hypothesis grade or qualify a device.

Codec labels are literal declarations, never executable converters.
Unknown labels and compound alternatives remain opaque strings. No width,
endian rule, enum mapping or sentinel is inferred from a label; unprovided
properties remain absent, rather than null or zero. The E201 unsigned-byte and
E401 signed declarations are retained as literal qualifiers, not decoding rules.
No numeric value is returned. E201 declares 100 W per unsigned byte, whereas
BA00 has the different label power and declared unit kW; no conversion API is added.
BA00 and E201 stay separate even though both names are environmental_power.

BC00 environmental versus delivered yield remains unresolved.
2401 ratio unit remains Unknown.
E901 pressure unit remains Unknown.
8000 integral codec and unit remain Unknown.
No unit is supplied for the slope declaration either. Candidate quantity names
remain separate from the codec and unit. They are not evidence of native support.
3F00, BB00, 1400 and E400 never acquire boiler semantics.
The heat_pump_interface_unit family has no entry in this dictionary.

## Accessor contract

The language-neutral operations are `metadata() -> rows` and
`lookup(key) -> row | no-row`, with a validation seam over supplied synthetic
rows. These names describe this page's example interface, not an imported or
promised external signature. The companion embedded accessor supplies the fixed
28 rows; this page adds neither an implementation nor an executable converter.
No pending schema/API is imported and no provider is registered.
Existing generic name correspondence and identity shapes are separate.
Generic raw access and discovery are unchanged.
eBUS MCP compatibility and GraphQL parity are unchanged.
Nothing is stable before Helianthus 1.0.
There is no new major or experimental namespace, runtime caller, transmit route,
scan-default change, active executor, authorization gate or automatic native qualification.
Any later roadmap expansion belongs to 0.11 and is outside this contract.

`key` is exactly the seven-field object shown in the formal contract. Family,
variant and direction are nonempty case-sensitive strings. Primary, secondary
and operation are integer bytes in 0..255; Boolean, float and string values are
not integer bytes. Selectors are strings of exactly four uppercase hex digits,
representing the literal ordered pair of bytes, first byte first. D000 means
D0 followed by 00; E201 means E2 followed by 01. No numeric address conversion
or byte swap occurs. The second selector byte is not interpreted as a page.

The selected variant is explicitly direct-symbolic-candidate.
No runtime device inference occurs.
Every row denotes read access under explicit B509 OP0D candidate selection;
`direction=request` selects that read request's metadata, while `positive`
is a distinct unmatched direction. This direction token does not associate a
response or supply a decoder. B5/09 is decimal primary=181, secondary=9;
OP0D is operation=13. No OP0E write row or OP29 alternate is implied.

A complete well-formed key with unknown family, variant, direction, service,
operation or selector returns no-row (JSON null), without a fallback. A missing
key field is malformed, distinct from an explicit zero byte or selector 0000,
which is well formed and unmatched here. Extra fields, null, bad kinds, byte
range errors and malformed selectors also fail validation; no partial key is
admitted. In the Python example seam a malformed key raises ValueError.

Each row contains exactly key, quantity, codec, grade and conflicts. Quantity is
a nonempty canonical name. Codec contains a required nonempty declaration string,
an optional nonempty unit string and optional qualifiers (a list of nonempty
literal strings). Conflicts is a required list of nonempty strings and may be
empty. Grade is always Hypothesis. Extra row/codec fields, missing required
fields, nulls, wrong kinds and duplicate complete keys are rejected atomically
with ValueError by the owned validation seam. Distinct names are not required;
distinct complete keys are. A failed catalog validation publishes no partial
replacement and leaves any caller-owned last-known-good catalog untouched.
The seam can inject isolated well-formed controls, including an unknown codec
or another synthetic family, to test exactness; it cannot extend the embedded
finite dictionary. The finite row set is checked independently below.

Inputs to the seam are already structured objects; no new wire parser or
external JSON ingestion API is defined. Metadata enumeration and lookup return
deep independent data, including nested key, codec qualifiers and conflict lists.
Mutating constructor input, any result or an enumeration cannot affect another
result or a later call. No shared mutable backing data is exposed.

## Finite metadata

All rows share the complete selected key except for the ordered selector. All
associations carry Hypothesis and read access. In this table absent means the
field is omitted in JSON, not an empty string, zero, null or inferred unit.
There are exactly 28 entries; none is an interface-unit entry.

| Selector | Quantity | Codec declaration | Unit | Qualifiers | Conflicts |
|---|---|---|---|---|---|
| D000 | heat_pump_status | hpstatus enum | absent | absent | none |
| BC00 | environmental_energy_yield_total | energy4 | kWh | absent | environmental versus delivered yield unresolved |
| BA00 | environmental_power | power | kW | absent | none |
| BB00 | environmental_power_ratio | percent0 | % | absent | none |
| 8D00 | refrigerant_superheat | temp | K delta | absent | none |
| 8E00 | refrigerant_subcooling | temp | K delta | absent | none |
| 0F00 | source_inlet_temperature | tempsensor | C | absent | none |
| 1400 | refrigerant_high_pressure | sensor | bar | absent | none |
| 1500 | refrigerant_low_pressure | sensor | bar | absent | none |
| E400 | compressor_state | UCH enum | absent | absent | none |
| E900 | compressor_control_state | UCH enum | absent | absent | none |
| E600 | compressor_minimum_on_duration | seconds | s | absent | none |
| E700 | compressor_minimum_off_duration | seconds | s | absent | none |
| E800 | compressor_minimum_start_interval | seconds | s | absent | none |
| A800 | compressor_dhw_start_count | counter | count | absent | none |
| B400 | compressor_high_pressure_cutout_count | counter | count | absent | none |
| CE01 | defrost_active | yesno | bool | absent | none |
| 5701 | phase_order_status | phaseok enum | absent | absent | none |
| 8800 | phase_status_flags | phase flags (bitmask) | absent | absent | none |
| 3F00 | inrush_current_limiter_output_active | on/off | absent | absent | none |
| A901 | noise_reduction_active | yesno | bool | absent | none |
| 2401 | noise_reduction_factor | percent0 | absent | absent | ratio unit Unknown |
| E201 | environmental_power | UCH | 100W units | 100 W per unsigned byte | none |
| E301 | bivalent_mode | UCH enum | absent | absent | none |
| E401 | source_temperature_limit_at_maximum_flow | SCH | C | signed | none |
| E501 | source_temperature_limit_slope | UCH (slope) | absent | absent | none |
| E901 | refrigerant_low_pressure_maximum | ULG | absent | absent | pressure unit Unknown |
| 8000 | compressor_energy_integral | value (unknown) | absent | absent | integral codec and unit Unknown |

## Formal software contract

The following local JSON fixes the metadata selection, grades and boundaries;
it is not a pending registry or gateway schema. `selected.selector` is a valid
control, not a default supplied for a missing key.

```json
{
  "key_fields": [
    "target_family",
    "variant",
    "primary",
    "secondary",
    "operation",
    "direction",
    "selector"
  ],
  "selected": {
    "target_family": "heat_pump",
    "variant": "direct-symbolic-candidate",
    "primary": 181,
    "secondary": 9,
    "operation": 13,
    "direction": "request",
    "selector": "D000"
  },
  "access": "read",
  "row_count": 28,
  "selector": "two ordered bytes as four uppercase hex digits",
  "software_grade": "Proven",
  "association_grade": "Hypothesis",
  "qualification": false,
  "unknown": [
    "native_support",
    "presence",
    "freshness",
    "execution",
    "effects",
    "persistence",
    "delivery",
    "physical_qualification"
  ],
  "absent_properties": [
    "width",
    "endian",
    "mapping",
    "sentinel",
    "converter"
  ],
  "no_row": null,
  "malformed": "ValueError",
  "copy_policy": "deep independent",
  "provider_registration": false,
  "generic_raw_access": "unchanged",
  "discovery": "unchanged",
  "mcp": "unchanged",
  "graphql": "unchanged"
}
```

## Synthetic results and partial state

The example-only envelope accepts a dictionary, key, opaque raw-field object
and caller-supplied last_known_good object. It returns exactly raw,
last_known_good, row, error and qualified=false. Raw and last_known_good are
deep detached copies; row is a detached match or null. Error is null on a
well-formed miss, or malformed-key when the example catches ValueError. No
value, unit, status, success or freshness is manufactured from the raw object.

Partial failure keeps raw bytes, independently useful fields and last-known-good state.
Raw fields may be absent, empty, zero-bearing, malformed or have unknown extra
names; they are preserved verbatim, without a decoding attempt. The partial-raw
case retains payload=[0], independent=[42], and unresolved=[] together. Every
case retains last_known_good.independent={raw:[42],grade:Unknown}; retaining it
does not assert freshness and does not overwrite it with missing or zero data.
The example envelope admits no native value and changes no shared state.
A failed dictionary construction likewise cannot replace caller-owned prior
state. This example envelope is not a new runtime cache or API requirement.

Each table row is repeated in the package with the exact key, raw fields,
last-known-good object and expected row selector/error. D000, BA00 and E201 in
Outcome mean metadata matches; no-row and malformed-key admit no metadata.
These synthetic arrays are fabricated test bytes, not captures or device observations.

| Case | Key change from D000 | Raw fields | Outcome |
|---|---|---|---|
| match | none | {"independent":[42],"payload":[0,17]} | D000 |
| same-name-ba | selector=BA00 | {"independent":[42],"payload":[0,17]} | BA00 |
| same-name-e2 | selector=E201 | {"independent":[42],"payload":[0,17]} | E201 |
| unknown-family | target_family=unknown | {"independent":[42],"payload":[0,17]} | no-row |
| interface-family | target_family=heat_pump_interface_unit | {"independent":[42],"payload":[0,17]} | no-row |
| other-variant | variant=other-candidate | {"independent":[42],"payload":[0,17]} | no-row |
| wrong-primary | primary=0 | {"independent":[42],"payload":[0,17]} | no-row |
| wrong-secondary | secondary=0 | {"independent":[42],"payload":[0,17]} | no-row |
| op0e | operation=14 | {"independent":[42],"payload":[0,17]} | no-row |
| op29 | operation=41 | {"independent":[42],"payload":[0,17]} | no-row |
| positive | direction=positive | {"independent":[42],"payload":[0,17]} | no-row |
| reversed | selector=00D0 | {"independent":[42],"payload":[0,17]} | no-row |
| first-byte | selector=D100 | {"independent":[42],"payload":[0,17]} | no-row |
| second-byte | selector=D001 | {"independent":[42],"payload":[0,17]} | no-row |
| zero-selector | selector=0000 | {"independent":[42],"payload":[0,17]} | no-row |
| missing-selector | selector=absent | {"independent":[42],"payload":[0,17]} | malformed-key |
| missing-operation | operation=absent | {"independent":[42],"payload":[0,17]} | malformed-key |
| zero-operation | operation=0 | {"independent":[42],"payload":[0,17]} | no-row |
| extra-key | extra=0 | {"independent":[42],"payload":[0,17]} | malformed-key |
| malformed-selector | selector=D0 | {"independent":[42],"payload":[0,17]} | malformed-key |
| raw-absent | none | {"independent":[42]} | D000 |
| raw-empty | none | {"independent":[42],"payload":[]} | D000 |
| raw-zero | none | {"independent":[42],"payload":[0]} | D000 |
| partial-raw | none | {"independent":[42],"payload":[0],"unresolved":[]} | D000 |

The focused standard-library unittest asserts the exact finite tuple set,
every table cell, independent key arithmetic, all cases, grades, validation,
unknown labels and nested ownership. It separately varies family, variant,
primary, secondary, operation, direction, both selector bytes, key presence and
kind, and metadata field presence/kind. The read request is a valid control;
positive, OP0E, OP29, reversed bytes and the interface-unit family never inherit it.
Unknown labels remain metadata-only even in injected controls.

Focused offline checks establish only this page/example software contract.
Independent committed-change review, full repository CI, full Gate D,
publication checks and applicable transport classification remain later ship
requirements. This page does not claim production implementation testing,
automatic qualification, transport smoke results or physical support.
