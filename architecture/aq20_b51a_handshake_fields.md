# B51A handshake field results and conditional raw spans

This pre-1.0 architecture companion defines the bounded local API for AQ19/AQ20.
It is ordinary partial progress toward issue #736, with no code-merge dependency
or unmerged registry entry required. It defines software representation, not a
native protocol contract or family qualification. The finite facts below are
its entire scope; no native-family completeness follows.

## Callable contract and admission

**Proven local API contract:** package `vaillant` exports:

```go
func Ab19Aq19Evaluate(ab19Aq19Input json.RawMessage) (json.RawMessage, error)
```

The evaluator is pure and uses only the Go standard library. This page requires
no Entries/Lookup catalog, schema, initialization side effect, persistent cache,
provider registration, automatic caller, pending helper or sibling checkout.
It does not add an implementation. Any new Go declaration, parameter, local,
field, helper or fixture ID for this contract starts `ab19aq19` or exported
`Ab19Aq19`; test functions start `TestAb19Aq19`. Literal JSON/protocol labels,
existing package/library symbols and standard-library members keep their spelling.
The compound stem is distinct from earlier `abNN` names.

Input is one JSON object containing `context`, `fields` and optional `arguments`.
`context` contains `primary`, `secondary`, optional `operation`, `direction`,
`view` and opaque family/variant keys. Primary, secondary and operation, when
present, are integers in 0..255. Omitted operation differs from explicit zero;
null is not an omitted operation and is rejected as a wrong kind. Context
identifiers select a candidate local view and never qualify a family.

`fields` contains named arrays of integer bytes in 0..255. An explicitly empty
opaque array is valid data, distinct from a missing field. `arguments` supplies
exactly the explicitly stated typed values for the selected view; no typed
argument or required argument is specified for the finite views on this page.
Unknown extra input keys are retained unchanged, independently of context,
raw fields and arguments; they do not enable additional formulas. The top-level
keys `state`, `results`, `physical` and `qualified` are reserved for generated
output: an input carrying any of them is rejected with an error, like a
duplicate key, so no retained extra can collide with a generated key.

Reject malformed JSON, trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional or out-of-range byte/integer arguments, and missing
required arguments with an error and no successful result. Strings, null and
Booleans are never coerced into numbers. This syntactic/type admission precedes
context selection, including for unsupported contexts.

Missing, short or overlong fixed-width fields instead produce per-field
`incomplete` state, retain their supplied raw form, and leave complete independent
siblings available. Missing raw stays absent; it is not replaced by null or an
empty array. No number is invented for incomplete data or an Unknown conversion.
Opaque spans have no fixed-width admission requirement.

## Finite candidate views

All combinations in this table have candidate meaning **Hypothesis**, including
the positive-response flag bits and the conditional `dsn`/`start`/`offset`
behavior; they are candidate local representation, not a native or response
layout contract, and their provenance is not published. Primary
is decimal 181 (`0xB5`) and secondary is decimal 26 (`0x1A`) throughout.
No other context combination applies these formulas.

| View | Operation | Direction | Fields |
| --- | --- | --- | --- |
| `reset` | absent | `request` | `sequence` |
| `reset` | absent | `positive` | `sequence`, `ack` |
| `handshake` | 1 | `request` | `sequence`, `flags`, `dsn`, `start`, `offset`, `crc` |
| `handshake` | 1 | `positive` | `sequence`, `flags`, `family_code`, conditional `dsn`, `start`, `offset` |
| `sequence-pair` | absent (reset) | `pair` | `request_sequence`, `response_sequence` |
| `sequence-pair` | 1 (handshake) | `pair` | `request_sequence`, `response_sequence` |

The absent reset operation is not an encoded zero. An explicit zero, a different
operation or an unsupported direction/view returns raw-only `Unknown`, with no
formula applied. No other operation inherits sequence-pair correlation.

