# AP06: B516 OP14 cycle reducer

This is a local software contract for issue #953, a partial slice of #736.
The umbrella stays open. The public [B516 native documentation](../protocols/vaillant/ebus-vaillant-b516-energy.md)
is the protocol boundary: sub-ID `0x14`, its quantity, unit and physical
availability remain candidate/Unknown. This reducer takes already converted u32
values; it establishes no conversion from those native bytes. Heat-pump and
backup-heater families are candidate associations only. No model is qualified.

## API and admission

The exact local signature in package `vaillant`, using the Go standard library, is:

```go
func Ab05Ap05Evaluate(ab05ap05Input json.RawMessage) (json.RawMessage, error)
```

This page specifies the API independently of any pending implementation. It adds
no Go package, caller or Python runtime feature. It is a pure library contract:
no initialization side effect, persistent cache, generic catalog or listing API.
New Go declarations, parameters, locals, fields and helpers use `ab05ap05` or
exported `Ab05Ap05`; Go test functions use `TestAb05Ap05`. Literal JSON labels,
existing package names and standard-library symbols keep their spelling.

The only supported selector tuple follows. Operation is decimal 20 (`0x14`),
not decimal 14. Selector values are software input, never native qualification.

| primary | secondary | operation | direction | view |
| --- | --- | --- | --- | --- |
| 181 | 22 | 20 | local | cycle |

Input is exactly one JSON object with required object members `context` and
`fields`. For the supported selector, `arguments` is a required object.
`context` retains opaque `family`, `variant` and all other keys verbatim.
Absent, explicit null and zero context values remain distinct. A missing or
unsupported selector member returns raw-only `Unknown`; no cycle formula runs.
Nonobject context/fields/arguments is an error. An unsupported selector does not
require cycle arguments, but malformed JSON, duplicate keys and invalid byte
arrays are still errors. Unknown argument keys are preserved without coercion.

| argument | kind | requirement |
| --- | --- | --- |
| slots | array | exactly 9 ordered objects, index 0..8 |
| failure_counter | u32 | required |
| counter_increment | u32 | optional; absent differs from zero |
| slots[].registered | Boolean | required |
| slots[].capable | Boolean | required |
| slots[].prior | u32 | required |
| slots[].prior_previous | u32 | required |
| slots[].prior_changed | Boolean | required |
| slots[].outcome | string | success, read-failure, parse-failure |
| slots[].value | u32 | required only for success; absent otherwise |

u8/u16/u32 are integral JSON numbers in 0..255/65535/4294967295. Boolean, null,
string, object and array kinds are explicit; none is coerced into a number.
Reject fractions, negative/out-of-range values, malformed JSON, nonfinite
numbers, duplicate keys anywhere and missing required arguments with an error
and no successful result. The outcome/value shape is checked even for skipped
slots. The caller resolves `registered` and `capable`; no raw bit is selected.
Unknown extra slot keys, like other opaque arguments, are preserved.

`fields` maps arbitrary names to arrays of u8, never scalars or null. No named
byte field, required width or relay vector is defined for this view. Thus every
valid array, including empty, short or overlong arrays, is retained as an
unmapped field, `state=Unknown`, with no invented label or number. Absence of an
opaque raw field does not make the cycle incomplete. Width-dependent views,
if separately defined, must retain missing/short/overlong fields as incomplete
and keep independent siblings; no width can be inferred here.

## Transition tables

These tables are normative, machine-checked local rules. `U` is a modulo base;
`sentinel` is an ordinary successful value too. No signed/absolute delta is used.

| rule | value |
| --- | --- |
| slot_count | 9 |
| modulus | 4294967296 |
| sentinel | 4294967295 |
| threshold | 2 |
| eligibility | registered && capable |
| delta | (current - prior) modulo U |
| changed | prior == sentinel OR delta >= threshold |
| sum | successful admitted current values modulo U |
| clean_counter | 0 |
| failed_counter | prior + explicit counter_increment modulo U; otherwise Unknown |
| partial_cycle | failed > 0 OR skipped > 0 |
| skip_count | skipped |
| partial_sum | retain |

| eligibility | supplied outcome | admitted | current | previous | changed | counted as |
| --- | --- | --- | --- | --- | --- | --- |
| false | any valid outcome | false | sentinel | prior_previous | Unknown | skipped |
| true | success | true | value | prior | formula | successful |
| true | read-failure | true | sentinel | prior | Unknown | failed |
| true | parse-failure | true | sentinel | prior | Unknown | failed |

Every result slot retains `prior_changed` separately. A failed attempt's change
rule is unprovided; it must not become false or reuse `prior_changed` as a
computed answer. Attempt count is `successful + failed`; skipped slots are not
attempts. All nine slots are processed independently. Sum includes successful
zero and every u32 bit pattern, wraps rather than saturates, and survives failure
of any sibling. No successful values gives an empty sum of zero.

