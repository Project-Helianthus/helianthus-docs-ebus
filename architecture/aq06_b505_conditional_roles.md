# B505 conditional role evaluation

This pre-1.0 local API contract defines a bounded explicit-input evaluator for
Vaillant family candidates. Nothing is stable before Helianthus 1.0. It makes no
new native wire claim: native protocol facts require the public native docs
contract first. Context selects a local candidate view and never qualifies a
family. Native support, physical effects, persistence and delivery remain
`Unknown`.

AK03/04 retains semantic associations; AQ adds this evaluator. AO01/02 and
AQ03/04 retain their own sentinels and overrides. This architecture companion
has no code-merge dependency or unmerged registry-entry requirement.

## Callable boundary

Package `vaillant` exports the following function, using only the Go standard
library and retaining the existing package spelling:

```go
func Ab05Aq05Evaluate(ab05Aq05Input json.RawMessage) (json.RawMessage, error)
```

The contract is a pure callable field evaluator, with no `Entries`/`Lookup`
catalog, schema, pending helper, sibling checkout, initialization side effect,
persistent cache, provider registration or automatic caller. This page adds no
production behavior, executor or automatic qualification. It changes neither
eBUS MCP compatibility nor GraphQL parity.

Any implementation declarations, parameters, locals, fields, helpers and fixture
IDs use the compound prefix `ab05aq05` or exported `Ab05Aq05`; test functions use
`TestAb05Aq05`. Literal JSON/protocol labels, existing package/library symbols
and standard-library members keep their spelling.

## Input, preservation and rejection

Input is one JSON object containing `context`, `fields` and optional `arguments`.
Unknown extra keys are retained unchanged at their original location, except
that the top-level names `state`, `results`, `physical` and `qualified` are
reserved for the evaluator output: an input carrying any of them at the top level
is rejected with an error. Nested keys of that spelling are ordinary extras. The
following are input shapes, not new wire encodings:

| Member | Local contract |
| --- | --- |
| `context.primary`, `context.secondary` | Integer bytes, 0..255. |
| `context.operation` | Integer byte, 0..255 when present. Absence differs from explicit 0; null is invalid. |
| `context.direction`, `context.view` | Context identifiers selecting the finite views below. |
| Family/variant keys in `context` | Opaque identifiers; no qualification or family completeness follows. |
| `fields` | Named arrays of integer bytes, 0..255. Explicit empty opaque data is `[]`, distinct from a missing field. |
| `arguments` | Exactly the explicitly stated typed values for the selected view; unknown extra keys remain uninterpreted and retained. |

Reject malformed JSON, trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional or out-of-range bytes or integer arguments, and
missing required arguments. Return an error and no successful result. Never
coerce a string, null or Boolean into a number. A wrong-kind field is an error;
a missing, short or overlong fixed-width byte array instead produces per-field
incomplete state, preserving its raw form and useful complete independent
siblings. Validation and raw preservation also apply to unsupported contexts;
unsupported context never authorizes a formula.

Absent, null, zero, false and explicit empty values remain distinct wherever
permitted. In particular, null is a permitted arbitrary scalar token for
`previous` or `requested`, but is not a byte or a numeric demand. An absent
operation is retained as absent and does not select an explicit operation.
Input and output storage cannot alter another call or a later result.

## Finite candidate views

Every supported row has `primary=181`, `secondary=5`, `direction="request"`.
Operations below are hexadecimal protocol labels with their decimal JSON values.
The view and operation must both match. These associations have candidate grade
`Hypothesis`; all other combinations return raw-only `Unknown` without a formula,
including absent operation, operation 0, another direction or another view.

