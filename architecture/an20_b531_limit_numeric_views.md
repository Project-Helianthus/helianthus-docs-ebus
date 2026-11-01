# B531 local numeric results without native units

This page is the AN20 companion of AN19. It states the ab19an19 pure-helper
boundary for local numeric results of one B531 limit pair. It describes a
software API. It does not restate a native family page, it does not add native
qualification, and it has no dependency on an implementation change.

Nothing in this contract is stable before Helianthus 1.0. The names below are
not a new major namespace. This page adds no authorization gate.

The native candidate record stays on the
[B531 native candidate page](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md).
This API does not copy that record. Native unit is Unknown. A local scaled
number is not a wire-unit claim.

## Grades

Proven software contract: the helpers below are pure. Each call takes an
explicit family, variant, operation and direction, plus independently
delimited minimum and maximum raw slices. Decode only a complete unsigned
LE16 field, then multiply each by 10 into a u32. Preserve the raw bytes and
the per-field missing or malformed state. Minimum greater than maximum is
retained. FFFF has no qualified sentinel. No local slot table, target
matcher, capability cache, pending command or runtime provider is read or
written.

Hypothesis: this local projection treats the numbers as scaled power while
native units remain unresolved. A separate getter transform takes a raw u32,
uses floor(raw/10), then keeps low16 bits. The order of division and
narrowing matters; it is not saturation or round-to-nearest. An OP02
failed-read state retains a caller-supplied prior pair as last-known values
with fresh=false. A successful individual field may be exposed on its own.
That success cannot invent a complete fresh pair when the sibling fails.
Old raw fields stay on the prior, separate from the new attempt.

Proven API: return new-attempt states and prior retained states separately.
fresh-pair requires both successful fields. Both successful fields means both
attempt states are `complete`.

Unknown: exact native packet association, response feedback, physical units,
physical support, slot generation, family-specific distribution and
special-slot formulas. This page states no bus executor and no
cross-protocol consumer policy.

Grades are independent of presence, freshness and execution. A fresh pair
still has native grade Unknown. A failed field does not change the numeric,
semantic or native grade of the call.

`OP02` here is the caller token for this B531 limit helper. It is not a B524
register opcode and it does not import a B524 register namespace.

## Pure-helper boundary

The helpers allocate no shared state. They do not match a target, update a
slot table, consult a capability cache, record a pending command, or call a
runtime provider. Two calls do not share raw buffers. Each call copies the
minimum slice, the maximum slice and both prior raw slices before it
returns. A later write to a caller buffer does not change an earlier result.

Hypothetical signatures, spelled the same way throughout this page:

```text
DecodeB531LimitField(raw []byte, read string) (field B531LimitField)

ProjectB531LimitPair(input B531LimitPairInput) (result B531LimitPairResult)

GetterB531LocalCount(raw uint32) uint16
```

There is no import path. The fixture spells the same fields in snake_case.

`B531LimitPairInput` carries `Family`, `Variant`, `Operation`, `Direction`,
`MinimumRaw`, `MaximumRaw`, `MinimumRead`, `MaximumRead`, `PriorMinimum` and
`PriorMaximum`.

`B531LimitPairResult` carries `Selection` (`selection`), `AttemptMinimum`
(`attempt_minimum`), `AttemptMaximum` (`attempt_maximum`), `PriorMinimum`
(`prior_minimum`), `PriorMaximum` (`prior_maximum`), `FreshPair` (`fresh_pair`)
and `FFFFSentinel` (`ffff_sentinel`). `FFFFSentinel` is always false.
The result echoes Family, Variant, Operation and Direction from
the input. It does not replace a caller token with a default, and it does
not rewrite another operation to `OP02`.

`Family` is a device-family label. The synthetic labels in the fixture are
`heat-pump` and `controller`. They are not product models.

## Field states

`DecodeB531LimitField` copies `raw` and then applies one rule:

| Condition | State | Scaled u32 |
|---|---|---|
| `read` is `failed` | `failed` | absent |
| `read` is `succeeded` and the copy length is 0 | `missing` | absent |
| `read` is `succeeded` and the copy length is 2 | `complete` | unsigned LE16 times 10 |
| `read` is `succeeded` and the copy length is anything else | `malformed` | absent |

A failed read wins over length. Empty bytes with `read=failed` stay `failed`
and are not reclassified as `missing`. A two-byte slice with `read=failed`
keeps those raw bytes and does not gain a scaled value. A one-byte or
three-byte slice with `read=succeeded` is `malformed`; the helper does not
pad, truncate or decode a prefix.

