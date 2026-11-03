# B517 local guard results

This pre-1.0 architecture contract defines a pure local field evaluator in
package `vaillant`. The API contract is **Proven**; the adaptation-guard candidate
meaning is **Hypothesis**. This page makes no new native protocol claim or family
qualification. Nothing is stable before Helianthus 1.0.

```go
func Ab11Aq11Evaluate(ab11Aq11Input json.RawMessage) (json.RawMessage, error)
```

Only the Go standard library is required. This is a callable evaluator, not an
Entries/Lookup catalog or schema. It requires no pending helper, initialization
side effect, persistent cache, provider registration, automatic caller or
unmerged registry entry. There is no code-merge dependency. Any implementation's
new declarations, parameters, locals, fields, helpers and fixture IDs start with
`ab11aq11` or exported `Ab11Aq11`; test functions start with `TestAb11Aq11`.
Literal JSON/protocol labels and existing package/library symbols retain their
spelling. This compound stem is distinct from earlier `abNN` names.

## Input and admission

Input is exactly one JSON object with `context`, `fields` and optional
`arguments`. The supported view requires all three. Unknown extra keys at every
depth are retained unchanged and independently of recognized values.

| Member | Admitted representation and role |
| --- | --- |
| `context.primary`, `context.secondary` | Integer bytes, 0..255 when present; select a local candidate view. |
| `context.operation` | Optional integer byte, 0..255. Absent differs from explicit zero; null is a wrong kind and is rejected. |
| `context.direction`, `context.view` | String identifiers selecting the local view. |
| `context.family`, `context.variant` | Opaque keys, retained without interpreting or qualifying a family. |
| `fields.request`, `fields.input` | Separate arrays of integer bytes, 0..255. Variable length; explicit empty arrays remain distinct from missing fields. |
| `arguments.ready_state`, `arguments.final_option` | Required u8 integers for the supported view. |
| `arguments.received_length` | Required nonnegative integer, 0..65535, for the supported view. |

The sole supported combination is `primary=181`, `secondary=23`,
`direction="local"`, **operation absent**, `view="adaptation-guard"`.
Family/variant keys are opaque, not qualification evidence. No other combination
selects a formula: valid unsupported contexts return raw-only **Unknown**.
In particular, explicit operation zero is unsupported, not equivalent to absent.
View-specific arguments are required only for the selected supported view.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range byte values or integer arguments, and
missing required arguments. Return an error with no successful result; do not
coerce strings, null or Booleans into numbers. `context`, `fields` and supplied
`arguments` must be objects; named raw fields are byte arrays. Preserve absent,
null, zero, false and explicit empty values independently wherever permitted,
including opaque and extra values. This preservation does not admit null as a
byte array or typed numeric argument.

Missing, short or overlong fixed-width fields generally retain their raw form
and produce per-field incomplete state, with complete independent siblings still
available. Neither array in this view is fixed-width: request needs at least two
bytes and input at least five initialized bytes. Extra bytes are retained, never
stripped; actual input length still participates in the predicate. Explicitly
empty opaque data is present data, not missing data.

## Complete Boolean predicate

All terms below are required. Evaluate only initialized bytes. A term requiring
a missing byte is unresolved; short arrays yield incomplete results and
`eligible=false`, never an indexing failure.

| Result flag | Exact local condition |
| --- | --- |
| `ready` | `ready_state == 3` |
| `option_nonzero` | `final_option != 0`, using the whole byte, not bit 0 |
| `input_initialized` | Input is present with length at least 5 |
| `length_formula` | With input byte 4 available, `input[4] + 6 == received_length`, using integer arithmetic |
| `length_matches_storage` | With input present, `received_length == len(input)` |
| `request_identity` | Request has at least two bytes and starts `0xB5, 0x17` |
| `input_identity` | Input has at least two bytes and starts `0xB5, 0x18` |
| `eligible` | Conjunction of every preceding flag; false if any term is false or unresolved |

Exact-length equality with initialized input is this API's memory boundary,
not a newly qualified physical check. Declared length beyond initialized storage
cannot pass. Do not omit a conjunction term, alias request/input identities to a
separately named B518 partial family entry, strip a prefix, or reconstruct bytes.
The request and input arrays remain independently identifiable raw evidence.

## Result boundaries and shapes

Return one JSON object retaining `context`, raw `fields`, `arguments` when
present, and all extra keys independently, plus `state`, `results`,
`physical="Unknown"` and `qualified=false`. Each result has `raw` and `state`,
and any applicable `number`, `label`, `flags`, `reserved`, `unmodeled`,
`candidate_domain` or `alternatives`. Do not fabricate unused semantic values.
Missing raw data remains absent, not synthesized as null or an empty array.
Input/output storage must not alter another result or a later call.

