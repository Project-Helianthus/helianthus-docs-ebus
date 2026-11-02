# B51A diagnostic field alternatives and raw save outcomes

The public [native evidence boundary](../protocols/vaillant/ebus-b51a-diagnostic-variants.md)
withholds detailed diagnostic mappings pending traceable native evidence. This
page does not admit those mappings as native facts. It defines a **Proven local
API contract** for finite synthetic views; candidate meanings remain
**Hypothesis**, and native interpretation and physical support remain **Unknown**.
Nothing is stable before Helianthus 1.0.

## Callable contract and admission

Package `vaillant` exports this Go standard-library-only interface:

```go
func Ab21Aq21Evaluate(ab21Aq21Input json.RawMessage) (json.RawMessage, error)
```

This is a pure callable field evaluator, not an Entries/Lookup catalog or schema.
This page supplies no implementation, automatic caller, provider registration,
initialization side effect or persistent cache. No pending helper, sibling
checkout, unmerged registry entry or code-merge dependency is required. New Go
declarations, parameters, locals, fields, helpers and fixture identifiers use
`ab21aq21` or exported `Ab21Aq21`; test functions use `TestAb21Aq21`. Literal
JSON/protocol labels and existing package/library symbols retain their spelling.

Input is one JSON object with required objects `context` and `fields`, and
optional object `arguments`. Context contains `primary`, `secondary`, optional
`operation`, `direction`, `view`, and opaque family/variant keys. Present primary,
secondary and operation selectors must be integers 0..255; missing operation,
explicit zero and null are distinct: zero is unsupported here, null is an invalid
numeric kind. Direction and view select the strings below. Context identifiers
select a local candidate view and never qualify a device family.

Each supplied field is an array of integer bytes 0..255. Empty opaque data is
distinct from missing data; none of the fixed-width fields below is opaque.
Arguments supply only the explicitly declared typed inputs for interpretation;
unknown extra keys, including nested extensions, remain unchanged and acquire
no semantics. Unknown extra input keys are retained independently at every level.
No string, null or Boolean is coerced into a number.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range bytes or integer arguments, and
missing required arguments with an error and no successful result. Validate
input before unsupported-context fallback. `arguments.value_width` is required
for the selected save view and must be integer 1 or 2. Other views declare no
typed arguments. Unsupported well-formed contexts return raw-only `Unknown`
without applying a formula.

## Finite views

Every supported row requires `primary=181`, `secondary=26` and
`direction="positive"`. Operation and view must match explicitly; field length
and flags never select a layout. All row meanings are Hypothesis.

| operation | view | named logical fields and exact widths |
| --- | --- | --- |
| 4 | enable-bits | `enable`: 13 bytes |
| 5 | range | `flags`: 1; `display_type`: 1; `value`, `minimum`, `maximum`: 2 each; `step`: 1 |
| 5 | enum | `flags`: 1; `alternatives`: 6 |
| 5 | four-byte | `flags`: 1; `value`: 4; `reserved`: 3 |
| 6 | save | `status`: 1; `mirror`, `symbol`: 2 each; `value`: exactly `arguments.value_width` bytes |

OP04 returns **104 independent Boolean positions**, never 13 summary bits.
Position `8*i+j` is bit `j` of byte `i`, for `i=0..12`, `j=0..7`, with bit 0
least significant. Preserve all 13 raw bytes. Logical footprint 17 and tail
tuple `(0,13,0)` do not describe physical length or wire offsets.

OP05 decodes the shared flags byte as follows:

| bits | local candidate meaning |
| --- | --- |
| 0 | disabled |
| 1 | writable |
| 2 | enum-versus-range |
| 3 | two alternatives: additional-four-byte/no-range; read-only overriding writable |
| 4..5 | reserved, preserved in original positions with mask `0x30` |
| 6..7 | text alternatives, retained as alternatives without an invented text mapping |

