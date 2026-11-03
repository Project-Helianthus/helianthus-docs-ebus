# Local energy extent and publication candidate

The native B516 OP14 wire candidate remains unconfirmed; it does not establish
a qualified power service.
The native candidate layout and unresolved wire behavior are documented in
[B516 energy](../protocols/vaillant/ebus-vaillant-B516-energy.md) §9
(sub-id 0x14, current electrical power candidate)
and [§11](../protocols/vaillant/ebus-vaillant-B516-energy.md#11-open-questions).
This page defines only the bounded local software candidate from
[issue #824](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/824),
a partial slice of [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).
All proposed rules below are **Hypothesis**. No runtime feature is implemented.
The local u32/W projection is not a reinterpretation of the native
candidate binary32 word. Numeric identity between them remains Unknown.
No offsets for either word are selected here.

## Evidence and identity boundary

| Property | Grade |
| --- | --- |
| Local software candidate | Hypothesis |
| Native behavior | Unknown |
| Numeric identity | Unknown |
| Receipt | Unknown |
| Word offsets | Unknown |
| Word1 type | Unknown |
| Physical qualification | Unknown |
| Variant callback mapping | Unknown |

Proven arithmetic or synthetic checks do not promote the candidate to Proven.
Evidence grade, local eligibility, attempt, receipt and physical qualification
are separate axes. The identity context retains B516, OP14, actor, participant
address and variant independently. No period/source/usage selectors from OP10
are imported. No request/reply or eBUS/PeBUS direction/profile equivalence is
asserted; those unprovided properties remain Unknown. Synthetic addresses below
are labels, not network coordinates. No device model or installation is used.

## Extent and actor tables

Declared extent and actual available bytes are independent prerequisites for a
complete local two-word OP14 decode. Completeness permits decoding only; it does
not establish semantics or publication eligibility. Both incomplete cases retain
all raw bytes and partial last-known-good state without changing its age.

| Declared extent | Available bytes | Local result |
| --- | --- | --- |
| 8 | 9 | incomplete/raw |
| 9 | 8 | incomplete/raw |
| 9 | 9 | complete |
| 10 | 10 | complete |
| 0 | 9 | incomplete/raw |
| 9 | 0 | incomplete/raw |

The general predicate is declared extent >= 9 AND available bytes >= 9.
Neither a declared length alone nor padding missing bytes satisfies it.

| Actor | Type/range | Metadata/predicate |
| --- | --- | --- |
| actor0 | u32; no inherited rating range | W; actor-domain 0..2; availability and change are independent |
| actor1 | 0..maximum | step100; separate from actor0 |

For synthetic predicate coverage, actor-domain membership and availability
permit a local actor0 value; change independently permits a change notification
only when that value is available. Raw actor0 zero stays integer 0 and has no
rating. Actor1's maximum remains symbolic; no numeric maximum is supplied.
A scale0 number may omit `scale`; absence means zero scale here, never a nonzero
scale. No nonzero-scale conversion or actor1 power projection is specified.

| Raw local power | Published current_power |
| --- | --- |
| 0 | 0 |
| 2^32 - 1 | null |
| 7 | 7 |
| 2^32 - 2 | 4294967294 |

These are local integer u32 inputs, not a byte decoder for native OP14.

## Status, serialization and publication transitions

A per-device status operation rereads registered AND capable slots. Each emitted
entry has exactly `participant_address`, `coupler_address` (integer 0), and
`current_power` (integer u32, or null for 2^32 - 1). Participant addresses remain
distinct; neither address nor variant substitutes for registration or capability.
Do not emit a second word, previous value, total or freshness. Zero is integer 0,
not null. Preserve serialized bytes and count exactly; this proposal defines no
wire encoding. It grants no automatic requests or polling defaults.

| Transition | Local acknowledgement | Attempt | Delivered |
| --- | --- | --- | --- |
| No eligible entries | true | false | Unknown |
| Sole eligible null, all checks allow | true | true | Unknown |
| Membership denied | true | false | Unknown |
| Restriction denied | true | false | Unknown |
| Connection denied | true | false | Unknown |

Local acknowledgement occurs before membership, restriction and connection
checks, including each denied case. These checks are post-ack publication
conditions, not a new authorization gate. One eligible entry, including a sole
null, can permit an attempt when all checks allow. No eligible entries cannot.
An attempt is not a receipt. Duplicates need not materialize another state;
acknowledgement alone does not require state materialization. Callback
availability differs by variant, independently of the publication conditions.
The fixtures' callback-present and callback-absent labels describe synthetic
variants only; mappings to actual variants remain Unknown. Callback availability
is not proof of invocation or delivery. Failed/incomplete inputs retain partial
last-known-good state; no failure manufactures a zero or fresh observation.

## Offline acceptance and compatibility

[Scenarios](fixtures/aj17_b516_projection.json) cover independent extents,
registration, capability, participant address, synthetic variant, actor-domain,
availability, change and each post-ack condition. The
[standard-library suite](../tests/test_aj17_b516_projection.py) checks tables and
scenarios with independent arithmetic and transition expectations. These checks
qualify only the document/fixture agreement, not runtime or physical behavior.
No energy cache, publisher or projection implementation changes. Existing eBUS
MCP compatibility and GraphQL parity remain required; this contract changes no
public envelope. Admission stays fail-closed and partial state remains intact.
Nothing is stable before 1.0. This adds no namespace or authorization gate; any
roadmap wording remains 0.11. Independent committed-change review, publication
checks, full CI, Gate D and transport classification remain later ship gates.