| `context.view` | Operation | Fields | Required arguments and branches |
| --- | --- | --- | --- |
| `unchanged` | OP5A (90) or OP3D (61) | No replacement byte is defined. | `replacement`: Boolean; `previous`, `requested`: arbitrary finite JSON scalar tokens. True retains previous and labels `unchanged`; false returns requested as `numeric-candidate`, without a new conversion. |
| `dhw-enable` | OP31 (49) | `enabled`: exactly one byte. | None. 1 labels `ordinary-DHW-eligible`; 0 labels `frost-only-eligible`; 2..255 remain `unmapped`. |
| `parallel-charge` | OP18 (24) or OP27 (39) | `disable`: exactly one byte. | `role`: `mixer`, `heating` or `dhw`; `parallel`: Boolean. Branches below. |
| `flow-excess` | OP17 (23) | No encoding defined. | Finite numeric `demand` and `excess`; return their mathematical sum as a local candidate. |
| `programmed-start` | OP09 (9) | Preserve `start` raw; no fixed width or conversion is specified. | `program_mode`: integer 0..255. Mode 0 labels `applicable`; other modes label `ignored`. |

Arbitrary scalar tokens mean strings, finite numbers, Booleans or null, with no
object/array token and no numerical coercion. For `unchanged`, preserve both
argument tokens and the replacement Boolean independently. A selected number
may be returned as `number`; selecting a nonnumeric scalar does not manufacture
a number. Replacement raw code and replacement numbers remain `Unknown`; no
sentinel is inferred from fields.

The `parallel-charge` branch table preserves role distinctions:

| `disable` | `role` | `parallel` | Label |
| --- | --- | --- | --- |
| 0 | Any permitted role | Either Boolean | `suppression-not-requested` |
| 1 | `heating` | false | `heating-suppressed` |
| 1 | `heating` | true | `exemption-unknown` |
| 1 | `mixer` | false | `heating-suppressed` |
| 1 | `mixer` | true | `mixer-parallel-exception` |
| 1 | `dhw` | Either Boolean | `not-applicable` |
| 2..255 | Any permitted role | Either Boolean | `unmapped` |

The mixer exception cannot establish parallel support for a non-mixer. Neither
DHW eligibility label proves a physical operating mode. Flow excess has no
encoding, physical unit or actuator bound. Programmed start is an opaque token;
explicit `[]` is present empty data, while an absent `start` supplies no token
to interpret. With a valid `program_mode` and no `start`, the result is still
`complete`: `start` has no fixed width, so absence is not incompleteness. Its
`raw` omits `start` and carries the `applicable` or `ignored` label from the
mode alone. Unstated offsets, parallel admission, enforcement, duration,
physical units and effects all remain `Unknown`.

## Result boundary and synthetic examples

The `results` map is keyed as follows, and no other keys appear. Every field in
`fields` that the view does not interpret gets a result keyed by its own name,
with `raw` set to the array as given and `state="complete"`. A field name equal
to a result key of the selected view below is rejected with an error, except
that `enabled` under `dhw-enable` and `disable` under `parallel-charge` are the
interpreted inputs of those views and are accepted.

| Context | Result key | `raw` contents and extra properties |
| --- | --- | --- |
| `unchanged` | `unchanged` | `{"replacement", "previous", "requested"}` as given; `label`, and `number` when the selected token is a number. |
| `dhw-enable` | `enabled` | The `enabled` array as given, or absent when the field is missing; `label` only when exactly one byte. |
| `parallel-charge` | `disable` | The `disable` array as given, or absent when missing; `label` only when exactly one byte, using `role` and `parallel`. |
| `flow-excess` | `flow-excess` | `{"demand", "excess"}`; `number` is the sum, with `candidate_domain` and `calculation`. |
| `programmed-start` | `programmed-start` | `{"program_mode"}` plus `start` when present; `label` from the mode alone. |
| Unsupported context | One key per name in `fields` | Each `raw` is the array as given, `state="Unknown"`, with no label or number. |

Return one JSON object retaining `context`, raw `fields`, `arguments` when
present, and extra keys independently, together with `state`, `results`,
`physical="Unknown"` and `qualified=false`. Each result has `raw`, `state` and
any applicable `number`, `label`, `flags`, `reserved`, `unmodeled`,
`candidate_domain` or `alternatives`. Do not invent these properties or a number
when the conversion is unknown or data incomplete. Missing raw members stay
absent rather than becoming null or empty arrays.

