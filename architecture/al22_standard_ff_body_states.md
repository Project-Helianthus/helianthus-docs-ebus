# Standard FF body states and raw remainders

## Native contract and scope

Read the public [native FF contract](../protocols/ebus-services/ebus-service-FFh.md)
first, particularly its query-direction, FF04 structural-distinction and FF06
structural-distinction sections. It cites the application-layer and network
management specifications. The native contract takes precedence over this
finite library representation. This page adds no native observations.

**Proven:** the seven native service identities and the finite representation
boundaries below. **Proven** for synthetic arithmetic means byte grouping only.
Any candidate interpretation remains **Hypothesis**. Physical qualification,
presence, freshness, native execution and installed support each remain
**Unknown**, independently of grade and representation completeness. Nothing is
stable before Helianthus 1.0.

## Ab54Entries and Ab54Lookup

The companion catalog prerequisite must merge before this page. Its merge state
and runtime behavior are unverified here. This is the declared contract for
`Ab54Entries()` and `Ab54Lookup(key)`, not evidence of a checked implementation.
No cross-repository runtime import is added.

`Ab54Entries()` returns the finite metadata collection or an error.
`Ab54Lookup(key)` returns an entry, a found boolean and an error. A successful
lookup returns the whole matching entry, true and no error. A well-formed miss
returns no entry, false and no error. Invalid catalog data returns an error,
no admitted collection or lookup entry, and false for lookup. Validation covers
the whole catalog before lookup: an invalid later row cannot admit an earlier
match. Duplicate exact identities are invalid. Failure is never an empty success.

The exact service identity axes in this finite contract are `(PB, SB, direction)`.
PB and SB are byte integers; direction is an exact, case-sensitive token.
Every axis is required. Missing, null, wrong-type or out-of-byte coordinates do
not select a row. No wildcard, direction conversion, nearest-key fallback or
selection by body length is permitted. These are semantic identity axes; this
page does not invent additional companion key fields or Go struct spellings.

| Service | PB | SB | Direction | Role |
|---|---:|---:|---|---|
| FF00 | 255 | 0 | broadcast | reset-status identity only |
| FF01 | 255 | 1 | broadcast | reset-target-configuration |
| FF02 | 255 | 2 | broadcast | failure-message |
| FF03 | 255 | 3 | initiator-to-target | net-status-query |
| FF04 | 255 | 4 | initiator-to-target | monitored-participants-query |
| FF05 | 255 | 5 | initiator-to-target | failed-nodes-query |
| FF06 | 255 | 6 | initiator-to-target | required-services-query |

This is seven distinct service identities, not seven executable routes or an
inventory of every body/field record. Initiator-to-target means initiator to the
queried initiator's companion target. Each query's reply belongs to that same
PB/SB service. Response-body examples below retain that query identity; they do
not convert a response-form lookup key into a query key. Target identity and
request/reply correlation remain Unknown here.

Every enumeration and successful lookup returns independently owned memory,
including nested/raw data. Mutating a result cannot change the catalog, another
result or a later call. On error or absence, consumers preserve partial
last-known-good state and its raw evidence separately; they must not replace it
with fabricated empty/zero values or relabel retained values as fresh. Admission
fails closed. No cache or state-update API is introduced.

## Finite body boundaries

FF01 has NN=0. Its Proven reset meaning concerns dynamic target configuration
and requires an explicit emission policy; this area adds no emitter. FF02 has
NN=0 independently of responder availability. Neither an empty body nor a
catalog hit supplies physical ACK. Bodies for FF00, FF03 and FF05 are outside
this area; none are fabricated in the examples.

For FF04, preserve the declared NN=1..10 interval. NN=1 cannot contain both
follow-block and status overhead and remains truncated/raw. NN=2 clears only
the minimum-overhead condition; full semantic validity remains Unknown.
Exact body fields beyond this lower bound remain Unknown in this contract.
Available overhead bytes remain useful raw evidence without an invented count
or semantic decode. The FF04 example remainder retains the entire body because
no further interpretation is admitted here.

For FF06, preserve the declared NN=1..10 interval. Complete service-pair layout
requires NN=1+2n for a nonnegative integer n. After the one overhead byte,
retain every whole two-byte group and any unmatched trailing byte separately.
Even lengths cannot contain whole pairs throughout and remain incomplete/raw.
An incomplete suffix must not erase preceding complete pairs. Pair bytes are
opaque; their count does not establish pair meaning or a peer response.
Pair-layout completeness does not establish full semantic validity or finished
pagination. No new normative maximum is inferred.

The [small synthetic example set](fixtures/al22_standard_ff_body_states.json)
contains isolated response-body bytes, not telegrams or a second dictionary or
native profile. NN is the length of that isolated byte array, not an independent
declared-length input. `available_overhead_raw`, `pair_bytes` and `raw_remainder`
are independently owned snapshots beside the unchanged `raw_body`.
`pair_layout_complete` is null for FF04, where only the minimum is checked.
`semantic_validity` remains Unknown for every example.

| Case | Service | NN | Minimum overhead met | Pair count | Pair layout complete | Body state | Raw remainder |
|---|---|---:|---|---|---|---|---|
| ff04-one | FF04 | 1 | false | absent | absent | truncated/raw | 80 |
| ff04-two | FF04 | 2 | true | absent | absent | minimum-overhead-only | 80 A5 |
| ff06-one | FF06 | 1 | true | 0 | true | complete-pairs | empty |
| ff06-two | FF06 | 2 | true | 0 | false | incomplete/raw | 31 |
| ff06-three | FF06 | 3 | true | 1 | true | complete-pairs | empty |
| ff06-four | FF06 | 4 | true | 1 | false | incomplete/raw | 53 |
| ff06-five | FF06 | 5 | true | 2 | true | complete-pairs | empty |

The normative local declaration is checked independently of the examples:

```json
{
  "identity_axes": ["PB", "SB", "direction"],
  "service_identity_count": 7,
  "invocable_route": false,
  "ff04_declared_nn": [1, 10],
  "ff04_minimum_overhead": 2,
  "ff04_minimum_implies_semantic_validity": false,
  "ff06_declared_nn": [1, 10],
  "ff06_complete_nn": "1+2n",
  "ff06_even_complete": false,
  "pair_count_implies_peer_response": false
}
```

## Verification and companion boundary

The [scoped standard-library test](../tests/test_al22_standard_ff_body_states.py)
checks this declaration, all seven identities, independent PB/SB/direction
controls, raw retention and the synthetic length results. It checks documentary
examples only; it does not execute Ab54Entries/Ab54Lookup, their allocation/error
paths or a native exchange. No code result, native effect or full parity is
claimed before its own checks.

Native emission, forwarding eligibility, target identity/correlation, lifecycle
effects and installed support remain separately Unknown. This page creates no
invocable route, transmitter, polling default, automatic native qualification
or write admission. Existing eBUS MCP compatibility and GraphQL parity remain
carried requirements with their own checks; no endpoint or schema is added.
Earlier liveness/reset-state policies, named codebooks, native FF prose repairs,
navigation and runtime integration are outside this residual area.

Refs helianthus-docs-ebus#1038 and helianthus-docs-ebus#736; this is a partial
child and does not close the parent. Full Gate D, independent committed-change
review, publication checks and applicable transport classification remain later
merge requirements.