| Field and branch | Width | Local result and retained boundary |
| --- | --- | --- |
| `sequence`, either single direction | 1 byte | Raw unsigned byte number; no success or completion meaning. |
| `ack`, reset positive | 1 byte | Bit 0 is candidate `denied`; bits 1..7 are `unmodeled`. Whole zero is only a default, never a success label. |
| `flags`, handshake request | 1 byte | Bits 0 `power-on/start`, 1 `change`, 2 `CRC-support`; bits 3..7 `reserved`. |
| `dsn`, `start`, `offset`, handshake request | Opaque arrays | Independent raw spans; widths and order are Unknown. |
| `crc`, handshake request | Exactly 2 bytes | LEu16 raw word: first byte + 256 × second byte. Algorithm, coverage and replacement number are Unknown. |
| `flags`, handshake positive | 1 byte | Bits 0 `valid`, 1 `invalid`, 2 `blocked`, 3 `change`, 4 `denied`, 5 `invalid-range`, 6 `not-user-adjustable`; bit 7 `reserved`. |
| `family_code`, handshake positive | 1 byte | Raw unsigned byte number; semantic family label is Unknown. It does not qualify a family. |
| `dsn`, `start`, `offset`, handshake positive | Opaque arrays | Bit 3 false: semantic state `absent-unless-change`, retaining each supplied raw array. Bit 3 true: retain each span independently, imposing no width. |
| `request_sequence`, `response_sequence`, sequence-pair | Exactly 1 byte each | Equality is a candidate correlation predicate only; mismatch yields `results.correlation.correlated=false`. |

Flags need not be exclusive. Request-change bit 1 and positive-change bit 3
are distinct: positive flags `02` means `invalid`, not `change`; positive `08`
selects the conditional spans. Hex byte notation here describes raw bytes,
while JSON examples use decimal integers. Reserved and unmodeled bits remain
visible; neither becomes a success/failure inference. If positive flags are
incomplete, their conditional semantic branch is Unknown and supplied spans
remain raw. An absent opaque span remains absent, including when change is true;
this page assigns no missing-span width or value.

## Result shape and grades

Return one JSON object retaining `context`, original raw `fields`, supplied
`arguments` and extra keys independently, with `state`, `results`,
`physical="Unknown"` and `qualified=false`. Every result retains `raw` when
supplied, a `state`, and applicable `number`, `label`, `flags`, `reserved`,
`unmodeled`, `candidate_domain` or `alternatives`. For `sequence-pair`, `results` holds the entries `request_sequence` and
`response_sequence` (each shaped like `sequence`) plus one entry `correlation`,
an object with `state`, Boolean `correlated`, `grade` and `calculation`; no
`correlated` key appears at the top level or inside the sequence entries. If
either sequence is incomplete, `correlation` has state `incomplete` and no
`correlated` key. A missing fixed-width field's result is
incomplete without a fabricated `raw`; a missing opaque span's result has state
`absent`, also without a fabricated `raw`. These examples use `grade` to keep
candidate meaning **Hypothesis**, with `calculation="Proven"` for exact local
arithmetic/bit extraction. Calculation grade never replaces candidate grade.

Top-level `complete` means local representation only; missing or incorrectly
sized fixed-width fields, and incomplete positive flags, yield `partial`.
Opaque `dsn`, `start` and `offset` spans are optional in every branch, including
request and change-positive input: an absent span is result state `absent` and
alone never makes the top level `partial`. Unsupported contexts yield `Unknown`
and raw-only results. An unresolved semantic label can coexist with complete
raw arithmetic, as for `family_code`. A conditional span's semantic
`absent-unless-change` state does not discard its raw value. These states do
not establish qualification, freshness, physical support, effects, persistence
or delivery. Input and output storage cannot alter a later result or another
call. Absent, null, zero, false and explicit empty values remain distinct
wherever their kinds are permitted (for example, in opaque extra metadata).

### Complete synthetic input and result

Reset positive, with omitted operation and ack byte `02`:

```json
{
  "context": {"primary": 181, "secondary": 26, "direction": "positive", "view": "reset"},
  "fields": {"sequence": [0], "ack": [2]},
  "arguments": {},
  "extra": {"unknown": null, "zero": 0, "enabled": false, "empty": []}
}
```

```json
{
  "context": {"primary": 181, "secondary": 26, "direction": "positive", "view": "reset"},
  "fields": {"sequence": [0], "ack": [2]},
  "arguments": {},
  "extra": {"unknown": null, "zero": 0, "enabled": false, "empty": []},
  "state": "complete",
  "physical": "Unknown",
  "qualified": false,
  "results": {
    "sequence": {"raw": [0], "state": "complete", "number": 0, "grade": "Hypothesis", "calculation": "Proven"},
    "ack": {"raw": [2], "state": "complete", "flags": {"denied": false}, "unmodeled": 2, "grade": "Hypothesis", "calculation": "Proven"}
  }
}
```

