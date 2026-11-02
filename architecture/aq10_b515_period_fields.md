# B515 finite-period field results

This pre-1.0 local API contract supplies finite period calculations and interval
results for AQ10 (Refs #984 and partial parent #736). It has no code-merge
dependency or unmerged registry-entry prerequisite. AC11/12 retains metadata;
AQ does not duplicate B524 or B555 schedule APIs. Nothing here establishes native
completion, family completeness, qualification or execution.

The [public native B515 contract](../protocols/vaillant/ebus-vaillant-B515.md)
keeps the timer layout at **Hypothesis**, including unresolved equal-endpoint
and `FF` meanings. The calculations below define local behavior; they do not
upgrade that native evidence.

## Callable boundary

Package `vaillant` exposes this pure, standard-library-only evaluator:

```go
func Ab09Aq09Evaluate(ab09Aq09Input json.RawMessage) (json.RawMessage, error)
```

The spelling is intentional. This is a field evaluator, with no additional
Entries/Lookup catalog or schema, pending helper, initialization side effect,
persistent cache, provider registration or automatic caller. This page adds no
production implementation. Any future Go declarations, parameters, locals,
fields, helpers and fixture IDs use `ab09aq09` or exported `Ab09Aq09`; test
functions use `TestAb09Aq09`. Literal JSON/protocol labels and existing
package/library symbols retain their spelling. This compound stem is distinct
from earlier `abNN` names.

## Input and admission

Input is one JSON object containing `context`, `fields` and optional
`arguments`. Context contains `primary`, `secondary`, `direction`, `view`,
optional `operation`, and opaque family/variant keys. Primary, secondary and
operation, where present, are integer bytes (`0..255`). Operation absence is
distinct from explicit zero and null; null is a wrong kind and is rejected.
Identifiers select a local candidate view and never qualify a family.

| Primary | Secondary | Operation | Direction | View | Typed arguments |
|---|---|---|---|---|---|
| 181 | 21 | absent | `request` or `positive` | `periods` | optional `minutes`: integer `0..1440` |
| 181 | 21 | absent | `request` | `intervals` | required `pairs`: exactly three pairs of integer bytes |

Only these combinations apply a formula. Other well-formed contexts, including
explicit operation zero or `intervals` with direction `positive`, return
raw-only `Unknown`. No operation, variant or inverse-mode default is inferred.

`fields` maps names to byte arrays, each element an integer `0..255`.
`periods` uses exactly one byte each from `period0`, `period1` and `period2`.
`intervals` uses the explicit argument endpoints; it does not infer a physical
layout from field positions. Weekday, channel and mode carriers remain raw and
opaque, including explicit empty arrays; five non-injective mode variants are
not decoded. Empty opaque data differs from missing data.

Arguments have exactly the stated typed meanings for the selected view. Unknown
extra keys at every level are retained unchanged and independently of context,
fields and arguments; they acquire no conversion meaning. Reject malformed or
trailing JSON, duplicate keys at any depth, wrong kinds, nonfinite numbers,
fractional or out-of-range byte/integer arguments, and missing required
arguments, with an error and no successful result. Never coerce strings, null
or Booleans into numbers. Wrong-kind field values are admission errors; missing,
empty, short or overlong fixed-width arrays are admitted as per-field
incomplete data, retaining their raw form. Complete independent siblings remain
available. Missing or malformed `pairs` is an argument error, not an incomplete
fixed-width field result.

## Result boundary

Return one JSON object retaining context, raw fields, arguments and extra keys
independently, plus `state`, `results`, `physical: "Unknown"` and
`qualified: false`. Each result retains `raw` and `state`, plus applicable
number, label, flags, reserved, unmodeled, candidate-domain or alternatives
information; do not fabricate inapplicable values. In the examples, `minutes`,
`hour` and `minute` name numeric calculation outputs, `label` is the display,
and `grade` distinguishes candidate meaning from `calculation`.

`complete` means local representation only. Missing or wrong-width period
fields produce `partial` overall, with incomplete per-field results and useful
complete siblings. Unsupported context is `Unknown`. An unresolved semantic
label may coexist with complete raw arithmetic; an Unknown conversion has no
invented number. An absent field has no fabricated `raw` array: its absence in
`fields` remains authoritative. Candidate meaning stays `Hypothesis`; exact
arithmetic may additionally carry `calculation: "Proven"`, which never replaces
the candidate grade. Qualification, freshness, physical support, effects,
persistence and delivery are separate from these grades.

Preserve absence, null, zero, false and explicit empty values wherever admitted
(for example in unknown extra keys); do not substitute one for another. Null
does not become valid in a typed numeric position. Input or output storage
cannot alter a later result or another call. No active executor, scan-default
change, automatic qualification, eBUS MCP incompatibility or GraphQL divergence
is introduced by this architecture companion.

## Period calculations

For each complete one-byte period, raw `0..144` gives `minutes = 10 * raw`,
`hour = minutes / 60` using integer division, and `minute = minutes % 60`.
Display uses two-digit hour/minute components. Exhausting the inclusive domain
produces **145 labels**, including both `00:00` and `24:00`; generating only
144 labels is incorrect. Never wrap `24:00` to `00:00`.

| Raw | Minutes | Display | Conversion state |
|---|---|---|---|
| 0 | 0 | `00:00` | complete |
| 54 | 540 | `09:00` | complete |
| 144 | 1440 | `24:00` | complete |
| 145 | no number | unresolved | Unknown, raw/unmapped |
| 255 | no number | unresolved | Unknown, raw/unmapped |

All raw `145..255` remain unmapped, never labeled unused or unavailable.
Optional `arguments.minutes` encodes only exact multiples of ten: `540` gives
raw `54`, reversibly. `545` gives `Unknown` with no encoded value; flooring,
rounding or an invented number is incorrect. Values outside `0..1440` or
noninteger minutes are admission errors. There is no inverse mode mapping.

A complete valid synthetic input and result:

```json
{"context":{"primary":181,"secondary":21,"direction":"positive","view":"periods","family":"candidate","variant":"opaque"},"fields":{"period0":[0],"period1":[54],"period2":[144],"mode":[]},"arguments":{"minutes":540},"extra":{"empty":[],"null":null,"zero":0,"false":false}}
```

```json
{"context":{"primary":181,"secondary":21,"direction":"positive","view":"periods","family":"candidate","variant":"opaque"},"fields":{"period0":[0],"period1":[54],"period2":[144],"mode":[]},"arguments":{"minutes":540},"extra":{"empty":[],"null":null,"zero":0,"false":false},"state":"complete","results":{"period0":{"raw":[0],"state":"complete","minutes":0,"hour":0,"minute":0,"label":"00:00","grade":"Hypothesis","calculation":"Proven"},"period1":{"raw":[54],"state":"complete","minutes":540,"hour":9,"minute":0,"label":"09:00","grade":"Hypothesis","calculation":"Proven"},"period2":{"raw":[144],"state":"complete","minutes":1440,"hour":24,"minute":0,"label":"24:00","grade":"Hypothesis","calculation":"Proven"},"minutes":{"raw":540,"state":"complete","encoded":54,"grade":"Hypothesis","calculation":"Proven"}},"physical":"Unknown","qualified":false}
```

Independent partial and Unknown examples (retained inputs and result excerpts;
the complete envelope always retains all input members):

| Input change from the complete example | Result |
|---|---|
| Remove `period0`; set `period1` to `[]`; leave `period2:[144]` | overall partial; period0 and period1 incomplete, period1 raw `[]`; period2 still complete, 1440 minutes / `24:00` |
| Set `period0` to `[0,54]` | partial; period0 raw `[0,54]`, incomplete with no number; period1 and period2 still complete |
| Set `period0` to `[145]` and `period1` to `[255]` | those conversions Unknown with their raw arrays and no numbers; period2 still complete |
| Set `arguments.minutes` to `545` | inverse conversion Unknown, raw 545, no encoded value; all three forward results remain available |
| Add `context.operation:0` | raw-only Unknown; apply no period formula |

## Intervals and unresolved scheduling

For `intervals` in the supported request context, use `fields:{}` and
`arguments:{"pairs":[[10,10],[20,30],[40,50]]}`. This is a complete valid
synthetic interval input when combined with the supported context. Retain the
exact three pairs as raw arguments. Per-pair result excerpts are:

```json
[{"raw":[10,10],"state":"complete","label":"disabled","grade":"Hypothesis"},{"raw":[20,30],"state":"complete","label":"enabled-candidate","grade":"Hypothesis"},{"raw":[40,50],"state":"complete","label":"enabled-candidate","grade":"Hypothesis"}]
```

Equality declares disabled independently of interpretability: `[255,255]`
remains disabled although both time conversions are Unknown. Unequal endpoints
retain enabled-candidate state and explicit endpoints even when unmapped.
Never infer deletion from an equal pair or discard its disabled state.

Report a separate local predicate `first.start < second.start < third.start`.
The example starts `10,20,40` yield true (`calculation: Proven`, candidate
meaning `Hypothesis`). Swapping the second and third starts gives
`[[10,10],[40,30],[20,50]]` and false; raw starts change as supplied, but pair
disabled/enabled-candidate classifications stay unchanged. This predicate
compares **only the three starts**. If any endpoint, including an end, is
unmapped, ordering is `Unknown`, with no Boolean substituted. For example
`[[10,10],[20,255],[40,50]]` retains the pair classifications but has Unknown
ordering. Native interval-order semantics remain Unknown.

Do not reject equal, reversed, overlapping or midnight-crossing pairs, and do
not claim device enforcement. In particular, `[40,30]` is admitted; calling it
a known native prohibition is incorrect. Defaults, physical layouts,
deletion/reset, overlap policy, timezone, persistence and enforcement remain
`Unknown`. No family support, physical result, write permission, delivery or
umbrella closure follows from these local results.
