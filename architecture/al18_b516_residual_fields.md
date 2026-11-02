# B516 residual fields: clock order and raw independence

Read the public [native B516 candidate contract](../protocols/vaillant/ebus-vaillant-B516-energy.md#10-other-b516-sub-ids-candidate)
first. It establishes the candidate boundary, not confirmation of these residual
layouts. The finite design facts in [issue #1024](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1024)
are the source of the additional Hypothesis statements below. This is a partial
companion to [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).
The catalog prerequisite must merge before this page. Its merge and runtime
checks are unverified here; no cross-repository runtime import is added.

This page specifies a finite library representation, not a native profile or a
second dictionary. **Hypothesis** grades candidate interpretation. **Proven** is
limited to checked synthetic arithmetic and declared representation shape;
companion code behavior requires its own checks. **Unknown** remains explicit
where facts are unprovided. Physical qualification, presence, freshness,
execution, effects, persistence and delivery are separate axes, all Unknown in
these examples. Metadata presence alone cannot establish any of them.

## Ab51Entries / Ab51Lookup contract

`Ab51Entries()` enumerates finite catalog metadata or returns an error.
`Ab51Lookup(key)` returns one exact entry, a found flag and an error. An exact
miss returns no usable entry, false and no error. Invalid catalog data returns
no usable enumeration; lookup returns no usable entry, false and an error.
The entire catalog must validate before a matching entry is admitted, including
invalid later entries. Malformed JSON, trailing input, unknown properties,
incomplete or duplicate exact keys and invalid grades fail closed.

The identity below is the representation key, not a newly established wire
layout. Synthetic examples deliberately supply no native direction or variant
association. Exact matching retains every axis; no wildcard, normalization,
case folding, cross-family fallback or nearest match is permitted.

| Key axis | Exact identity rule |
| --- | --- |
| family | exact family token |
| variant | exact variant token; synthetic token is not a native association |
| primary | exact primary service |
| secondary | null differs from zero |
| operation | null differs from zero; OP02/03/08/0D/0E remain distinct |
| direction | explicit none token differs from request or positive |
| field | exact field token |
| alternative | explicit none token differs from a named alternative |
| group | null differs from zero; no B524 group is inferred |
| instance_scope | explicit none token differs from a supplied scope |
| register | null differs from zero; no B524 register is inferred |

Every returned enumeration and lookup owns independent memory, including
nested maps, slices, raw buffers and optional key storage. Mutating one result
must not change another held result or a later call. These are requirements of
the companion contract, not a claim that this documentation executes its API.
On failure preserve previously retained, independently owned last-known-good
state and its raw provenance. Failed new data must not be admitted as fresh or
qualified. Independently useful fields survive a partial interpretation failure;
unknown semantics never justify discarding their raw bytes.

## Finite residual interpretation

| Operation | Candidate contract | Grade / unresolved boundary |
| --- | --- | --- |
| OP08 | setpoint u8 / 2 degrees Celsius; mode; special-function; five independent message bytes; then minute/hour/day/month/year | Hypothesis; unprovided widths, offsets and variant associations Unknown |
| OP08 clock | FF replacement selection precedes packed-decimal validation; FA remains invalid/raw | Hypothesis; replacement meaning, century and timezone Unknown |
| OP0D | four independent raw little-endian u16 fields | Hypothesis; units, labels, sentinels, offsets and variant associations Unknown |
| OP0E | page plus variable raw data, including empty metadata | Hypothesis; page width, data maximum and peer acceptance Unknown |
| OP02 | minute metadata on a second field conflicts with unprovided field associations; day/month default0 is out-of-domain | Hypothesis; associations unresolved, calendar conflict retained |
| voltage | conversion is variant-specific | Unknown here; no converter selected |
| OP03 | decimal software-version structures and identity-bearing structures exist as candidates | Hypothesis; unprovided fields not imported or instantiated |

Order means logical order only, not inferred byte offsets. The clock has exactly
five components, **minute/hour/day/month/year**, with no seconds. Message bytes
are five independent bytes; their values are not enums or a concatenated text
field. Mode and special-function remain separate raw metadata without invented
widths or labels. Setpoint is u8 with the candidate half-degree scale; it does
not establish a full OP08 frame. No century or timezone is inferred.

For each clock component, retain raw FF and select replacement before decimal
validation. No replacement value or native effect is invented. Raw 12 yields
12 under packed-decimal conversion, not binary 18; FA has no decoded value.
The synthetic vector 12/23/31/12/99 yields 12/23/31/12/99 in that exact order.
If only one component is invalid, preserve every independent valid component
and retain the previous useful value for the failed component separately from
its new raw token. Retention is illustrative partial-state representation,
not proof of a device update policy or acceptance.

OP0D words 00 00, 01 00, 00 01, FF FF yield 0, 1, 256, 65535.
They stay four fields; zero and FF FF have no inferred sentinel meaning or unit.
OP0E page width stays null, not u8 by analogy. Variable data has no established
maximum. Empty data is a metadata example, not evidence of peer acceptance.
The OP02 minute association remains unresolved; day/month default0 conflicts
with their 1-based calendar domains and must not be silently repaired or erased.

## Synthetic controls and admission boundary

The [small JSON example set](fixtures/al18_b516_residual_fields.json) carries
representation keys and independent expected results, not a full catalog.
Its keys are explicitly synthetic, with family B516, primary 181, secondary 22,
variant synthetic-residual, direction/alternative/instance_scope none and
null group/register. Field tokens name illustrative scenarios only. Numeric
operations are decimal: 8, 13, 14 and 2. These are not observed telegrams.

The scoped standard-library tests use independent literal results for time
conversion, four-word decoding, raw retention and conflicts. They vary every
key axis separately, every clock component, every message byte and each word
with otherwise valid controls. They check page/fixture sensitivity, not a
production parser, memory-copy implementation, full catalog cardinality or
full companion parity. Only the five message bytes, five clock components and
four raw words have supplied cardinalities; total catalog size is Unknown.

Existing passive energy, OP14 aggregation, time-positive alternatives,
energy-type flags, meter/clear enums and physical identity work stay separate.
No earlier codebook or cached-state policy is repeated. No transmitter, polling
default, write admission or automatic native qualification is added. Existing
eBUS MCP compatibility and GraphQL parity remain requirements for later
integration; this page registers no application endpoint. Nothing is stable
before Helianthus 1.0. No new major or experimental namespace is introduced.
No authorization gate is introduced before 0.9; roadmap wording remains 0.11.
