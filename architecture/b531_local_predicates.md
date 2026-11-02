# B531 local capability and effective-limit predicates

This is a bounded candidate oracle for local software behavior, supplied by
issue #819 (partial child of #736). Read the public native
[B531 family contract](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md)
first: its layouts remain unconfirmed on the wire. This page adds no native
protocol fact or installed support claim. All tuples are synthetic.

## Scope and grades

Hypothesis: in the local OP01 normal loop, registered means whole-value
nonzero. For a registered entry, result zero clears capability; result one
sets capability only if prior is zero. Equal truth retains the raw prior.
Other result values and unregistered updates are Unknown. Each injected step
stores FFFF before updating capability, unconditionally; this marker does not
identify a physical frame or pointer. No timer or transfer semantics are supplied.

Hypothesis: the cached helper tests capability bit zero. A different selector
requires each of three whole fields to be nonzero and returns 9 on no match.
The single candidate in the selector table has local index 0. These predicates
must remain distinct: raw 2 is false for the helper, true as a whole value.

Hypothesis: ordinary entries contribute tokens and maxima only if registered
and capable (whole-value nonzero) and failure is zero. Index 1 belongs to a
separate unsupported branch; it is excluded from ordinary sums, and its
contribution to a full calculation is Unknown. For an already selected ordinary
set, effective = (unsigned64 token sum < unsigned64 maximum sum) AND
(limited-u32 != 0). Inputs and sums must fit their unsigned ranges; overflow
handling is unprovided and returns Unknown. Raw counts have no established units.

Hypothesis: OP03 gate byte 00 requests state 0. Any nonzero whole byte requests
1 + effective. This is not a bit-zero test. Requested state is distinct from
response feedback and applied state: both remain Unknown. There is no routing,
queue, control executor, publication, freshness or physical qualification claim.
Partial last-known-good raw values survive equal-truth updates; unknown inputs
do not authorize admission. No runtime, eBUS MCP or GraphQL behavior changes.

Proven applies only to the declared synthetic representation and arithmetic
checked by the accompanying unittest. It does not promote the local Hypothesis
claims to native Proven evidence. The raw 2 versus normalized 1 alternative,
helper versus whole-value disagreement, and unsupported special branch remain
visible rather than resolved by inference.

## Executable tables

Cells use JSON scalar notation. Row order is part of this bounded fixture.
Entry indices are local synthetic identities, not addresses or routing keys.
The oracle bounds identity, registered, capability and failure to unsigned32
synthetic representations; their actual storage widths are Unknown. Tokens
and maxima use unsigned64 arithmetic, and limited uses unsigned32. Invalid
inputs return Unknown within this candidate oracle, not a runtime error claim.
The entry table deliberately includes a special slot and three independently
ineligible controls. Ordinary selected indices are 0 and 2, with sums 3 and 4.

### transitions

| case | prior | result | next | leading_store | helper | whole |
| --- | --- | --- | --- | --- | --- | --- |
| "retain" | 2 | 1 | 2 | "FFFF" | false | true |
| "set" | 0 | 1 | 1 | "FFFF" | true | true |
| "clear" | 2 | 0 | 0 | "FFFF" | false | false |
| "equal_zero" | 0 | 0 | 0 | "FFFF" | false | false |

### selectors

| case | field_a | field_b | field_c | selected |
| --- | --- | --- | --- | --- |
| "all" | 2 | 2 | 2 | 0 |
| "first_zero" | 0 | 2 | 2 | 9 |
| "second_zero" | 2 | 0 | 2 | 9 |
| "third_zero" | 2 | 2 | 0 | 9 |

### entries

| index | registered | capability | failure | tokens | maximum |
| --- | --- | --- | --- | --- | --- |
| 0 | 2 | 2 | 0 | 1 | 2 |
| 2 | 1 | 1 | 0 | 2 | 2 |
| 1 | 1 | 1 | 0 | 100 | 1 |
| 3 | 0 | 1 | 0 | 50 | 1 |
| 4 | 1 | 0 | 0 | 50 | 1 |
| 5 | 1 | 1 | 1 | 50 | 1 |

### limits

| case | token_sum | maximum_sum | limited_u32 | effective |
| --- | --- | --- | --- | --- |
| "less" | 3 | 4 | 1 | true |
| "equal" | 4 | 4 | 1 | false |
| "greater" | 5 | 4 | 1 | false |
| "disabled" | 3 | 4 | 0 | false |
| "disabled_equal" | 4 | 4 | 0 | false |

### gates

| case | gate_byte | effective | requested | feedback | applied |
| --- | --- | --- | --- | --- | --- |
| "off_true" | 0 | true | 0 | "Unknown" | "Unknown" |
| "off_false" | 0 | false | 0 | "Unknown" | "Unknown" |
| "on_true" | 2 | true | 2 | "Unknown" | "Unknown" |
| "on_false" | 2 | false | 1 | "Unknown" | "Unknown" |

### unknown

| branch | result |
| --- | --- |
| "index_1" | "Unknown" |
| "unregistered_update" | "Unknown" |
| "result_2" | "Unknown" |
| "overflow" | "Unknown" |
| "units" | "Unknown" |
| "routing" | "Unknown" |
| "queue" | "Unknown" |
| "executor" | "Unknown" |
| "freshness" | "Unknown" |
| "qualification" | "Unknown" |

### claims

| claim | grade |
| --- | --- |
| "normal_loop" | "Hypothesis" |
| "cached_helper" | "Hypothesis" |
| "selector" | "Hypothesis" |
| "effective_limit" | "Hypothesis" |
| "requested_state" | "Hypothesis" |
| "synthetic_representation" | "Proven" |

The [synthetic fixture](fixtures/ai27_b531_local_predicates.json) and
[bounded unittest](../tests/test_ai27_b531_local_predicates.py) validate these
tables together. No device observations, capture provenance or native units
are supplied; repeatability here concerns injected local steps only.
