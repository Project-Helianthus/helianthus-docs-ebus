# B51B programming field candidates

This finite Vaillant family catalog supplements the [native overview](ebus-vaillant.md).
The overview leaves B5 1B layouts unestablished; these declarations remain candidates.

**Hypothesis** applies to every candidate layout, meaning and physical interpretation.

**Proven** describes synthetic representation checks only.

Physical qualification remains **Unknown**.

Logical coordinates include B5/1B/operation at 0/1/2; they are not established physical wire offsets.

OP06 retains three independent raw numbers without BCD or version conversion.

OP07 requests programming; OP0A requests block commit; OP0B requests CRC.

OP0C has no request arguments; OP0D and OP0E have only their listed input.

Constant 08 at position 2 is an operation, not a block number; bytes FF FF FF FF are not a sentinel.

Empty OP09 data does not establish peer acceptance.

OP0D byte 0F stays 15 minutes, without encoding 900 or converting to seconds.

Commit feedback does not prove persistence.

Requests that start, commit or transition are mutative declarations only.

No runtime capability or write admission follows from this catalog.

Unknown extent is absent information, never zero length.

Preserve raw bytes, unresolved alternatives and independent useful fields; a failed interpretation does not erase last-known-good information.

Other qualified variants remain separate; this partial catalog does not replace them.

## Candidate logical layouts

| Family | Variant | Direction | Service | Operation | Alternative | Fields at logical position | Extent | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Vaillant | Unknown | request | B51B | 06 | request | none | 3 | Hypothesis |
| Vaillant | Unknown | response | B51B | 06 | positive | raw-a@3, raw-b@4, raw-c@5 | 6 | Hypothesis |
| Vaillant | Unknown | response | B51B | 06 | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 07 | request | none | 3 | Hypothesis |
| Vaillant | Unknown | response | B51B | 07 | positive | generic-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 07 | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 08 | request | block@3, segment@7 | 11 | Hypothesis |
| Vaillant | Unknown | response | B51B | 08 | positive | block-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 08 | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 09 | request | offset@3, data@5 | 5+k | Hypothesis |
| Vaillant | Unknown | response | B51B | 09 | positive | generic-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 09 | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 0A | request | none | 3 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0A | positive | generic-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0A | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 0B | request | none | 3 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0B | positive | CRC@3 | 5 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0B | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 0C | request | none | 3 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0C | positive | state@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0C | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 0D | request | timeout@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0D | positive | generic-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0D | negative | Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | request | B51B | 0E | request | direction@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0E | positive | generic-feedback@3 | 4 | Hypothesis |
| Vaillant | Unknown | response | B51B | 0E | negative | Unknown | Unknown | Hypothesis |

## Candidate field representations

| Field | Representation | Domain | Default | Conversion | Width or extent | Labels | Grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| raw-a, raw-b, raw-c | raw u8 independent | 0..255 | 0 each | unchanged | 1 each | none | Hypothesis |
| block, segment | LE u32 independent | 0..4294967295 | 0 each | unchanged | 4 each | none | Hypothesis |
| offset | LE u16 | 0..65535 | Unknown | unchanged | 2 | none | Hypothesis |
| data | opaque bytes | minimum 0; maximum absent | Unknown | unchanged | k; maximum absent | none | Hypothesis |
| CRC | LE u16 | 0..65535 | Unknown | unchanged | 2 | none | Hypothesis |
| state | raw u8 | 0..255 | Unknown | unchanged | 1 | 0 hardware-init; 1 wait-programming-request; 2 check-application-CRC; 3 preparation; 4 active; 5 application-running; 6..FF unlabeled | Hypothesis |
| timeout | raw u8 minutes | 0..255 | 15 | unchanged | 1 | zero has no special meaning | Hypothesis |
| direction | raw u8 | 0..255 | F0 application | unchanged | 1 | 0F boot-loader; F0 application; others unlabeled | Hypothesis |

## Separate feedback labels

| Field | Labels | Grade |
| --- | --- | --- |
| generic-feedback | 01 accepted; 00 and 02..FF rejected | Hypothesis |
| block-feedback | 00 rejected; 33 block-unavailable; 55 accepted; AA protected; others unlabeled | Hypothesis |

## Unresolved properties

| Property | Grade |
| --- | --- |
| full forwarding variants | Unknown |
| segmentation variants | Unknown |
| local CRC variants | Unknown |
| physical addresses | Unknown |
| response adaptation | Unknown |
| geometry | Unknown |
| peer algorithm | Unknown |
| CRC coverage | Unknown |
| persistence | Unknown |
| native adaptation | Unknown |
| peer effects | Unknown |
| physical qualification | Unknown |
| negative response layouts | Unknown |
| variant | Unknown |

## Synthetic representation examples

The [synthetic fixture](fixtures/ac18_program_blocks.json) validates declarations only.

- OP08 block 16909060 (decimal), segment 84281096 (decimal): `B5 1B 08 04 03 02 01 08 07 06 05`.
- OP09 offset `0x1234`, data `[00, FF]`: `B5 1B 09 34 12 00 FF`; extent is `5+k`.
- OP0B raw CRC `34 12` is numeric `0x1234`; peer algorithm and coverage are Unknown.
- State 6 remains unlabeled. Feedback 55 is accepted only by the OP08 table, rejected by generic feedback; AA is protected only by OP08.

Full forwarding, segmentation and local CRC variants remain outside this partial catalog.
