# Vaillant B523 sensor fields and status alternatives

## Evidence and scope

**Hypothesis:** these functional-module sensor declarations refine the candidate
layouts in the [B523 family reference](ebus-vaillant-B523.md#candidate-layouts).
That public native contract comes first: no candidate layout is confirmed on the
wire. The [native tuples](fixtures/ai22_b523_sensor_fields.json) are entirely
synthetic, with no device observations or installed-support evidence.

**Unknown:** source and destination, direction, firmware, physical terminal
mapping, actual response extents, and installed support. Logical coordinates
include the service prefix (`B5`, `23`, OP at 0, 1, 2). They do not establish
wire offsets or lengths. The fixture's 19-byte logical vectors are synthetic
containers, not telegrams or evidence of a 19-byte response.

All layout, branch, status, PWM and opaque declarations below are individually
**Hypothesis**. **Proven** applies only to synthetic arithmetic under those
assumptions; it does not promote the native declarations. Physical qualification
remains **Unknown**, independently of either grade. Synthetic checks confer no
freshness, persistence, physical support or execution permission.

## Occurrences

There are nineteen occurrences, identified by (OP, sensor); S1 in OP03 and S1 in
OP06 remain distinct. Both status alternatives apply to each occurrence, without
assigning either alternative to an installed family member.

| OP | Sensor | Word position | Status position | Pair bit | Grade |
| --- | --- | --- | --- | --- | --- |
| 03 | S1 | 3 | 16 | 0 | Hypothesis |
| 03 | S2 | 5 | 16 | 2 | Hypothesis |
| 03 | S3 | 7 | 16 | 4 | Hypothesis |
| 03 | S4 | 9 | 16 | 6 | Hypothesis |
| 03 | S5 | 11 | 17 | 0 | Hypothesis |
| 03 | S6 | 13 | 17 | 2 | Hypothesis |
| 06 | S1 | 3 | 17 | 0 | Hypothesis |
| 06 | S2 | 5 | 17 | 2 | Hypothesis |
| 06 | S3 | 7 | 17 | 4 | Hypothesis |
| 06 | S4 | 9 | 17 | 6 | Hypothesis |
| 06 | S5 | 11 | 18 | 0 | Hypothesis |
| 06 | S6 | 13 | 18 | 2 | Hypothesis |
| 06 | S7 | 15 | 18 | 4 | Hypothesis |
| 07 | S8 | 3 | 16 | 0 | Hypothesis |
| 07 | S9 | 5 | 16 | 2 | Hypothesis |
| 07 | S10 | 7 | 16 | 4 | Hypothesis |
| 07 | S11 | 9 | 16 | 6 | Hypothesis |
| 07 | S12 | 12 | 17 | 0 | Hypothesis |
| 07 | S13 | 14 | 17 | 2 | Hypothesis |

## Branches

| Branch | Selector | Encoding | Divisor | Unit | Raw minimum | Raw maximum | Default | Scaled minimum | Scaled maximum | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| replacement | raw-u16 == 32768 | LE u16 | 1 | raw | 0 | 65535 | 32768 | 0 | 65535 | Hypothesis |
| normal | raw-u16 != 32768 | LE i16 | 16 | Celsius | -32768 | 32767 | 0 | -2048 | 2047.9375 | Hypothesis |

Selection compares the unsigned little-endian raw word with 32768 (`0x8000`,
bytes `00 80`) **before** signed conversion. Keep the original bytes and branch.
The replacement branch carries raw data and does not establish unavailable.
The normal branch's declared signed domain includes -32768, but its selector
excludes that raw encoding; the reachable normal minimum is -2047.9375 Celsius.
No clipping is declared. **Unknown:** comparing a signed selector with 32768 is
an unresolved materialization conflict; do not silently resolve it by decoding
`00 80` as -2048 Celsius. The broader family reference leaves the reserved
value's meaning unresolved, which remains unresolved here.

## Status alternatives

| Variant | 0 | 1 | 2 | 3 | Default | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| zero-valid-value | valid-value | open-circuit | closed-circuit | high-level | 0 | Hypothesis |
| zero-valid-value-or-low-level | valid-value-or-low-level | open-circuit | closed-circuit | high-level | 0 | Hypothesis |

Each two-bit pair occupies the indicated bit and its successor, least-significant
pair first. Status is separate from temperature branch selection. Zero defaults
must retain their variant-specific labels; no physical interpretation selects
one alternative over the other.

## Reserved tails

| OP | Position | First bit | Last bit | Grade |
| --- | --- | --- | --- | --- |
| 03 | 17 | 4 | 7 | Hypothesis |
| 06 | 18 | 6 | 7 | Hypothesis |
| 07 | 17 | 4 | 7 | Hypothesis |

Retain each reserved bit in the raw byte. No sensor state is claimed for those
bits; no reserved value is silently cleared or merged into a status pair.

## Auxiliary fields

| OP | Field | Position | Encoding | Divisor | Unit | Raw minimum | Raw maximum | Scaled minimum | Scaled maximum | Default | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 03 | PWM | 15 | u8 | 2 | percent | 0 | 255 | 0 | 127.5 | Unknown | Hypothesis |
| 07 | opaque | 11 | u8 | none | Unknown | 0 | 255 | Unknown | Unknown | Unknown | Hypothesis |

OP03 PWM is unsigned divided by two across the full declared raw domain:
`FF` gives 127.5 percent, not a clipped value. Its default is Unknown. OP07
position 11 is an opaque unsigned byte, distinct from S12 at 12 and S13 at 14.
Its meaning, unit, scaling and default remain Unknown.

## Word examples

| Bytes in order | Raw u16 | Branch | Value | Unit | Grade |
| --- | --- | --- | --- | --- | --- |
| 00 80 | 32768 | replacement | 32768 | raw | Proven |
| 10 00 | 16 | normal | 1 | Celsius | Proven |
| F0 FF | 65520 | normal | -1 | Celsius | Proven |

These are local predicate and arithmetic examples for every occurrence, not
captures. Each sensor word is varied alone in the fixture; each status pair is
varied alone under both alternatives, and each reserved bit is toggled alone.
The fixture also retains OP07's intermediate byte while S12 and S13 differ.
