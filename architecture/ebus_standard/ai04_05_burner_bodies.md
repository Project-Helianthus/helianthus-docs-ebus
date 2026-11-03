# Burner metadata library API contract

This focused contract describes synthetic declarations for the Vaillant burner
family. The public native contract is [service 05](../../protocols/ebus-services/ebus-service-05h.md#vaillant-variants);
its standard tables and family alternatives remain separate. This page adds no
native wire claim and does not qualify installed support. All examples in the
[fixture](fixtures/ai04_05_burner_bodies.json) are synthetic.

## Library boundary

**Proven (application contract):** catalog presence does not make a standard
command executable. Preserve the [provider behavior](08-provider-contract.md)
and [identification scanner](03-identification.md). No active executor is added.
The metadata is independent of eBUS MCP compatibility and GraphQL projections:
retain the same raw alternatives, grades, unresolved conflicts and partial
last-known-good data in either projection. A failed local predicate retains raw
input and prior valid metadata; it never admits execution or overwrites that
prior state with an invalid candidate. No new endpoint or envelope is defined.

Nothing here is stable before Helianthus 1.0. Candidate defaults describe
metadata, not omitted physical fields or default materialization by a peer.
Evidence grade is independent of physical qualification, freshness, persistence
and execution permission; all four remain Unknown for these synthetic cases.

## Forms

Logical coordinates are library positions, not physical offsets. PB occupies
logical 0 and SB logical 1. Selecting a form requires its exact identity and
form; the same prefix alone cannot choose between the two candidate alternatives.

| Form | PB | SB | Logical fields | Grade | Interpretation |
|---|---|---|---|---|---|
| request | 05 | 01 | 2,3,4,5,6 | Hypothesis | five independent bytes |
| positive | 05 | 01 | none | Hypothesis | two constants only |
| standard_response | 05 | 04 | separate | Proven | standard three-field response; no candidate alias |

The standard-response row identifies the independent public standard table,
not family support. The positive declaration has no invented feedback field.
A single constant is incomplete; this declaration proves neither ACK nor echo.
Physical positive body and acknowledgement remain Unknown.

## Candidate fields

Each field is eight bits wide. Signed decoding is two's complement; every
conversion has scale 1 and offset 0. Celsius unit metadata adds no scale or
offset. Range failure preserves raw bytes, without clamping or substitution.

| Logical | Field | Carrier | Minimum | Maximum | Default | Unit | Scale | Offset | Grade |
|---|---|---|---|---|---|---|---|---|---|
| 2 | heat_state | u8 | 0 | 255 | 0 | none | 1 | 0 | Hypothesis |
| 3 | boiler_target | u8 | 0 | 90 | 0 | degC | 1 | 0 | Hypothesis |
| 4 | dhw_target | u8 | 0 | 90 | 0 | degC | 1 | 0 | Hypothesis |
| 5 | outside_temp | signed8 | -128 | 127 | 0 | degC | 1 | 0 | Hypothesis |
| 6 | setting_degree | u8 | 0 | 255 | 0 | % | 1 | 0 | Hypothesis |

## Candidate heat labels

The default heat state is shutdown. Unlabelled bytes remain numeric raw data.
DD check semantics remain separate and unresolved, and are not enabled by this
candidate; the standard table's DD meaning is not imported.

| Raw | Label | Grade |
|---|---|---|
| 00 | shutdown | Hypothesis |
| 55 | DHW | Hypothesis |
| AA | heating | Hypothesis |
| CC | emission check | Hypothesis |
| EE | controller stop | Hypothesis |
| DD | unresolved separate check | Unknown |

## Synthetic results

The numeric request columns follow the five-field order. Local validity means
only exact form/identity, length and declared byte domains; it grants no control
permission. A raw unlabelled heat value can satisfy a carrier predicate without
acquiring a supported meaning. Each result retains Hypothesis grade even when
its arithmetic is independently verified.

| Case | PB | SB | Raw fields | Values | Local valid | Grade |
|---|---|---|---|---|---|---|
| heating | 05 | 01 | AA,5A,00,FF,FF | 170,90,0,-1,255 | true | Hypothesis |
| boiler_91 | 05 | 01 | AA,5B,00,FF,FF | 170,91,0,-1,255 | false | Hypothesis |
| dhw_91 | 05 | 01 | AA,00,5B,FF,FF | 170,0,91,-1,255 | false | Hypothesis |
| outside_3f | 05 | 01 | AA,00,00,3F,FF | 170,0,0,63,255 | true | Hypothesis |
| outside_min | 05 | 01 | 00,00,00,80,00 | 0,0,0,-128,0 | true | Hypothesis |
| outside_max | 05 | 01 | EE,5A,5A,7F,FF | 238,90,90,127,255 | true | Hypothesis |

Outside 3F remains numeric raw 63, with no candidate sentinel. The standard
0..100 target bounds, setting limit and outside replacement are conflicting
alternatives, not corrections to this family candidate. Setting 255 stays in
its full byte domain. The heating case retains the label heating.

## Unknowns

| Property | Grade |
|---|---|
| physical_positive_body | Unknown |
| acknowledgement | Unknown |
| outside_3F_replacement | Unknown |
| control_permission | Unknown |
| scheduling | Unknown |
| other_05_candidate_bodies | Unknown |
| physical_qualification | Unknown |
| freshness | Unknown |
| persistence | Unknown |
| execution_permission | Unknown |

The same-batch catalog companion AI03 must merge first. Reverse navigation is
a later link-only task. These declarations neither widen scanning nor establish
polling, physical support or an executable command.
