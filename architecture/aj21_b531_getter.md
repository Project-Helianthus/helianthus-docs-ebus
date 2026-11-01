# AJ21: B531 cached limits and local getter candidate

This focused pre-1.0 software contract is a `Hypothesis` for the B531 family
slice. It describes a local candidate, not native eBUS behavior. No native wire
contract or capture is supplied here; native behavior remains `Unknown`.
Nothing is stable before 1.0. This slice does not implement a getter, cache,
distribution path, transport, or API change.

## Evidence and admission

The supplied bounded issue requirements are the sole basis for the synthetic
candidate. The [synthetic scenarios](fixtures/aj21_b531_getter.json) preserve
raw inputs beside expected software outcomes. Arithmetic checks prove only the
internal consistency of these examples; they do not promote the candidate.
A native protocol claim would first require the public native documentation
contract and its primary evidence. No physical qualification or admission follows
from this page. Missing evidence keeps admission closed.

| Property | Grade or value |
| --- | --- |
| Local software candidate | Hypothesis |
| Native behavior | Unknown |
| Physical qualification | Unknown |
| Admission | closed |
| Factor operation order | Unknown |
| Factor application | Unknown |
| Timer argument | Unknown |
| Delayed initial job timing | Unknown |
| Physical cadence | Unknown |

## Failed read and partial state

For this candidate, an OP02 failure retains the preceding cached minimum and
maximum independently. Preserve the failed raw outcome alongside that last-known-good
state. A failed attempt has freshness `false`, matching `FreshPair`; retained
values cannot make the pair fresh. The failure adds no fresh metadata. A preceding
metadata record remains separate from new metadata.
The following are synthetic controls, with no capture or installation identity.

| Case | Before min | Before max | Read outcome | After min | After max | Freshness | New metadata |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base | 4 | 7 | failed | 4 | 7 | false | none |
| minimum-only | 5 | 7 | failed | 5 | 7 | false | none |
| maximum-only | 4 | 8 | failed | 4 | 8 | false | none |

## Getter arithmetic

The local getter candidate accepts a u32. First compute integer floor division
by 10, then retain the low 16 bits of that quotient. Preserve the original u32
beside the result. Do not saturate. Inputs outside u32 and any native unit or
encoding remain unprovided, hence `Unknown`.

| Raw u32 | Floor quotient | Low16 result |
| --- | --- | --- |
| 0 | 0 | 0 |
| 9 | 0 | 0 |
| 10 | 1 | 1 |
| 655359 | 65535 | 65535 |
| 655360 | 65536 | 0 |
| 4294967295 | 429496729 | 39321 |

At 655360, both divide-then-narrow and narrow-then-divide yield 0: the
input is exactly ten times 65536. This case cannot distinguish operation order.
It does distinguish saturation, which would yield 65535. At 4294967295,
divide-then-narrow yields 39321, whereas narrow-then-divide yields 6553;
this supplied vector distinguishes operation order. The request to distinguish
operation order at 655360 is arithmetically unsatisfiable.

## Distribution alternatives and identity

Direct distribution and aggregation are separate alternatives; neither selects
the other. One aggregate path names factor 86500 as uninterpreted metadata.
Its operation order and application are `Unknown`; no multiply or divide by
that factor is licensed. Aggregate output values remain `Unknown`.
Participant, slot, and route are independent local identity axes. Aggregation
must preserve every complete identity, including participants sharing a slot and
route. The scenarios vary each axis independently in both alternatives; they do
not invent protocol selectors, directions, predicates, or capability evidence.

| Alternative | Participant | Slot | Route | Output value | Factor |
| --- | --- | --- | --- | --- | --- |
| direct | synthetic-a | 2 | route-a | Unknown | Unknown |
| direct | synthetic-b | 2 | route-a | Unknown | Unknown |
| direct | synthetic-a | 3 | route-a | Unknown | Unknown |
| direct | synthetic-a | 2 | route-b | Unknown | Unknown |
| aggregate | synthetic-a | 2 | route-a | Unknown | 86500 |
| aggregate | synthetic-b | 2 | route-a | Unknown | 86500 |
| aggregate | synthetic-a | 3 | route-a | Unknown | 86500 |
| aggregate | synthetic-a | 2 | route-b | Unknown | 86500 |

## Lifecycle and boundaries

A timer argument and a delayed initial job are distinct lifecycle events. Neither
establishes physical cadence, polling defaults, or authorization to execute
control. Their relationship and actual argument/timing values remain `Unknown`.

| Event | Argument | Timing | Physical cadence |
| --- | --- | --- | --- |
| timer | Unknown | Unknown | Unknown |
| delayed-initial-job | Unknown | Unknown | Unknown |

The earlier raw-word times 10 conversion, capability predicates, and special
index 1 branch are outside this slice. No active requests or live writes are
authorized. Existing eBUS MCP compatibility and GraphQL parity are preserved;
this contract defines no new surface or namespace. No authorization gate or
roadmap milestone is introduced. The parent remains open; this is a partial
slice of issue #736, tracked by issue #828.
