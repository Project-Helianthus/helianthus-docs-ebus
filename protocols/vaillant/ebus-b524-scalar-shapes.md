# B524 scalar alternatives and room selectors

## Native scope and evidence

The [native B524 contract](ebus-vaillant-B524.md) comes first: OP02 and
OP06 are independent namespaces. Its [register map](ebus-vaillant-B524-register-map.md)
provides contextual names, not qualification for the candidates below.
The [synthetic native tuples](fixtures/ai06_b524_scalar_shapes.json) are isolated
field bytes, not captures or complete replies. Service is B5/24. Source and
destination, product and firmware, and capture conditions are not supplied;
there is no observed installation in these examples.

**Proven (identity rule):** opcode, group, instance and register remain distinct;
family qualification, direction and field role also remain distinct from a
usable value or physical support. An omitted family or instance is explicit
missing qualification, never a wildcard and never an inferred concrete instance.
Here `Unknown` in an identity cell denotes that omission (`null` in the tuples).
The controller-family label is a qualification axis, not a single product name.

**Hypothesis (native mappings):** every row below is a separate candidate.
No synthetic calculation promotes a mapping to Proven. The widths describe
isolated field bytes only; logical positions in a complete message are Unknown.
Table order preserves the two RR001B alternatives followed by the separate
GG01 fields and room-control roles; it is not selector priority.

## Candidate declarations

| Candidate | OP | GG | II | RR | Family | Direction | Role | Codec | Width | Order | Factor | Offset | Unit | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| zone-u8 | 02 | 03 | Unknown | 001B | Unknown | read | scalar | u8 | 1 | not-applicable | 1 | 0 | Unknown | Hypothesis |
| zone-u16 | 02 | 03 | Unknown | 001B | Unknown | read | scalar | u16 | 2 | little-endian | 1 | 0 | Unknown | Hypothesis |
| gg01-byte14 | 02 | 01 | Unknown | 0014 | Unknown | read | scalar | u8 | 1 | not-applicable | 1 | 0 | Unknown | Hypothesis |
| gg01-byte19 | 02 | 01 | Unknown | 0019 | Unknown | read | scalar | u8 | 1 | not-applicable | 1 | 0 | Unknown | Hypothesis |
| gg01-float15 | 02 | 01 | Unknown | 0015 | Unknown | read | scalar | binary32 | 4 | little-endian | 1 | 0 | Unknown | Hypothesis |
| room-mode | 02 | 03 | Unknown | 0006 | controller-family | write | mode | u16 | 2 | little-endian | 1 | 0 | Unknown | Hypothesis |
| room-manual | 02 | 03 | Unknown | 0022 | controller-family | write | manual-temperature | binary32 | 4 | little-endian | 1 | 0 | Unknown | Hypothesis |
| room-comfort | 02 | 03 | Unknown | 0007 | controller-family | write | comfort-temperature | binary32 | 4 | little-endian | 1 | 0 | Unknown | Hypothesis |

Unsigned-byte representation has range 0..255; little-endian unsigned u16 has
range 0..65535. These are representation ranges, not qualified native limits
or complete enums. Binary32 means raw IEEE 754 little-endian binary32, factor
1 and offset 0; no Celsius offset or unit is established here.

## Synthetic field arithmetic

**Proven (local arithmetic only):** the following outcomes check the declared
shapes. `raw-only` means no successful typed claim for that candidate, while
all bytes remain available. Equal float bytes do not merge manual and comfort
roles, and RR0014 and RR0019 remain separate byte fields.

| Candidate | Raw field bytes | Local result |
| --- | --- | --- |
| zone-u8 | 01 | 1 |
| zone-u16 | 01 | raw-only |
| zone-u8 | 01 00 | raw-only |
| zone-u16 | 01 00 | 1 |
| zone-u8 | 00 01 | raw-only |
| zone-u16 | 00 01 | 256 |
| gg01-byte14 | 0E | 14 |
| gg01-byte19 | 13 | 19 |
| gg01-float15 | 00 00 80 3F | 1.0 |
| room-mode | 01 01 | 257 |
| room-manual | 00 00 80 3F | 1.0 |
| room-comfort | 00 00 80 3F | 1.0 |

RR001B raw `01` fits only the one-byte shape; `01 00` fits the two-byte
candidate. Neither observation decides family qualification or chooses which
semantic alternative is supported. `00 01` represents 256 only under the u16
candidate. Mode `01 01` represents the full u16 257, not its low byte.

A six-byte read request (`02 00 GG II RRlo RRhi`) does not choose returned value
width. Reply length can reject a candidate shape, but cannot select a family or
resolve the RR001B conflict. The native reply classifications still apply:
a status-only byte is not an isolated scalar value, and header bytes must not
be treated as field bytes. Short or extra field bytes remain raw with no
successful typed claim. Changing OP to 06, GG, RR, II, family or read/write
direction must not inherit an OP02 declaration, even if raw bytes agree.

## Unresolved qualification and retained evidence

**Unknown:** installed support, omitted instance predicates, complete enums,
units for the three GG01 values, persistence and wire adaptation. Units for the
room-temperature candidates and complete message positions are also Unknown.
The two RR001B alternatives remain unresolved; these declarations do not
supersede differently qualified mappings in the register map.

**Hypothesis (retention behavior, corroborating implementation evidence):** a
decode failure retains a prior cached value with uncertain freshness. Retaining
that prior value does not validate the new raw bytes or make the old value
fresh. These declarations supply no cache updater.

The three room rows are distinct write-role declarations only. No active
builder or executor is supplied. Synthetic representation checks establish no
physical support, freshness, persistence, admission or execution permission;
missing qualification withholds a usable native claim while preserving raw
alternatives and any prior last-known-good value.

## Sources

The local native contract and register map linked above define the evidence
boundary. The companion AI05 catalog in helianthus-ebusreg, file
`catalog/vaillant/data/ab85_b524_scalar_shapes.json`, corroborates these finite
candidate declarations and retention limitations as implementation evidence
only. No public native capture has been supplied for these candidate mappings.