The following concrete shape uses `results.request` and `results.input` for
independent field states, and `results.guard` for the predicate and its raw pair.
`complete` means local representation only; `incomplete` describes an individual
short/missing field or dependent guard, and top-level `partial` retains useful
complete siblings. Other mismatches give complete local predicate results with
false eligibility. An unresolved semantic label can coexist with complete raw
arithmetic. Unknown conversions and incomplete data receive no invented number.
Candidate results retain `grade="Hypothesis"`; exact local calculations may
add `calculation="Proven"` without replacing that candidate grade.

All examples are synthetic. JSON numbers below are decimal: 181 is `0xB5`,
23 is `0x17`, 24 is `0x18`, and option 128 is `0x80`.

Complete input:

```json
{
  "context": {"primary": 181, "secondary": 23, "direction": "local", "view": "adaptation-guard"},
  "fields": {"request": [181, 23], "input": [181, 24, 0, 0, 4, 0, 0, 0, 0, 0]},
  "arguments": {"ready_state": 3, "final_option": 2, "received_length": 10}
}
```

Complete result:

```json
{
  "context": {"primary": 181, "secondary": 23, "direction": "local", "view": "adaptation-guard"},
  "fields": {"request": [181, 23], "input": [181, 24, 0, 0, 4, 0, 0, 0, 0, 0]},
  "arguments": {"ready_state": 3, "final_option": 2, "received_length": 10},
  "state": "complete",
  "results": {
    "request": {"raw": [181, 23], "state": "complete"},
    "input": {"raw": [181, 24, 0, 0, 4, 0, 0, 0, 0, 0], "state": "complete"},
    "guard": {
      "raw": {"request": [181, 23], "input": [181, 24, 0, 0, 4, 0, 0, 0, 0, 0]},
      "state": "complete", "grade": "Hypothesis", "calculation": "Proven",
      "flags": {"ready": true, "option_nonzero": true, "input_initialized": true,
        "length_formula": true, "length_matches_storage": true,
        "request_identity": true, "input_identity": true, "eligible": true}
    }
  },
  "physical": "Unknown", "qualified": false
}
```

Independent changes to that complete input have these local results; unchanged
values remain as above. Hexadecimal labels here name bytes, not JSON literals.

| Single change | Result |
| --- | --- |
| `ready_state=2` | Complete; `ready=false`, `eligible=false`. |
| `final_option=0` | Complete; `option_nonzero=false`, `eligible=false`. |
| `input[4]=5` | Complete; 5+6=11 differs from 10, so `length_formula=false`, `eligible=false`. |
| `received_length=9` | Complete; both length flags false, `eligible=false`. |
| Request second byte becomes `0x18` | Complete; `request_identity=false`, `eligible=false`. |
| Input second byte becomes `0x17` | Complete; `input_identity=false`, `eligible=false`. |
| `final_option=0x80` | Complete; whole-byte nonzero is true, `eligible=true`. |

Partial example: replace only input with `[]`, keeping the supported context,
request and arguments above. The enclosing result still retains those members;
its changed state/results fragment is:

```json
{
  "state": "partial",
  "results": {
    "request": {"raw": [181, 23], "state": "complete"},
    "input": {"raw": [], "state": "incomplete"},
    "guard": {
      "raw": {"request": [181, 23], "input": []},
      "state": "incomplete", "grade": "Hypothesis", "calculation": "Proven",
      "flags": {"ready": true, "option_nonzero": true, "input_initialized": false,
        "length_formula": null, "length_matches_storage": false,
        "request_identity": true, "input_identity": null, "eligible": false}
    }
  },
  "physical": "Unknown", "qualified": false
}
```

Here null flags mean unresolved comparisons, not numeric conversions. Input
lengths 0, 1, 2, 3 and 4 all remain incomplete with false eligibility and no
access to byte 4. Available identity comparisons remain usable at lengths 2..4.
A missing input similarly leaves the request complete but omits input `raw` and
the guard's raw input member; storage comparison is then unresolved. A missing
or one-byte request leaves a complete input available and the guard incomplete.

Independent unknown example: add `"operation": 0` to the complete input's
context. Retain the full input, return top-level `state="Unknown"`,
`physical="Unknown"`, `qualified=false`, and raw-only results such as
`"request": {"raw": [181, 23], "state": "Unknown"}` and the corresponding
raw input result. Do not evaluate the guard or emit calculated eligibility.
An independent error example is `"final_option": null` in the supported view:
it returns an error with no successful JSON result.

## Candidate and integration limits

Destination roles, framing, correlation, write permission, timeout, peer support
and the physical B517/B518 relationship remain **Unknown**. Qualification,
freshness, physical support, effects, persistence and delivery are separate from
local completeness and calculation grades. This predicate cannot enable any
communication, native completion, active executor, scan-default change or
automatic qualification.

AC13/14 retains tunnel metadata and AJ25 retains predicate prose; this companion
adds only the complete Boolean predicate contract. There is no tunnel client or
transport adaptation. eBUS MCP compatibility and GraphQL parity are constraints;
this page introduces no changes to either surface. Protocol facts require the
public native documentation contract first. This architecture page establishes
no native-family completeness claim and requires no hardware execution.
