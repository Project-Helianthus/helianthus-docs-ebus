# B523 configuration and mixer conflicts

## Evidence and scope

The public [B523 native contract](ebus-vaillant-b523.md#candidate-layouts)
comes first: these layouts are unconfirmed on the wire. This focused supplement
records only candidate configuration and mixer fields. The
[synthetic tuples](fixtures/aj10_b523_config_mixer.json) are arithmetic examples,
not captures or physical qualification. Families are smaller and larger
functional-module variants; no installed member is selected.

**Hypothesis:** logical coordinates begin B5/23/operation at positions 0/1/2.
Request and positive-response extents below are logical extents, not bus frame
lengths. Mapping positive-response positions to wire bytes remains **Unknown**.
All native field declarations are individually **Hypothesis**. **Proven** in
examples means only arithmetic conditional on the candidate encoding.
Qualification remains **Unknown**, independent of grade.

## Coordinates

| OP | Variant | Direction | Field | Position | Meaning | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| 00 | smaller | request | relay-groups134/256 | 3/4 | 0 output default; 1 mixer | Hypothesis |
| 00 | smaller | request | S1..S6 | 5..10 | 0 kindA default; 1 kindB; 2 digital; other undefined-or-ignored | Hypothesis |
| 00 | smaller | request/positive | extent | 11/4 | logical only | Hypothesis |
| 04 | larger | request | R1/R7/R8;R2/R9/R10;R3/R11/R12 | 3..5 | 0 output default; 1 mixer | Hypothesis |
| 04 | larger | request/positive | extent | 13/4 | logical only | Hypothesis |
| 02 | smaller/larger | request | circuit | 3 | 0 first; 1 second; 2 third only larger; others ignored | Hypothesis |
| 02 | smaller/larger | request | mode | 4 | 0 stop/pump-off/close; 1 heating-regulation; 2 cooling-regulation; 3 pump-off/open; 4 pump-on/close; 5 pump-on/open; others ignored | Hypothesis |
| 02 | smaller/larger | request | setpoint | 5 | relevant only mode 1/2; signed i8 times 0.5 Celsius; default 0; range -64..63.5; competing raw 190 means 95 Celsius with 95 clamp | Hypothesis |
| 02 | smaller/larger | positive | feedback | 3 | raw retained; no new meaning | Hypothesis |
| 02 | smaller/larger | positive | movement | 4 | signed i8 percent; 0 stopped; -100..-1 closing; 1..100 opening; magnitude 100 maximum; outside unresolved | Hypothesis |

## Sensor flags

| OP | Variant | Direction | Sensor | Position | kindA bit | kindB bit | digital bit | PWM bit | Reserved bits | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 04 | larger | request | S1 | 6 | 0 | 1 | 2 | none | 3/7 | Hypothesis |
| 04 | larger | request | S2 | 6 | 4 | 5 | 6 | none | 3/7 | Hypothesis |
| 04 | larger | request | S3 | 7 | 0 | 1 | 2 | none | 3/7 | Hypothesis |
| 04 | larger | request | S4 | 7 | 4 | 5 | 6 | none | 3/7 | Hypothesis |
| 04 | larger | request | S5 | 8 | 0 | 1 | 2 | none | 3/7 | Hypothesis |
| 04 | larger | request | S6 | 8 | 4 | 5 | 6 | none | 3/7 | Hypothesis |
| 04 | larger | request | S7 | 9 | 0 | 1 | 2 | none | 3/7 | Hypothesis |
| 04 | larger | request | S8 | 9 | 4 | 5 | 6 | none | 3/7 | Hypothesis |
| 04 | larger | request | S9 | 10 | 0 | 1 | 2 | 3 | none | Hypothesis |
| 04 | larger | request | S10 | 10 | 4 | 5 | 6 | 7 | none | Hypothesis |
| 04 | larger | request | S11 | 11 | 0 | 1 | 2 | none | 3..7 | Hypothesis |
| 04 | larger | request | S12 | 12 | 0 | 1 | 2 | none | 3/7 | Hypothesis |
| 04 | larger | request | S13 | 12 | 4 | 5 | 6 | none | 3/7 | Hypothesis |

## Examples

| Raw | Field | Interpretations | Grade |
| --- | --- | --- | --- |
| BE | setpoint | -33 Celsius signed; separate 95 Celsius candidate; selection Unknown | Proven |
| 9C | movement | -100 closing | Proven |
| 64 | movement | 100 opening | Proven |
| 9B | movement | -101 outside named intervals | Proven |
| 65 | movement | 101 outside named intervals | Proven |

## Unknowns

| Property | Grade |
| --- | --- |
| physical adaptation | Unknown |
| selected competing interpretation | Unknown |
| support | Unknown |
| executed movement | Unknown |
| physical qualification | Unknown |
| source and destination | Unknown |
| wire response offsets | Unknown |

## Unresolved alternatives and preservation

OP04 kindA defaults true; kindB, digital and PWM default false; reserved bits
default zero. Each listed flag is independent. Two bits set must remain
representable: there is no one-hot rule. PWM exists at bits 3/7 only for S9/S10.
Other pairs reserve bits 3/7; S11 reserves bits 3..7. Preserve every raw bit,
including reserved bits. The competing nibble-code interpretation and repeated
sensor associations remain unresolved; do not select either representation.

OP02 mode 1/2 alone makes the setpoint relevant. Other modes retain its raw byte
without relevance. BE is raw 190: signed -66 times 0.5 gives -33 Celsius; the
separate candidate gives 95 Celsius with a 95 clamp. Neither selects the other.
Positive feedback is opaque raw data here. Outside the named movement intervals,
preserve the raw byte and unresolved status; do not clamp or reverse direction.

Partial data retains raw bytes and last-known-good fields, separately from
missing fields. A short or mismatched tuple establishes no complete field set;
never fill missing fields with defaults or infer support, adaptation or executed
movement. Existing relay/PWM timing and feedback tables are outside this slice.
