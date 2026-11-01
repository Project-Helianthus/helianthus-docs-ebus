# B51A mirror-field local API contract

This architecture contract is **Proven** as a local representation specification.
It does not establish a wire implementation. The public native contract is
[Candidate mirror and diagnosis layouts](../protocols/vaillant/ebus-vaillant-B51A.md#candidate-mirror-and-diagnosis-layouts).
That source keeps logical coordinates including B5/1A/OP and the competing
configured forms separate. The finer fields below are **Hypothesis** from the
finite synthetic contract; native confirmation remains **Unknown**.

The specified Go standard-library API in package `vaillant` is exactly:

```go
func Ab19Ap19Evaluate(ab19ap19Input json.RawMessage) (json.RawMessage, error)
```

This page specifies the API; this slice supplies no implementation or runtime
caller. It is a pure function: no initialization side effect, persistent cache,
generic catalog, listing API, executor or method registration. eBUS MCP
compatibility and GraphQL parity require preserving the same raw/context/state
and qualification distinctions; no transport or schema change is introduced.

## JSON input and admission

Input is one JSON object: `{"context": {...}, "fields": {...}, "arguments": {...}}`.
`context` and `fields` are required objects. `arguments` is an optional object;
none of these four views declares an interpreted argument or required argument.
Unknown argument keys, including selectors, are preserved without interpretation.
Opaque context keys such as `family`, `variant` and nested extensions are
preserved verbatim. No model or family selector qualifies native support.

Matched contexts require integer `primary=181`, integer `secondary=26`, an
operation, direction and explicit view from the table. Present numeric context
selectors must be integral u8 or null; direction/view must be strings or null.
Missing, null and zero remain distinct; a missing/null selector is unsupported.
Unknown selector values produce raw-only `state="Unknown"`, semantic `fields={}`;
no formula is applied. Strict JSON kinds distinguish Boolean false from zero.

Every entry of input `fields` is a byte array with integral values 0..255.
Unknown field names retain their validated raw bytes without acquiring meaning.
Malformed JSON, duplicate keys at any nesting level, non-JSON constants, wrong
kinds, fractions and out-of-range bytes or typed arguments return an error and
no successful result. u8/u16/u32, when declared, have ranges 0..255,
0..65535 and 0..4294967295. There is no coercion, implicit default or relay vector
in these views. Opaque JSON arguments are not assigned invented numeric types.
Missing required arguments in any declared contract are errors; this slice has
none. Invalid input is rejected before unsupported-context fallback.

## Allowed views and field extents

Each row is Hypothesis. Coordinates are logical B5/1A/OP coordinates, never
physical bus-response offsets. Do not subtract a prefix to infer physical
positions. Width `0..end` has minimum zero and unspecified maximum. The decoder
consumes each supplied named field independently, not an assembled telegram.

| operation | direction | view | field | logical coordinate | width | decoder | named mask | reserved mask |
|---|---|---|---|---|---|---|---|---|
| 2 | request | mirror-get | sequence | 3 | 1 | u8 | 0 | 0 |
| 2 | request | mirror-get | flags | 4 | 1 | bits | 1 | 254 |
| 2 | request | mirror-get | length | 5 | 1 | u8 | 0 | 0 |
| 2 | request | mirror-get | address | 6 | 2 | le16 | 0 | 0 |
| 2 | positive | mirror-get | sequence | 3 | 1 | u8 | 0 | 0 |
| 2 | positive | mirror-get | status | 4 | 1 | alternatives | 1 | 0 |
| 2 | positive | mirror-get | data | 5 | 0..end | opaque | 0 | 0 |
| 3 | request | mirror-put | sequence | 3 | 1 | u8 | 0 | 0 |
| 3 | request | mirror-put | flags | 4 | 1 | bits | 3 | 252 |
| 3 | request | mirror-put | mirror_address | 5 | 2 | le16 | 0 | 0 |
| 3 | request | mirror-put | symbol_address | 7 | 2 | le16 | 0 | 0 |
| 3 | request | mirror-put | data | 9 | 0..end | opaque | 0 | 0 |
| 3 | positive | mirror-put | sequence | 3 | 1 | u8 | 0 | 0 |
| 3 | positive | mirror-put | flags | 4 | 1 | bits | 15 | 240 |

`le16` is `raw[0] + 256 * raw[1]`; `u8` is `raw[0]`.
For `bits`, named bit i is `(raw[0] & (1 << i)) != 0` and reserved is
`raw[0] & reserved_mask`, preserving original bit positions. Exact numbers and
bit calculations may additionally carry `calculation="Proven"`; field family
`grade="Hypothesis"` is unchanged. Numeric defaults 0 and false are metadata,
never replacements for missing bytes.

| operation | direction | bit | name |
|---|---|---|---|
| 2 | request | 0 | triple-storage |
| 3 | request | 0 | triple-storage |
| 3 | request | 1 | direct-update |
| 3 | positive | 0 | not-written |
| 3 | positive | 1 | invalid-symbol |
| 3 | positive | 2 | invalid-parameter |
| 3 | positive | 3 | storage-error |

## Result shape and transitions

A successful output object has `context` unchanged, `raw` as a deep independent
copy of input `fields`, optional `arguments` unchanged if supplied, `state`,
semantic `fields`, `physical="Unknown"`, and `qualified=false`.
No extra inferred success, correlation, address dictionary or selector appears.
Every semantic field has `state` and `grade="Hypothesis"`; present fields also
retain `raw`, including short/overlong arrays. A missing field omits `raw`.
A fixed-width field is complete only at its exact width; zero bytes in an empty
fixed-width array are not a default. Missing, short or overlong fields are
`state="incomplete"` without number, label, flags or calculation. Opaque data is
complete for every explicit array, including `[]`; missing data is incomplete.
Complete independent siblings survive incomplete fields and unresolved candidate
branches. Aggregate state is `partial` when any required field is incomplete,
otherwise `complete` for a supported view, even if a status branch is unmapped.
An unsupported view instead has state `Unknown` and no semantic fields.

Complete u8/le16 results have `number` and `calculation="Proven"`. Address
results additionally have `logical_validity="Unknown"`: 65535 is an ordinary
full-range value, never an all-addresses token. Mirror and symbol limits are
missing. Opaque results have `unmodeled=true`, without invented numbers or labels.
Complete flags results have `flags` keyed by the table names, `reserved`, and
`calculation="Proven"`.

Positive OP02 status retains `number`, `calculation="Proven"`, and BOTH
`alternatives` below. Neither branch synthesizes success or chooses a polarity.

| whole status | whole_boolean state | whole_boolean label | out_of_area flag |
|---|---|---|---|
| 0 | complete | false | false |
| 1 | complete | true | true |
| 2 | unmapped | absent | false |
| 3 | unmapped | absent | true |
| 4..255 | unmapped | absent | bit0 |

`alternatives.whole_boolean` contains `state` and, only for 0/1, Boolean `label`.
`alternatives.out_of_area` contains `state="complete"` and
`flags={"out-of-area": bit0}`. Unmapped quantities invent no label.
No candidate domain or saturation is declared here; if a future view declares
an explicit calculation outside a candidate domain it must retain that number
with `candidate_domain=false`, not silently suppress it.

Requested length and returned opaque extent are independent. A request length
of 3 and a positive data array of length 2 remain 3 and 2. Separate calls retain
both contexts even with sequences 0 and 255; no reset/01 correlation rule is
transferred to OP02/03. Configured-register selectors and OP06 conditional widths
are outside this contract and cannot activate another view.

Input mutation, result mutation, and later calls share no nested storage. Missing
versus null, explicit empty, zero and false survive JSON round trips. Partial
results retain last-known-good independent fields only within that result;
no cache or previous-call repair is allowed. Errors never expose a successful
partial result. Physical association, support, freshness, effects, persistence
and delivery remain Unknown, irrespective of exact arithmetic. No native
qualification, hardware operation or umbrella closure follows.

## Decision tables

These local transitions are independent of physical qualification. Validation
precedes view matching; field completeness is evaluated independently per row.

| admission or extent | result state | semantic payload |
|---|---|---|
| invalid JSON or kind | error | no successful result |
| unsupported context | Unknown | empty semantic fields |
| missing required field | incomplete | no raw or number |
| fixed field shorter than width | incomplete | retain raw only |
| fixed field longer than width | incomplete | retain raw only |
| fixed field exactly width | complete | apply declared decoder |
| opaque explicit empty | complete | raw empty and unmodeled |
| opaque explicit nonempty | complete | raw unchanged and unmodeled |
| any incomplete sibling | partial | retain complete siblings |
| all required fields complete | complete | retain unresolved alternatives |

## Synthetic validation

[Owned scenarios](fixtures/ap20_b51a_mirror_fields.json) contain input/result
pairs, paired extents and rejected JSON texts. The standard-library
[contract suite](../tests/test_ap20_b51a_mirror_fields.py) validates table values,
independent constants and bounded transition oracles. It does not implement a
runtime feature or claim to invoke an absent Go function. Focused checks are
supplemental: the fixed full-gate list does not discover this suite automatically.
Full repository CI, independent committed-change review, publication checks and
applicable transport classification remain later ship requirements.
