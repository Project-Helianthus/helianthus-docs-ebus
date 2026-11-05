# Vaillant B503 history markers, flags and feedback

## Evidence and scope

This is a focused candidate contract for the Vaillant diagnostic family, read
alongside the [B503 family reference](ebus-vaillant-B503.md). The
[synthetic field tuples](fixtures/ai08_b503_history_flags.json) preserve raw
alternatives; they are not captured telegrams. Every native interpretation below
is **Hypothesis**. **Proven** applies only to the declared synthetic representation
and its local arithmetic, never installed support. Physical qualification is
**Unknown**, independently of evidence grade.

No source, destination, direction, product, firmware or capture conditions are
asserted by these synthetic tuples. Unprovided marker, code and calendar absolute
positions remain `null`; the ordered calendar components are field-level values,
not invented packet offsets. The history code's width and byte order are
**Unknown**. OP07 word encoding does not supply those missing OP01 properties.

## Family identity

| Family | PB | SB | Grade |
|---|---|---|---|
| B503 | 0xB5 | 0x03 | Hypothesis |

## OP01 history validity

Branch on the marker before interpreting any calendar component. Marker 01 with
replacement time bytes retains the code: it must not become no-item. Other
markers, or marker 00 with a different tail, remain **Unknown** with raw data
retained. The tail below declares a no-item alternative only; it does not locate
code or time subfields within a physical reply.

| Marker | Raw condition | Candidate result | Grade |
|---|---|---|---|
| 0x00 | seven 0xFF bytes | no_item | Hypothesis |
| 0x01 | code retained, even with five 0xFF components | code_only | Hypothesis |
| 0x02 | validate each of five components first | calendar_components | Hypothesis |

Each component first selects its replacement or validity branch, then its decimal
interpretation. Values here are component integers; no physical BCD packing is
asserted. A replacement or out-of-domain component has no calendar claim; retain
the raw component and other last-known valid component values independently.

| Component | Minimum | Maximum | Replacement | Absolute position | Grade |
|---|---|---|---|---|---|
| minute | 0 | 59 | 0xFF | null | Hypothesis |
| hour | 0 | 23 | 0xFF | null | Hypothesis |
| day | 1 | 31 | 0xFF | null | Hypothesis |
| month | 1 | 12 | 0xFF | null | Hypothesis |
| year | 0 | 99 | 0xFF | null | Hypothesis |

Minute 60 and hour 24 are outside these candidate domains. Even five valid
components establish no century, timezone or full calendar validity. A single
invalid component does not erase the retained code or valid sibling components.

## Reset acceptance Boolean

This is an unsigned byte, default zero; its operation and absolute position are
`null`. It is a separate declaration from history validity and OP07 feedback.

| Raw range | Label | Default | Grade |
|---|---|---|---|
| 0 | false | 0 | Hypothesis |
| 1 | true | none | Hypothesis |
| 2..255 | unlabeled | none | Hypothesis |

## OP07 history flags

Names identify bit positions only; category meanings are **Unknown**. Preserve
reserved bits raw without adding them to the named flag set.

| Bit | Name | Grade |
|---|---|---|
| 0 | history_flag_0 | Hypothesis |
| 1 | history_flag_1 | Hypothesis |
| 2 | history_flag_2 | Hypothesis |
| 3 | history_flag_3 | Hypothesis |
| 4 | history_flag_4 | Hypothesis |
| 5..7 | reserved | Hypothesis |

## OP07 current errors

Five independent unsigned 16-bit words are little-endian: `low + 256 * high`.
The order below is logical word order, without asserting an absolute packet
offset. No code-to-text or empty-slot interpretation is supplied here.

| Word | Low byte | High byte | Decimal value | Grade |
|---|---|---|---|---|
| current_error_1 | 0x01 | 0x00 | 1 | Hypothesis |
| current_error_2 | 0x00 | 0x01 | 256 | Hypothesis |
| current_error_3 | 0x34 | 0x12 | 4660 | Hypothesis |
| current_error_4 | 0x00 | 0x00 | 0 | Hypothesis |
| current_error_5 | 0xFF | 0xFF | 65535 | Hypothesis |

## OP07 feedback

| Raw range | Result | Grade |
|---|---|---|
| 0 | rejected | Hypothesis |
| 1 | accepted | Hypothesis |
| 2..255 | rejected | Hypothesis |

Thus reset byte 2 is unlabeled while OP07 feedback byte 2 is rejected. An
accepted feedback value establishes neither physical ACK nor reset effect.

## Synthetic alternatives

| Case | Field-level raw alternative | Independent expected result |
|---|---|---|
| no_item | marker 0x00; tail FF FF FF FF FF FF FF | no_item; no code or calendar claim |
| code_only | marker 0x01; code 0x1234; components FF FF FF FF FF | code 4660 retained; no calendar claim |
| calendar | marker 0x02; components 59,23,31,12,99 | preserve 59,23,31,12,99; date validity Unknown |
| minute_outside | marker 0x02; components 60,23,31,12,99 | minute invalid; retain valid sibling components |
| hour_outside | marker 0x02; components 59,24,31,12,99 | hour invalid; retain valid sibling components |
| named_flags | flags 0x1F | named bits 0,1,2,3,4; reserved raw 0 |
| reserved_flags | flags 0xE0 | no named bits; reserved raw 224 |
| reset_two | reset acceptance 2 | unlabeled |
| feedback_two | OP07 feedback 2 | rejected |

## Conflicts and unknowns

The family reference retains a category-form candidate with proposed offsets,
BCD and a year relation, while also listing the marker meaning as unresolved.
This page preserves marker 01/code-only and marker 02/components as hypotheses;
it does not reconcile those alternatives or adopt their proposed physical
positions, century relation or local-time interpretation. The family reference's
OP06 feedback alternatives are also distinct from this reset Boolean and OP07.

**Unknown**: century, timezone, full calendar validity, copied-span adaptation,
physical ACK, reset effect, persistence, freshness, execution permission,
unprovided layouts and flag meanings, and broader family completeness. Raw
alternatives and partial valid values remain available when interpretation is
unknown; no uncertain interpretation establishes support or permission to act.