Retain bit 3's two alternatives together. When bit 1 and bit 3 are set, report
the writable/read-only conflict without producing effective authorization.
Neither bit 2 nor bit 3 auto-selects a view. If disabled bit 0 is true, retain
all subsequent raw fields but do not interpret them: no numbers, conversions,
enum values or semantic reserved-field decoding are produced for those fields.

For enabled range, decode `display_type` and `step` independently as u8 and
`value`, `minimum`, `maximum` independently as LEu16. Do not enforce a range or
invent display conversion. For enabled enum, retain six ordered byte positions,
including duplicates; there is no current-value field. For enabled four-byte,
decode `value` as LEu32 and retain `reserved` as exactly three uninterpreted raw
bytes, with `unmodeled=true`. Do not turn reserved bytes into a number.

OP06 decodes `status` as u8 with these candidate labels:

| status | label |
| --- | --- |
| 0 | value-not-saved |
| 1 | point-not-found |
| 2 | write-protected |
| 3 | range-violation |
| 4 | misconfiguration |
| 5..255 | unmapped |

No status establishes success. An unmapped status retains its number and raw
byte without inventing a semantic label or success. Decode `mirror` and `symbol`
independently as LEu16. The explicit `value_width=1` alternative decodes `value`
as u8; the explicit `value_width=2` alternative decodes it as LEu16. Preserve
these two possible interpretations as alternatives in the contract; only the
explicit argument chooses one result. Never infer width or the display-type
algorithm from bytes, status, family, or another field.

## Results, partial data and grades

Successful output is one JSON object containing unchanged `context`, `raw`
(the input `fields`), unchanged `arguments` if supplied, all extra keys, `state`,
`results`, `physical="Unknown"` and `qualified=false`. Each named result has
`state`, `grade="Hypothesis"` and its supplied `raw`; missing fields omit `raw`.
Applicable results additionally contain `number`, `label`, `flags`, `reserved`,
`unmodeled`, `candidate_domain` or `alternatives`. No candidate domain or display
conversion is specified here; do not manufacture a domain check or a converted
number. Unknown conversion produces no number for that conversion, even when
raw arithmetic is complete.

| condition | result boundary |
| --- | --- |
| invalid input | error; no successful output |
| unsupported context | aggregate `Unknown`, empty `results`, raw retained |
| missing, short or overlong fixed-width field | field `incomplete`; supplied raw retained; no invented number |
| complete independent field | retained even when a sibling is incomplete |
| any incomplete required field | aggregate `partial` |
| all required widths complete | aggregate `complete`, meaning local representation only |
| disabled OP05 subsequent field with complete width | raw-only `Unknown`, no interpretation; aggregate may remain `complete` |
| complete raw arithmetic, unresolved meaning | retain arithmetic and unresolved semantic alternative together |

Exact u8, LEu16, LEu32 and bit calculations may additionally carry
`calculation="Proven"`; this never replaces `grade="Hypothesis"`. LEu16 is
`raw[0]+256*raw[1]`; LEu32 extends that sum with `65536*raw[2]+16777216*raw[3]`.
Numeric default 0 is metadata, never a replacement for missing bytes. Preserve
absent, null, zero, false and explicit empty values independently wherever their
kinds are permitted, including opaque extensions. Null is not a byte array or
typed numeric argument. Explicit `[]` is incomplete for a fixed-width field;
an explicitly opaque empty field remains present and unmodeled.

Input storage, returned nested storage and subsequent calls are independent.
Incomplete siblings do not erase useful last-known-good complete fields in the
same result; no cache fills gaps from earlier calls. Rejected input cannot
replace separately retained last-known-good evidence with a successful result.

## Synthetic examples

A complete valid range input and output (decimal JSON bytes; hexadecimal byte
pairs in prose are in transmitted little-endian order):

```json
{"context":{"primary":181,"secondary":26,"operation":5,"direction":"positive","view":"range"},"fields":{"flags":[0],"display_type":[0],"value":[52,18],"minimum":[1,0],"maximum":[255,255],"step":[0]},"extension":{"present":false,"empty":[],"nullable":null}}
```

