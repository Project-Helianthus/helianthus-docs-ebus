# B516 OP14 declared and available body extents

**Proven — software contract.** AN18 defines `ab17an17.view(context, body)`,
a pure B516 OP14 candidate-body view. The hypothetical signature is the whole
helper boundary. This page does not import companion code and does not wait
for a code change. Pair with AN17. This ordinary companion has no dependency
on the code.

The public native contract comes first:
[sub-ID 0x14 candidate](../protocols/vaillant/ebus-vaillant-B516-energy.md).
That section is **Hypothesis**, unconfirmed on the wire. This page does not
repeat that family page and does not add native qualification.
Physical reply extent, support, cache generation, cadence, runtime publication and native units stay Unknown.
See also
[open questions](../protocols/vaillant/ebus-vaillant-B516-energy.md#11-open-questions).

## Pure helper boundary

`ab17an17.view(context, body)` returns one result and performs no routing.
It accepts a preselected normalized body and does no transport adaptation.
Family, variant, operation and positive direction are explicit inputs.
The helper infers no offset, no packet association and no family.
`body` is the owned available-byte slice. Logical byte 0 is the first byte
of that slice. The helper does not search the slice for a sub-ID.

`context` is a mapping. `body` is `bytes`, `bytearray` or `memoryview`.
Any other container raises `TypeError` and yields no result.
The result deep-copies context and copies the slice before interpretation.
Caller memory and result memory are detached. Extra context keys are retained
and cannot promote native support, units, presence or physical adaptation.

The helper owns no stored last-known-good state. Callers keep that state
themselves. A partial result keeps raw bytes and every field the extents
actually cover.

## Admission

Required context fields are `family`, `variant`, `operation`, `direction`,
`declared_count` and `selection`. Admitted families are
`synthetic-power-family-a` and `synthetic-power-family-b`.
Admitted variants are `synthetic-variant-a` and `synthetic-variant-b`.
These are synthetic controls. The page admits no real device family.
Admitted operation is `OP14`. Admitted direction is the explicit token
`positive`. Admitted selection is the explicit token `preselected`.
`declared_count` is a nonnegative integer and is not a Boolean.

Any other family, variant, operation or direction is a raw-only view.
Wrong operation stays raw-only. A missing or different selection is
`missing_selection` and exposes no candidate field. A negative, non-integer
or Boolean declared count is raw-only. Missing inputs stay missing.
Raw-only and missing-selection keep the owned slice.

The normative policy below is repeated in the
[synthetic example package](fixtures/an18_b516_two_word_views.json).

```json
{
  "helper": "ab17an17.view(context, body)",
  "context_fields": [
    "family",
    "variant",
    "operation",
    "direction",
    "declared_count",
    "selection"
  ],
  "families": [
    "synthetic-power-family-a",
    "synthetic-power-family-b"
  ],
  "variants": [
    "synthetic-variant-a",
    "synthetic-variant-b"
  ],
  "operation": "OP14",
  "direction": "positive",
  "selection": "preselected",
  "declared_count": "nonnegative integer",
  "body": "owned available-byte slice",
  "transport_adaptation": false,
  "preselected_normalized_body": true,
  "extent_rule": "both",
  "status_end": 1,
  "word0_end": 5,
  "word1_end": 9,
  "two_word_minimum": 9,
  "accept_eight_byte_two_words": false,
  "declared_count_alone": false,
  "available_length_alone": false,
  "capacity_is_extent": false,
  "read_past_actual": false,
  "status_label": null,
  "status_converter": null,
  "word0_codec": "float32le",
  "word0_quantity": "candidate_power",
  "word0_unit": null,
  "word0_native_sign": "Unknown",
  "asserts_watts": false,
  "unsigned_power_conversion": false,
  "word1_label": null,
  "word1_type": "Unknown",
  "word1_scale": "Unknown",
  "word1_sign": "Unknown",
  "word1_converter": null,
  "partial_word0_without_word1": true,
  "retain_nonfinite_raw": true,
  "usable_finite_for_nonfinite": false,
  "trailing_raw": true,
  "complete_two_word_implies_complete_message": false,
  "complete_two_word_implies_successful_response": false,
  "complete_two_word_implies_presence": false,
  "physical_reply_extent": "Unknown",
  "support": "Unknown",
  "cache_generation": "Unknown",
  "cadence": "Unknown",
  "runtime_publication": "Unknown",
  "native_units": "Unknown",
  "interpretation_grade": "Hypothesis",
  "software_contract": "Proven",
  "native_grade": "Unknown"
}
```

## Declared count and available extent

**Hypothesis — candidate representation.** On an admitted view, logical body
byte 0 is an opaque status, bytes 1..4 are little-endian IEEE binary32 word0,
and bytes 5..8 are a second opaque four-byte word. Word1 type, scale and sign
are Unknown. Word0 has a candidate power interpretation. Native sign and unit
are Unknown.

Declared count, actual available extent, raw bytes and trailing bytes stay
independent. A field is available only when both the declared count and the
actual available length cover it. Status needs both values at least 1.
Word0 needs both values at least 5. Word1 needs both values at least 9.
Complete-two-word state requires both declared count>=9 and available length>=9.
Neither declared count alone nor available length alone admits a field.
Neither a larger buffer capacity nor one larger count suffices.
Eight available bytes are not two complete words.
The helper does not read past the actual available slice.
A memoryview shorter than its backing store uses the view length.

A fully available word0 may be returned as a partial candidate field when the second is incomplete.
Actual8/declared9 and actual9/declared8 are not complete-two-word.
Actual9/declared4 does not expose word0.
Every available length from 0 through 10 is paired with every declared count from 0 through 10.

Bytes `00 00 00 80 3F 01 02 03 04` with declared 9 give raw status 0,
candidate word0 1, opaque word1 `[1, 2, 3, 4]` and complete-two-word true.
Trailing bytes past the nine-byte window stay raw. The extra tail `AA` is
not a third word.

| Case | Declared | Available | Status | Word0 | Word1 | Complete |
| --- | --- | --- | --- | --- | --- | --- |
| both0 | 0 | 0 | false | false | false | false |
| both1 | 1 | 1 | true | false | false | false |
| both5 | 5 | 5 | true | true | false | false |
| actual9_declared4 | 4 | 9 | true | false | false | false |
| actual8_declared9 | 9 | 8 | true | true | false | false |
| actual9_declared8 | 8 | 9 | true | true | false | false |
| canonical | 9 | 9 | true | true | true | true |
| tail10 | 10 | 10 | true | true | true | true |

## Status, word0 and word1

Status stays unlabelled and has no converter.
Word1 stays unlabelled and has no converter.
Unknown status and word1 never acquire labels or a converter.
Word0 is never watts and is never an unsigned integer.
No conversion of negative or nonfinite bits to unsigned power.
NaN and infinities retain raw bits and have no usable finite numeric value.
A zero finite value and a negative finite value stay finite numbers.
Negative zero keeps its sign bit. A finite word0 publishes
`candidate_power` with unit null. That quantity is not a watt claim.

| Case | Word0 raw | Finite | Numeric |
| --- | --- | --- | --- |
| canonical | 00 00 80 3F | true | 1 |
| zero | 00 00 00 00 | true | 0 |
| negative_zero | 00 00 00 80 | true | -0 |
| negative | 00 00 80 BF | true | -1 |
| nan | 00 00 C0 7F | false | none |
| payload_nan | 01 00 80 7F | false | none |
| positive_infinity | 00 00 80 7F | false | none |
| negative_infinity | 00 00 80 FF | false | none |

## Result grades

The software contract is Proven on every result. Admitted interpretation
grade is Hypothesis. Raw-only interpretation grade is null.
Native grade stays Unknown on every result, including a finite word0.
Numeric grade for a finite word0 is Hypothesis. Semantic grade for the
candidate power quantity is Hypothesis. Status and word1 semantic grades
stay Unknown. These grades are not collapsed. Presence, freshness,
execution and physical qualification stay Unknown and separate from these
grades.

complete-two-word is not a complete message, a successful response, or presence.
`complete_message` and `successful_response` stay false. `presence` stays
Unknown.

The result publishes independent `status_available`, `word0_available`,
`word1_available`, `finite_numeric` and `complete_two_word`, plus `raw`,
`trailing`, `declared_count` and `available_length`.

No new major or experimental namespace is introduced. No authorization gate
is added. eBUS MCP compatibility and GraphQL parity are preserved because this
page changes no runtime interface. This helper is not an MCP tool and adds no
GraphQL field. Nothing here is stable before Helianthus 1.0.

The [focused standard-library tests](../tests/test_an18_b516_two_word_views.py)
exercise a local reference model of this prose. Expected numbers use an
independent binary32 decoding. Focused checks establish this software
contract only. Full Gate D, independent review, publication checks and
applicable transport classification remain later ship requirements.
