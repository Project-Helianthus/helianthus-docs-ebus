# B512 flow and emergency logical-field results (AP16)

This architecture contract defines a pure local software representation for
synthetic heat-pump and ventilation families. It is partial work under #736;
no umbrella closure or runtime invocation follows. The public native contract
is [B512 candidate sub-commands](../protocols/vaillant/ebus-vaillant-B512.md#candidate-sub-commands-op).
That source labels OP11/OP12 layouts Hypothesis, unconfirmed on the wire.
The signed flow rule and the conflicting positive prefix below are explicit
local candidate rules; they do not upgrade the native evidence.

## API and JSON shape

Package `vaillant` exposes exactly:

```go
func Ab15Ap15Evaluate(ab15ap15Input json.RawMessage) (json.RawMessage, error)
```

The API uses only the Go standard library. This page specifies it independently
of any pending implementation. There is no initialization side effect,
persistent cache, generic catalog, listing API, runtime caller, packet decoder,
active executor, method registration, scan-default change or peer communication.
eBUS MCP compatibility and GraphQL parity are unchanged: no transport or schema
entry point is introduced. Local representations confer no automatic qualification.

Input is one JSON object: required `context` object and `fields` object,
optional `arguments` object. Context retains every key verbatim, including
opaque `family`, `variant` and nested values. Selection uses integer primary=181,
secondary=18, operation=17 (hex11) or 18 (hex12), direction `request` or
`positive`, and explicit view as enumerated below. The selector is software
input, never native qualification. Missing, null and zero selectors remain
distinct; each unsupported combination produces raw-only Unknown. Numeric
selectors are null or u8 integers, direction/view null or strings; other kinds
are errors. Opaque context values have no semantic constraints.

Every field value, including an unmapped name, is an array of integers 0..255.
Boolean, null, strings, nested arrays, fractions and out-of-range bytes are
errors, never coerced. Known arrays of incorrect length (including empty) are
incomplete, retained intact; missing known arrays remain absent. Unknown field
names retain raw with state Unknown. No relay vector is defined for these views.

No typed or required arguments are defined for these four views. When supplied,
arguments must be an object; all its keys are opaque extras, preserved verbatim,
including false, null, zero, strings and nested arrays. No invented typed
argument, u16/u32 carrier or required argument is admitted by this contract.
For future explicitly typed arguments, u8/u16/u32 mean integral 0..255,
0..65535 and 0..4294967295 respectively; missing required arguments, wrong
kinds, fractions and range violations must be errors. No such extension is
selected here. Root keys outside context/fields/arguments are errors.

Reject malformed JSON, non-JSON numeric constants and duplicate keys anywhere
(including nested opaque objects) with an error and no successful result.
Validation precedes view selection: unsupported selectors cannot bypass invalid
bytes or invalid structure. There is no partial successful result for an error.

Output is an object with `context` unchanged, `raw` a deep independent copy of
fields, `arguments` unchanged iff supplied, `state`, semantic `fields`,
`physical="Unknown"`, and `qualified=false`. A positive supported view also has
`candidate` as specified below. A field result contains `state`,
`grade="Hypothesis"`, `presence` (absent/present), and `raw` iff present.
Complete numeric results add `number`, `unit`, `calculation="Proven"`; flags
add `flags` with Boolean labels, `reserved` and `unmodeled` as separate integer
bit masks. Setpoint additionally has `candidate_domain`. Unmapped fields have
only raw and state Unknown. No number or label is invented for incomplete or
unmapped fields. Raw-u8 is an uninterpreted numeric carrier, with unit `none`;
its arithmetic grade does not imply a pump or switch operating state.

Supported views are complete as local representations unless any known field
is incomplete, in which case the top state is partial. Independent complete
siblings remain available, without fallback substitution or erasure of raw.
Unsupported views yield state Unknown, fields={}, no candidate, no formulas.
Unresolved candidate physical association coexists with complete siblings.
No state is cached across calls; incomplete input cannot overwrite a previous
call's independent last-known-good result. No missing value is silently filled
from a previous call. Every context/raw/state distinction survives JSON round
trips. Mutating input, output raw, a semantic raw array, context, arguments or
candidate storage cannot affect any other copy, another result or a later call.

## Finite machine-readable API contract

```json ab15ap15-contract
{
  "package": "vaillant",
  "signature": "Ab15Ap15Evaluate(ab15ap15Input json.RawMessage) (json.RawMessage, error)",
  "input_required": [
    "context",
    "fields"
  ],
  "input_optional": [
    "arguments"
  ],
  "context_selector": {
    "primary": 181,
    "secondary": 18
  },
  "views": [
    {
      "operation": 17,
      "direction": "request",
      "view": "flow-io",
      "arguments": []
    },
    {
      "operation": 17,
      "direction": "positive",
      "view": "flow-io",
      "arguments": [],
      "candidate_positive_prefix": [
        181,
        18,
        12
      ],
      "physical_association": "Unknown",
      "matches_requested_operation": false
    },
    {
      "operation": 18,
      "direction": "request",
      "view": "emergency-io",
      "arguments": []
    },
    {
      "operation": 18,
      "direction": "positive",
      "view": "emergency-io",
      "arguments": [],
      "candidate_positive_prefix": [
        181,
        18,
        12
      ],
      "physical_association": "Unknown",
      "matches_requested_operation": false
    }
  ],
  "output_required": [
    "context",
    "raw",
    "state",
    "fields",
    "physical",
    "qualified"
  ],
  "output_optional": [
    "arguments",
    "candidate"
  ],
  "physical": "Unknown",
  "qualified": false,
  "semantic_grade": "Hypothesis",
  "calculation_grade": "Proven",
  "states": [
    "complete",
    "partial",
    "Unknown"
  ],
  "field_states": [
    "complete",
    "incomplete",
    "Unknown"
  ],
  "setpoint_candidate_domain": [
    0,
    100
  ],
  "typed_arguments": [],
  "duplicate_keys": "reject anywhere",
  "copy": "deep independent",
  "unsupported": "raw-only",
  "runtime_caller": false,
  "persistent_cache": false,
  "physical_packet_decoder": false
}
```

## Logical fields

The operation column is decimal; widths are bytes. Masks are decimal retained
bit masks, not requirements that reserved bits be zero. Every row's family and
behavior grade is Hypothesis; exact numeric arithmetic additionally is Proven.

| view | operation | direction | field | width | formula | unit | known | reserved | unmodeled |
|---|---|---|---|---|---|---|---|---|---|
| flow-io | 17 | request | temperature1 | 2 | signedLE16/16 | Celsius | 0 | 0 | 0 |
| flow-io | 17 | request | temperature2 | 2 | signedLE16/16 | Celsius | 0 | 0 | 0 |
| flow-io | 17 | request | temperature3 | 2 | signedLE16/16 | Celsius | 0 | 0 | 0 |
| flow-io | 17 | request | pressure | 1 | u8/10 | bar | 0 | 0 | 0 |
| flow-io | 17 | request | flow | 1 | signed8*10 | l/h | 0 | 0 | 0 |
| flow-io | 17 | request | pump_status | 1 | raw-u8 | none | 0 | 0 | 0 |
| flow-io | 17 | request | flags | 1 | bits | none | 1 | 126 | 128 |
| flow-io | 17 | positive | flags | 1 | bits | none | 3 | 252 | 0 |
| flow-io | 17 | positive | setpoint | 1 | u8 | percent | 0 | 0 | 0 |
| emergency-io | 18 | request | flags | 1 | bits | none | 1 | 126 | 128 |
| emergency-io | 18 | request | switch | 1 | raw-u8 | none | 0 | 0 | 0 |
| emergency-io | 18 | request | co2_1 | 2 | LEu16 | ppm | 0 | 0 | 0 |
| emergency-io | 18 | request | co2_2 | 2 | LEu16 | ppm | 0 | 0 | 0 |
| emergency-io | 18 | positive | flags | 1 | bits | none | 1 | 126 | 128 |

`signedLE16/16`: let u=lo+256*hi, s=u if u<32768 else u-65536;
number=s/16 Celsius. `signed8*10`: let s=b if b<128 else b-256;
number=s*10 l/h. `u8/10`: number=b/10 bar. `LEu16`: number=lo+256*hi
ppm, full 0..65535. `u8` and `raw-u8`: number=b. No sentinel or
operating state is inferred from raw FF or FFFF.

OP11 request flags: bit0 `compressor-off`, reserved bits1..6, unmodeled bit7.
OP11 positive flags: bit0 `compressor-off`, bit1 `pump-relay`, reserved bits2..7,
unmodeled mask0. OP12 request flags: bit0 `emergency`; positive: bit0 `LED`;
both reserve bits1..6 and independently retain unmodeled bit7.
Setpoint candidate domain is inclusive 0..100 percent. Outside-domain carriers
retain raw and number with candidate_domain=false; never clamp or discard.

## Positive-prefix conflict and grades

Both positive views separately expose candidate.positive_prefix=[181,18,12],
the literal B5/12/0C, candidate.requested_operation equal to the requested
17 or 18, candidate.matches_requested_operation=false,
candidate.physical_association="Unknown", candidate.grade="Hypothesis".
Neither requested11 nor requested12 matches literal0C. Changing the operation
alone cannot select a physical packet decoder; a mismatched logical view is
raw-only Unknown. No correlation or accepted feedback is established.
Physical association, native support, effects, freshness, persistence and
delivery all remain Unknown. Calculation Proven never replaces family
Hypothesis; physical Unknown and qualified=false hold for every result.
All missing mappings remain Unknown. Nothing is stable before Helianthus 1.0;
this contract introduces no new major or experimental namespace.

## Independent synthetic controls

These values are checked independently against the scenario results, not used
as native qualification. The scenario file includes absent/empty/short/overlong,
zero and maximum carriers for every named field, independent selector changes,
opaque context and argument preservation, and strict error examples.

| control | raw | expected | interpretation |
|---|---|---|---|
| flow-negative-one | FF | -10 | l/h |
| flow-negative-boundary | 80 | -1280 | l/h |
| flow-positive-boundary | 7F | 1270 | l/h |
| temperature-one | 10 00 | 1 | Celsius |
| pressure-maximum | FF | 25.5 | bar |
| flow-request-flags | 81 | 128 | unmodeled; compressor-off=true |
| flow-positive-flags | 81 | 128 | reserved; compressor-off=true |
| setpoint-outside | 65 | 101 | candidate_domain=false |
| emergency-co2-first | FF FF | 65535 | ppm; no sentinel |
| emergency-co2-second | 01 00 | 1 | ppm; independent field |
| emergency-request-flags | 80 | 128 | unmodeled |
| emergency-positive-flags | 80 | 128 | unmodeled |
| flow-positive-prefix | B5 12 0C | 12 | conflict with requested17 |
| emergency-positive-prefix | B5 12 0C | 12 | conflict with requested18 |

[Scenario tuples](fixtures/ap16_b512_emergency_flow.json) are synthetic
input/result and rejection examples, not captures. The
[standard-library contract test](../tests/test_ap16_b512_emergency_flow.py)
checks tables, shapes, independent arithmetic/bit controls and bounded
transitions. It implements test oracles only; it does not provide a Python
runtime feature or exercise a Go implementation. It is an explicit supplemental
ship check: the repository's fixed full-gate list does not automatically include
it. Full CI, publication checks and independent committed-change review remain
required; focused contract checks do not demonstrate physical behavior.
