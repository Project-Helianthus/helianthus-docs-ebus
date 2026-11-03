# B555 weekly refresh: local representation contract

This architecture contract is partial work for [#954](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/954), referencing [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736); the umbrella remains open. All examples are synthetic. This page specifies a pure library interface; it does not supply an implementation or runtime caller.

The public [B555 native contract](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#521-a4-reply-acceptance-by-a-requester-candidate) owns wire claims. Its candidate requester acceptance and write behavior do not establish this local reducer. In particular its whole-reply acceptance and zero-count write discussion are separate from the local incremental policy and zero-slot shape here. No native write, request encoder, read-back, retry, rollback or acceptance policy follows. No physical maximum follows from `slot_limit`.

## Interface and admission

The declared package is `vaillant`, using only the Go standard library:

```go
func Ab07Ap07Evaluate(ab07ap07Input json.RawMessage) (json.RawMessage, error)
```

No initialization side effect, persistent cache, generic catalog, listing API, active executor or method registration is defined. No pending helper API is required. New implementation identifiers, if later supplied, use `ab07ap07` or `Ab07Ap07`; Go tests use `TestAb07Ap07`.

Input is one JSON object `{context, fields, arguments?}`. `context` and `fields` are required objects. Context is preserved verbatim as JSON values, including opaque family, variant and extra keys. Missing, explicit null and zero stay distinct. Selectors are software inputs, never native qualification. Unsupported or absent selectors return raw-only `Unknown`, without formulas. Recognized selectors are exactly:

| primary | secondary | operation | direction | view | arguments |
|---|---|---|---|---|---|
| 181 | 85 | 164 | local | weekly | status_ok, slot_limit, days |
| 181 | 85 | 166 | local | nonheating-shape | initial, count, slot_setpoints |

`fields` maps names to byte arrays, integers in 0..255. No named native quantity, required byte width or relay vector is declared by these two views: all supplied byte fields are retained as unmodeled `Unknown`, with no number or label. Empty arrays are valid raw arrays. A future independently declared field of missing/short/overlong width must remain incomplete with complete independent siblings available; this page supplies no such width to infer. Unknown extra argument keys are preserved. For a supported view, arguments is required and has the following types; no type coercion occurs.

| argument | type | constraint |
|---|---|---|
| status_ok | Boolean | false terminates before slot work |
| slot_limit | u8 | 0..255, local policy |
| days | array | exactly seven ordered entries, positions 0..6 |
| days[].count | u8 | 0..255 |
| days[].slots | array | synthetic slot objects |
| days[].slots[].ok | Boolean | false stops processing |
| days[].slots[].raw | byte array | integers 0..255; no width inferred |
| initial | array | exactly five opaque JSON scalars |
| count | u8 | 0..255 |
| slot_setpoints | array of u16 | integers 0..65535; length at least count |

Opaque scalars are null, Boolean, string or finite JSON number; arrays and objects are not scalars. Typed numeric inputs exclude Booleans, fractions and strings. General u32 range, if used by another declaration, is 0..4294967295; neither view declares a u32 argument. Reject malformed JSON, duplicate keys anywhere (including opaque objects), wrong kinds and out-of-range typed arguments or bytes. Missing required arguments are errors, including on status-failure inputs; syntactic/type validation precedes reduction. An error returns no successful JSON result. Absent arguments on an unsupported context need no view-specific validation; supplied arguments must still be an object and raw bytes remain validated.

## Results and transitions

Output is `{context, raw, arguments?, state, fields, physical, qualified}`. `context` is unchanged, `raw` is a deep independent copy of input `fields`, and `arguments` is unchanged and present exactly when supplied. `physical="Unknown"` and `qualified=false` always. Every semantic field retains its raw evidence and state plus only applicable `number`, `label`, `flags`, `reserved`, `unmodeled`, `candidate_domain` or `alternatives`. No absent, unmapped or incomplete quantity acquires a number or label. A declared out-of-domain calculation is retained with `candidate_domain=false`; neither view here declares such a domain or numeric byte decoder.

The `fields` object contains one unmodeled raw result per input byte field and a view result named `weekly` or `nonheating-shape` for supported views. Unmodeled results are `{raw: <array>, state: "Unknown", unmodeled: true}`. View results retain `raw` as the complete supplied arguments, `state`, `grade="Hypothesis"`, `calculation="Proven"` for the exact local counts/replacement arithmetic, and the summary below. A same-named raw field stays in `raw`; view results occupy their declared result name. For unsupported views only the unmodeled byte fields remain and top-level state is `Unknown`.

| condition | top-level state | view state | complete | reason |
|---|---|---|---|---|
| weekly success | complete | complete | true | null |
| status rejected | partial | partial | false | status-failure |
| day count exceeds policy | partial | partial | false | count-overflow |
| attempted slot fails | partial | partial | false | slot-failure |
| required slot absent | partial | partial | false | missing-slot |
| nonheating shape valid | complete | complete | not applicable | not applicable |
| unsupported selector | Unknown | absent | not applicable | not applicable |

A weekly result has `reason`, `attempts`, `completed_days`, `successful_slots`, `complete` and `days`. The `days` result lists the reached days in order; each retains its input raw day, index, successful slot prefix, state and unused supplied slots. Overflow includes the stopped day with no attempted slots. Missing/failed slots include the stopped day as partial. Later days remain in unchanged arguments. Successful slots retain their original raw bytes; a failed slot remains in the stopped day's raw input. Unused entries never become successes.

Start with attempts=0, completed_days=0, successful_slots=0 and an empty prefix. If status_ok=false, stop immediately with status-failure. Otherwise process days 0..6 in order. Before each day, count>slot_limit stops with count-overflow; retain all prior completed days and attempts. Never preflight a later overflow and discard earlier progress. On an eligible day inspect exactly count entries in order: a missing entry stops with missing-slot without incrementing attempts; a present entry increments attempts once, and ok=false stops with slot-failure. Each ok=true appends that slot and increments successful_slots. Count=0 completes the day with zero attempts, even if extra slots were supplied. Increment completed_days only after all count slots succeed. A stopped week is never complete. Complete=true exactly when all seven days complete. No retry or rollback is inferred.

The shape result has `initial`, `processed`, `unused` and `processed_slots`. For count=c, initial is copied unchanged, processed_slots=c, processed is exactly c copies of 65535 (FFFF), and unused=slot_setpoints[c:]. Count=0 emits no processed slot and preserves all five initial scalars; count=1 replaces exactly one processed value. Do not prefill every supplied setpoint. This is an offline shape, not a write acceptance or persistence contract.

Every nested context, raw field, argument, result day and slot is independently owned. Mutating an input or returned result cannot change another result or a later call. All absent/null/zero/raw/state distinctions survive JSON round trips. Complete independent sibling fields survive partial input; an unresolved candidate branch does not erase them. Family/behavior grade remains Hypothesis even when exact local arithmetic has calculation=Proven. Physical association, support, effects, delivery, week atomicity, stale-generation admission, persistence and heating kinds remain Unknown. eBUS MCP and GraphQL gain no method, schema change or qualification from this page.

## Synthetic scenarios and verification

The [owned fixture](fixtures/ap08_b555_weekly_refresh.json) includes shape counts 0, 1 and 2, status failure, zero-count week, later overflow, every day/slot failure, a first-slot failure, missing data and unused extra data. Independent summary controls are:

| case | attempts | completed_days | successful_slots | complete | reason |
|---|---|---|---|---|---|
| ab07ap07_status | 0 | 0 | 0 | false | status-failure |
| ab07ap07_zero | 0 | 7 | 0 | true | null |
| ab07ap07_overflow | 2 | 2 | 2 | false | count-overflow |
| ab07ap07_first_failure | 1 | 0 | 0 | false | slot-failure |
| ab07ap07_missing | 0 | 0 | 0 | false | missing-slot |
| ab07ap07_extra | 1 | 7 | 1 | true | null |

The standard-library unittest is a documentation and scenario contract checker with small bounded transition oracles, not a Python runtime API. It cannot verify an absent Go implementation. Explicit supplemental ship command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_ap08_b555_weekly_refresh.py -v
```

The supplemental command is mandatory even though Gate D has a fixed test list. Full repository CI with its prescribed read-only references, fresh independent committed-change review, publication checks and applicable transport classification remain later ship requirements. Focused checks establish neither full CI nor physical behavior. Nothing is stable before Helianthus 1.0; this contract introduces no major or experimental namespace or authorization gate.

The following machine-readable declaration fixes the output keys, grades and arithmetic independently of the scenario table. Conditional keys appear only for their applicable view; byte-field names remain opaque.

```json
{
  "signature": "Ab07Ap07Evaluate(ab07ap07Input json.RawMessage) (json.RawMessage, error)",
  "output_required": ["context", "raw", "state", "fields", "physical", "qualified"],
  "output_optional": ["arguments"],
  "unmodeled_keys": ["raw", "state", "unmodeled"],
  "view_common_keys": ["raw", "state", "grade", "calculation"],
  "weekly_keys": ["reason", "attempts", "completed_days", "successful_slots", "complete", "days"],
  "shape_keys": ["initial", "processed", "unused", "processed_slots"],
  "physical": "Unknown",
  "qualified": false,
  "grade": "Hypothesis",
  "calculation": "Proven",
  "days": 7,
  "replacement": 65535,
  "zero_processed_slots": 0,
  "attempt_on_missing": 0,
  "attempt_on_present_failure": 1,
  "status_failure_attempts": 0,
  "overflow_policy": "stop-at-reached-day-preserve-prefix",
  "complete_predicate": "all-seven-days-completed",
  "processed_length": "count",
  "unused_slice": "slot_setpoints[count:]",
  "copy_policy": "deep-independent",
  "unsupported_state": "Unknown"
}
```
