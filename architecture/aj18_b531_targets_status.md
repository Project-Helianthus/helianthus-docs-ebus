# AJ18: local power targets and status publication

## Evidence boundary

**Hypothesis**: this is a bounded local software candidate for issue #825,
part of [parent #736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).
The parent remains open. The public native contract comes first:
[B531 power limit](../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md)
labels its layouts unconfirmed on the wire. Nothing here upgrades that evidence.
Native behavior, physical qualification and every unprovided property are
**Unknown**. **Proven** is not a grade assigned to this candidate; passing
synthetic checks proves only consistency of these local examples.

The [synthetic scenarios](fixtures/aj18_b531_targets_status.json) contain no
installation observations. Boolean family and record predicates are explicit
inputs for a hypothetical qualifying device family. The exact family prefix
and record matcher are Unknown; no real identity is supplied or inferred.
Addresses below are synthetic tuple values; participant `76` denotes hexadecimal
`0x76`, while SPN `375` is decimal. No family is qualified by these examples.

## Independent identity and predicates

Each slot keeps slot index, participant address, route address, registered,
capability, eligibility and failure separately. Failure is retained as supplied;
no failure enum or extra failure-based admission predicate is established.
The generic heat-generator class and the other classifier are separate axes,
even when both contain the number 3. Generic class 3 is neither necessary nor
sufficient for the special marker. Marker eligibility and publication are
separate decisions: the eligible tuple alone cannot publish a device entry.

| Predicate | Required for marker 1 | Unknown treatment |
|---|---|---|
| participant_address | 76 hex | deny marker 1 |
| spn | 375 decimal | deny marker 1 |
| family_match | true | deny marker 1 |
| record_match | true | deny marker 1 |

All four predicates must match. This evaluates permission for marker 1, not an
assignment of an alternative marker when denied. A supplied eligibility value
is preserved separately; this contract does not overwrite it. Slot and route
changes do not substitute for participant identity. Classifier values do not
answer eligibility.

## Publication shape and partial state

| registered | capability | device entry |
|---|---|---|
| true | true | present |
| true | false | absent |
| false | true | absent |
| false | false | absent |

Registered-and-capable gates each entry, independently of marker eligibility.
A present entry carries participant and route addresses separately. The
conditional `power_limit` field is included only when a limit is present;
`min` and `max` are joined after that conditional field and are not suppressed
when the limit is absent. This specifies join order, not a new wire encoding.
No missing value becomes zero. Raw values and prior partial last-known-good
state remain available beside the projection. The fixture's partial observations
explicitly supply one changed value at a time and retain the other two values;
they do not establish a runtime update policy for every failure or missing field.

| Status field | Treatment | Grade |
|---|---|---|
| lpc_effective | retain raw independently | Hypothesis |
| lpc_possible | retain raw independently | Hypothesis |
| lpc_active | retain raw independently | Hypothesis |
| lpc_device_status | retain raw independently | Hypothesis |

No status encoding, Boolean interpretation, physical unit or relation among these
four fields is established. Fixture arithmetic is only raw integer subtraction:
`11 - 2 = 9`; it is not a physical power calculation or a limit-validity rule.

## Local acknowledgement and observed transitions

| Observation | Local acknowledgement | Receipt | Delivery | Materialized state |
|---|---|---|---|---|
| connection denial | true | Unknown | Unknown | prior retained in fixture |
| membership denial | true | Unknown | Unknown | prior retained in fixture |
| restriction denial | true | Unknown | Unknown | prior retained in fixture |
| duplicate | true | Unknown | Unknown | prior retained in fixture |
| local control | true | Unknown | Unknown | partial update in fixture |

An early local acknowledgement may precede membership, restriction or connection
denial. With connection=false it remains local-only. A duplicate attempt need
not update materialized state; these examples retain the prior values without
claiming every duplicate must do so. Even the local-control example is solely
an explicit local observation, with no implication of receipt or execution.
No-acknowledgement, startup and Boolean-control variants are also explicit
fixture inputs, not inferred protocol transitions.

Startup restriction `1` is a separate input from subsequent Boolean control;
neither establishes actual delivery. Unknown evidence fails closed: it cannot
become a positive identity match, native qualification or execution authority.

## Publication limits

This change adds no publisher, route registration, active limit request, polling
or control execution. It defines no new eBUS MCP command or GraphQL field and
changes neither interface; any future implementation must preserve eBUS MCP
compatibility and GraphQL parity. No raw/partial state may be erased to produce
an apparently complete result. No receipt, delivery, physical capability or
qualification follows from these local checks.

Nothing is stable before 1.0. There is no new major or experimental namespace,
and no authorization gate is introduced before 0.9; roadmap wording is 0.11.
Full documentation gates, independent committed-change review, publication
checks, full CI and transport classification remain later ship requirements.
