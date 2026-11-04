# B520 block fields and negative alternatives

## Evidence and logical representation

The source is the finite declaration set supplied in issue #1009. It is not a
vendor specification or reproducible native capture. Every native declaration
is **Hypothesis**; unprovided properties remain **Unknown**. **Proven** applies
only to synthetic representation and local arithmetic, never native behavior.
These are Vaillant family candidates, without installed support, freshness,
persistence or execution permission. Physical qualification is independent and
**Unknown**. See the adjacent [B523 family](ebus-b523-sensor-fields.md) for its
separate namespace; it supplies no evidence for B520.

The [synthetic fixture](fixtures/ai20_b520_blocks.json) and tables below form
one finite candidate contract. Positions are zero-based logical positions,
including three prefix positions, not physical telegram offsets. A case body
starts at logical 3 and omits the prefix. Negative OP02/03/04 constants are
`B5 20 02`, `B5 20 03`, `B5 20 04`; negative OP06 has constants `B5 20 06`.
The prefix column retains these constants; other prefix constants and
physical response framing remain Unknown. Direction labels
name abstract alternatives, not selected transport branches.

## Candidate fields

Each field is independently Hypothesis. `-` is inapplicable; `unset` means no
supplied data maximum, not a transport capacity. OP03 data is opaque and delimited
by the end of the abstract object; other data extents remain as declared.
Defaults describe declarations, not meanings or values to substitute for
missing bytes. OP03 positive adds data at 5; the
status and block fields retain their declared positions and candidate domains.
OP04 request and OP06 both alternatives retain
opaque data with Unknown length bounds.

| operation | direction | field | position | encoding | domain | minimum | maximum | default | prefix | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | request | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 01 | positive | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | address | 4 | u32 LE | 0..4294967295 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | flags | 8 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | size-bits | 9 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | block | 10 | u8 | 0..254 | - | - | 0 | Unknown | Hypothesis |
| 02 | request | start-bit | 11 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 02 | positive | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 03 | request | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 03 | request | block | 4 | u8 | 0..254 | - | - | Unknown | Unknown | Hypothesis |
| 03 | positive | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 03 | positive | block | 4 | u8 | 0..254 | - | - | Unknown | Unknown | Hypothesis |
| 03 | positive | data | 5 | opaque | - | 0 | unset | Unknown | Unknown | Hypothesis |
| 04 | request | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 04 | request | block | 4 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 04 | request | data | 5 | opaque | - | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 04 | positive | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 05 | request | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | status | 3 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | version | 4 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | max-block-length | 5 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | max-variable-count | 6 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | current-variable-count | 7 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | max-block-count | 8 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | current-block-count | 9 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 05 | positive | error-code | 10 | u8 | 0..255 | - | - | 0 | Unknown | Hypothesis |
| 06 | request | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 06 | request | write-block | 4 | u8 | 0..254 | - | - | Unknown | Unknown | Hypothesis |
| 06 | request | read-block | 5 | u8 | 0..254 | - | - | Unknown | Unknown | Hypothesis |
| 06 | request | data | 6 | opaque | - | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 06 | positive | status | 3 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 06 | positive | write-block | 4 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 06 | positive | read-block | 5 | u8 | 0..255 | - | - | Unknown | Unknown | Hypothesis |
| 06 | positive | data | 6 | opaque | - | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 07 | request | reserved-identifier | 3 | u32 LE | 0..4294967295 | - | - | 0 | Unknown | Hypothesis |
| 07 | request | reserved-offset | 7 | u16 LE | 0..65535 | - | - | 0 | Unknown | Hypothesis |
| 07 | request | data | 9 | opaque | - | 0 | 23 | 0 | Unknown | Hypothesis |
| 07 | positive | reserved-identifier | 3 | u32 LE | 0..4294967295 | - | - | 0 | Unknown | Hypothesis |
| 07 | positive | reserved-offset | 7 | u16 LE | 0..65535 | - | - | 0 | Unknown | Hypothesis |
| 07 | positive | data | 9 | opaque | - | 0 | 23 | 0 | Unknown | Hypothesis |
| 02 | negative | status | 3 | u8 | 0..255 | - | - | Unknown | B5 20 02 | Hypothesis |
| 02 | negative | error | 4 | u8 | 0..255 | - | - | 0 | B5 20 02 | Hypothesis |
| 03 | negative | status | 3 | u8 | 0..255 | - | - | Unknown | B5 20 03 | Hypothesis |
| 03 | negative | error | 4 | u8 | 0..255 | - | - | 0 | B5 20 03 | Hypothesis |
| 04 | negative | status | 3 | u8 | 0..255 | - | - | Unknown | B5 20 04 | Hypothesis |
| 04 | negative | error | 4 | u8 | 0..255 | - | - | 0 | B5 20 04 | Hypothesis |
| 06 | negative | status | 3 | u8 | 0..255 | - | - | Unknown | B5 20 06 | Hypothesis |
| 06 | negative | write-error | 4 | u8 | 0..255 | - | - | 0 | B5 20 06 | Hypothesis |
| 06 | negative | read-error | 5 | u8 | 0..255 | - | - | 0 | B5 20 06 | Hypothesis |

