# B503 control-field results and category boundaries

This pre-1.0 architecture contract defines a pure local field evaluator for the
Vaillant family. Its API contract is **Proven** as a local definition; candidate
meanings remain **Hypothesis**, independently of exact arithmetic. Nothing here
establishes native-family completeness, physical support or successful execution.

The [public native B503 contract](../protocols/vaillant/ebus-vaillant-B503.md)
retains the wire evidence and unresolved layouts. The local views below do not
settle those layouts or import other catalog/category labels. In particular,
local reset acceptance is distinct from the native page's candidate OP06 feedback
table. AI07/08 and AJ03/04 retain declarations; AN05/06 retains history/calendar
parsing. OP01 is outside this evaluator.

## Callable boundary

Package `vaillant` exports, using only the Go standard library:

```go
func Ab07Aq07Evaluate(ab07Aq07Input json.RawMessage) (json.RawMessage, error)
```

This is a callable evaluator, with no Entries/Lookup catalog or schema,
initialization side effect, persistent cache, provider registration, automatic
caller or pending helper. This page requires no unmerged registry entry or code
merge dependency. It adds no implementation. Every new Go declaration,
parameter, local, field, helper and fixture ID uses `ab07aq07` or exported
`Ab07Aq07`; test functions use `TestAb07Aq07`. Existing package/library symbols,
standard-library members and literal JSON/protocol labels retain their spelling.

## Input and admission

Input is one JSON object containing `context`, `fields` and optional `arguments`.
`context` contains `primary`, `secondary`, `operation` when present, `direction`,
`view`, and opaque family/variant keys. Primary, secondary and operation are
integers 0..255 when present. An absent operation differs from explicit zero;
null is not a byte and is rejected. Context identifiers select a local candidate
view and never qualify a family.

`fields` maps names to arrays of integer bytes 0..255. Explicitly empty opaque
data is `[]`, distinct from missing data. `arguments`, when supplied, contains
exactly the explicitly stated typed values for the selected view; none of the
views below requires an argument. Unknown extra input keys are retained unchanged
at their original scope, independently of interpreted data.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range bytes or integer arguments, and
missing required arguments: return an error and no successful result. Never
coerce strings, null or Booleans into numbers. Missing, short or overlong
fixed-width fields instead produce per-field incomplete state, preserve their
raw form and retain complete independent siblings. No number is invented for an
incomplete field or an Unknown conversion.

## Finite supported views

All rows require `primary=181`, `secondary=3`. Operations below are decimal
(the OP names use hexadecimal notation). Each selected interpretation is
**Hypothesis**. Any other combination, including absent operation, is raw-only
**Unknown**, with no formula applied.

| View | Operation | Direction | Fixed-width fields |
|---|---|---|---|
| `reset-acceptance` | 3 or 6 (OP03/OP06) | `positive` | `acceptance`: 1 byte |
| `current-errors` | 7 (OP07) | `positive` | `flags`: 1; `error0` through `error4`: 2 each; `feedback`: 1 byte |
| `category-common` | 4 (OP04) | `request` | `category`: 1 byte |
| `category-reset` | 3 or 6 (OP03/OP06) | `request` | `category`: 1 byte |

| View/field | Complete local interpretation | Unresolved boundary |
|---|---|---|
| `reset-acceptance.acceptance` | 0 labels false; 1 labels true; 2..255 unmapped | Default 0 is metadata only; never materialize it when absent. This candidate Boolean is distinct from generic accepted/rejected feedback. |
| `current-errors.flags` | Independent positions 0..4: `(byte >> position) & 1`; reserved value `byte & 0xE0` | Do not assign semantic labels to reserved bits or synthesize errors from flags. |
| `current-errors.error0` through `error4` | Each separate LEu16: `raw[0] + 256 * raw[1]` | No code-to-text conversion or special sentinel meaning is supplied. |
| `current-errors.feedback` | 1 labels `accepted`; every other byte labels `rejected` | Acceptance proves no reset effect. |
| `category-common.category` | 2 labels `predictive-maintenance`; retain `candidate_domain` 1..5 | Labels for 1, 3, 4, 5 remain Unknown; other byte labels are also Unknown. |
| `category-reset.category` | 1 labels `error`; 3 labels `status` | 2 stays unlabeled; no other label or common-table inheritance is supplied. |

## Result boundary

Return one JSON object retaining `context`, raw `fields`, `arguments` when
present, and extra keys independently, plus `state`, `results`,
`physical="Unknown"` and `qualified=false`. Each present field result has its
`raw` plus `state` and applicable `number`, `label`, `flags`, `reserved`,
`unmodeled`, `candidate_domain` or `alternatives`. A missing field has an
incomplete result without a fabricated `raw`; its absence also remains visible
in `fields`. Unknown extra data is preserved without invented interpretation.

`state="complete"` means local representation only. Missing or wrong-width
fixed fields yield aggregate `state="partial"`; complete siblings remain
available. Unsupported context yields `state="Unknown"`. An unresolved semantic
label can coexist with complete raw arithmetic. Examples use `grade` for the
candidate meaning (**Hypothesis**) and, where exact arithmetic applies,
`calculation="Proven"`; the calculation never replaces the candidate grade.
A label of `"Unknown"` denotes an unresolved label, not a new mapping.

Retain absent, null, zero, false and explicit empty values independently wherever
the contract permits them, including opaque extra data. Numeric fields do not
permit null. Input/output storage cannot alter a later result or another call.