Unsigned LE16 uses both bytes. The low byte is first. `01 00` is 1 and
scales to 10. `FF FF` is 65535 and scales to 655350. The product fits in a
u32. The helper does not clamp it.

FFFF has no qualified sentinel. The word is a complete numeric field when
the read succeeded. It is not unavailable.

Minimum greater than maximum is retained. Raw minimum 10 (`0A 00`, local
100) with raw maximum 5 (`05 00`, local 50) stays 100 then 50. The helper
does not swap the fields and does not reject the pair.

Prior fields are copied as supplied. The helper does not decode prior raw
again, does not fill a missing prior from the new attempt, and does not
replace a caller-supplied scaled value. On success, the new numbers live
only on the attempt. The prior still holds the old raw bytes and the old
values.

`FreshPair` is true only when both attempt states are `complete`. Any
`failed`, `missing` or `malformed` attempt field makes `FreshPair` false.
Retained prior limits do not make the pair fresh.

## Getter

`GetterB531LocalCount` is a Hypothesis. It takes the local u32, divides by
10 with floor, then keeps the low 16 bits: `(raw / 10) & 0xFFFF` in integer
arithmetic. Division happens before narrowing.

| Raw u32 | Result u16 | Why this value |
|---:|---:|---|
| 655360 | 0 | floor division yields 65536, then low16 is 0 |
| 655359 | 65535 | floor division yields 65535, then low16 stays 65535 |
| 19 | 1 | floor division yields 1 |

The getter grade is Hypothesis for the numeric transform, Hypothesis for the
scaled-power reading, and Unknown for the native unit.

## Rejected

The following readings are outside this contract:

- decoding a field as a signed 16-bit integer
- clamping a scaled result, or a getter quotient, to 65535
- taking the low 16 bits before dividing by 10
- rounding a quotient to the nearest integer, including mapping 19 to 2
- treating the raw word FFFF as unavailable or as a qualified sentinel
- sorting or swapping the minimum and the maximum
- marking a pair fresh because the retained prior limits are present

## Acceptance examples

The rows below use the baseline prior pair unless a cell says otherwise:
prior minimum raw `02 00`, state `complete`, scaled 20; prior maximum raw
`03 00`, state `complete`, scaled 30. Selection for these rows is family
`heat-pump`, variant `primary`, operation `OP02`, direction `request`.
Numeric grade for these pair rows is Proven. Semantic grade is Hypothesis.
Native grade is Unknown.

| id | min_read | min_raw | max_read | max_raw | min_scaled | max_scaled | fresh_pair | prior_min_scaled | prior_max_scaled |
|---|---|---|---|---|---|---|---|---|---|
| limits-ffff | succeeded | 01 00 | succeeded | FF FF | 10 | 655350 | true | 20 | 30 |
| limits-unsorted | succeeded | 0A 00 | succeeded | 05 00 | 100 | 50 | true | 20 | 30 |
| outcome-min-failed | failed | 01 00 | succeeded | FF FF | absent | 655350 | false | 20 | 30 |
| outcome-both-failed | failed | 01 00 | failed | FF FF | absent | absent | false | 20 | 30 |

`limits-ffff` has no FFFF sentinel: the maximum state is `complete`.
`limits-unsorted` keeps 100 and 50 in that order. `outcome-min-failed`
retains prior minimum 20, exposes the new maximum 655350, and is not a fresh
pair. `outcome-both-failed` retains both prior fields, 20 and 30, with
fresh=false. Attempt raw bytes of a failed field remain on the attempt.

Getter examples, each with numeric grade Hypothesis, semantic grade
Hypothesis and native grade Unknown:

| raw_u32 | result_u16 |
|---:|---:|
| 655360 | 0 |
| 655359 | 65535 |
| 19 | 1 |

The fixture varies family, variant, operation, direction, word bytes,
length, field outcome, prior state and prior value one axis at a time.
Those rows are the finite example set for the identities above. Each example
is a separate call with its own raw copies.

## Machine policy

The policy block is normative for the tokens a checker can compare. Prose
above is the same contract.

<!-- an20-policy:begin -->
```json
{
  "api": "ab19an19",
  "decode": "unsigned_le16",
  "scale": "mul10_to_u32",
  "ffff_sentinel": false,
  "min_max_order": "retain",
  "getter": "floor_div_10_then_low16",
  "fresh_pair": "both_attempt_fields_complete",
  "native_unit": "Unknown",
  "numeric_grade": "Proven",
  "semantic_grade": "Hypothesis",
  "getter_numeric_grade": "Hypothesis",
  "raw_buffers": "copied_per_call"
}
```
<!-- an20-policy:end -->