`complete` means local representation only. Missing or wrong-width fixed fields
give overall `partial` and per-field `incomplete`; complete independent siblings
remain available. Unsupported contexts give `Unknown`. An unresolved semantic
label, including an unmapped byte, can coexist with complete raw arithmetic.
Candidate meaning stays `Hypothesis`; exact calculations may additionally carry
`calculation="Proven"`. A calculation grade never replaces a candidate grade.
Qualification, freshness, physical support, effects, persistence and delivery
are separate from these grades; evaluation proves none of them.

A complete valid synthetic input and illustrative result shape follow. Here
`candidate_domain` records the candidate grade; the addition has a separate
calculation grade.

```json
{
  "context": {"primary": 181, "secondary": 5, "operation": 23,
              "direction": "request", "view": "flow-excess"},
  "fields": {"opaque": []},
  "arguments": {"demand": 40, "excess": 5},
  "extra": false
}
```

```json
{
  "context": {"primary": 181, "secondary": 5, "operation": 23,
              "direction": "request", "view": "flow-excess"},
  "fields": {"opaque": []},
  "arguments": {"demand": 40, "excess": 5},
  "extra": false,
  "state": "complete",
  "results": {
    "flow-excess": {"raw": {"demand": 40, "excess": 5},
                    "state": "complete", "number": 45,
                    "candidate_domain": "Hypothesis", "calculation": "Proven"},
    "opaque": {"raw": [], "state": "complete"}
  },
  "physical": "Unknown",
  "qualified": false
}
```

Independent partial example: supported OP31 `dhw-enable` with
`fields={"enabled":[],"opaque":[7]}` has overall `partial`, an `enabled` result
with `raw=[]`, `state="incomplete"` and no number or eligibility label. Both raw
fields survive; `[7]` remains complete independent raw data without gaining a
semantic conversion. Missing `enabled` likewise yields incomplete state but
retains absence; `[0,1]` retains both bytes and is overlong/incomplete. These
are length outcomes, unlike `enabled=null`, which is an error.

Independent unknown example: the complete flow-excess input above with
`operation=0` instead of 23 retains context, fields, arguments and `extra=false`,
returns `state="Unknown"`, raw-only results, `physical="Unknown"` and
`qualified=false`. It produces no sum. Omitting operation is also unsupported
and remains distinct from the explicit zero. Null operation is an error.

The remaining synthetic cases assert the branch boundaries directly:

| View and explicit inputs | Local result |
| --- | --- |
| `unchanged`, previous 17, requested 23, replacement true | Retain 17, label `unchanged`; no raw sentinel. |
| Same tokens, replacement false | Return 23, label `numeric-candidate`; no raw sentinel or conversion. |
| `dhw-enable`, enabled `[0]` / `[1]` / `[2]` | `frost-only-eligible` / `ordinary-DHW-eligible` / `unmapped`, respectively; all are complete one-byte representations. |
| `parallel-charge`, disable `[1]`, mixer, parallel true | `mixer-parallel-exception`. |
| Same byte, heating, parallel true | `exemption-unknown`. |
| Same byte, mixer, parallel false | `heating-suppressed`. |
| `flow-excess`, demand 40, excess 5 | 45; candidate `Hypothesis`, calculation `Proven`. |
| `programmed-start`, start `[7,8]`, program_mode 0 / 1 | Identical raw token retained; `applicable` / `ignored`, respectively. |

Always overwriting previous violates replacement=true. Inferring a replacement
byte invents an unknown sentinel. Coercing enabled 2 to true violates its
unmapped branch. Applying the mixer exception to heating violates the role
boundary. Subtracting excess gives 35 instead of 45 and violates addition.
Applying OP09 outside mode 0 violates the ignored branch. These are page
assertions, not evidence of peer implementation behavior or executed mutations.

This finite contract claims no native-family completeness or actuator guarantee.
Full Gate D with its prescribed read-only prerequisites, publication checks and
fresh independent review of committed changes remain required before merge;
no native completion or execution follows from this companion.
