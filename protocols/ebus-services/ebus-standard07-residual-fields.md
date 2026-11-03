# Standard 07 residual candidate fields

## Evidence and scope

**Hypothesis:** the candidate system-data family has identities `0700`, `0702`,
`0703`, `0704`, `0705`, `07FE`, and `07FF`. The public native
[service 07 contract](ebus-service-07h.md#vaillant-variants) supplies the candidate
family context. This supplement records only the residual fields below for the
Vaillant family. `0704` remains identity-only here; no `0704` fields are recopied. No `0701` candidate body is defined.

The standard weekday and duration descriptions in the parent remain distinct
from these candidate relationships. **Unknown:** native support, emission,
physical responses, physical effects, persistence, and delivery. Synthetic
correctness establishes only the declared representation, not qualification.

## Finite body shapes

All coordinates start after the PB/SB pair; they exclude framing, addressing,
and the PB/SB bytes themselves. A positive body is distinct from a request body.
Every row in both tables is **Hypothesis**, with qualification **Unknown**.

| Service | Direction | Body bytes |
|---|---|---:|
| 0700 | body | 9 |
| 0702 | request | 3 |
| 0703 | request | 1 |
| 0703 | positive | 10 |
| 0705 | request | 2 |
| 0705 | positive | 10 |
| 07FE | pair-only | 0 |
| 07FF | pair-only | 0 |

`07FE` inquiry and `07FF` sign-of-life retain separate PB/SB identities, each
with no argument body. Emission and physical responses are **Unknown**. No
direct inquiry reply is required by these candidate structures.

## Finite fields

A dash means no stated domain, unit, default, or labels. Packed-decimal domains
are named logical domains; they do not establish complete native decimal
conversion or calendar validation. Each bitmap remains an independent raw byte.

| Service | Direction | Field | Offset | Width | Encoding | Domain | Unit | Default | Labels |
|---|---|---|---:|---:|---|---|---|---|---|
| 0700 | body | outside_temperature | 0 | 2 | signed-le16/256 | -50..50 | degrees Celsius | - | - |
| 0700 | body | second | 2 | 1 | packed-decimal | 0..59 | none | - | - |
| 0700 | body | minute | 3 | 1 | packed-decimal | 0..59 | none | - | - |
| 0700 | body | hour | 4 | 1 | packed-decimal | 0..23 | none | - | - |
| 0700 | body | day | 5 | 1 | packed-decimal | 1..31 | none | - | - |
| 0700 | body | month | 6 | 1 | packed-decimal | 1..12 | none | - | - |
| 0700 | body | weekday | 7 | 1 | u8 | 0..255 | none | - | 0 Monday; 1 Tuesday; 2 Wednesday; 3 Thursday; 4 Friday; 5 Saturday; 6 Sunday |
| 0700 | body | year | 8 | 1 | packed-decimal | 0..99 | none | - | - |
| 0702 | request | outside_temperature | 0 | 2 | signed-le16/256 | -50..50 | degrees Celsius | - | - |
| 0702 | request | duration | 2 | 1 | u8 | 0..255 | minutes | 0 | - |
| 0703 | request | secondary_block | 0 | 1 | u8 | 0..255 | none | - | - |
| 0705 | request | secondary_block | 0 | 1 | u8 | 0..255 | none | - | - |
| 0705 | request | primary_block | 1 | 1 | u8 | 0..255 | none | - | - |
| 0703 | positive | version | 0 | 1 | packed-decimal | 0..99 | none | - | - |
| 0703 | positive | revision | 1 | 1 | packed-decimal | 0..99 | none | - | - |
| 0703 | positive | bitmap_0 | 2 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_1 | 3 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_2 | 4 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_3 | 5 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_4 | 6 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_5 | 7 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_6 | 8 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0703 | positive | bitmap_7 | 9 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | version | 0 | 1 | packed-decimal | 0..99 | none | - | - |
| 0705 | positive | revision | 1 | 1 | packed-decimal | 0..99 | none | - | - |
| 0705 | positive | bitmap_0 | 2 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_1 | 3 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_2 | 4 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_3 | 5 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_4 | 6 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_5 | 7 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_6 | 8 | 1 | raw-bitmap | 0..255 | none | - | - |
| 0705 | positive | bitmap_7 | 9 | 1 | raw-bitmap | 0..255 | none | - | - |

## Candidate interpretation boundaries

- **Hypothesis:** weekday is a raw u8 carrier. Only 0 Monday through 6 Sunday
  have labels; 7..255 remains raw and unlabelled. It is not BCD 1..7.
- **Hypothesis:** signed LE16 divided by 256 maps raw -12800..12800 to
  -50..50 degrees Celsius. The raw word `8000` has **Unknown** sentinel meaning;
  no qualified replacement value follows from this representation.
- **Hypothesis:** duration is a raw u8 number of minutes, with literal default 0.
  **Unknown:** duration zero has no established permanent meaning in this variant.
- **Hypothesis:** candidate default literal 6 belongs to `0700` metadata and
  candidate default literal 1 belongs to `0702` metadata. The exact field
  association of each is **Unknown**; neither literal is assigned to a field.
- **Hypothesis:** version and revision are two independent packed-decimal bytes,
  followed by eight independent raw bitmap bytes in each positive body.
  **Unknown:** exact bit selection, selected services, and version-control overlap
  with `0704`. Bitmap `80` establishes no selected service.
- **Unknown:** century, timezone, calendar validation, and complete native decimal
  conversion. Explicit candidate logical examples are not executable schemas.

## Synthetic cases

[Finite synthetic data](fixtures/ak18_standard07_residual_fields.json) retains raw
bytes beside candidate interpretations. These are constructed values with no
physical observation claim. **Proven:** the following arithmetic and byte counts
hold for the explicit representations; all native relationships remain
**Hypothesis**, with physical qualification **Unknown**.

| Case | Raw body bytes | Candidate logical result |
|---|---|---|
| Weekday Sunday | 00 00 00 00 00 01 01 06 00 | raw 6; Sunday |
| Weekday unlabelled | 00 00 00 00 00 01 01 07 00 | raw 7; no label |
| Weekday unlabelled maximum | 00 00 00 00 00 01 01 FF 00 | raw 255; no label |
| Temperature upper boundary | 00 32 00 | 50 degrees Celsius; duration 0; permanent Unknown |
| Temperature lower boundary | 00 CE 00 | -50 degrees Celsius; duration 0; permanent Unknown |
| Duration zero | 00 00 00 | 0 degrees Celsius; duration 0; permanent Unknown |
| Calendar domains | 00 00 59 58 23 31 12 06 99 | second 59; minute 58; hour 23; day 31; month 12; weekday Sunday; year 99 |
| 0703 positive | 12 34 80 01 02 04 08 10 20 40 | version 12; revision 34; eight raw bitmaps; selected services Unknown |
| 0705 positive | 12 34 80 01 02 04 08 10 20 40 | version 12; revision 34; eight raw bitmaps; selected services Unknown |
| 0703 request | 00; 01; FF | one independent raw secondary block |
| 0705 request | 00 00; 01 00; 00 01; FF 00; 00 FF | secondary and primary blocks varied independently |
| 07FE inquiry | empty | PB/SB 07 FE; no argument body; emission Unknown |
| 07FF sign-of-life | empty | PB/SB 07 FF; no argument body; emission Unknown |

The raw positive bytes `12 34` remain separate logical values 12 and 34. The
bitmap byte `80` stays raw. Neither block-selector variation establishes a bit
selection algorithm. No physical support follows from these synthetic cases.
