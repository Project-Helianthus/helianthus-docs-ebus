# Numeric and character representation axes

**Hypothesis:** a family type contract states representation, signedness, bit
width, byte order, computation and unit as separate axes. An encoding label
alone selects neither a scale, a unit nor a native field.

**Proven:** the finite synthetic arithmetic below follows the explicitly selected
representations. Packed decimal uses two decimal nibbles; unpacked decimal uses
one decimal digit per byte; ASCII digits use bytes 30 through 39 hex. These are
independent of two-complement integers and binary32. Invalid digits and wrong
widths have no numeric result (`invalid`); no fallback interpretation is selected.
The ASCII sequence 34 32 spells 42: it is neither binary integer 42 nor unpacked
decimal digits. Equal numeric results do not establish equal representations.

## Synthetic arithmetic

All bytes are hexadecimal. Results are decimal. Each row is **Proven** only as
representation arithmetic; native qualification is **Unknown** in every row.

| Case | Representation | Raw bytes | Bits | Byte order | Signedness | Result | Native |
|---|---|---|---|---|---|---|---|
| packed42 | packed-decimal | 42 | 8 | not-applicable | not-applicable | 42 | Unknown |
| packed00 | packed-decimal | 00 | 8 | not-applicable | not-applicable | 0 | Unknown |
| packed99 | packed-decimal | 99 | 8 | not-applicable | not-applicable | 99 | Unknown |
| packedFA | packed-decimal | FA | 8 | not-applicable | not-applicable | invalid | Unknown |
| packed_low_invalid | packed-decimal | 4A | 8 | not-applicable | not-applicable | invalid | Unknown |
| packed_empty | packed-decimal | empty | 8 | not-applicable | not-applicable | invalid | Unknown |
| packed_wide | packed-decimal | 00 42 | 8 | not-applicable | not-applicable | invalid | Unknown |
| unpacked-decimal_42 | unpacked-decimal | 04 02 | 16 | not-applicable | not-applicable | 42 | Unknown |
| unpacked-decimal_leading | unpacked-decimal | 00 02 | 16 | not-applicable | not-applicable | 2 | Unknown |
| unpacked-decimal_invalid | unpacked-decimal | 04 0A | 16 | not-applicable | not-applicable | invalid | Unknown |
| unpacked-decimal_ascii | unpacked-decimal | 34 32 | 16 | not-applicable | not-applicable | invalid | Unknown |
| unpacked-decimal_short | unpacked-decimal | 04 | 16 | not-applicable | not-applicable | invalid | Unknown |
| ASCII-digits_42 | ASCII-digits | 34 32 | 16 | not-applicable | not-applicable | 42 | Unknown |
| ASCII-digits_leading | ASCII-digits | 30 32 | 16 | not-applicable | not-applicable | 2 | Unknown |
| ASCII-digits_invalid | ASCII-digits | 34 41 | 16 | not-applicable | not-applicable | invalid | Unknown |
| ASCII-digits_unpacked | ASCII-digits | 04 02 | 16 | not-applicable | not-applicable | invalid | Unknown |
| ASCII-digits_short | ASCII-digits | 34 | 16 | not-applicable | not-applicable | invalid | Unknown |
| signed_le | integer | FE FF | 16 | little | signed | -2 | Unknown |
| signed_be | integer | FE FF | 16 | big | signed | -257 | Unknown |
| unsigned_le | integer | FE FF | 16 | little | unsigned | 65534 | Unknown |
| signed_min | integer | 00 80 | 16 | little | signed | -32768 | Unknown |
| signed_max | integer | FF 7F | 16 | little | signed | 32767 | Unknown |
| integer_short | integer | FE | 16 | little | signed | invalid | Unknown |
| float | binary32 | 00 00 C0 3F | 32 | little | not-applicable | 1.5 | Unknown |
| float_integer | integer | 00 00 C0 3F | 32 | little | unsigned | 1069547520 | Unknown |
| float_short | binary32 | 00 C0 3F | 32 | little | not-applicable | invalid | Unknown |

## Independent axes

**Proven:** each scenario changes one declared axis relative to `base`, except
`signedness`, which changes only signedness relative to `sign_control`.
The character-digit representation is unsigned here; its declared little-endian
metadata has no arithmetic effect because character order is explicit.
A computation `raw/16` does not select a unit. Unit metadata alone adds no 273.15.

| Scenario | Representation | Raw bytes | Bits | Byte order | Signedness | Computation | Unit | Result | Native |
|---|---|---|---|---|---|---|---|---|---|
| base | integer | 34 32 | 16 | little | unsigned | identity | Unknown | 12852 | Unknown |
| representation | ASCII-digits | 34 32 | 16 | little | unsigned | identity | Unknown | 42 | Unknown |
| width_bits | integer | 34 32 | 8 | little | unsigned | identity | Unknown | invalid | Unknown |
| byte_order | integer | 34 32 | 16 | big | unsigned | identity | Unknown | 13362 | Unknown |
| computation | integer | 34 32 | 16 | little | unsigned | raw/16 | Unknown | 803.25 | Unknown |
| unit | integer | 34 32 | 16 | little | unsigned | identity | degrees Celsius | 12852 | Unknown |
| sign_control | integer | FE FF | 16 | little | unsigned | identity | Unknown | 65534 | Unknown |
| signedness | integer | FE FF | 16 | little | signed | identity | Unknown | -2 | Unknown |

## Raw character and domain boundaries

**Proven:** a fixed character field retains embedded and trailing zero bytes and
all raw bytes. The fixed 40-bit array below remains the same array. Text encoding,
termination, padding and normalization each need their own qualified contract.

| Raw bytes | Retained bytes | Bits | Text encoding | Termination | Padding | Normalization | Native |
|---|---|---|---|---|---|---|---|
| 41 00 42 00 00 | 41 00 42 00 00 | 40 | Unknown | Unknown | Unknown | Unknown | Unknown |

**Hypothesis:** byte width, raw domain and allowed semantic domain are independent.
These candidate domain rows hold width, raw domain and value constant; only the
allowed semantic domain changes. Admission is conditional on that explicit domain.

| Bits | Raw domain | Allowed semantic domain | Value | Admitted | Native |
|---|---|---|---|---|---|
| 16 | 0..65535 | 0..100 | 42 | true | Unknown |
| 16 | 0..65535 | 0..40 | 42 | false | Unknown |

## Evidence and limits

The [synthetic tables](fixtures/ak25_type_representation_axes.json) preserve raw
bytes beside their mathematical interpretations. The existing
[primitive declarations](primitives.md) provide the native type context; these
examples select no additional eBUS field or device-family mapping.

**Unknown:** native field selection, mixed encodings, decimal sign conventions,
physical qualification, native support, physical effects, persistence and delivery.
Mathematical **Proven** and candidate **Hypothesis** grades do not qualify any of
those properties. Invalid examples remain invalid under the declared contract;
previously valid raw evidence remains intact and carries no claim of freshness.
No codec implementation, namespace, generic family schema or replacement for
existing B524 helpers is added.
