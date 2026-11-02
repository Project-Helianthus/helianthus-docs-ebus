# B555 integer64 and float64 narrowing

Software contract for the hypothetical `ab21an21` helpers `narrowInteger64` and `narrowFloat64`. This is an architecture contract for a local conversion. It is not a native family page and it does not qualify a physical timer value. Nothing in this contract is stable before Helianthus 1.0. Roadmap wording for a later binding, if any, is 0.11. This page does not open that binding and does not define an authorization gate.

This page is the ordinary companion of AN21 and does not depend on a code change. Issue 875 is a partial child of issue 736.

The public native contract is [the B555 timer protocol](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md). A candidate statement there says an A6 setpoint is multiplied by 10, truncated toward zero, and sent as its low 16 bits, with no clamp. This page does not restate that family and does not assert controller behavior.

Worked examples, raw bytes, context, and grades live in [numeric narrowing examples](fixtures/an22_b555_numeric_narrowing.json).

## Grades

**Proven** on this page means a software rule of this helper. It does not mean a native qualification.
**Hypothesis** means a resolved carrier is only a candidate local-carrier conversion.
**Unknown** means this page does not decide the question.

On a resolved result the numeric grade is Proven, the semantic grade is Hypothesis, and the native grade is Unknown. On an unresolved or malformed result every grade is Unknown. The three grades move independently. A resolved number does not make the semantic or native grade Proven.

Native grade stays Unknown on every result.

## Helper boundary

narrowInteger64 and narrowFloat64 are separate helpers. Each input keeps its own timer-kind token, device family, and software-variant token. The helper does not select a module, group, instance, day, or native constructor. Caller state is echoed and is not a selection.

No blanket generic encoder, setter, control state, or runtime registration is added. Existing A3, A4, A5, and A6 typed methods stay untouched. This helper adds no GraphQL field and no MCP tool.

A missing family stays missing and does not become a qualified native family. A missing timer-kind token stays missing. A missing software variant stays missing. An empty family string stays empty. Every result keeps native-family qualification false.

## Subjects

`narrowInteger64` takes an integer64 subject:

- The operand is a base-10 integer literal in the closed int64 range, from -9223372036854775808 through 9223372036854775807. Any other literal is malformed.
- The timer-kind token, family, and software variant are each either a supplied string or absent.
- Caller state is either absent or an opaque record. Its module, group, instance, day, constructor, and request tokens are not selections.

`narrowFloat64` takes a float64 subject with the same context fields. The operand is a finite base-10 literal. A non-numeric literal is malformed. NaN and infinity are not published literals; a caller that already holds those binary64 values still gets the unresolved results below.

## Results

Every result keeps the selected path, the supplied context, and the caller state independently. It also keeps these fields:

- Disposition is `resolved`, `unresolved`, or `malformed`.
- `carrier_low16` is an integer from 0 through 65535, or absent. `carrier_raw_le` is that value as two little-endian bytes, or absent.
- `original_literal` and `original_raw_le` keep the operand that was actually parsed. Integer raw form is eight little-endian two's-complement bytes. Float raw form is eight little-endian binary64 bytes.
- `rounded_literal` and `rounded_raw_le` exist only on the float64 path after the binary32 step. The raw form is four little-endian binary32 bytes. A nonfinite rounded value keeps those bytes and leaves the literal absent.
- `scaled_literal` is the widened binary32 value multiplied by 10, when that product is finite.
- `truncated_uint32` is present only after truncation of a supported product.
- `raw_classification` is absent on a resolved result. Otherwise it is `negative`, `nan`, `infinite`, `overflow`, or `malformed_operand`.
- Intermediate status names each stage as `applied`, `not_applied`, or `not_applicable`, and names the rejecting stage when there is one.
- Selection flags for module, group, instance, day, and native constructor stay false.

A malformed or unresolved result does not invent a carrier, a family, or a raw encoding that the operand did not have. Supplied context remains the partial last-known state.

## Integer64 path

The integer64 helper keeps the low 16 bits and does not apply a binary32 conversion. Those bits are the low 16 bits of the two's-complement int64 value. Every in-range int64 is supported, including negative values. The operand 65537 yields carrier 1. The operand -1 yields carrier 65535. The operand 0 yields carrier 0. Integer 65536 yields carrier 0. Saturation to the unsigned 16-bit range is not this helper.

