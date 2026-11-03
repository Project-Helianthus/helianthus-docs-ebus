# B504 selected-field evaluation (AQ02)

This pre-1.0 architecture contract describes a pure local evaluator in package
`vaillant`, not a native wire specification or a family qualification. Its local
API contract is **Proven**; the selected B504 interpretations below are
**Hypothesis**. All examples are synthetic. Native support, freshness, physical
adaptation, effects, persistence and delivery remain **Unknown**. Nothing here is
stable before Helianthus 1.0.

AE01/02 and AK01/02 retain metadata and role declarations; AQ adds field
evaluation. AO01/02 retains B505 OP32, and AM scalar bindings remain separate.
This ordinary companion needs no unmerged registry entry or code-merge dependency.
It adds no implementation, native-family completeness claim or execution step.

## Callable boundary

```go
func Ab01Aq01Evaluate(ab01Aq01Input json.RawMessage) (json.RawMessage, error)
```

The evaluator uses only the Go standard library. It is a callable field evaluator,
not another Entries/Lookup catalog or schema. It requires no pending helper,
sibling checkout, initialization side effect, persistent cache, provider
registration or automatic caller. No request, emitter or role discovery is
implemented. This page introduces no change to eBUS MCP compatibility or GraphQL
parity and defines no transport binding.

Any future Go declarations, parameters, locals, fields, helpers and fixture IDs
for this contract start `ab01aq01` or exported `Ab01Aq01`; tests start
`TestAb01Aq01`. This compound stem is distinct from earlier `abNN` names. Literal
JSON/protocol labels, existing package/library symbols and standard-library
members retain their spelling.

## Input, admission and output

Input is exactly one JSON object containing `context`, `fields` and optional
`arguments`. Context contains `primary`, `secondary`, `direction`, `view`, opaque
`family`/`variant` keys, and `operation` when present. Primary, secondary and
operation are integers in 0..255 where present. Absent operation differs from
explicit zero; null is not an integer and is rejected. Context identifiers select
a local candidate view and never qualify a family or choose a divisor.

`fields` holds named byte arrays whose elements are integers in 0..255.
An explicitly opaque field can retain an empty array, distinct from a missing
field. `arguments` supplies exactly the typed arguments stated for a selected
view below. Unknown extra input keys are retained unchanged, independently of
context, raw fields and arguments; they do not acquire semantics. Unrecognized
field values must still satisfy the byte-array kind. Extras do not become typed
arguments or select formulas.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
nonfinite numbers, fractional/out-of-range bytes or integer arguments, and missing
required arguments. Return an error with no successful result. Do not coerce
strings, null or Booleans to numbers. These admission failures differ from an
admitted missing, short or overlong fixed-width field: that field is incomplete,
its raw form survives, and complete independent siblings remain available.
An empty array for a required one-byte token is present but incomplete.

The result is one JSON object retaining context, raw `fields`, `arguments` when
present, and extra keys, with `state`, `results`, `physical: "Unknown"` and
`qualified: false`. Each named result has `raw`, `state` and any applicable
`number`, `label`, `flags`, `reserved`, `unmodeled`, `candidate_domain` or
`alternatives`. Do not invent values for these optional properties. A missing
field has no `raw` property; an explicit empty array has `raw: []`.

`state: "complete"` means local representation only. Missing or wrong-width
fixed fields have per-field `state: "incomplete"` and make the overall result
`"partial"`. An unresolved semantic label can coexist with complete raw arithmetic
or a complete raw token. Unsupported contexts return overall `"Unknown"` with
raw-only results and no formula. Incomplete data and Unknown conversions have no
invented `number`. Candidate results retain `grade: "Hypothesis"`; exact arithmetic
may additionally carry `calculation: "Proven"`, never replacing the candidate
grade. Unknown meanings remain Unknown even when their raw representation is
complete.

Retain absent, null, zero, false and explicit empty values independently wherever
the contract permits them, including extras. Null is not a substitute for a byte
array or typed argument. Retained data is detached: changing input or output
storage cannot change a later result or another call.

## Finite candidate views

All five views require primary **181**, secondary **4**, direction **positive**,
and the matching operation and view below. Hexadecimal OP notation in this table
corresponds to decimal integers in JSON. Views are independent. Missing operation,
explicit operation zero, another direction, or any other unsupported combination
returns raw-only Unknown without applying a formula. Opaque family/variant keys
do not imply support.

| View | Operation | Selected fields | Explicit arguments | Local candidate result |
| --- | --- | --- | --- | --- |
| `corrected-outside` | OP16 (22) | `temperature`: exactly 2 bytes | `divisor`: integer 16 or 256 | Signed LE16 divided by the explicit divisor. |
| `demand` | OP20 (32) | `setpoint`: exactly 1 byte | None | Zero: `no-demand`; nonzero: `offset-included-candidate`; no missing offset is computed. |
| `protection` | OP21 (33) | `temperature`: exactly 1 byte | None | Zero: `off`; positive: `protection-active`. |
| `adjustment` | OP26 (38) | `adjustment` and `room`: separately exactly 1 byte each | None | Only adjustment 1: `change-permitted`; other adjustment bytes remain unmapped. Room 255: contextual unavailable candidate; other room bytes have no assigned temperature scale. |
| `circuit-role` | OP0D (13) | `temperature`: exactly 1 opaque byte; optional `dhw_request`: exactly 1 byte when present | `role`: explicit string selecting `burner`, `mixer` or `dhw` | Temperature roles respectively `common-sensor`, `flow`, `tank`; numeric byte retained without a codec. `dhw_request` has a DHW role only for `dhw`. |

