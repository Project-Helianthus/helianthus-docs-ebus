# B506 RF counts and sequence extents

## Native scope and evidence

The [native B506 contract](ebus-vaillant-B506.md) supplies the service context:
PB=0xB5, SB=0x06, Vaillant RF family. OP12, OP13 and OP14 are hexadecimal
operation labels in this page. The [synthetic declarations](fixtures/ak06_b506_rf_sequence.json)
contain isolated candidate fields, not complete telegrams or observed exchanges.
Source, destination, product, firmware and capture conditions are Unknown.

**Hypothesis:** OP13 count and sequence describe separate candidate properties.
The parent lists candidate lengths; those do not establish the RF sequence
extents here. No native capture qualifies these relationships or resolves that
uncertainty. Neither declaration supersedes the other's evidence boundary.

## Count candidates

**Hypothesis:** count byte 0 denotes unlimited count; 1..255 denotes the finite
count value. This count is not a retry budget or a payload length. Count field
position is Unknown.

| Count byte (decimal) | Candidate meaning | Grade |
| --- | --- | --- |
| 0 | unlimited | Hypothesis |
| 1 | finite-1 | Hypothesis |
| 2 | finite-2 | Hypothesis |
| 255 | finite-255 | Hypothesis |

## Sequence candidates

**Hypothesis:** sequence choices 0/1/2 share one extent class and choice 3 has
a distinct class. Class labels express candidate equality only, never a byte
length. All other byte values (4..255) remain unmapped.

| Sequence (decimal) | Extent class | Exact bytes | Minimum bytes | Maximum bytes | Field position | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | rf-class-a | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 1 | rf-class-a | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 2 | rf-class-a | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 3 | rf-class-b | Unknown | Unknown | Unknown | Unknown | Hypothesis |
| 4 | unmapped | Unknown | Unknown | Unknown | Unknown | Unknown |

**Unknown:** exact, minimum and maximum byte extents and sequence field
position. Explicit `null` metadata preserves absence; an absent extent is not
zero. Empty and nonempty fabricated payloads both remain unqualified when
extent is absent. A class match cannot admit a complete payload.

| Fabricated payload (hex) | Qualification | Exact bytes |
| --- | --- | --- |
| empty | Unknown | Unknown |
| 23 45 | Unknown | Unknown |

## Stop associations

**Hypothesis:** stop OP14 is associated independently with activation OP12 and
activation OP13. The relationship is not an ordered activation sequence.

| Stop | Related activation | Grade | Activation order | Delivery guarantee | Completed stop |
| --- | --- | --- | --- | --- | --- |
| OP14 | OP12 | Hypothesis | Unknown | Unknown | Unknown |
| OP14 | OP13 | Hypothesis | Unknown | Unknown | Unknown |

**Unknown:** retry count, timeout, delivery guarantee and completed stop.
Association establishes none of these. Native support, physical effects and
persistence are also Unknown. Original raw bytes remain available even when a
candidate cannot be interpreted. Missing qualification preserves any partial
last-known-good state with uncertain freshness; it does not replace it with a
fabricated value or qualify new bytes.

**Proven (synthetic representation only):** the isolated cases distinguish count
meaning from extent classes and preserve absent metadata. Synthetic correctness
does not establish native support, physical effects, persistence or delivery.
