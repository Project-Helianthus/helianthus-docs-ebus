# B525 supplied spectrum blocks

**Proven — software contract.** AM26 defines a pure view and optional join of
explicitly supplied logical blocks for companion AM25. The
[public native B525 contract](../protocols/vaillant/ebus-vaillant.md#b525-radio-diagnosis)
comes first: it calls the layout candidate and unconfirmed on the wire. This
architecture page owns application input/output and synthetic example policy;
it does not upgrade native evidence or implement a transport parser.

**Hypothesis — candidate representation.** Logical request selectors `10`..`17`
are hexadecimal (JSON uses integers 16..23). Each carries 32 signed8 values at
abstract positions 3..34 after `B5 / 25 / OP`; OP is the selector, not a second
operation byte. Positive declarations are prefix-only and contain no additional
32-value vector. The companion receives an already isolated vector, never
searches a telegram for values, and never treats a positive prefix as a vector.

| Selector (hex) | First index | Last index |
| --- | --- | --- |
| 10 | 0 | 31 |
| 11 | 32 | 63 |
| 12 | 64 | 95 |
| 13 | 96 | 127 |
| 14 | 128 | 159 |
| 15 | 160 | 191 |
| 16 | 192 | 223 |
| 17 | 224 | 255 |

## Exact input and block result

Input is `(context, raw)`; `raw` must be bytes, bytearray or memoryview. Other
containers raise TypeError, never coerce or decode. Context must be a mapping;
a non-mapping is TypeError. Deep-copy the entire mapping, including extra fields,
and copy raw bytes before interpretation. No result or later caller mutation may
alias caller memory or another result. Each required field is independently
validated. Missing, null, empty, wrong-type, unknown and explicit zero are kept
distinct in the retained context. Boolean selectors are not integers.

The normative policy below is repeated exactly in the
[synthetic example package](fixtures/am26_b525_spectrum_blocks.json). Its finite
family/variant declarations are synthetic controls, not native family support.
A real consumer requires its separately evidenced explicit declaration; this
page admits no additional real family. `operation` is the application service
identity `B525`, not another wire byte. `direction` and `form` are explicit
normalizer inputs, never inferred from width. Only request + isolated_values
admits values. Known positive_prefix and unknown forms remain raw-only even if
32 or more bytes are supplied. Unknown operation, direction, selector, family
or variant also remains raw-only. No fallback between contexts is allowed.

```json
{
  "context_fields": ["family", "variant", "operation", "direction", "selector", "form", "candidate_grade"],
  "families": ["synthetic-radio-family-a", "synthetic-radio-family-b"],
  "variants": ["synthetic-variant-a", "synthetic-variant-b"],
  "operation": "B525",
  "direction": "request",
  "form": "isolated_values",
  "selectors": [16, 17, 18, 19, 20, 21, 22, 23],
  "width": 32,
  "codec": "signed8",
  "grade": "Hypothesis",
  "positive_values": false,
  "frequency_mapping": false,
  "fill_missing": false,
  "complete_distinct_blocks": 8
}
```

Output retains `context`, `raw`, `grade`, `values` (ordered index/value pairs),
`present_indices` (the sparse present-index mask), `valid`, `incomplete`, `extra`,
`remainder`, and `state`. A raw-only result has grade null, no pairs or indices,
valid false, incomplete true, extra false, the entire raw buffer as remainder,
and state raw_only. Input candidate_grade must be Hypothesis or Proven to admit
candidate arithmetic; output grade stays Hypothesis in either case. Unknown,
missing or malformed grade is raw-only; it cannot promote native evidence.

For selected inputs, each of the first at most 32 bytes is independently
sign-extended and paired with start + offset. `00 / 7F / 80 / FF` yield
`0 / 127 / -128 / -1`. Index is a logical integer, never a frequency or scaled
quantity. Preserve every raw byte. `valid` requires exactly 32 bytes; fewer
bytes yield state short and incomplete true but retain all available pairs.
More bytes yield state extra, extra true, incomplete false, valid false, the
first 32 pairs and the suffix as remainder. Extra values never advance into
the next block. An exact vector has state exact, incomplete false, extra false
and empty remainder. Raw-only is distinct from an admitted empty short vector.

## Pure join and partial results

The join accepts a sequence of supplied `(context, raw)` inputs and applies the
block view to each, retaining all block results in input order even on rejection.
It returns `blocks`, `accepted`, `reason`, `values`, `present_indices`, `complete`
and `grade`. Values sort by logical index, independent of arrival order.
A block identity is (family, variant, operation, direction, selector). All
contexts must have equal family, variant, operation and direction; any difference
rejects the aggregate with reason cross_context. It cannot combine families or
variants even when bytes match. Conflicting duplicates of one identity (different
raw bytes or retained context, including form or grade) reject with reason
conflicting_duplicate. Identical duplicates coalesce, never add indices or count
toward eight. Cross-context rejection takes precedence. Rejection leaves the
aggregate values/mask empty, complete false and grade null; each block's raw,
validity and independently useful partial fields survive in blocks.

Otherwise accepted is true and reason null. Join only selected candidate pairs;
raw-only inputs add none. Short and extra blocks contribute their bounded pairs
but remain individually invalid. Absent indices stay absent, including when an
actual supplied byte is zero. Complete is true only for eight distinct valid
exact 32-byte blocks, one per selector. An invalid duplicate cannot repair an
invalid block. An empty join is accepted, incomplete, empty and grade null;
otherwise aggregate grade is Hypothesis if any block has candidate grade,
including an admitted empty short block. Retained partial/raw results must not
erase a consumer's last-known-good state; this pure API owns no persistent state
or admission route. It supplies no freshness, presence or execution evidence.

## Synthetic cases and limits

The package repeats `00 7F 80 FF` eight times in each exact block. Every selector
checks both ends and all signed values. Scenarios replace only the named context
fields and raw vector; absent names remove fields. Joins reference those cases.
The following table is normative and repeated in the package; blocks count
supplied inputs, indices count present logical indices, absent counts the
complement within 0..255. Conflict controls change one byte; cross-family and
cross-variant controls change only their named field.

| Join case | Blocks | Indices | Absent | Accepted | Complete |
| --- | --- | --- | --- | --- | --- |
| all_reversed | 8 | 256 | 0 | true | true |
| missing_middle | 7 | 224 | 32 | true | false |
| short_last | 8 | 228 | 28 | true | false |
| extra_last | 8 | 256 | 0 | true | false |
| conflicting_duplicate | 9 | 0 | 256 | false | false |
| cross_family | 8 | 0 | 256 | false | false |
| cross_variant | 8 | 0 | 256 | false | false |
| identical_duplicate | 9 | 256 | 0 | true | true |
| positive_only | 1 | 0 | 256 | true | false |
| empty | 0 | 0 | 256 | true | false |

**Unknown — native properties.** Frequency, band, channel spacing, RSSI unit,
cadence and native scan action remain Unknown. Physical support, effects,
persistence, delivery, presence and freshness remain Unknown, independently of
Proven software behavior and Hypothesis candidate representation. The join
only describes supplied logical data, never an active scan or one atomic device
result. Existing radio-field metadata and encrypted/opaque payload declarations
retain their ownership; they are not reimplemented here. No live writes,
transmit route, scan-default change, active executor, automatic qualification,
new namespace or authorization gate is added. Nothing is stable before
Helianthus 1.0. eBUS MCP compatibility and GraphQL parity are preserved; no
runtime interface is changed by this page.

The [focused standard-library tests](../tests/test_am26_b525_spectrum_blocks.py)
exercise a local reference model of the prose, not companion production code.
Expected signed numbers use independent struct/int arithmetic. Page tables and
policy are checked against independent constants and the examples. Every
context field has independent missing, malformed and changed controls; raw
ownership, partial/extra vectors and sparse joins are checked separately.
Focused offline results establish only this software/page contract. Full Gate D,
independent committed-change review, publication checks and applicable transport
classification remain later ship requirements. Focused discovery does not claim
automatic Gate D discovery or production mutation coverage.