An unsupported explicit divisor is rejected as an invalid typed argument; neither
field length nor family selects a divisor. In corrected-outside, the unused
variable tail remains uninterpreted: its start and extent are Unknown. This page
does not locate or extract that tail.

An unknown string role retains raw tokens with Unknown role meaning; it does not
discover a role. Role eligibility and token values are separate: a mixer
`dhw_request` remains raw with no DHW role. Absence of that optional field alone
does not make a result partial. If present with wrong width, it is incomplete.
All unstated locations, conversions, bounds, formulas, sentinels, support and
physical adaptation remain Unknown.

## Complete synthetic example

Input (byte notation `10 00` becomes decimal JSON `[16, 0]`):

```json
{"context":{"primary":181,"secondary":4,"operation":22,"direction":"positive","view":"corrected-outside","family":"candidate-family","variant":"opaque"},"fields":{"temperature":[16,0]},"arguments":{"divisor":16},"extra":{"unset":null,"enabled":false,"zero":0,"empty":[]}}
```

Complete result; extra values retain their kinds and presence:

```json
{"context":{"primary":181,"secondary":4,"operation":22,"direction":"positive","view":"corrected-outside","family":"candidate-family","variant":"opaque"},"fields":{"temperature":[16,0]},"arguments":{"divisor":16},"extra":{"unset":null,"enabled":false,"zero":0,"empty":[]},"state":"complete","results":{"temperature":{"raw":[16,0],"state":"complete","number":1,"grade":"Hypothesis","calculation":"Proven"}},"physical":"Unknown","qualified":false}
```

| Raw bytes | Explicit divisor | Signed LE16 | Result number |
| --- | --- | --- | --- |
| `10 00` | 16 | 16 | 1 |
| `10 00` | 256 | 16 | 0.0625 |
| `F0 FF` | 16 | -16 | -1 |
| `F0 FF` | 256 | -16 | -0.0625 |

These calculations are Proven; their candidate meaning stays Hypothesis. No unit
or additional conversion is inferred.

| Independent branch example | Distinct result |
| --- | --- |
| Demand `setpoint: [0]` versus `[1]` | `no-demand` versus `offset-included-candidate`; no offset number. |
| Protection `temperature: [0]` versus `[1]` | `off` versus `protection-active`. |
| Adjustment `adjustment: [1]` versus `[2]` | `change-permitted` versus unmapped meaning (Unknown), both raw bytes retained. |
| Adjustment `room: [255]` versus `[254]` | Contextual unavailable candidate versus Unknown conversion; neither supplies a temperature number. |
| Circuit temperature `[40]`, roles burner / mixer / dhw | `common-sensor` / `flow` / `tank`, respectively, with the same numeric byte preserved in `raw`. |
| Mixer with `dhw_request: [40]` | Raw token retained; no DHW role or codec. |

## Independent partial and Unknown examples

A short temperature does not erase a complete independent DHW field:

```json
{"context":{"primary":181,"secondary":4,"operation":13,"direction":"positive","view":"circuit-role"},"fields":{"temperature":[],"dhw_request":[40]},"arguments":{"role":"dhw"}}
```

```json
{"context":{"primary":181,"secondary":4,"operation":13,"direction":"positive","view":"circuit-role"},"fields":{"temperature":[],"dhw_request":[40]},"arguments":{"role":"dhw"},"state":"partial","results":{"temperature":{"raw":[],"state":"incomplete","grade":"Hypothesis"},"dhw_request":{"raw":[40],"state":"complete","label":"dhw","grade":"Hypothesis"}},"physical":"Unknown","qualified":false}
```

Likewise, adjustment `[1]` with missing `room` retains complete
`change-permitted`; the room result is incomplete with no raw property. Room `[]`
has explicit empty raw, and room `[255, 254]` preserves the overlong raw array;
both are incomplete, without a number or unavailable label.

Unsupported context example, using explicit zero operation:

```json
{"context":{"primary":181,"secondary":4,"operation":0,"direction":"positive","view":"corrected-outside"},"fields":{"temperature":[16,0]},"arguments":{"divisor":16},"state":"Unknown","results":{"temperature":{"raw":[16,0],"state":"Unknown"}},"physical":"Unknown","qualified":false}
```

The corresponding input is the retained context, fields and arguments alone.
Absent operation also produces raw-only Unknown; explicit null operation instead
fails admission. Separately, an admitted unknown circuit role preserves `[40]`
without a role label or temperature number. A recognized mixer role labels its
temperature `[40]` as flow and leaves any DHW request raw. These Unknown meanings
do not imply qualification, freshness or physical support.

## Review assertions and shipping boundary

The page's discriminators are explicit: choosing a divisor by length is invalid;
applying /256 to the explicit /16 branch is invalid; OP20 zero is `no-demand`,
not a heat-demand label; adjustment 1 must not extend to every nonzero byte;
room FF has only the contextual adjustment meaning above and must not transfer
to other views; mixer temperature is flow and must not receive the tank role.

This page defines a local API contract only. New native protocol facts require
the public native documentation contract first. Full Gate D with its prescribed
read-only reference prerequisites, publication checks, fresh independent review
of the committed change and applicable transport classification remain mandatory
before a docs merge. No native completion, physical result or umbrella closure
follows from this companion.
