# B516 clock cells and raw word views

**Proven — software contract.** AN16 defines `ab15an15.view(context, fields)`, a pure
field view for caller-separated B516 OP08 clock cells and OP0D raw words. The
hypothetical signature is the whole helper boundary. This page does not import
companion code and does not wait for a code change. Pair with AN15. This
ordinary companion has no dependency on the code.

The public native contract comes first:
[other B516 sub-IDs](../protocols/vaillant/ebus-vaillant-B516-energy.md#10-other-b516-sub-ids-candidate).
That section is **Hypothesis**, unconfirmed on the wire. It names sub-ID `08`
only inside the candidate group `06..08` (displayed message: pages, number,
display fields) and sub-ID `0D` as an RF statistic parameter. It does not
establish clock-cell order, packed-decimal replacement, setpoint scaling, or
word positions. This page does not repeat that family page and does not add
native qualification.

Sub-ID `00` on the same native page is a different candidate layout. This helper
does not import it. Clock order is minute, hour, day, month, year.
There is no seconds component.

## Pure helper boundary

`ab15an15.view(context, fields)` returns one result and performs no routing.
Family, variant, operation and direction are explicit inputs. The helper infers
no offset, no packet association and no family. Bytes are admitted only as
already separated values. A five-byte clock blob and an eight-byte word blob
stay retained raw and yield no clock numerics and no word numerics.

Context and fields are mappings. Any other container raises `TypeError`. The
result deep-copies context and copies every supplied buffer before
interpretation. Caller memory and result memory are detached. Extra context
keys are retained and cannot promote native support or physical adaptation.

A failed cell does not discard its neighbors. The helper owns no stored
last-known-good state. Callers keep that state themselves. A partial result
leaves every other supplied raw field available.

## Admission

Required context fields are `family`, `variant`, `operation` and `direction`.
Each admitted value is a non-empty string. Admitted families are
`synthetic-display-family-a` and `synthetic-display-family-b`. Admitted
variants are `synthetic-variant-a` and `synthetic-variant-b`. These are
synthetic controls. The page admits no real device family. Admitted direction
is the explicit token `positive`. Admitted operations are `OP08` and `OP0D`.

Any other family, variant, operation or direction is a raw-only view, including
`OP10`. Wrong operation is a raw-only view. Raw-only keeps supplied buffers,
emits no clock numeric, no setpoint numeric and no word numeric, and does not
classify raw `FF` as replacement. Missing inputs stay missing.

The normative policy below is repeated in the
[synthetic example package](fixtures/an16_b516_clock_word_views.json).

```json
{
  "context_fields": ["family", "variant", "operation", "direction"],
  "families": ["synthetic-display-family-a", "synthetic-display-family-b"],
  "variants": ["synthetic-variant-a", "synthetic-variant-b"],
  "operations": ["OP08", "OP0D"],
  "direction": "positive",
  "clock_order": ["minute", "hour", "day", "month", "year"],
  "seconds_component": false,
  "century": false,
  "timezone": false,
  "implicit_date_completion": false,
  "replacement_byte": 255,
  "replacement_before_packed_decimal": true,
  "both_nibbles_required": true,
  "numeric_min": 0,
  "numeric_max": 99,
  "clock_numeric_of_raw_12": 12,
  "plain_byte_value_of_raw_12": 18,
  "calendar_validator": false,
  "setpoint_divisor": 2,
  "setpoint_unit": "Celsius",
  "missing_setpoint_is_zero": false,
  "message_count": 5,
  "word_count": 4,
  "word_codec": "uint16le",
  "word_unit": null,
  "word_scale": 1,
  "word_sentinel": false,
  "word_positions": "Unknown",
  "failed_cell_discards_neighbors": false,
  "native_support": "Unknown",
  "physical_adaptation": "Unknown",
  "interpretation_grade": "Hypothesis",
  "software_contract": "Proven"
}
```

## OP08 clock cells

**Hypothesis — candidate representation.** On admitted `OP08` only, each named
cell is independent and optional. Named keys are `minute`, `hour`, `day`,
`month` and `year`, in that order.
The helper adds no century, no timezone and no implicit date completion.
It adds no calendar validator. Day `31` and year
`99` stay numeric results.

Replacement is selected on raw FF before packed-decimal conversion.
Both nibbles must be decimal digits.
Numeric interpretation is 0..99. Raw `12`
decodes to twelve. The unsigned byte value eighteen is the wrong clock result.
FA and 1A are malformed decimal and retain raw.
A0 is malformed decimal and retains raw.
A one-byte buffer is the only decodable clock value. Any
other supplied object is failed and retains its buffer when it is a buffer.
Absent and null are missing. A present numeric zero is a present cell.

| Case | Cell | Raw | State | Numeric |
| --- | --- | --- | --- | --- |
| canonical | minute | 12 | present_numeric | 12 |
| canonical | hour | 23 | present_numeric | 23 |
| canonical | day | 31 | present_numeric | 31 |
| canonical | month | 12 | present_numeric | 12 |
| canonical | year | 99 | present_numeric | 99 |
| replacement | minute | FF | replacement | none |
| malformed_fa | minute | FA | malformed_decimal | none |
| malformed_low | minute | 1A | malformed_decimal | none |
| malformed_high | minute | A0 | malformed_decimal | none |
| missing_month | month | missing | missing | none |
| failed_month | month | 3112 | failed | none |

`3112` means two supplied bytes, `31 12`, which are not one clock byte.

| Case | Minute | Hour | Day | Month | Year |
| --- | --- | --- | --- | --- | --- |
| missing_month | 12 | 23 | 31 | missing | 99 |
| failed_month | 12 | 23 | 31 | failed | 99 |

A failed cell does not discard its neighbors.
Missing month keeps the other four cells.
A present clock numeric grade is Hypothesis.
Clock calendar semantics stay Unknown.
Replacement semantic grade is Hypothesis.
Native grade stays Unknown.

## OP08 setpoint, mode, special function and messages

On admitted `OP08`, setpoint is an optional one-byte field.
Setpoint 01 is 0.5 Celsius.
The divisor is two. Raw `00` is present numeric 0.0 Celsius.
Missing setpoint is not zero. Setpoint `FF` stays the ordinary byte divided by
two, 127.5 Celsius, and is not a clock replacement. The Celsius reading is
Hypothesis. Native setpoint support stays Unknown.

Mode and special-function are optional raw bytes.
Mode, special-function and message tables stay Unknown.
They have no numeric conversion.

Exactly five message slots are independently optional.
Each message byte remains separately available.
A message buffer of one byte is `present_raw`.
The helper does not split one five-byte message blob into slots. Message raw
`FA` stays `present_raw`.

| Case | Raw | State | Numeric | Unit |
| --- | --- | --- | --- | --- |
| present_half | 01 | present_numeric | 0.5 | Celsius |
| present_zero | 00 | present_numeric | 0.0 | Celsius |
| missing | missing | missing | none | none |

| Index | Raw | State |
| --- | --- | --- |
| 0 | 10 | present_raw |
| 1 | 21 | present_raw |
| 2 | 32 | present_raw |
| 3 | 43 | present_raw |
| 4 | 54 | present_raw |

## OP0D raw words

**Hypothesis — candidate representation.** On admitted `OP0D` only, four
optional word slices are already delimited.
Words are raw unsigned little-endian 16-bit values.
Identity conversion has no units, scaling or sentinel.
FFFF is 65535 and is not a sentinel.
Absolute word positions are Unknown.
A slice decodes only when it is exactly two bytes. A shorter or
longer slice is failed and retains raw. A missing slice is missing and is not
numeric zero. One eight-byte buffer is not four words.

On `OP08`, supplied word slices stay raw-only. On `OP0D`, supplied clock cells,
setpoint, mode, special-function and messages stay raw-only.
The passive energy decoder, statistics selectors, voltage variants and identity-bearing structures receive no changes from either branch.

| Index | Raw | State | Numeric | Unit | Sentinel |
| --- | --- | --- | --- | --- | --- |
| 0 | 00 00 | present_numeric | 0 | none | false |
| 1 | 01 00 | present_numeric | 1 | none | false |
| 2 | 00 01 | present_numeric | 256 | none | false |
| 3 | FF FF | present_numeric | 65535 | none | false |

| Operation | Branch | Clock | Words |
| --- | --- | --- | --- |
| OP08 | OP08 | admitted | withheld |
| OP0D | OP0D | withheld | admitted |
| OP10 | none | withheld | withheld |

## Result grades and unchanged surface

The software contract grade on every result is Proven. Admitted interpretation
grade is Hypothesis. Raw-only interpretation grade is null.
Native support and physical adaptation stay Unknown on every result, including a full numeric
example. Presence, freshness, execution and physical qualification stay
Unknown and separate from these grades.

The result always publishes `clock` in minute, hour, day, month, year order,
five `messages` and four `words`, plus `setpoint`, `mode` and
`special_function`. Clock cell states are `present_numeric`, `replacement`,
`malformed_decimal`, `missing` and `failed`. Admission uses `raw_only` for a
supplied buffer on the wrong branch. `present_raw` is the OP08 state for mode,
special-function and message bytes.

No new major or experimental namespace is introduced. No authorization gate is
added. eBUS MCP compatibility and GraphQL parity are preserved because this
page changes no runtime interface. Nothing here is stable before Helianthus 1.0.

The [focused standard-library tests](../tests/test_an16_b516_clock_word_views.py)
exercise a local reference model of this prose. Expected clock numbers and
word numbers use independent arithmetic. Focused checks establish this
software contract only. Full Gate D, independent review, publication checks
and applicable transport classification remain later ship requirements.
