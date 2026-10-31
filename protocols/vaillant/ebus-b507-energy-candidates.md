# B507 capacity, preference and cost candidates

This focused supplement concerns the Vaillant heat-generator family,
`PB=0xB5`, `SB=0x07`. All meanings below are candidates, not physical
qualification. No supported device or firmware range is established.

## Evidence and limits

The public [B507 native reference](ebus-vaillant-B507.md#candidate-layouts)
and its [open questions](ebus-vaillant-B507.md#open-questions) retain the wider
candidate layout and conflicting capacity readings. This supplement narrows
only the fields below; it does not resolve those conflicts through observation.
The [synthetic tuples](fixtures/aj14_b507_energy_candidates.json) are arithmetic
and scope examples, not captured telegrams or independent wire evidence.
**Proven** applies only to their synthetic construction and arithmetic, not to
candidate wire meanings. **Hypothesis** marks candidate meanings; **Unknown**
marks absent facts. Physical support remains **Unknown** independently of grade.

No source/destination, payload coordinate, direction, product or firmware is
established for these tuples. Raw values are isolated field examples, not whole
frames. Their mode labels are synthetic predicates, not native mode codes.
All fields have Unknown coordinates and actual reference. Widths other than
OP06 capacity's candidate byte remain Unknown here.
The existing half-percent correction is outside this supplement.

## Field boundaries

| Operation | Field | Grade | Width bits | Encoding | Conversion or role | Quantity origin |
|---|---|---|---|---|---|---|
| 06 | capacity | Hypothesis | 8 | unsigned | raw / 10 kW; raw 0..250 only | Unknown |
| 06 | cost | Hypothesis | Unknown | Unknown | mode and monetary/emissions reference dependent; converter Unknown | calculated or estimated possible |
| 06 | temperature | Hypothesis | Unknown | Unknown | converter Unknown | calculated or estimated possible |

For OP06 capacity, the candidate is an unsigned byte divided by 10. Negative
mode-related prose remains a separate unresolved alternative; neither signed8
reinterpretation nor multiplication by 10 is selected. Raw 251 is outside this
candidate domain and remains raw, without clipping or a candidate kW value.

| Raw capacity | Candidate kW | Domain status |
|---|---|---|
| 0 | 0 | inside |
| 1 | 0.1 | inside |
| 250 | 25 | inside |
| 251 | Unknown | outside |

## Other operations

OP08, OP09 and OP0B are outside these synthetic tuples. Their distinct candidate
request and response fields remain in the native reference; no shared preference
field is established. OP08 sentinel meanings for `0000` and `FFFF` remain
Unknown: the cited reference supplies no such mapping.

## Cost context and partial knowledge

OP06 cost depends independently on operating mode and on whether the reference
is monetary or emissions based. The actual reference, exact cost converter,
unit, field coordinates and physical support remain Unknown. Cost and
temperature may be calculated or estimated; neither is qualified as a direct
sensor measurement. No numeric cost value is justified by these examples.

| Synthetic mode | Assumed reference context | Raw cost | Numeric cost | Quantity origin | Direct measurement status |
|---|---|---|---|---|---|
| mode-a | monetary | 173 | Unknown | calculated or estimated possible | Unknown |
| mode-a | emissions | 173 | Unknown | calculated or estimated possible | Unknown |
| mode-b | monetary | 173 | Unknown | calculated or estimated possible | Unknown |
| mode-b | emissions | 173 | Unknown | calculated or estimated possible | Unknown |

The assumed contexts are independent synthetic conditions, not evidence of an
actual reference or supported mode. Preserve the raw value alongside any
candidate interpretation. An unknown or out-of-domain field does not erase
other known raw fields; partial knowledge must remain partial. Readable values
establish neither writable behavior nor permission to act.
