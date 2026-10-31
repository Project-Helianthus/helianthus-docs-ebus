# B555 numeric range and contextual units

## Scope and evidence

This Vaillant-family native declaration supplements the
[B555 timer family](ebus-vaillant-b555-timer-protocol.md). B555 has service
bytes PB `B5`, SB `55`. The declarations below are **Hypothesis**, except
where explicitly **Unknown**. They are not new wire observations.
The [synthetic tuples](fixtures/ai24_b555_numeric_units.json) are public,
constructed examples; no installed device, product or firmware is qualified.

**Proven** is limited to local arithmetic under the declared representation:
an unsigned 16-bit integer divided by ten spans 0 through 6553.5 inclusive.
This does not promote the representation to a Proven native contract.
Raw bytes, the formal numeric alternative and the contextual branch remain
separate even when a replacement role is selected.

The existing family reference describes Celsius and FF-unavailable A3 bounds
for qualified conditions, and different FFFF roles in its timer-value section.
Those interpretations do not establish generic A3 units or a universal FFFF
sentinel. Its unit-code 2 candidate interpretation remains unresolved for
unqualified combinations here. Neither interpretation erases the other raw
alternative. No additional native evidence resolving those contexts is supplied.

## Declarations

Logical field descriptions below do not assert new byte positions or layouts.
No A3/A4/A5/A6 method, group/day mapping or persistence claim is extended.
For generic A3 minimum and maximum setpoints, unsigned byte FF is raw 255;
Celsius, enforcement and FF-unavailable require separately qualified conditions.
The two synthetic conditions are illustrative branches, not device variants.

| id | field | context | bits | byte_order | conversion | raw_min | raw_max | numeric_min | numeric_max | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| u16 | numeric | generic | 16 | little-endian | divide by 10 | 0 | 65535 | 0 | 6553.5 | Hypothesis |
| u16-context | numeric | synthetic replacement condition | 16 | little-endian | divide by 10 | 0 | 65535 | 0 | 6553.5 | Hypothesis |
| a3-min | A3 minimum setpoint | generic | 8 | not applicable | identity | 0 | 255 | 0 | 255 | Hypothesis |
| a3-max | A3 maximum setpoint | generic | 8 | not applicable | identity | 0 | 255 | 0 | 255 | Hypothesis |
| a3-qualified | A3 minimum setpoint | synthetic Celsius condition | 8 | not applicable | identity | 0 | 255 | 0 | 255 | Hypothesis |
| unit2 | raw numeric material | unqualified unit 2 | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |

## Interpretations

Replacement selection is confined to its own stated condition. A formal
numeric value is retained alongside it; it is not a physical setpoint claim.

| id | unit_code | unit | unit_grade | replacement_raw | replacement_role | replacement_grade |
| --- | --- | --- | --- | --- | --- | --- |
| u16 | Unknown | Unknown | Unknown | none selected | none selected | Unknown |
| u16-context | Unknown | Unknown | Unknown | 65535 | contextual replacement | Hypothesis |
| a3-min | Unknown | Unknown | Unknown | none selected | none selected | Unknown |
| a3-max | Unknown | Unknown | Unknown | none selected | none selected | Unknown |
| a3-qualified | Unknown | degrees C | Hypothesis | 255 | unavailable | Hypothesis |
| unit2 | 2 | Unknown | Unknown | none selected | none selected | Unknown |

## Synthetic tuples

Rows are ordered examples, not transactions. Raw numeric material for unit 2
is supplied as synthetic material, not decoded through an inferred width,
scale or unit. Both unit-2 byte alternatives retain Unknown conversion and
semantic value. In particular, no Celsius or fan-stage conversion is inherited.

| id | declaration | raw_bytes | raw_numeric_material | formal_numeric | contextual_branch | semantic_value | grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| zero | u16 | 00 00 | 0 | 0 | none selected | Unknown | Hypothesis |
| tenth | u16 | 01 00 | 1 | 0.1 | none selected | Unknown | Hypothesis |
| byte-order | u16 | 00 01 | 256 | 25.6 | none selected | Unknown | Hypothesis |
| maximum | u16 | FF FF | 65535 | 6553.5 | none selected | Unknown | Hypothesis |
| replacement | u16-context | FF FF | 65535 | 6553.5 | contextual replacement | Unknown | Hypothesis |
| minimum-ff | a3-min | FF | 255 | 255 | none selected | Unknown | Hypothesis |
| maximum-ff | a3-max | FF | 255 | 255 | none selected | Unknown | Hypothesis |
| qualified-ff | a3-qualified | FF | 255 | 255 | unavailable | Unknown | Hypothesis |
| unit2-one | unit2 | 01 00 | 1 | Unknown | none selected | Unknown | Unknown |
| unit2-ff | unit2 | FF FF | 65535 | Unknown | none selected | Unknown | Unknown |

## Boundaries

| claim | grade |
| --- | --- |
| physical qualification | Unknown |
| native support | Unknown |
| freshness | Unknown |
| persistence | Unknown |
| execution permission | Unknown |
| enforcement | Unknown |
| peer effects | Unknown |
| unqualified units | Unknown |
| sentinels outside their own contexts | Unknown |

Synthetic arithmetic checks establish only the declared representation and
local predicates. They confer no physical support, freshness, persistence or
execution permission. Unknowns remain Unknown; raw alternatives are retained.