The integer64 stages do not include a binary32 round-trip, a widening, a multiply by 10, or a truncation. Those names are `not_applicable` on this path. A malformed integer literal applies no low-16 step.

## Float64 path

The float64 helper converts float64 to IEEE binary32, widens that value to float64, multiplies by 10, truncates toward zero into uint32, then keeps the low 16 bits. Binary32 conversion uses roundTiesToEven. Truncation is toward zero, including for a product whose fractional part is one half. The supported domain is a finite input that does not compare less than zero and whose rounded-and-scaled product is finite and lies in 0 through 4294967295 inclusive.

Signed zero is inside that domain. Its carrier is 0, and the original sign bit stays in the raw bytes. A nonzero input whose product truncates to 0 still has carrier 0 and keeps the nonzero original.

Bypassing the binary32 round-trip for 0.7 yields the wrong carrier 7; the helper returns 6. The binary32 image of 0.7 is below 0.7. The operand 1.25 yields carrier 12, not the half-away rounding 13. The operand 6553.6 yields low 16 carrier 0. Its uint32 truncation is 65536. The same half-away mistake on 0.25 would yield 3; the helper returns 2.

Round-ties-to-even is visible around 0.7 and around 0.8. The midpoint 0.7000000178813934 rounds to the even neighbor above it and yields carrier 7. The value just below that midpoint yields carrier 6. The midpoint 0.7999999821186066 rounds to the even neighbor below it and yields carrier 7. The value just above that midpoint yields carrier 8.

The largest supported binary32 scale point in this helper is 429496704. Its uint32 truncation is 4294967040 and its carrier is 65280. The tie at 429496720 stays on that binary32 value. The next binary32 step, the finite input 429496720.00000006, and the finite input 429496729.5 are overflow. Skipping the binary32 step on 429496729.5 would fabricate a carrier; this helper does not.

Negative, NaN, infinite, and overflowing scaled operands are unresolved and have no carrier. No native behavior is asserted for those operands. Classification uses the input first:

- An input that compares less than zero is `negative`, including a tiny negative that rounds to signed zero and a finite negative whose binary32 image is infinite.
- An input NaN is `nan`.
- An input that is already infinite is `infinite`. Positive and negative infinities stay distinct in their raw bytes.
- A non-negative finite input whose rounded-and-scaled product is nonfinite, or is greater than 4294967295, is `overflow`.

The binary32, widen, and multiply stages still record what they produced. Truncation and the low-16 step are `not_applied`. The carrier stays absent, and the numeric grade stays Unknown.

Float -1.0 is the negative class and has no carrier. That result is not the integer64 carrier 65535. The integer64 and float64 paths are not merged.

## Unknowns

Units, timer-kind effects, physical persistence, availability, count materialization, and write admission stay Unknown. Timer-kind tokens are retained, not interpreted. This page does not qualify a physical timer value.

## Normative tokens

integer64-stages: low16
float64-stages: binary32-round-trip | widen-to-float64 | multiply-by-10 | truncate-toward-zero-uint32 | low16
forbidden: skip-binary32 | round-instead-of-truncate | saturate-instead-of-low16 | merge-integer-and-float | admit-negative-nonfinite-overflow
binary32-rounding: roundTiesToEven
truncation: toward-zero
low16-integer: twos-complement
missing-family: stays-missing
native-grade: Unknown
semantic-grade-resolved: Hypothesis
numeric-grade-resolved: Proven
numeric-grade-unresolved: Unknown
admit-negative: false
admit-nonfinite: false
admit-overflow: false
merge-paths: false
saturate-low16: false
skip-binary32: false
round-instead-of-truncate: false

## Examples

