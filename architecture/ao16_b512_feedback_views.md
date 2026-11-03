# B512 OP01 Directional Fields: Software API Results

This page is a software API companion. It describes one pure library function
and the JSON it accepts and returns. It does not amend a protocol page, list a
native qualification or add catalog entries. Native physical support, effects
and persistence stay Unknown; no result of this function qualifies a device
family, and no candidate label grants permission to act.

## Function

```go
func Ab15Ao15Interpret(ab15ao15Input json.RawMessage) (json.RawMessage, error)
```

The function lives in package `vaillant`, uses only the standard library and is
a pure selected field/state interpreter: no global cache, no generic catalog,
no metadata listing, no registration and no runtime call site. Each call returns
a fresh result; mutating an input after the call or a returned result afterwards
cannot alter any other result or any later call.

## Input

A JSON object with exactly `context`, `fields` and optional `arguments`. Any
other top-level key is an error.

- `context` is an object. It must carry `primary` (integer, 181), `secondary`
  (integer, 18), `operation` (integer), `direction` (string) and `view`
  (string). Every other key, such as opaque family or variant values of any JSON
  kind, is preserved unchanged and never consulted.
- `fields` is an object of named byte arrays. Every element is a JSON integer
  literal in 0..255 (no fraction or exponent). Unmodelled field names and
  unmodelled tail bytes are accepted and preserved.
- `arguments` is optional and may contain only `actual_signal` (boolean).

Duplicate object keys at any depth, malformed JSON, trailing data, wrong JSON
kinds and invalid byte elements return an error and no result. Absent versus
explicit zero, and missing versus empty, stay distinct: an absent field is
`missing`, an empty array is `short`, and an absent `arguments` object differs
from an empty one.

## Selection

Selection uses only the explicit `context` values. A name, a payload length or
a family label never selects a view. Operation 1 with direction `request` or
`positive` and view `directional-fields` selects the interpretation below. A
different primary, secondary, operation, direction or view returns state
`unknown` with a `reason` (`unknown-primary`, `unknown-secondary`,
`unknown-operation`, `unknown-direction`, `unknown-view`, checked in that
order), an empty `fields` object and the preserved raw input; nothing is
guessed. A view token chooses a software interpretation; it cannot qualify
family applicability.

## Fields

Hypothesis: OP01 carries six independent raw u8 fields at logical positions 3
to 8 on both the request and the positive side.

| Logical | Name | Kind |
| --- | --- | --- |
| 3 | `secondary_heating_pump` | pump |
| 4 | `circulation_pump` | pump |
| 5 | `solar_pump` | pump |
| 6 | `error_relay` | candidate |
| 7 | `loading_pump` | pump |
| 8 | `fume_flap` | candidate |

Each result field has `raw` (omitted when missing), `state`, `grade`
(`Hypothesis`) and optionally `label`. No field has a `number`: no speed
converter or physical value exists.

- Pump fields: byte FF with direction `request` is `mapped` / `leave-unchanged`;
  byte FF with direction `positive` is `mapped` / `function-unavailable`; every
  other byte is `raw` with no label.
- `error_relay` and `fume_flap`: byte 0F is `candidate` / `state-0F`, byte F0 is
  `candidate` / `state-F0`, every other byte (including 00, 01 and FF) is
  `candidate` / `no-action-candidate`. No on/off polarity is stated.
- A missing field is `missing`, an empty array `short`, an array of more than
  one byte `overlong`; the supplied bytes are kept in `raw` and no label is
  given. These never erase valid siblings.

## Feedback fallback

Feedback without an internal actual signal may fall back to the setpoint, and
equal bytes never prove an actual value. The `feedback` object has `origin`,
`grade` (`Hypothesis`) and, only when `fields` supplies single-byte `setpoint`
and `feedback` arrays, `raw_equal` with `calculation` `Proven` (an exact byte
comparison that does not promote the family grade). Both arrays stay in `raw`
unmodified.

