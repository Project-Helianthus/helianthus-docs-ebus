# AJ24: two-bit timer-manager eligibility candidate

This pre-1.0 architecture contract is **Hypothesis**, a bounded local software
candidate for issue #831. Refs helianthus-docs-ebus#736; this partial slice does
not close the parent. It adds no runtime feature, request builder, active timer
path, polling, control execution, API contract or namespace. Nothing is stable
before 1.0. eBUS MCP compatibility and GraphQL parity remain unchanged.

## Evidence and scope

The public native contract comes first: [B555 candidate inventory and framing](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#31-sub-command-inventory-candidate)
and [EM status candidate](../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#56-em-status-request-and-em-control-entries-candidate).
Those sections describe candidate OP00 flags and an unresolved response adapter;
they do not prove this application predicate. The issue supplies the local
controller-type, SPN and family predicates. No native observation is added.
All tuples in the [synthetic fixture](fixtures/aj24_b555_manager_predicate.json)
are invented controls, with no installation identifiers or physical evidence.

| Property | Grade |
|---|---|
| local_candidate | Hypothesis |
| native_behavior | Unknown |
| exact_family_prefix | Unknown |
| response_adaptation | Unknown |
| physical_qualification | Unknown |
| other_caller_prerequisites | Unknown |
| runtime_transition_policy | Unknown |

No candidate is promoted to Proven by passing these checks. Eligibility does
not grant trust or write permission, admission to execution, or physical
qualification. Unprovided properties remain Unknown. Families, rather than
individual models, are the scope of the family predicate; no prefix is invented.

## Abstract request and distinct roles

These are protocol role constants for a synthetic tuple, never instructions to
contact a participant. Count includes the opcode byte. The direction names the
abstract request; this contract does not define response adaptation or another
transport variant. R1 below is an already supplied candidate response byte,
not a claim about where to extract it from an arbitrary response.

| Request field | Value |
|---|---|
| initiator | F1 |
| target | 08 |
| service | B555 |
| count | 1 |
| data | 00 |
| direction | initiator_to_target |

| Role property | Address |
|---|---|
| family_address | 15 |
| route_address | 08 |

Address `15` is the family role; address `08` is the route role. They are
independent properties, not interchangeable identities. A matching route is
not evidence of a matching family.

## Local arithmetic and policy

| Output | R1 bit |
|---|---|
| first | 0 |
| second | 1 |

For a supplied byte, independently select `first = (R1 & 1) != 0` and
`second = (R1 & 2) != 0`. Preserve the raw byte and the uninterpreted remainder
`R1 & 252`. High bits have no invented meaning. The local candidate flag is
true exactly when controller type equals 2, SPN equals 385, family_match is
explicitly true, and both output Booleans are true. Unknown family fails closed.
The distinct first-bit-only caller policy consumes only `first`: it accepts
`01`, while the both-bit gate rejects it. Its other prerequisites are Unknown;
this isolated bit policy is not a complete caller admission contract.

| R1 | first | second | unknown_high_bits | both_bits | first_bit_policy |
|---|---|---|---|---|---|
| 00 | false | false | 0 | false | false |
| 01 | true | false | 0 | false | true |
| 02 | false | true | 0 | false | false |
| 03 | true | true | 0 | true | true |
| 80 | false | false | 128 | false | false |

The all-true control uses type 2, SPN 385 and family_match true. Separate
synthetic cases change only type, only SPN, and only family_match; another
uses Unknown family. Each fails eligibility despite `03`. A missing byte keeps
both outputs and the high-bit remainder Unknown (JSON null); eligibility and
the current candidate flag remain false. Raw and partial outcomes stay separate
from semantic interpretation and qualification. The fixture retains a distinct
last-known-good record unchanged across every case, including the partial case;
it never substitutes that record for a missing current byte. This is synthetic
bookkeeping, not a specified runtime transition or persistence policy.

## Offline validation and mutation obligations

The standard-library unittest checks these page tables against independent
literal expectations, then checks fixture scenarios against independent bit
arithmetic and a transition oracle. The oracle replaces the current result and
retains last-known-good separately; it is test-local, not a runtime feature.
Every byte value is exercised locally. Negative contract controls vary each
request field (initiator, target, service, count, data, direction), each address
role, each output position, controller type, SPN, family_match, required bits,
and conjunction operator. They catch altered constants, reversed direction,
merged roles, swapped outputs, missing predicates and either-bit truth.
Scenario controls vary raw_r1, type, SPN, family true/false/Unknown and missing
response independently. Grade and Unknown controls reject promotion and
fabricated knowledge. These are synthetic contract checks, not native evidence,
transport tests, smoke tests or physical results. Full ship gates and independent
committed-change review remain later requirements.
