# AJ19: independent distribution and consumer state

Refs #826; partial child of #736. The parent stays open.

This is a **Hypothesis**: a bounded local software candidate for the B531
workstream. No distribution service or consumer is implemented here. These
application rules do not establish a native wire contract. Native behavior,
physical capability, execution authority and qualification remain **Unknown**.
No native opcode, register, direction, device mapping or formula is supplied.
Any later protocol claim requires the public native documentation contract first.

The fixture uses synthetic tuples and generic families only. Local operation
names and variant labels are scenario selectors, not native identifiers. No
capture, installation identity or runtime observation is represented.

## Independent retention and explicit reset

Each field has its own value; no field is an alias of another. Integral units
remain Unknown. Gates are retained local state, not an authorization mechanism.
Reset takes explicit `new_current` and `new_energy` arguments; zero and false
are supplied scenario values, not inferred native defaults.

| Field | Reset effect | Grade |
| --- | --- | --- |
| cap | retain | Hypothesis |
| sequence | retain | Hypothesis |
| limited | retain | Hypothesis |
| changed | retain | Hypothesis |
| current_integral | new_current | Hypothesis |
| aggregate_integral | retain | Hypothesis |
| sequence_count | retain | Hypothesis |
| energy_flag | new_energy | Hypothesis |
| counter | retain | Hypothesis |
| gates | retain | Hypothesis |

For `(current=7, energy=true, aggregate=19, counter=3, gates=5)`, explicit
`(new_current=0, new_energy=false)` yields `(0, false, 19, 3, 5)`.
Current changes by -7; aggregate, counter and gates each change by zero.
Sequence, limited and changed also survive reset. This arithmetic is local
fixture evidence; it does not determine energy units or accumulation semantics.

## Consumer distinctions

| Status input | Local class | Grade |
| --- | --- | --- |
| 0..4 | in_range | Hypothesis |
| >4 | above_range | Hypothesis |

| Marker width | Raw null | Numeric zero | Grade |
| --- | --- | --- | --- |
| 32 | FFFFFFFF | value | Hypothesis |
| 16 | FFFF | value | Hypothesis |

Both capability and status consumers retain raw input beside classification.
States 0 through 4 remain individually visible; state 5 is above_range, not a
synonym for any of them. Null is distinct from numeric zero at either width.
Widths and raw markers must not be interchanged. Unknown inputs stay Unknown;
these tables do not imply decoding rules for other widths or encodings.

Capability formula inputs remain separate. `input_a` and `input_b` are synthetic
opaque slots used to test independent retention, not supplied native field
names. No energy flag is added to those inputs. The actual formula, result,
units and eligibility predicates remain Unknown; there is no invented arithmetic
combination or admission decision.

## Operations and variants

| Selector | Local behavior | Grade |
| --- | --- | --- |
| set_limit | ack_before_execution_possible | Hypothesis |
| set_limited | ack_before_execution_possible | Hypothesis |
| direct | direct_recalculation | Hypothesis |
| timer | timer_driven_recalculation | Hypothesis |
| ignored_completion | retain_requested_state | Hypothesis |
| replay_a | separate_unknown_replay | Hypothesis |
| replay_b | separate_unknown_replay | Hypothesis |

An acknowledgment and setter execution are separate outcomes: acknowledgment
may precede execution and cannot prove receipt or execution by a controller.
Direct and timer-driven recalculation remain distinct local variants. The label
`daily` establishes no cadence; actual cadence and timing remain Unknown.

Supported-use-case order is `limit-control`, then `temperature-control`.
Do not sort alphabetically or treat the order as a native execution sequence.
An ignored false completion retains requested local state, without rollback.
Other replay variants remain distinct and their behavior remains Unknown; do
not generalize the ignored-completion rule to them.

Partial outcomes retain raw evidence and last-known-good values independently
from pending requested values. A pending setter or missing observation cannot
replace a retained value with fabricated success, zero or null. Admission stays
closed without independent qualification. Neither grade nor a local check
establishes physical qualification. Existing eBUS MCP compatibility and GraphQL
parity are obligations on any later implementation; this contract changes
neither interface and supplies no endpoint or artifact schema for them.

## Verification and boundary

The adjacent [synthetic scenarios](fixtures/aj19_b531_distribution_consumers.json)
and [standard-library checks](../tests/test_aj19_b531_distribution_consumers.py)
check table consistency, explicit reset arithmetic and independent field
preservation. Their success proves only that these local artifacts agree with
this bounded candidate. Runtime, native semantics and physical results are not
qualified. Nothing is stable before 1.0; no new major or experimental namespace
is introduced. There is no authorization gate before 0.9; roadmap wording is
0.11. No active requests, polling defaults or control execution are specified.
