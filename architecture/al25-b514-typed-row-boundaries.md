# B514 typed row boundaries

Refs helianthus-docs-ebus#736. This page bounds what the B514 row shapes may
claim. It is a shape and anomaly contract, not a substitute for the missing
twenty-row (OP02) and 128-row (OP05) finite row tables. No validator and no
synthetic row population is added. Finite data:
[fixture](fixtures/al25_b514_typed_row_boundaries.json). Grades
(Proven/Hypothesis/Unknown) are independent of physical qualification,
presence, freshness and execution. Nothing is stable before Helianthus 1.0.

## OP02 key-to-row-to-value contracts

**Hypothesis:** OP02 has twenty key-to-row-to-value contracts at logical base 5.
They reuse the existing key at position 3; no other key is inserted.
Each concrete row still needs exact width, byte order, scale, unit, default and
enum.

| Row key to width association | Grade |
| --- | --- |
| any of the twenty rows | Unknown (known associations: 0, guessed types: 0) |

Unprovided associations stay Unknown and are never filled with guessed types.

### u8 representability conflict

Two distinct alternatives declare the raw default 256 in a u8 field. The u8
mathematical domain is 0..255, which excludes 256. This is an unresolved
representability conflict, not a byte zero. The literal conflicting default and
domain are kept side by side; no modulo repair is applied.

## OP03

Ten separate bytes carry 80 independent bit positions (10 x 8).

## OP04

Twelve scalar enum tables hold 96 mappings collectively. They are not twelve
bitmasks. No equal distribution and no bitwise semantics are asserted.

## OP05

128 typed rows, of which fifty use a /10 scale. The unit of those fifty rows
remains raw (Unknown); they are not Celsius.

The separate temperature candidate is signed little-endian 16-bit with /16.
It must not be copied across the /10 map.

| Case | Bytes | Interpretation | Result |
| --- | --- | --- | --- |
| temperature candidate | F0 FF | signed LE16, /16 | -1 |
| /10 row | F0 FF | unsigned LE16 counter, /10 | 6552.0, unit Unknown |

These arithmetic examples do not choose an actual missing row.

## Raw03 activity flags

No Boolean mapping is established (Unknown).