| `arguments.actual_signal` | `origin` |
| --- | --- |
| absent | `origin-Unknown` |
| `false` | `fallback-candidate` |
| `true` | `actual-input-candidate` |

The origin is independent of `raw_equal`. Nothing here is measured or Proven.
The boolean default-true has no established encoded byte and is never
materialized as 01 or any other byte; a missing field stays missing.

## Output

An object with `context` (deep copy), `raw` (independent copy of `fields`),
`arguments` (independent copy, only if supplied), `state`, optional `reason`,
`fields`, `feedback` (selected view only), `unknowns`, `physical` (`Unknown`)
and `qualified` (`false`).

- `state` is `complete` when all six fields are single bytes, `partial` when at
  least one but not all are, `raw-only` when none is, and `unknown` for an
  unselected branch. A partial result retains every complete field.
- `unknowns` always lists `Unknown` for physical values, the actual-signal wire
  discriminator, materialized defaults, peer support, relay polarity and the
  default-true encoding.
- Each field and `feedback` stay Hypothesis; native qualification is never
  inferred from context or from a successful call.

## Machine-readable contract

The table below is the finite contract checked by the focused test. Case rows
give the input as a change from `control_input` (`set`, `context_set` where
null means the key is absent, `extra_fields`, `arguments`) and the expected
result as `deviations` from `control_summary`. The complete expected results
are in [the fixture](fixtures/ao16_b512_feedback_views.json).

