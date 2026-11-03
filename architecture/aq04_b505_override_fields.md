# B505 override and priority field results

This pre-1.0 architecture contract defines a pure local field evaluator for the
Vaillant family. It adds no production behavior or native-family completeness
claim. The [native B505 contract](../protocols/vaillant/ebus-vaillant-B505.md#bounded-sentinel-and-override-candidates)
retains the underlying candidate declarations and their Unknowns. AE03/04 retains
declarations; AO01/02 owns the OP32 replacement API. OP32 is outside this page.
This ordinary companion to AQ03 has no code-merge dependency or unmerged registry
entry requirement. Refs #975 and #736; the parent remains open.

## Callable and admission

Package `vaillant` exports this standard-library-only callable:

```go
func Ab03Aq03Evaluate(ab03Aq03Input json.RawMessage) (json.RawMessage, error)
```

The spelling and compound stem are intentional. Any implementation's new Go
declarations, parameters, locals, fields, helpers and fixture IDs start
`ab03aq03` or exported `Ab03Aq03`; test functions start `TestAb03Aq03`.
Literal JSON/protocol labels and existing library symbols retain their spelling.
This is a field evaluator, with no additional Entries/Lookup catalogue or schema,
initialization side effect, persistent cache, provider registration, automatic
caller, clock, timer or write builder.

Input is exactly one JSON object containing `context`, `fields` and optional
`arguments`, plus independently preserved extra keys. `context` contains
`primary`, `secondary`, `operation` when present, `direction`, `view`, and opaque
family/variant keys. Primary, secondary and operation, when present, are integers
0..255. An absent operation differs from explicit zero; null is invalid for a
numeric selector. Family/variant identifiers select local candidate views and
never qualify a family. No family-specific interpretation is introduced here.

`fields` is an object of named byte arrays, each element an integer 0..255.
`arguments`, when supplied, is an object; the only specified typed argument is
`display_percent`, required for the OP4D display evaluation, an integer 0..255.
OP61 and priority require no typed arguments. Extra input keys at every level are
retained unchanged; they acquire no formula or meaning.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range bytes or integer arguments, and missing
required arguments: return an error with no successful result. Strings, null and
Booleans never become numbers. Absent, null, zero, false and explicit empty values
remain distinct wherever permitted (for example in opaque extra keys); typed
selectors, byte arrays and typed arguments still obey their admission rules.

## Finite supported views

All rows require `primary=181`, `secondary=5`, `direction="request"`.
These local selections and candidate meanings are **Hypothesis**. The local
request direction and named field grouping do not resolve native direction,
remote-control operation identity, pump-display operation identity or offsets.

| View | Operation (JSON integer) | Fields and branches | Typed arguments | Candidate metadata |
|---|---|---|---|---|
| `override` | OP4D (77) | Independent one-byte `sensor_status` and `remote_control` | `display_percent`: integer 0..255 | `candidate_validity_seconds=900` |
| `override` | OP61 (97) | `dhw_setpoint` is opaque; retain every supplied field raw | None required | `candidate_validity_seconds=900` |
| `priority` | OP4E (78) | One-byte `priority`: number 0..255, ascending order | None required | No duration |

Unknown combinations, including another direction/view/operation or absent
operation, return raw-only `Unknown` without a formula. Explicit operation zero
is retained as zero and is unsupported. Invalid selector kinds fail admission.
For OP61, setpoint width and conversion remain Unknown; an explicitly empty
opaque array is present data, distinct from a missing field. A supplied
`sensor_status=[85]` stays raw, without any OP4D label.

| OP4D branch | Exact local result | Limit |
|---|---|---|
| `sensor_status=[85]` (hex 55) | `label="short-circuit"` | Candidate meaning |
| `sensor_status=[170]` (hex AA) | `label="open"` | Candidate meaning |
| `sensor_status=[84]` (hex 54), or any other byte | `label="unmapped"` | Semantic meaning Unknown |
| `remote_control=[1]` | `label="enabled"` | Candidate meaning |
| `remote_control=[2]`, or any byte other than 1 | `label="unmapped"` | Semantic meaning Unknown |
| `display_percent` in 0, 25, 50, 75, 100 | `candidate_domain=true` | Discrete display values only |
| Any other admitted `display_percent`, including 26 | `candidate_domain=false` | Preserve 26; no rounding |

The display result uses the argument, never a raw pump byte. No raw-to-percent
conversion is known. Both override operations retain 900 only as a candidate
declaration; neither starts a timer or asserts expiration. Priority has no
inherited duration, quantity codec, freshness, control eligibility or execution.

## Result shape and partial boundaries

Return one JSON object retaining `context`, raw `fields`, `arguments` (including
its absence) and extra keys independently, with `state`, `results`,
`physical="Unknown"` and `qualified=false`. Each result retains `raw` and `state`,
and any applicable `number`, `label`, `flags`, `reserved`, `unmodeled`,
`candidate_domain` or `alternatives`. Do not invent flags or conversions.
Candidate meanings retain `grade="Hypothesis"`; exact local arithmetic or domain
checks may additionally carry `calculation="Proven"`. Calculation grade never
replaces candidate grade.

`complete` means local representation only. Unresolved semantic labels may
coexist with complete raw arithmetic. Missing, short or overlong fixed-width
fields give a per-field `incomplete` state and aggregate `partial`, preserving
the original form and complete independent siblings. Missing raw data stays
absent, rather than becoming null or an empty array. No number is invented for
incomplete data or Unknown conversion. Opaque fields with Unknown conversion
remain `Unknown`, even when their raw data is present.

Storage is isolated: changing input or returned output cannot change another
call or a later result. Errors supply no successful replacement. A caller may
retain useful partial last-known-good state separately; neither a partial result
nor an error admits unsupported semantic data or silently overwrites prior raw
evidence. This pure evaluator performs no persistence.

## Synthetic examples

A complete valid OP4D input and result (JSON bytes use decimal notation):

```json
{"context":{"primary":181,"secondary":5,"operation":77,"direction":"request","view":"override","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"sensor_status":[85],"remote_control":[1]},"arguments":{"display_percent":25},"extra":{"absent_is_distinct":null,"zero":0,"false":false,"empty":[]}}
```

```json
{"context":{"primary":181,"secondary":5,"operation":77,"direction":"request","view":"override","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"sensor_status":[85],"remote_control":[1]},"arguments":{"display_percent":25},"extra":{"absent_is_distinct":null,"zero":0,"false":false,"empty":[]},"state":"complete","results":{"sensor_status":{"raw":[85],"state":"complete","label":"short-circuit","grade":"Hypothesis"},"remote_control":{"raw":[1],"state":"complete","label":"enabled","grade":"Hypothesis"},"display_percent":{"raw":25,"state":"complete","number":25,"candidate_domain":true,"grade":"Hypothesis","calculation":"Proven"}},"candidate_validity_seconds":900,"grade":"Hypothesis","physical":"Unknown","qualified":false}
```

Independent partial example: with the same OP4D context, `fields` equal to
`{"sensor_status":[],"remote_control":[1]}` and `arguments={"display_percent":26}`,
the aggregate state is `partial`. The relevant results are:

```json
{"sensor_status":{"raw":[],"state":"incomplete"},"remote_control":{"raw":[1],"state":"complete","label":"enabled","grade":"Hypothesis"},"display_percent":{"raw":26,"state":"complete","number":26,"candidate_domain":false,"grade":"Hypothesis","calculation":"Proven"}}
```

Omitting `sensor_status` instead leaves its result's `raw` absent with
`state="incomplete"`; `[85,170]` preserves both bytes and remains incomplete.
The remote-control and display results stay available in each case.

Independent Unknown examples: OP61 with `fields={"sensor_status":[85],"dhw_setpoint":[]}`
and no arguments retains both arrays, gives raw-only `Unknown` results without
sensor labels or a setpoint number, and retains candidate metadata 900. Omitting
`dhw_setpoint` keeps that absence distinct from `[]`. OP4D context with
`operation=0` instead returns aggregate and raw-only results `Unknown`, retains
all supplied arguments/extra keys, and applies neither labels, display-domain
checks nor duration metadata. Neither case reports qualification.

For priority, use the supported OP4E context and no arguments:

| `fields.priority` | Result number | Candidate label | Ordering |
|---|---|---|---|
| `[0]` | 0 | `lowest` | Below 127 and 255 |
| `[127]` | 127 | None invented | Between 0 and 255 |
| `[255]` | 255 | `highest` | Above 0 and 127 |

Each priority result retains its raw array, is locally `complete`, and keeps
`grade="Hypothesis"` with exact numeric calculation `Proven`, physical Unknown
and qualification false. No priority result has candidate duration.

These page assertions reject the following substitutions: decoding hex 54 as
open; enabling every nonzero remote-control byte; rounding 26 to 25; copying OP4D
sensor meanings into OP61; reversing priority order; assigning duration to OP4E.
They constrain local representation, not peer behavior.

## Evidence and shipping limits

Field locations, setpoint conversion, peer acceptance, override expiration and
physical effects remain **Unknown**. Native support, acknowledgement,
qualification, freshness, persistence, delivery and execution are not established.
No native completion, active executor, scan-default change or automatic
qualification follows. Existing eBUS MCP compatibility and GraphQL parity remain
requirements; this page changes neither interface and introduces no namespace.
Nothing here is stable before Helianthus 1.0.

Before merge, Gate D with its prescribed read-only prerequisites, full repository
CI, publication checks and fresh independent committed-change review remain
mandatory. Transport classification is documentation-only: no transport code or
hardware smoke result is supplied by these synthetic examples.
