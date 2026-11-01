# Pending B531 work and scaled-number boundary

Refs #827; partial child of #736. This is a bounded local software candidate,
graded **Hypothesis**, for heat-pump and backup-heater families. It implements
no runtime feature. Native behavior and every unprovided property remain
**Unknown**; neither grade establishes physical qualification.

The public native contract comes first: [B531 candidate wire evidence](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md).
Its unconfirmed requester layouts do not prove target behavior. This page adds
no native wire fact, unit, feedback enumeration, or applied OP01/03 claim.
The [synthetic scenarios](fixtures/aj20_b531_pending_conversion.json) contain
local example parameters only, with no installation evidence.

## Local pending work

Hypothesis: pending OP03 work has finite explicit local capacity. Production
capacity, replacement and coalescing policy remain Unknown. Capacity **2** is
solely a synthetic example. Three distinct requested identities cannot silently
become three completed operations. The fixture queues two, dispatches one, and
leaves the third requested with overflow marked `unresolved policy`; it does
not choose a production overflow policy.

Requested, queued, dispatched and completed are independently retained fields.
The following illustrative progression is not a required runtime transition
algorithm. Even local completion does not establish application on a target.

| Stage | Requested | Queued | Dispatched | Completed | Applied |
|---|---|---|---|---|---|
| requested only | true | false | false | false | Unknown |
| queued | true | true | false | false | Unknown |
| dispatched | true | true | true | false | Unknown |
| completed | true | true | true | true | Unknown |

Initialization, reset, topology change and late completion can change capability
independently of request and feedback. Synthetic counterexamples vary each event
with both request and feedback Booleans: capability changes from true to false
while partial last-known-good number/scale remains retained, and admission stays
false. These examples do not specify the real event predicates or a universal
capability transition. A late completion must not re-admit a stale capability.
Ten-second local health timing is not a physical control timeout.

## Finite scaled numbers

Hypothesis: the upstream numeric candidate is a signed 64-bit number multiplied
by 10 raised to a signed scale, evaluated as float64, then truncated toward zero
and saturated to u32. These four finite examples have independent expected
results. Nonfinite and intermediate overflow handling remain Unknown; do not
extrapolate this bounded arithmetic to those cases. Raw number and scale remain
available alongside the converted candidate.

| Number | Scale | u32 candidate |
|---|---|---|
| 123 | -1 | 12 |
| 2 | 1 | 20 |
| -2 | 0 | 0 |
| 4294967296 | 0 | 4294967295 |

W metadata for consume/obligation/active-power-limit does not establish native
units, a B531 conversion factor, or target capability.

## Independent fields and partial outcomes

Each field below is independently retained. Synthetic variation changes one
field at a time from a valid control; no field is a substitute for another.
These are local selectors and values, not a claim of a native identity schema.

| Field | Control | Independent variant |
|---|---|---|
| family | synthetic-heat-pump | synthetic-backup-heater |
| limit_id | limit-a | limit-b |
| operation | merge | partial; delete separately |
| direction | local-request | local-feedback |
| value | 123 | 124 |
| number | 123 | 124 |
| scale | -1 | 1 |
| active | true | false |
| duration | 60 | 61 |
| end_time | 120 | 121 |
| changeable | true | false |

Limit identity, merge/partial/delete, value/number/active state, duration/end-time
and changeability gates stay distinct. Duration and end-time here are synthetic
numbers with no inferred native units or clock semantics. A partial record
containing only `active: false` preserves omitted fields, raw patch and prior
values; omission is neither deletion nor permission to act. Merge is not partial
and delete is not inactive. Exact unprovided active/changeability predicates are
Unknown: either Boolean alone cannot authorize a write. Candidate data remains
fail-closed for admission, including complete data with plausible flags.

## Local feedback does not correlate requests

The local `(u32,u32,bool)->bool` acknowledgement, heartbeat arguments 60/120
seconds, statuses 2/3/8 and optional two-second `(value, engaged)` wait have no
request identifier. Two identical acknowledgements cannot be assigned to two
different pending requests. Changing either u32 or either Boolean, status,
heartbeat argument, waited value or engaged flag cannot create a request
identifier. Their meaning beyond the supplied facts remains Unknown. Local
feedback cannot prove applied OP01/03.

| Boundary | Value | Grade |
|---|---|---|
| candidate_grade | Hypothesis | Hypothesis |
| native_behavior | Unknown | Unknown |
| physical_qualification | Unknown | Unknown |
| production_capacity | Unknown | Unknown |
| replacement_policy | Unknown | Unknown |
| coalescing_policy | Unknown | Unknown |
| nonfinite_handling | Unknown | Unknown |
| intermediate_overflow_handling | Unknown | Unknown |
| native_units | Unknown | Unknown |
| exact_changeability_predicate | Unknown | Unknown |
| exact_active_predicate | Unknown | Unknown |
| ack_correlation | Unknown | Unknown |
| applied_OP01 | Unknown | Unknown |
| applied_OP03 | Unknown | Unknown |

No queue, heartbeat, writer or acknowledgement protocol is implemented. eBUS MCP
compatibility and GraphQL parity are unchanged; these scenarios add no API or
execution path. Nothing is stable before 1.0. This adds no major or experimental
namespace and no authorization gate before 0.9; roadmap wording remains 0.11.
The standard-library checks validate only the page tables and synthetic contract,
not transport, native behavior, runtime integration, or physical results.