## Interpretation boundaries

Status polarity and clear effect are Unknown. OP02 address bytes `78 56 34 12`
represent the raw little-endian unsigned value 305419896, with no pointer or flash interpretation.
OP07 reserved identifier and offset are raw, without pointer semantics. OP05
maximum and current fields remain independent: a current value above a returned
maximum does not violate any universal limit. All error bytes retain their
full domain and zero default without an error enum. Defaults not supplied for
OP03/04/06 nonnegative fields or negative status remain Unknown. OP06 write-error 1 and
read-error 2 are independent, not a combined error.

OP03 request block 254 fits and 255 fails its candidate domain. OP04 request
255 stays raw. OP06 request 255 fails while positive 255 stays raw. No global
FF sentinel is defined. OP07 data begins at 9: 23 bytes fit the abstract
maximum and 24 exceed it. A negative object is separate from a physical NAK.
Positive and negative alternatives can share prefixes; bytes alone do not
select a response branch. These unresolved alternatives remain visible.

The following boundaries are explicit contract declarations, each qualified by
its value; raw representation is not physical qualification.

| property | value |
| --- | --- |
| native-grade | Hypothesis |
| physical-qualification | Unknown |
| status-semantics | Unknown |
| block-correlation | Unknown |
| atomicity | Unknown |
| physical-adaptation | Unknown |
| effects | Unknown |
| support | Unknown |
| address-meaning | raw |
| reserved-meaning | raw |
| ff-meaning | raw; no universal sentinel |
| returned-maxima | raw; no universal limit |
| error-meaning | raw; no enum |
| negative-is-nak | false |
| automatic-branch-selection | false |
| incomplete-admission | false |
| last-known-good | retain |

## Synthetic cases

`fits` is a local predicate for supplied field constraints in the explicitly
named alternative. Unknown data bounds do not establish native completeness;
the synthetic body simply retains all remaining bytes as raw data. It establishes
no response selection or physical support. Bodies are hexadecimal logical
bytes beginning at 3, including uninterpreted gaps.

| operation | direction | body | fits |
| --- | --- | --- | --- |
| 03 | request | 00 FE | true |
| 03 | request | 00 FF | false |
| 04 | request | 00 FF | true |
| 06 | request | 00 FF 01 | false |
| 06 | positive | 00 FF FF | true |
| 02 | request | 00 78 56 34 12 00 00 FE 00 | true |
| 05 | positive | 00 01 02 03 04 05 06 07 | true |
| 07 | request | 78 56 34 12 34 12 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 | true |
| 07 | positive | 78 56 34 12 34 12 00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17 | false |
| 06 | negative | 00 01 02 | true |
| 02 | negative | 00 FF | true |
| 03 | negative | 00 00 | true |
| 04 | negative | 00 00 | true |
| 03 | positive | 00 00 | true |
| 04 | positive | 00 | true |

Incomplete or out-of-domain objects retain their raw bytes but are not admitted
as complete candidate values. They do not replace a complete last-known-good
value. Abstract admission does not establish native adaptation, block
correlation, atomicity, effects or permission to execute; all remain Unknown.