```json
{"context":{"primary":181,"secondary":26,"operation":5,"direction":"positive","view":"range"},"raw":{"flags":[0],"display_type":[0],"value":[52,18],"minimum":[1,0],"maximum":[255,255],"step":[0]},"extension":{"present":false,"empty":[],"nullable":null},"state":"complete","results":{"flags":{"raw":[0],"state":"complete","grade":"Hypothesis","calculation":"Proven","flags":{"disabled":false,"writable":false,"enum-versus-range":false},"reserved":0,"alternatives":{"bit3":{"additional-four-byte/no-range":false,"read-only-overriding-writable":false},"text-bits":[false,false]}},"display_type":{"raw":[0],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":0},"value":{"raw":[52,18],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":4660},"minimum":{"raw":[1,0],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":1},"maximum":{"raw":[255,255],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":65535},"step":{"raw":[0],"state":"complete","grade":"Hypothesis","calculation":"Proven","number":0}},"physical":"Unknown","qualified":false}
```

Independent partial example: replace only `value` with `[52]` in that input.
Output remains raw-preserving with aggregate `state="partial"`;
`results.value={"raw":[52],"state":"incomplete","grade":"Hypothesis"}`.
Minimum 1, maximum 65535 and step 0 remain complete. Missing `value` omits its
result raw; `[52,18,0]` is also incomplete, never truncated to 4660.

Independent unknown example: change only `operation` to 7 in the complete
input. Retain context, raw and extension unchanged; return `state="Unknown"`,
`results={}`, `physical="Unknown"`, `qualified=false`. Do not reuse the range
arithmetic. A duplicate nested key or `arguments.value_width=null` for save
instead causes an error, with no successful partial or Unknown output.

Further finite assertions:

| selected view / raw or argument | local result |
| --- | --- |
| enable-bits / thirteen zero bytes | exactly 104 false positions |
| enable-bits / set bit `j` in each byte `i` independently | each change flips exactly position `8*i+j`; setting bit 0 in every byte yields positions 0,8,16,24,32,40,48,56,64,72,80,88,96 |
| range / flags `0A` | writable true, bit 3 true with both alternatives and conflict; no authorization |
| range / flags `01`, other bytes unchanged | disabled true, all subsequent raw retained without interpretation |
| range / value `3412`, minimum `0100`, maximum `FFFF`, step `00` | 4660, 1, 65535, 0 independently |
| enum / flags `[0]`, alternatives `[1,2,2,3,4,4]` | six ordered values, duplicates intact, no current value |
| four-byte / flags `[0]`, value `78563412`, reserved `[0,0,0]` | value 305419896; reserved raw unmodeled |
| save / status `[0]`, `[1]`, `[5]` in separate inputs | value-not-saved, point-not-found, unmapped; no success |
| save / width 1, value `[52]` | u8 number 52 |
| save / width 2, value `[52,18]` | LEu16 number 4660 |
| save / width 2, value `[52]` | incomplete, no value number; complete status/mirror/symbol survive |
| save / value supplied without width argument | error, never infer width |

For the save rows, complete independent `mirror=[1,0]` and `symbol=[2,0]`
yield 1 and 2; a complete status can coexist with incomplete value. The width
choices are distinct even when both could represent zero.

## Scope and consumer boundaries

AI15/AJ07 retain metadata; AP19/20 retain OP02/03; AQ19/20 retain reset/OP01.
This slice adds only explicitly selected OP04/05/06 logical field results.
Native adaptation, enum materialization, point selection, save success,
persistence and enforcement remain **Unknown**. Qualification, freshness,
physical effects and delivery are independent and remain **Unknown**; no family
completeness, physical result or execution follows. Existing eBUS MCP
compatibility and GraphQL parity remain requirements for consumers of these
raw/context/state distinctions; this page adds no transport surface.

This architecture-only companion is partial progress on #736 and does not close
that parent. Full repository CI, Gate D with its prescribed read-only reference
prerequisites, fresh independent committed-change review, publication checks
and applicable transport classification remain required before merge.