Decoding reset ack `02` as denied violates this contract: its bit 0 is clear.
The unmodeled high bit must survive. Ack `00` likewise carries no success label.

### Other complete branch results

The rows below give independent synthetic fields for the exact contexts named
above; each retains its own complete context and raw fields in the output.

| Context and fields | Result assertions |
| --- | --- |
| Handshake request: `sequence=[7]`, `flags=[2]`, `dsn=[17]`, `start=[34,35]`, `offset=[]`, `crc=[52,18]` | Request `change=true`; `CRC-support=false`. Raw CRC bytes `34 12` produce `number=4660`, calculation Proven, candidate meaning Hypothesis. No CRC-valid assertion is available. The three opaque arrays remain distinct, including the empty offset. |
| Handshake positive: `sequence=[7]`, `flags=[2]`, `family_code=[9]`, `dsn=[17]`, `start=[34,35]`, `offset=[]` | `invalid=true`, `change=false`; each span has semantic state `absent-unless-change` and keeps its own raw array. Family code has complete raw `number=9` and Unknown label meaning. |
| Handshake positive: same fields but `flags=[8]` | `change=true`, `invalid=false`; retain `dsn=[17]`, `start=[34,35]`, `offset=[]` independently without a width or ordering claim. |
| Sequence-pair, absent operation: `request_sequence=[0]`, `response_sequence=[255]` | Complete local comparison, `results.correlation.correlated=false`, grade Hypothesis, calculation Proven; no success. |
| Sequence-pair, operation 1: `request_sequence=[255]`, `response_sequence=[255]` | Complete local comparison, `results.correlation.correlated=true`, grade Hypothesis, calculation Proven; no success. |

A positive result must not borrow the request's change bit. Neither branch may
impose fixed DSN/start/offset widths or discard supplied conditional raw arrays.
Sequence mismatch must never yield `correlated=true`; equality never proves
success. The CRC numeric value proves only LEu16 arithmetic, never validation.

### Independent partial, Unknown and rejected cases

| Synthetic input case | Required boundary |
| --- | --- |
| Reset positive: `sequence=[255]`, missing `ack` | Top-level `partial`; sequence remains complete with number 255; ack is incomplete with raw absent and no denied inference. |
| Handshake request: `sequence=[7]`, `flags=[2]`, `dsn=[17]`, `start=[]`, `offset=[51]`, `crc=[52]` | Top-level `partial`; CRC raw `[52]` is incomplete with no number. Sequence, flags and independent opaque arrays remain available. CRC `[]` or `[52,18,0]` is likewise incomplete, not rejected for width alone. |
| Handshake positive: `sequence=[7]`, `flags=[]`, `family_code=[9]`, `dsn=[17]` | Top-level `partial`; flags incomplete, conditional branch Unknown, DSN raw retained, family raw number 9 still complete with semantic meaning Unknown. Absent `start` and `offset` are result state `absent`. |
| Reset context with explicit `operation=0` and valid byte arrays | Raw-only `Unknown`; no ack formula or sequence correlation. |
| Primary 180 with otherwise valid handshake request input | Raw-only `Unknown`; raw fields and extras survive without a CRC conversion. |
| Handshake request: `sequence=[7]`, `flags=[2]`, `crc=[52,18]`, no `dsn`, `start` or `offset` | Top-level `complete`; each absent span is result state `absent` with raw absent. |
| Input carrying a top-level `state`, `results`, `physical` or `qualified` key, operation null, `crc=[52.5,18]`, byte 256, Boolean byte, duplicate nested key, trailing object, or malformed JSON | Error, no successful result; none becomes a partial numeric conversion. |

## Remaining boundaries

CRC algorithm, coverage and replacement number, physical offsets, startup
suppression, TTL, native support and completion remain **Unknown**. Physical
effects, persistence and delivery also remain Unknown. No executor, scan-default
change, automatic qualification or native-family completeness claim follows.
AI15/AJ07 retain declarations; AP19/20 owns OP02/03 mirror data. Configured-register
tables and diagnostic OP04..06 remain separate. This page introduces no eBUS MCP
or GraphQL surface change; parity and compatibility are not established by a
local arithmetic example.

No new protocol fact is established here. Native claims require the public native
documentation contract and independently attributable evidence first. Full Gate D
with its prescribed read-only references, publication checks, applicable transport
classification and fresh independent review of the committed change remain
required before merge. No physical result or parent-issue closure follows.
