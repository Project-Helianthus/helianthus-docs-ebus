# AJ25: local tunnel identity and adaptation predicates

This pre-1.0 contract is a bounded local software candidate, graded
**Hypothesis**. It describes no implemented runtime feature. Nothing here is
stable before 1.0. Refs helianthus-docs-ebus#832 and the partial parent
helianthus-docs-ebus#736; the parent remains open.

The [public native B517/B518 contract](../protocols/vaillant/ebus-vaillant.md#b517-and-b518-sub-ebus-tunnel)
comes first for wire claims. It records candidate layouts and unresolved B518
readings. The local rules below neither resolve those readings nor establish
native behavior. The local declarations remain Hypothesis candidates;
provenance is not published. All fixtures are synthetic; no device or
installation is represented.

## Identity and envelope

The client candidate accepts tunnel destinations 1 through 254 inclusive.
It selects one symbolic `fixed-channel`; its numeric value is Unknown.
The outer destination is the tunnel destination. The original destination and
original raw PDU occupy separate inner fields. Original service context is
retained independently and governs interpretation of returned data. The PDU is
opaque: no bytes are removed or inferred from a service label.

The following tables are the mechanically checked local contract. Values in
the second column are JSON literals, including strings; they are application
rules, not native wire field definitions.

| Identity key | Candidate value |
|---|---|
| grade | "Hypothesis" |
| tunnel_destination_min | 1 |
| tunnel_destination_max | 254 |
| channel | "fixed-channel" |
| channel_number | null |
| outer_destination | "tunnel_destination" |
| inner_destination | "original_destination" |
| inner_pdu | "original_pdu" |
| returned_context | "original_service" |
| raw_policy | "preserve" |

## Distinct adaptation exception

This local exception applies to the conjunction below. It is not a universal
eBUS or PeBUS prefix rule. Logical request PB/SB and input PB/SB are separate
selectors; neither is extracted from the opaque PDU by this contract.
The actual received length is the number of bytes in the supplied input array.
Check that index 4 exists before reading it. Missing index 4 produces
`incomplete`, even when other predicates fail. With sufficient data, any false
predicate produces `ineligible`; only their conjunction produces `eligible`.
Eligibility grants no transport, decoding, physical or admission qualification.

| Predicate key | Candidate value |
|---|---|
| grade | "Hypothesis" |
| ready | 3 |
| final_option | "nonzero" |
| minimum_input_length | 5 |
| length_index | 4 |
| length_bias | 6 |
| length_relation | "input[4] + 6 == len(input)" |
| request_service | [181, 23] |
| input_service | [181, 24] |
| prefix_policy | "no universal stripping" |

## Outcomes and partial state

Local codes 10, 6 and 7 remain raw local results. Their meanings are Unknown.
Remote negative feedback remains a separate outcome axis. In particular, a
local code 6 is never converted into a remote NACK. Neither a local result nor
remote feedback proves correlation, successful execution or admission.

| State key | Candidate value |
|---|---|
| grade | "Hypothesis" |
| local_codes | [10, 6, 7] |
| code_meanings | "Unknown" |
| remote_feedback | "separate" |
| incomplete | "preserve raw and last_known_good" |
| ineligible | "preserve raw and last_known_good" |
| admission | "withheld" |

Raw input and every original identity field survive eligible, ineligible and
incomplete outcomes. A partial input does not erase the separate last-known-good
record or promote that record into a fresh result. Direction labels in the
fixtures describe client request, returned data, local result and remote
feedback; they are not extra wire predicates. There is no claim that opposite
directions share semantics. Unknown facts and admission remain independent of
the Hypothesis grade and of a predicate passing.

| Property | Grade |
|---|---|
| native_behavior | "Unknown" |
| physical_route | "Unknown" |
| fragmentation | "Unknown" |
| timeout | "Unknown" |
| correlation | "Unknown" |
| negative_code_mapping | "Unknown" |
| trust | "Unknown" |
| channel_number | "Unknown" |
| code_meanings | "Unknown" |
| physical_qualification | "Unknown" |

## Scope and executable evidence

The [synthetic scenarios](fixtures/aj25_b517_local_tunnel.json) and
[standard-library unittest](../tests/test_aj25_b517_local_tunnel.py) check the
page tables, envelope identity, original return context, arithmetic conjunction,
raw local/remote separation and partial last-known-good preservation.
The tests independently vary ready state, option truth, length byte, actual
length, request PB, request SB, input PB and input SB. They retain a passing
control and cover arrays of lengths zero through four. Envelope controls vary
tunnel destination, original destination, raw PDU and both original service
components independently. They include boundary destinations 0, 1, 254 and 255.
Opaque PDUs and returns include B5/18-like bytes to guard against stripping.

No transport, channel opener or tunnel executor changes are proposed here.
No eBUS MCP or GraphQL contract changes follow; compatibility and parity remain
required of any later implementation. No active requests, polling defaults,
control execution or writable behavior are authorized. Runtime, transport,
smoke and physical qualification remain unperformed. Unsupported or incomplete
evidence keeps admission withheld. No new major or experimental namespace or
authorization gate is introduced; roadmap wording remains 0.11.