## Synthetic examples

A complete valid OP07 input keeps five words independent and preserves opaque
extras (all numbers in JSON are decimal):

```json
{"context":{"primary":181,"secondary":3,"operation":7,"direction":"positive","view":"current-errors","family":"synthetic"},"fields":{"flags":[31],"error0":[1,0],"error1":[0,1],"error2":[52,18],"error3":[0,0],"error4":[255,255],"feedback":[2],"opaque":[]},"arguments":{},"extra":{"nil":null,"zero":0,"off":false}}
```

Its complete result is:

```json
{"context":{"primary":181,"secondary":3,"operation":7,"direction":"positive","view":"current-errors","family":"synthetic"},"fields":{"flags":[31],"error0":[1,0],"error1":[0,1],"error2":[52,18],"error3":[0,0],"error4":[255,255],"feedback":[2],"opaque":[]},"arguments":{},"extra":{"nil":null,"zero":0,"off":false},"state":"complete","physical":"Unknown","qualified":false,"results":{"flags":{"raw":[31],"state":"complete","flags":[true,true,true,true,true],"reserved":0,"grade":"Hypothesis","calculation":"Proven"},"error0":{"raw":[1,0],"state":"complete","number":1,"grade":"Hypothesis","calculation":"Proven"},"error1":{"raw":[0,1],"state":"complete","number":256,"grade":"Hypothesis","calculation":"Proven"},"error2":{"raw":[52,18],"state":"complete","number":4660,"grade":"Hypothesis","calculation":"Proven"},"error3":{"raw":[0,0],"state":"complete","number":0,"grade":"Hypothesis","calculation":"Proven"},"error4":{"raw":[255,255],"state":"complete","number":65535,"grade":"Hypothesis","calculation":"Proven"},"feedback":{"raw":[2],"state":"complete","label":"rejected","grade":"Hypothesis"}}}
```

Flag array positions above are bits 0 through 4, in order. Replacing `[31]`
(`1F`) with `[224]` (`E0`) gives `[false,false,false,false,false]` and
`reserved=224`; no reserved flag receives a label. Neither value creates errors.

Independent partial example: remove only `error2` from the complete input.
The output retains that omission in `fields`, has `state="partial"`, and has
`results.error2={"state":"incomplete"}`. All other results above remain complete:
`error0=1`, `error1=256`, `error3=0`, `error4=65535`, with flags and feedback
unchanged. Supplying `error2:[]`, `[52]` or `[52,18,0]` instead retains that exact
raw array in an incomplete result with no `number`. These states cannot erase
useful last-known-good independent sibling results; there is no cross-call cache.

An independent unsupported-context input and raw-only result:

```json
{"context":{"primary":181,"secondary":3,"operation":0,"direction":"positive","view":"current-errors"},"fields":{"error0":[1,0]},"extra":false}
```

```json
{"context":{"primary":181,"secondary":3,"operation":0,"direction":"positive","view":"current-errors"},"fields":{"error0":[1,0]},"extra":false,"state":"Unknown","results":{},"physical":"Unknown","qualified":false}
```

The following complete-field examples use the matching supported context. Raw
arrays are retained; all candidate meanings retain **Hypothesis**. An unresolved
label does not make a complete one-byte field incomplete.

| View | Field/raw | Result assertion |
|---|---|---|
| `reset-acceptance` | `acceptance:[0]` / `[1]` | False / true candidate Boolean labels, respectively; no reset execution. |
| `reset-acceptance` | `acceptance:[2]` | Complete raw value, unmapped label Unknown; never `rejected`. |
| `current-errors` | `feedback:[2]` | Complete label `rejected`; do not merge acceptance and feedback tables. |
| `current-errors` | `feedback:[1]` | Complete label `accepted`; no inference of a successful reset. |
| `category-common` | `category:[2]` | Complete `predictive-maintenance`, `candidate_domain:[1,2,3,4,5]`. |
| `category-common` | `category:[1]`, `[3]`, `[4]`, `[5]` | Complete raw values, labels Unknown; retain the same candidate domain. |
| `category-reset` | `category:[2]` | Complete raw value, label Unknown; never inherit `predictive-maintenance`. |
| `category-reset` | `category:[1]` / `[3]` | Complete labels `error` / `status`, respectively. |

The ordered words `[1,256,4660,0,65535]` assert little-endian interpretation and
five separate results: big-endian decoding or collapsing the words violates this
contract. Missing acceptance is incomplete, never a synthesized false default.
Invalid byte input such as `acceptance:[true]` returns an error, not a partial
successful result.

## Remaining Unknowns and companion scope

Unlock character encoding and coordinates, OP05 mode position, physical reply
forms, reset effects, forwarding, freshness and session exclusivity remain
**Unknown**. Native support, persistence and delivery also remain **Unknown**.
There is no unlock parser, reset executor, active executor, scan-default change
or automatic qualification. No physical outcome follows from local completeness
or accepted feedback. This pure evaluator adds no eBUS MCP or GraphQL surface
change; those compatibility and parity boundaries remain applicable to callers.

This is partial progress for #736 via #985, an ordinary companion to AQ07 with no
merge dependency. Gate D with its prescribed read-only reference prerequisites,
full repository CI, publication checks and fresh independent committed-change
review remain mandatory before merge; applicable transport classification must
also be recorded. This page does not close the parent or establish execution.