| id | path | operand | disposition | carrier_low16 | raw_classification | numeric | semantic | native |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| integer-zero | integer64 | 0 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| integer-65537 | integer64 | 65537 | resolved | 1 | none | Proven | Hypothesis | Unknown |
| integer-neg-one | integer64 | -1 | resolved | 65535 | none | Proven | Hypothesis | Unknown |
| integer-65536 | integer64 | 65536 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| integer-neg-65536 | integer64 | -65536 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| integer-int64-max | integer64 | 9223372036854775807 | resolved | 65535 | none | Proven | Hypothesis | Unknown |
| integer-int64-min | integer64 | -9223372036854775808 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| integer-missing-family | integer64 | 3 | resolved | 3 | none | Proven | Hypothesis | Unknown |
| integer-missing-all-context | integer64 | 65537 | resolved | 1 | none | Proven | Hypothesis | Unknown |
| integer-empty-family | integer64 | 4 | resolved | 4 | none | Proven | Hypothesis | Unknown |
| integer-malformed-fraction | integer64 | 3.5 | malformed | none | malformed_operand | Unknown | Unknown | Unknown |
| integer-malformed-above-int64 | integer64 | 9223372036854775808 | malformed | none | malformed_operand | Unknown | Unknown | Unknown |
| integer-malformed-below-int64 | integer64 | -9223372036854775809 | malformed | none | malformed_operand | Unknown | Unknown | Unknown |
| float-zero | float64 | 0.0 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| float-signed-zero | float64 | -0.0 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| float-0-7 | float64 | 0.7 | resolved | 6 | none | Proven | Hypothesis | Unknown |
| float-1-25 | float64 | 1.25 | resolved | 12 | none | Proven | Hypothesis | Unknown |
| float-6553-6 | float64 | 6553.6 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| float-0-05 | float64 | 0.05 | resolved | 0 | none | Proven | Hypothesis | Unknown |
| float-0-25 | float64 | 0.25 | resolved | 2 | none | Proven | Hypothesis | Unknown |
| float-tie-below | float64 | 0.7000000178813933 | resolved | 6 | none | Proven | Hypothesis | Unknown |
| float-tie-mid-to-even-up | float64 | 0.7000000178813934 | resolved | 7 | none | Proven | Hypothesis | Unknown |
| float-tie-above | float64 | 0.7000000178813935 | resolved | 7 | none | Proven | Hypothesis | Unknown |
| float-tie-mid-to-even-down | float64 | 0.7999999821186066 | resolved | 7 | none | Proven | Hypothesis | Unknown |
| float-tie-above-even-down | float64 | 0.7999999821186067 | resolved | 8 | none | Proven | Hypothesis | Unknown |
| float-domain-max | float64 | 429496704.0 | resolved | 65280 | none | Proven | Hypothesis | Unknown |
| float-domain-tie-inside | float64 | 429496720.0 | resolved | 65280 | none | Proven | Hypothesis | Unknown |
| float-domain-just-outside | float64 | 429496720.00000006 | unresolved | none | overflow | Unknown | Unknown | Unknown |
| float-overflow-429496729-5 | float64 | 429496729.5 | unresolved | none | overflow | Unknown | Unknown | Unknown |
| float-overflow-scaled-finite | float64 | 429496736.0 | unresolved | none | overflow | Unknown | Unknown | Unknown |
| float-overflow-binary32 | float64 | 1e39 | unresolved | none | overflow | Unknown | Unknown | Unknown |
| float-negative-0-1 | float64 | -0.1 | unresolved | none | negative | Unknown | Unknown | Unknown |
| float-negative-one | float64 | -1.0 | unresolved | none | negative | Unknown | Unknown | Unknown |
| float-negative-6553-6 | float64 | -6553.6 | unresolved | none | negative | Unknown | Unknown | Unknown |
| float-negative-tiny | float64 | -5e-324 | unresolved | none | negative | Unknown | Unknown | Unknown |
| float-negative-huge | float64 | -1e39 | unresolved | none | negative | Unknown | Unknown | Unknown |
| float-missing-timer | float64 | 1.25 | resolved | 12 | none | Proven | Hypothesis | Unknown |
| float-missing-variant | float64 | 0.7 | resolved | 6 | none | Proven | Hypothesis | Unknown |
| float-malformed-text | float64 | not-a-number | malformed | none | malformed_operand | Unknown | Unknown | Unknown |
| float-malformed-blank | float64 |  | malformed | none | malformed_operand | Unknown | Unknown | Unknown |
