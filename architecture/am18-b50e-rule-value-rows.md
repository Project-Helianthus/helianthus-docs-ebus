# B50E row-relative rule values

The public [native B50E contract](../protocols/vaillant/ebus-vaillant-b50e.md#data-types-of-the-rule-read-reply)
comes first. Its OP02 rule-read table supplies these **Hypothesis** candidates.
This page defines the finite application metadata and synthetic example-package
contract for AM18, following registry prerequisite AM17 in ebusreg. It does not
establish that the companion is implemented or verified. Refs #1030 and #736;
this partial child leaves the parent open. Nothing is stable before Helianthus 1.0.

**Proven (software contract):** embed exactly 19 metadata entries, with keys
0..18 exactly once. **Hypothesis:** every row meaning, Boolean/status meaning,
width and companion position below. **Unknown:** native qualification, physical
support, presence, freshness, execution, effects, persistence and delivery.
These grades are independent of each other and of `qualified=false`.

## Exact metadata API

This bounded contract specifies enumeration, exact lookup and raw projection;
it introduces no production function names. Enumeration yields all 19 entries
in key order with independently owned storage. Lookup input has exactly eight
fields: `family`, `variant`, `primary`, `secondary`, `operation`, `direction`,
`key`, `field`. String fields require nonempty strings; byte fields and `key`
require integers 0..255, excluding Booleans. Missing, extra, null, mistyped or
out-of-domain fields are malformed. Explicit zero is present, never a wildcard.
The supported application identity is family `vaillant`, variant `B50E`,
primary B5, secondary 0E, operation OP02, direction `positive`, row field
`rule_value_row`. These are exact catalog tokens, not a device qualification.
Well-formed mismatches, including OP03, another variant and key 19, return
`no_match` with no metadata. There is no normalization or fallback.

A hit returns the key, `grade=Hypothesis`, value kind, row-relative offset zero,
optional width, and optional companion kind/offset/width. Opaque keys omit
width; omission differs from an explicit width of zero, which is invalid.
Companion absence differs from a zero-width companion. End-of-data keys
0/15/16 do not mean zero-width values. All offsets count from an already
isolated value row; neither enclosing logical nor physical base is added.
This API cannot isolate a row from a bus frame or validate that isolation.

| Key | Value kind | Value offset | Value width | Companion | Companion offset | Companion width | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | opaque | 0 | absent | absent | absent | absent | Hypothesis |
| 1 | boolean_u8 | 0 | 1 | absent | absent | absent | Hypothesis |
| 2 | u8 | 0 | 1 | absent | absent | absent | Hypothesis |
| 3 | i8 | 0 | 1 | absent | absent | absent | Hypothesis |
| 4 | u16 | 0 | 2 | absent | absent | absent | Hypothesis |
| 5 | i16 | 0 | 2 | absent | absent | absent | Hypothesis |
| 6 | u32 | 0 | 4 | absent | absent | absent | Hypothesis |
| 7 | i32 | 0 | 4 | absent | absent | absent | Hypothesis |
| 8 | secure_boolean_u8 | 0 | 1 | absent | absent | absent | Hypothesis |
| 9 | u8 | 0 | 1 | inverse | 1 | 1 | Hypothesis |
| 10 | i8 | 0 | 1 | inverse | 1 | 1 | Hypothesis |
| 11 | u16 | 0 | 2 | inverse | 2 | 2 | Hypothesis |
| 12 | i16 | 0 | 2 | inverse | 2 | 2 | Hypothesis |
| 13 | u32 | 0 | 4 | inverse | 4 | 4 | Hypothesis |
| 14 | i32 | 0 | 4 | inverse | 4 | 4 | Hypothesis |
| 15 | opaque | 0 | absent | absent | absent | absent | Hypothesis |
| 16 | opaque | 0 | absent | absent | absent | absent | Hypothesis |
| 17 | temperature_i16_div16_celsius | 0 | 2 | status | 2 | 1 | Hypothesis |
| 18 | temperature_i16_div16_celsius | 0 | 2 | inverse | 2 | 2 | Hypothesis |

Key 1 has no completed Boolean table here. Key 8 maps only `0F` to true and
`F0` to false; `00` and every other byte remain unmapped. Key 17 status maps
only `00` to okay, `55` to short, `AA` to interrupted; `FF` and other bytes
remain unmapped. The temperature carrier domain is -32768..32767 and its
candidate scale is /16 Celsius, giving -2048..2047.9375. No signed word is
decoded without explicit byte-order qualification. This dictionary provides
no numeric decoder, universal Boolean meaning or unprovided defaults.

Byte order and defaults remain Unknown in this dictionary. The native page
also contains a general little-endian statement; that broader proposal is not
imported into this row dictionary and does not qualify its byte order. Native
logical/physical adaptation remains Unknown. Inverse means an opaque companion
field, with no bitwise-complement validation. Arbitrary non-complement bytes
are retained. The OP02 table must not decode OP03 buffer bytes. Existing
comparison flags, the clear-index catalog and active rule execution remain
separate. No route, scan default, executor or automatic qualification is added.
Existing eBUS MCP compatibility and GraphQL parity remain unchanged; no new
transport surface is introduced.

## Mapping example agreement

These complete synthetic rows assert only the named byte mapping, never a
numeric temperature decode. Every other key-8 Boolean or key-17 status byte
stays unmapped.

| Case | Key | Raw row | Mapping |
| --- | --- | --- | --- |
| key8_true | 8 | 0f | true |
| key8_false | 8 | f0 | false |
| key8_unmapped | 8 | 00 | unmapped |
| key17_okay | 17 | 123400 | okay |
| key17_short | 17 | 123455 | short |
| key17_interrupted | 17 | 1234aa | interrupted |
| key17_unmapped | 17 | 1234ff | unmapped |

## Synthetic projection and admission

The [example package](fixtures/am18_b50e_rule_value_rows.json) contains metadata,
one raw control per key, seven mapping cases, a partial row and an extra-tail
case. Its exact policy is:

```json
{
  "identity": {
    "family": "vaillant",
    "variant": "B50E",
    "primary": 181,
    "secondary": 14,
    "operation": 2,
    "direction": "positive",
    "field": "rule_value_row"
  },
  "count": 19,
  "offset_origin": "isolated_row",
  "byte_order": "Unknown",
  "default": "Unknown",
  "inverse": "opaque",
  "numeric_decoder": false,
  "universal_boolean": false,
  "qualified": false,
  "grades": {
    "software": "Proven",
    "meaning": "Hypothesis",
    "native": "Unknown"
  },
  "unknown": [
    "physical_support",
    "presence",
    "freshness",
    "execution",
    "effects",
    "persistence",
    "delivery",
    "physical_base",
    "logical_base"
  ]
}
```

The [standard-library suite](../tests/test_am18_b50e_rule_value_rows.py) owns a
test-only seam, not a production decoder. The seam admits only the exact
metadata schema above: count, uniqueness, keys, kinds, offsets, optional widths,
companion shapes and grades must agree. Malformed, partial or extra metadata
fails closed for the entire catalog. No independently useful prior state or
raw input is erased by catalog admission failure.

Projection inputs are the exact lookup identity, an already isolated bytes or
bytearray row, and independently supplied last-known-good fields. Outputs are
`status`, optional `metadata`, `fields`, full owned `raw`, `tail`, owned
`last_known_good`, `grade` and `qualified=false`. Each available field contains
its raw slice and `complete`; only complete key-8 values and key-17 statuses
add `mapping`. Mapping results are the lowercase strings listed above; an
unmapped byte stays raw and is not coerced. Numeric fields remain raw.
A lookup/admission failure has grade Unknown, no metadata or fields, with
`malformed` or `no_match` status; a hit retains Hypothesis grade even if partial.
Invalid raw input is malformed with no fabricated bytes. Valid bytes are
preserved even when another input is malformed.

For a known extent, a short row is `partial`: preserve each available prefix
and every independently complete field; never zero-pad, decode an incomplete
field or merge cached bytes into a fresh field. A complete row is `complete`;
extra bytes are preserved as `tail`, without extrapolating new fields. Opaque
rows have status `opaque` with all bytes in `fields.value.raw` and unknown
completeness (`null`); they have no asserted end or tail extent. An empty opaque
row remains opaque, not a proven zero-width value.

The partial key-13 example is `123456780724`: the complete four-byte value
survives beside the partial inverse `0724`, and previous `independent_field=0`
is retained. The extra key-9 example is `a517ee`: value `a5`, inverse `17`,
tail `ee`. Key-17 row `1234` retains the complete raw temperature while status
is incomplete. No failure discards full raw input. Input bytes, metadata and
prior state are copied; modifying an output cannot change later lookup,
enumeration or source storage. Returning a raw fallback does not admit it as
qualified semantics or execution authority.

## Verification limits

Tests independently assert every table cell and every example, enumerate the
unmapped Boolean/status bytes, vary every identity axis independently, and
vary every inverse byte without complement assumptions. Signed bounds and
scaled endpoints are checked by struct and integer arithmetic; explicit test
byte order is an arithmetic qualification, not dictionary byte-order evidence.
Tests cover malformed/partial/extra/unknown/valid controls and mutable storage.
Disposable mutations establish page/fixture sensitivity only. Production AM17
parity and any production mutation coverage remain unverified here.

Focused offline results establish only this software/page contract. Full
repository CI, Gate D, publication checks, independent committed-change review
and applicable transport classification remain later ship requirements. No
focused pass is claimed as a complete gate result or native qualification.
