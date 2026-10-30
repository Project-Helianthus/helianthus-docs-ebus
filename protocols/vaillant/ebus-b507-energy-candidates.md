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
OP06 capacity's candidate byte and OP08's candidate word remain Unknown here.
The existing half-percent correction is outside this supplement.

## Field boundaries

| Operation | Field | Grade | Width bits | Encoding | Conversion or role | Quantity origin |
|---|---|---|---|---|---|---|
| 06 | capacity | Hypothesis | 8 | unsigned | raw / 10 kW; raw 0..250 only | Unknown |
| 06 | cost | Hypothesis | Unknown | Unknown | mode and monetary/emissions reference dependent; converter Unknown | calculated or estimated possible |
| 06 | temperature | Hypothesis | Unknown | Unknown | converter Unknown | calculated or estimated possible |
| 08 | preference word | Hypothesis | 16 | Unknown | operation-local candidate labels only | Unknown |
| 09 | preference word | Unknown | Unknown | Unknown | raw; no transferred labels | Unknown |
| 0B | preference word | Unknown | Unknown | Unknown | raw; no transferred labels | Unknown |

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

## Operation-local words

Word notation below does not assert byte order or coordinates. OP08's labels
confer no execution permission and do not transfer to OP09, OP0B, another field,
or another family. The OP09/OP0B examples do not establish field widths.

| Operation | Raw word | Interpretation | Grade |
|---|---|---|---|
| 08 | 0000 | appliance-unavailable candidate | Hypothesis |
| 08 | FFFF | maximum-efficiency-preference | Hypothesis |
| 08 | 0001 | unmapped | Unknown |
| 09 | 0000 | raw | Unknown |
| 09 | FFFF | raw | Unknown |
| 09 | 0001 | raw | Unknown |
| 0B | 0000 | raw | Unknown |
| 0B | FFFF | raw | Unknown |
| 0B | 0001 | raw | Unknown |

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
and preference labels establish neither writable behavior nor permission to act.