With any failed admitted attempt, the native increment count is Unknown. An
explicit `counter_increment` yields only local modulo arithmetic. Without it,
computed counter has `state=Unknown`, no number, and cycle `state=partial`;
`prior_failure_counter` remains available. With no failed attempts the computed
counter resets to zero even if an increment is supplied or some slots skipped.

## Result shape and grades

The result is one JSON object. All raw JSON trees are detached deep copies;
mutating input or any returned nested tree cannot affect another result or a
later call. All distinctions survive JSON round trips. JSON member order is
irrelevant; absence and null are distinct.

| member | supported cycle representation |
| --- | --- |
| context | unchanged object |
| raw | independent deep copy of fields |
| arguments | unchanged object if supplied; absent if absent |
| state | partial if any failure or skip; otherwise complete |
| grade | Hypothesis |
| physical | Unknown |
| qualified | false |
| fields | one raw/state=Unknown/unmodeled=true object per supplied raw field |
| cycle.slots | exactly nine results in input order |
| cycle.successful | successful admitted count |
| cycle.failed | failed admitted count |
| cycle.skipped | nonadmitted count |
| cycle.attempts | successful + failed |
| cycle.sum | state=complete, number=u32 sum, grade=Hypothesis, calculation=Proven |
| cycle.counter | complete/number/calculation=Proven if computable; otherwise Unknown without number; grade=Hypothesis |
| cycle.prior_failure_counter | unchanged input failure_counter |
| cycle.partial_cycle | true if failure or skip; false otherwise |

Each `cycle.slots` entry has `index`, `raw` (detached input slot), `admitted`,
`outcome` (`skipped` when ineligible, otherwise the supplied outcome), `state`
(`complete` for success, `partial` otherwise), `current`, `previous`,
`prior_changed`, `changed`, and `grade=Hypothesis`. `current` and `previous`
are u32 quantities with `state=complete`, `number`, `grade=Hypothesis` and
`calculation=Proven`. `changed` has `state=complete`, `flags={"changed":Boolean}`
and `calculation=Proven` on success; otherwise `state=Unknown` and no flags.
Its grade remains Hypothesis. Here `complete` means local representation only.
An unresolved branch does not remove complete sibling fields or the partial sum.

Unsupported selectors return `state=Unknown`, `grade=Unknown`, `context`, `raw`,
`fields`, optional `arguments`, `physical=Unknown`, `qualified=false`; `cycle`
is absent. Unmapped fields carry their `raw` and `unmodeled=true`; they have no
`number` or `label`. No flags, reserved bits, alternatives or candidate domain
are inferred from opaque bytes. No candidate numeric domain is declared for
cycle u32 arithmetic: zero and the sentinel are included. Where a separately
declared calculation lies outside a candidate domain it must remain available
with `candidate_domain=false`; this page declares no such domain or formula.

The family/behavior result stays Hypothesis even where arithmetic is Proven.
Physical support, association, effects, freshness, persistence and delivery stay
Unknown. No publication, scheduling, float conversion, negative/NaN conversion,
transport invocation, eBUS MCP change, GraphQL change, scan-default change,
method registration or active executor follows. There is no new namespace,
authorization gate or stable pre-1.0 guarantee. MCP compatibility and GraphQL
parity are preserved because this slice introduces no runtime interface change.

## Synthetic evidence and supplemental gate

[The owned scenarios](fixtures/ap06_b516_cycle_reducer.json) use a base input
and cases with `slot_updates` keyed by decimal index, `argument_updates` and
optional `remove_arguments`. Slot updates replace the entire selected slot object; argument updates
replace members of the arguments object; each case starts with a fresh deep copy of the base.
`expected.slots` tuples are ordered as
`[index, admitted, outcome, current, previous, changed, prior_changed]`;
`"Unknown"` is a semantic state, not a Boolean. Expected counters are either
a u32 or `"Unknown"`. This compact fixture notation is not the API input shape.
All cases are synthetic; these are local examples, not device observations.

[The standard-library test](../tests/test_ap06_b516_cycle_reducer.py) compares
page tables to independent constants and scenario outcomes to small bounded
transition oracles. It validates admission, copies and round trips in a test
model, not a production evaluator. No Go implementation is imported or invoked.
The mandatory explicit supplemental command is:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap06_b516_cycle_reducer.py -v
```

Run `python3 scripts/check_public_domain_boundary.py` separately. Focused success
is not full CI: Gate D has a fixed test list and does not discover this suite.
Full Gate D with prescribed read-only prerequisites, publication checks and a
fresh independent committed-change review remain ship requirements. No native
or transport conformance result follows from these tests.
