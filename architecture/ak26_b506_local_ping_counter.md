# AK26: B506 local diagnostic counter boundaries

This pre-1.0 contract is a bounded local software candidate, graded
**Hypothesis**. It describes no implemented runtime feature. Nothing here is
stable before 1.0. Refs helianthus-docs-ebus#736 (partial parent; it remains
open).

The [public native B506 contract](../protocols/vaillant/ebus-vaillant-B506.md)
comes first for wire claims. The local rules below add no native claim and do
not change any parser or radio counter. All fixtures are synthetic; no device
or installation is represented.

## Counter representation

A diagnostic ping counter may count admitted output lines. It does not count
radio packets, delivered packets or parsed numeric values. In the explicit
counter representation below, an event object carries an `admitted` Boolean and
an opaque text token. An admitted-line event advances an unsigned32 counter by
exactly one, modulo 2^32. A non-admitted event leaves the counter unchanged.
The opaque token is never parsed and is never the increment amount. Wrap from
FFFFFFFF to 0 is arithmetic only; it is not a physical reset.

| Representation key | Candidate value |
|---|---|
| grade | "Hypothesis" |
| counter_type | "unsigned32" |
| modulus | 4294967296 |
| counts | "admitted output lines" |
| increment_per_admitted_line | 1 |
| increment_per_non_admitted_line | 0 |
| overflow | "wrap modulo 2^32" |
| text_token_role | "opaque; not the increment amount" |
| not_counted_as | ["radio packets", "delivered packets", "parsed numeric values"] |
| wrap_is_reset | false |

## Contexts

RX and TX selection are separate candidate contexts. Each context keeps its own
counter. This contract chooses no native code for either context and assumes no
reset shared across contexts.

| Context key | Candidate value |
|---|---|
| grade | "Hypothesis" |
| contexts | ["RX", "TX"] |
| counters | "separate per context" |
| native_codes | null |
| cross_context_reset | "not assumed" |

## Reset and Unknown boundaries

A reset event whose rules are not provided stays Unknown and yields no next
count; no value, including 0, is fabricated for it. Likewise no fallback state
and no initial state is invented.

| Property | Grade |
|---|---|
| line_admission_rule | "Unknown" |
| rx_tx_selection | "Unknown" |
| reset_conditions | "Unknown" |
| fallback_conditions | "Unknown" |
| initial_state | "Unknown" |
| native_support | "Unknown" |
| physical_effects | "Unknown" |
| persistence | "Unknown" |
| delivery | "Unknown" |

The counter arithmetic is mathematical for the declared representation; the
declarations themselves remain Hypothesis candidates.

## Scope and executable evidence

The [synthetic scenarios](fixtures/ak26_b506_local_ping_counter.json) and
[standard-library unittest](../tests/test_ak26_b506_local_ping_counter.py) check
the page tables and the arithmetic independently. Scenarios include counter 7
plus one admitted line becoming 8 even with opaque token 100, a non-admitted
event leaving 7, FFFFFFFE advancing to FFFFFFFF and then wrapping to 0, RX and
TX as separate labels, and an unprovided reset staying Unknown. The tests vary
the starting counter, the admitted flag, the opaque token and the context label
independently, with passing controls. Synthetic correctness establishes the
declared representation only.

No parser, radio counter, transmit route, scan default, active executor or
automatic native qualification is added. No hardware, transport or wall-clock
procedure is defined. No eBUS MCP or GraphQL contract changes follow;
compatibility and parity remain required of any later implementation. No new
major or experimental namespace or authorization gate is introduced; roadmap
wording remains 0.11.
