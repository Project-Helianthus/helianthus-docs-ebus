# B512 power and stepper field results

Refs Project-Helianthus/helianthus-docs-ebus#995 and
Project-Helianthus/helianthus-docs-ebus#736 (partial parent slice).

## Contract and evidence boundary

The public native [B512 candidate contract](../protocols/vaillant/ebus-vaillant-b512.md#candidate-sub-commands-op)
comes first; the [stepper supplement](../protocols/vaillant/ebus-b512-dhw-stepper.md)
retains the candidate OP08/09 detail. These references do not establish native
support. This page defines only the finite pre-1.0 local API for OP07/08/09;
the supplied local contract defines the power arithmetic and candidate domain.
All candidate meanings below are **Hypothesis**. Exact calculations may also
carry `calculation: "Proven"`; that never replaces `grade: "Hypothesis"`.

Package `vaillant` exports this pure callable field evaluator using only the Go
standard library:

```go
func Ab25Aq25Evaluate(ab25Aq25Input json.RawMessage) (json.RawMessage, error)
```

The compound naming stem is `ab25aq25` or exported `Ab25Aq25`: every new Go
declaration, parameter, local, field, helper and fixture ID uses that stem;
test functions start `TestAb25Aq25`. Literal JSON/protocol labels and existing
package and standard-library symbols retain their spelling. This is a contract,
not an Entries/Lookup catalog or schema. It requires no pending helper, sibling
checkout, initialization side effect, persistent cache, provider registration,
automatic caller or unmerged registry entry. There is no code-merge dependency.

## Input, admission and result shape

Input is one JSON object with `context`, `fields` and optional `arguments`.
`context` retains `primary`, `secondary`, `operation` when present, `direction`,
`view` and opaque family/variant keys. Present primary, secondary and operation
values must be integers 0..255. An absent operation differs from explicit zero;
`null` is neither and is rejected for a numeric context field. Identifiers select
a local candidate view and never qualify a family. Context, raw fields,
arguments and unknown extra keys are retained independently and unchanged.

`fields` maps field names to arrays of integer bytes 0..255. Empty arrays are
explicit data, not absence: an explicitly opaque empty field remains empty;
for a fixed-width field an empty array is incomplete. No extra opaque conversion
is defined here. `arguments`, when present, is an object containing exactly the
explicitly stated typed arguments for the selected view. None of these six
branches declares an argument, so a present `arguments` must be an empty object
and any entry in it is rejected. Unknown extra keys remain uninterpreted and
retained; they do not create additional typed arguments or supported fields.

Reject malformed or trailing JSON, duplicate keys at any depth, wrong kinds,
root keys named `state`, `results`, `physical` or `qualified` (reserved for the
output envelope, so retained extra keys are never overwritten),
nonfinite numbers, fractional or out-of-range bytes or integer arguments,
undeclared arguments, and
missing required arguments with an error and no successful result. No string,
`null` or Boolean is coerced to a number. Malformed byte arrays are admission
errors; valid arrays with missing, short or overlong fixed-width data instead
produce per-field incomplete results. Preserve each raw form and complete
independent siblings. Defaults never fill missing observations.

A successful return is one JSON object retaining the input components and extra
keys, with `state`, `results`, `physical: "Unknown"` and `qualified: false`.
Each result carries `raw` when present, `state`, candidate `grade` and applicable
`number`, `label`, `flags`, `reserved`, `unmodeled`, `candidate_domain` or
`alternatives`. Missing raw is absent, never replaced by `null`, zero or `[]`.
Permitted absent, null, zero, false and explicit empty values in opaque/extra
data remain distinct. No number is invented for incomplete data or an Unknown
conversion. Input and output storage cannot alter a later result or another
call; the evaluator owns no last-known-good cache.

`complete` means local representation only. Any required incomplete field makes
the overall state `partial`, while complete siblings remain available. An
unresolved semantic label can coexist with complete raw arithmetic. Unsupported
context yields raw-only `Unknown` with no formula applied. Independent useful
last-known-good state must survive partial interpretation; this pure call does
not manufacture freshness or promote prior data to a new observation.

## Finite supported branches

Every row requires primary **181** (B5), secondary **18** (12),
`view: "power-stepper"` and the exact direction and operation below. JSON numbers
are decimal; OP names and byte samples in prose are hexadecimal. Family/variant
keys are opaque, not support evidence. Other combinations, including an absent
operation, explicit operation zero, OP0A and a partial B51214 identity, remain
raw-only Unknown. No OP0A body or B51214 operation is inferred.

| Operation | Direction | Required fields and byte widths | Local result (all meanings Hypothesis) |
|---|---|---|---|
| 7 (OP07) | request | No fields | Empty request is complete; no power quantity inferred. |
| 7 (OP07) | positive | `maximum_power`: 1; `minimum_power`: 1 | Maximum u8 kW; minimum u8 / 2 percent. Both declaration defaults are 0. |
| 8 (OP08) | request | `inlet`: 2; `status`: 1; `stepper`: 1 | Inlet signedLE16 / 16 Celsius; status mapping below; stepper flags. |
| 8 (OP08) | positive | `setpoint`: 2; `stepper`: 1 | Independent setpoint signedLE16 / 16 Celsius; stepper flags; no status field. |
| 9 (OP09) | request | `release`: 1 | Independent request release flags. |
| 9 (OP09) | positive | `release`: 1 | Independent positive release flags. |

For `minimum_power`, the candidate raw domain is 0..250, yielding 0..125%.
Raw 251..255 retains arithmetic and `candidate_domain: false`, with no clipping
or sentinel. SignedLE16 first combines low then high byte and interprets a signed
16-bit integer, then divides by 16. Request inlet and positive setpoint never
substitute for one another. Status belongs only to the OP08 request.

| OP08 request status byte | Label | Representation |
|---|---|---|
| 00 | `valid` | Complete raw status; candidate meaning Hypothesis. |
| 55 | `short` | Complete raw status; candidate meaning Hypothesis. |
| AA | `interruption-or-disconnected` | Complete raw status; candidate meaning Hypothesis. |
| Any other byte, including 54 | `unmapped` | Raw remains complete; semantic meaning Unknown. |

For every OP08 `stepper` and OP09 `release` byte on either direction, bit 0 is
`flags.release`; bits 1..7 are reserved. Examples represent `reserved` as the
unchanged masked byte (`raw & 254`), preserving every reserved bit independently.
`01` gives release true and reserved 0; `80` gives release false and reserved 128.
A release flag never asserts movement or contact state.

## Synthetic complete example

OP07 positive input:

```json
{"context":{"primary":181,"secondary":18,"operation":7,"direction":"positive","view":"power-stepper","family":"synthetic-family","variant":"synthetic-variant"},"fields":{"maximum_power":[255],"minimum_power":[250]},"arguments":{},"extra":{"value":null,"enabled":false,"zero":0,"empty":[]}}
```

Complete result (numbers and units are local candidate interpretations):

```json
{
  "context": {"primary":181,"secondary":18,"operation":7,"direction":"positive","view":"power-stepper","family":"synthetic-family","variant":"synthetic-variant"},
  "fields": {"maximum_power":[255],"minimum_power":[250]},
  "arguments": {},
  "extra": {"value":null,"enabled":false,"zero":0,"empty":[]},
  "state": "complete",
  "results": {
    "maximum_power": {"raw":[255],"state":"complete","number":255,"grade":"Hypothesis","calculation":"Proven"},
    "minimum_power": {"raw":[250],"state":"complete","number":125,"candidate_domain":true,"grade":"Hypothesis","calculation":"Proven"}
  },
  "physical": "Unknown",
  "qualified": false
}
```

Changing only `minimum_power` to `[255]` gives number 127.5 percent,
`candidate_domain: false`, and retains `[255]`; maximum remains 255 kW.
Neither FF field is unavailable. Changing minimum to `[0]` gives 0 percent,
not absence. OP07 request with `fields: {}` is complete with `results: {}`;
the same empty fields in OP07 positive are partial with both quantities missing
and no numeric results. Declaration defaults do not repair that positive input.

## Independent partial and Unknown examples

OP08 request with short inlet, unmapped status and reserved bit:

```json
{"context":{"primary":181,"secondary":18,"operation":8,"direction":"request","view":"power-stepper"},"fields":{"inlet":[240],"status":[84],"stepper":[128]}}
```

Its result retains that context and those fields, leaves `arguments` absent,
and has `state: "partial"`, `physical: "Unknown"`, `qualified: false` with:

```json
{
  "inlet": {"raw":[240],"state":"incomplete","grade":"Hypothesis"},
  "status": {"raw":[84],"state":"complete","label":"unmapped","grade":"Hypothesis"},
  "stepper": {"raw":[128],"state":"complete","flags":{"release":false},"reserved":128,"grade":"Hypothesis","calculation":"Proven"}
}
```

This block is the `results` member. The inlet has no number. Missing inlet
omits its `raw`; `[]` or `[240,255,0]` retains that exact array and is incomplete
too. Complete status and flags remain available in each case.

A separate OP08 request with `inlet: [240,255]`, `status: [85]` and
`stepper: [1]` is complete: inlet is -1 Celsius, status is `short`, release is
true and reserved is 0. Status `[170]` gives `interruption-or-disconnected`;
`[84]` gives `unmapped` without suppressing complete inlet arithmetic.
Independently, OP08 positive with `setpoint: [16,0]`, `stepper: [128]` is
complete with setpoint 1 Celsius, release false and reserved 128. It has no
request status result. An extra supplied positive `status` remains raw extra
field data, never a supported status interpretation. Positive `stepper: [1]`
gives release true and reserved 0, independently of the request.

For each OP09 direction separately, `release: [1]` gives release true, reserved
0; `release: [128]` gives release false, reserved 128. Neither direction borrows
the other's byte. These complete flag representations establish no movement.

Unsupported context example:

```json
{"context":{"primary":181,"secondary":18,"operation":10,"direction":"positive","view":"power-stepper"},"fields":{"minimum_power":[255]},"extra":false}
```

Return the context, fields and extra unchanged with `state: "Unknown"`,
`physical: "Unknown"`, `qualified: false` and no interpreted results. In
particular there is no 127.5 conversion under OP0A. An absent operation and an
explicit zero likewise remain distinct raw-only Unknown contexts. A numeric
`operation: null`, duplicate nested key, fractional byte or trailing JSON is an
error with no successful result, rather than a partial or Unknown success.

## Required discriminators and remaining limits

The page asserts: do not clip minimum power to 100%; do not treat FF as
unavailable; do not conflate request inlet and positive setpoint; do not import
a positive status; do not label 80 release; do not equate release with movement.
Exact arithmetic being Proven does not qualify any family or candidate meaning.

Native support, physical layout, actual actuation, contact state, freshness,
physical effects, persistence, timeout and delivery remain **Unknown**.
`physical: "Unknown"` and `qualified: false` apply to every result, including
complete results. No active executor, automatic qualification, scan-default
change, native-family completeness claim or native completion follows.

AE17/AJ05 retain metadata; AQ23/24 covers valve/pump, AN13/14 OP06, and
AP11..16 other selected heat-pump fields. This ordinary AQ25 companion has no
merge dependency. Existing eBUS MCP compatibility and GraphQL parity remain
requirements; this page adds no transport endpoint or execution policy.
Nothing is stable before Helianthus 1.0; no new major or experimental namespace
is introduced. Gate D with its prescribed read-only references, publication
checks and fresh independent committed-change review remain mandatory before
merge. This documentation contract supplies no hardware or transport smoke
execution evidence and does not close the parent issue.