```json ao16-contract
{
 "contract_id": "ab15ao15-b512-op01-directional-fields",
 "signature": "func Ab15Ao15Interpret(ab15ao15Input json.RawMessage) (json.RawMessage, error)",
 "package": "vaillant",
 "family_grade": "Hypothesis",
 "qualification": "Unknown",
 "physical": "Unknown",
 "qualified": false,
 "input_keys": {"required": ["context", "fields"], "optional": ["arguments"]},
 "context": {"primary": 181, "secondary": 18, "operation": 1, "directions": ["request", "positive"], "view": "directional-fields"},
 "arguments": {"actual_signal": ["absent", "false", "true"]},
 "fields": [{"name": "secondary_heating_pump", "logical": 3, "kind": "pump"}, {"name": "circulation_pump", "logical": 4, "kind": "pump"}, {"name": "solar_pump", "logical": 5, "kind": "pump"}, {"name": "error_relay", "logical": 6, "kind": "candidate"}, {"name": "loading_pump", "logical": 7, "kind": "pump"}, {"name": "fume_flap", "logical": 8, "kind": "candidate"}],
 "pump_labels": {"request_FF": "leave-unchanged", "positive_FF": "function-unavailable", "other": "raw"},
 "candidate_labels": {"0F": "state-0F", "F0": "state-F0", "other": "no-action-candidate"},
 "field_states": ["mapped", "raw", "candidate", "missing", "short", "overlong"],
 "result_states": ["complete", "partial", "raw-only", "unknown"],
 "feedback_origins": {"absent": "origin-Unknown", "false": "fallback-candidate", "true": "actual-input-candidate"},
 "output_keys": ["context", "raw", "arguments", "state", "reason", "fields", "feedback", "unknowns", "physical", "qualified"],
 "unknowns": ["physical_values", "actual_signal_wire_discriminator", "materialized_defaults", "peer_support", "relay_polarity", "default_true_encoding"],
 "unknown_reasons": ["unknown-primary", "unknown-secondary", "unknown-operation", "unknown-direction", "unknown-view"],
 "numbers": "none",
 "control_input": {"secondary_heating_pump": [32], "circulation_pump": [64], "solar_pump": [80], "error_relay": [15], "loading_pump": [96], "fume_flap": [240]},
 "control_summary": {"secondary_heating_pump": "raw", "circulation_pump": "raw", "solar_pump": "raw", "error_relay": "candidate:state-0F", "loading_pump": "raw", "fume_flap": "candidate:state-F0"},
 "error_ids": [
  "ab15ao15-error-duplicate-top-level-key",
  "ab15ao15-error-duplicate-field-key",
  "ab15ao15-error-duplicate-context-key",
  "ab15ao15-error-malformed-json",
  "ab15ao15-error-trailing-data",
  "ab15ao15-error-byte-256",
  "ab15ao15-error-byte-negative",
  "ab15ao15-error-byte-fraction",
  "ab15ao15-error-byte-exponent",
  "ab15ao15-error-byte-string",
  "ab15ao15-error-byte-null",
  "ab15ao15-error-field-not-array",
  "ab15ao15-error-field-null",
  "ab15ao15-error-fields-not-object",
  "ab15ao15-error-fields-missing",
  "ab15ao15-error-context-missing",
  "ab15ao15-error-context-not-object",
  "ab15ao15-error-operation-string",
  "ab15ao15-error-primary-missing",
  "ab15ao15-error-direction-not-string",
  "ab15ao15-error-view-missing",
  "ab15ao15-error-actual-signal-string",
  "ab15ao15-error-actual-signal-null",
  "ab15ao15-error-actual-signal-integer",
  "ab15ao15-error-arguments-unknown-key",
  "ab15ao15-error-arguments-not-object",
  "ab15ao15-error-top-level-unknown-key",
  "ab15ao15-error-top-level-not-object"
 ],
 "cases": [
  {"id": "ab15ao15-control-request", "direction": "request", "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-control-positive", "direction": "positive", "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-request-secondary_heating_pump", "direction": "request", "set": {"secondary_heating_pump": [255]}, "state": "complete", "deviations": {"secondary_heating_pump": "mapped:leave-unchanged"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-positive-secondary_heating_pump", "direction": "positive", "set": {"secondary_heating_pump": [255]}, "state": "complete", "deviations": {"secondary_heating_pump": "mapped:function-unavailable"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-request-circulation_pump", "direction": "request", "set": {"circulation_pump": [255]}, "state": "complete", "deviations": {"circulation_pump": "mapped:leave-unchanged"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-positive-circulation_pump", "direction": "positive", "set": {"circulation_pump": [255]}, "state": "complete", "deviations": {"circulation_pump": "mapped:function-unavailable"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-request-solar_pump", "direction": "request", "set": {"solar_pump": [255]}, "state": "complete", "deviations": {"solar_pump": "mapped:leave-unchanged"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-positive-solar_pump", "direction": "positive", "set": {"solar_pump": [255]}, "state": "complete", "deviations": {"solar_pump": "mapped:function-unavailable"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-request-loading_pump", "direction": "request", "set": {"loading_pump": [255]}, "state": "complete", "deviations": {"loading_pump": "mapped:leave-unchanged"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-ff-positive-loading_pump", "direction": "positive", "set": {"loading_pump": [255]}, "state": "complete", "deviations": {"loading_pump": "mapped:function-unavailable"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-0F", "direction": "request", "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-F0", "direction": "request", "set": {"error_relay": [240]}, "state": "complete", "deviations": {"error_relay": "candidate:state-F0"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-00", "direction": "request", "set": {"error_relay": [0]}, "state": "complete", "deviations": {"error_relay": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-01", "direction": "request", "set": {"error_relay": [1]}, "state": "complete", "deviations": {"error_relay": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-FF", "direction": "request", "set": {"error_relay": [255]}, "state": "complete", "deviations": {"error_relay": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-fume-0F", "direction": "request", "set": {"fume_flap": [15]}, "state": "complete", "deviations": {"fume_flap": "candidate:state-0F"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-fume-F0", "direction": "request", "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-fume-00", "direction": "request", "set": {"fume_flap": [0]}, "state": "complete", "deviations": {"fume_flap": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-fume-01", "direction": "request", "set": {"fume_flap": [1]}, "state": "complete", "deviations": {"fume_flap": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-fume-FF", "direction": "request", "set": {"fume_flap": [255]}, "state": "complete", "deviations": {"fume_flap": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-relay-01-positive", "direction": "positive", "set": {"error_relay": [1]}, "state": "complete", "deviations": {"error_relay": "candidate:no-action-candidate"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-actual-absent-equal", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [50]}, "state": "complete", "origin": "origin-Unknown", "raw_equal": true},
  {"id": "ab15ao15-actual-absent-differ", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [51]}, "state": "complete", "origin": "origin-Unknown", "raw_equal": false},
  {"id": "ab15ao15-actual-false-equal", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [50]}, "arguments": {"actual_signal": false}, "state": "complete", "origin": "fallback-candidate", "raw_equal": true},
  {"id": "ab15ao15-actual-false-differ", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [51]}, "arguments": {"actual_signal": false}, "state": "complete", "origin": "fallback-candidate", "raw_equal": false},
  {"id": "ab15ao15-actual-true-equal", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [50]}, "arguments": {"actual_signal": true}, "state": "complete", "origin": "actual-input-candidate", "raw_equal": true},
  {"id": "ab15ao15-actual-true-differ", "direction": "request", "extra_fields": {"setpoint": [50], "feedback": [51]}, "arguments": {"actual_signal": true}, "state": "complete", "origin": "actual-input-candidate", "raw_equal": false},
  {"id": "ab15ao15-actual-absent-empty-arguments", "direction": "request", "arguments": {}, "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-actual-true-no-feedback-field", "direction": "request", "extra_fields": {"setpoint": [50]}, "arguments": {"actual_signal": true}, "state": "complete", "origin": "actual-input-candidate", "raw_equal": null},
  {"id": "ab15ao15-missing-error-relay", "direction": "request", "set": {"error_relay": null}, "state": "partial", "deviations": {"error_relay": "missing"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-short-solar-pump", "direction": "request", "set": {"solar_pump": []}, "state": "partial", "deviations": {"solar_pump": "short"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-overlong-circulation-pump", "direction": "request", "set": {"circulation_pump": [1, 2]}, "state": "partial", "deviations": {"circulation_pump": "overlong"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-missing-all-fields", "direction": "request", "set": {"secondary_heating_pump": null, "circulation_pump": null, "solar_pump": null, "error_relay": null, "loading_pump": null, "fume_flap": null}, "state": "raw-only", "deviations": {"secondary_heating_pump": "missing", "circulation_pump": "missing", "solar_pump": "missing", "error_relay": "missing", "loading_pump": "missing", "fume_flap": "missing"}, "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-tail-and-context-preserved", "direction": "request", "context_set": {"note": {"nested": [1, {"k": true}]}}, "extra_fields": {"unmodelled_tail": [9, 8, 0, 255]}, "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-opaque-context-b", "direction": "request", "context_set": {"family": "opaque-family-b", "variant": 7}, "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-opaque-context-absent-labels", "direction": "request", "context_set": {"family": null, "variant": null}, "state": "complete", "origin": "origin-Unknown", "raw_equal": null},
  {"id": "ab15ao15-unknown-primary", "direction": "request", "context_set": {"primary": 180}, "state": "unknown", "reason": "unknown-primary"},
  {"id": "ab15ao15-unknown-secondary", "direction": "request", "context_set": {"secondary": 19}, "state": "unknown", "reason": "unknown-secondary"},
  {"id": "ab15ao15-unknown-operation", "direction": "request", "context_set": {"operation": 2}, "state": "unknown", "reason": "unknown-operation"},
  {"id": "ab15ao15-unknown-operation-zero", "direction": "request", "context_set": {"operation": 0}, "state": "unknown", "reason": "unknown-operation"},
  {"id": "ab15ao15-unknown-direction", "direction": "response", "state": "unknown", "reason": "unknown-direction"},
  {"id": "ab15ao15-unknown-view", "direction": "request", "context_set": {"view": "directional-fields-v2"}, "state": "unknown", "reason": "unknown-view"}
 ]
}
```
