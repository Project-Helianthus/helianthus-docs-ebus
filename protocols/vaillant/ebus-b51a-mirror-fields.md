# B51A mirror storage and diagnostic save candidates

## Scope and evidence

**Hypothesis:** The Vaillant B51A mirror/diagnosis forms are separate from
configured-register tables. The public native starting contract is
[candidate mirror and diagnosis layouts](ebus-vaillant-B51A.md#candidate-mirror-and-diagnosis-layouts).
That reference supplies the broad operation meanings, sequence fields and reset
acknowledgement bit. It supplies no supplemental OP02, OP03 or OP06 field layout.
No source artifact for those supplemental mappings is available here, so their
positions, widths, encodings, defaults, bounds, bit assignments and status
meanings are **Unknown**. Synthetic examples cannot supply that provenance.
The [configured-register forms](ebus-vaillant-B51A.md#wire-shape) retain their
separate identity; a configured IDX is not established as a candidate sequence
byte. The overlap with the backup-heater OP06 form remains unresolved.
No address dictionary from another form is imported.

Positions are logical offsets counting PB at 0, SB at 1 and operation at 2:
`B5 1A OP sequence ...`. The sequence on each side is its own u8 field.
A positive tuple below includes a **synthetic logical prefix**, not a physical
response header. Actual eBUS response data has no such service prefix; physical
adaptation of these logical response positions is **Unknown**.

**Proven** on a synthetic tuple means only its byte representation or local
arithmetic under the cited candidate layout. It does not promote that layout
to a Proven native contract. Installed family support, freshness, durability,
acceptance, execution permission and resulting device state remain **Unknown**.

## Candidate fields

Only the listed operations are covered. Defaults are **Unknown** because the
starting reference does not specify them. A `supplemental_layout` row records
missing knowledge; it declares no field, offset or decoder.

| Op | Side | Field | Position | Width | Encoding | Default | Formal domain | Logical limit | Grade |
|---|---|---|---|---|---|---|---|---|---|
| 00 | request | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 00 | positive | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 01 | request | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 01 | positive | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | request | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | positive | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 03 | request | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 03 | positive | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 06 | request | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 06 | positive | sequence | 3 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 00 | positive | acknowledgement | 4 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | request | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| 02 | positive | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| 03 | request | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| 03 | positive | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| 06 | request | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |
| 06 | positive | supplemental_layout | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown | Unknown |

## Interpretations and unknowns

The reset acknowledgement is a whole u8; only bit 0 has a candidate name in the
starting reference. Raw `02` changes an unnamed high bit, not denied bit 0.
For OP02, OP03 and OP06, bytes after the candidate sequence remain uninterpreted.
No flag, address, status, value width or range can be derived from these examples.

| Rule | Declaration | Grade |
|---|---|---|
| reset-bit | 0:denied; default Unknown | Hypothesis |
| reset-other | 1..7:unnamed; defaults Unknown | Unknown |
| correlation | Unknown | Unknown |
| read-layout | Unknown | Unknown |
| write-layout | Unknown | Unknown |
| save-layout | Unknown | Unknown |
| physical-adaptation | Unknown | Unknown |
| storage-durability | Unknown | Unknown |
| success-semantics | Unknown | Unknown |

## Synthetic logical tuples

All tuples are synthetic, without endpoints or device observations. The
[companion synthetic tuples](fixtures/ai16_b51a_mirror_fields.json) retain bytes
beside results in the same order as this page. Sequence and reset results are
conditional on the cited Hypothesis layout; their Proven grade applies only to
the local predicate. Opaque examples retain their bytes with Unknown results;
neither their length nor their contents establishes a supplemental mapping.

| Case | Op | Side | Logical bytes | Alternative | Result | Grade |
|---|---|---|---|---|---|---|
| seq-00-request-0 | 00 | request | B5 1A 00 00 | - | sequence=0 | Proven |
| seq-00-request-255 | 00 | request | B5 1A 00 FF | - | sequence=255 | Proven |
| seq-00-positive-0 | 00 | positive | B5 1A 00 00 | - | sequence=0 | Proven |
| seq-00-positive-255 | 00 | positive | B5 1A 00 FF | - | sequence=255 | Proven |
| seq-01-request-0 | 01 | request | B5 1A 01 00 | - | sequence=0 | Proven |
| seq-01-request-255 | 01 | request | B5 1A 01 FF | - | sequence=255 | Proven |
| seq-01-positive-0 | 01 | positive | B5 1A 01 00 | - | sequence=0 | Proven |
| seq-01-positive-255 | 01 | positive | B5 1A 01 FF | - | sequence=255 | Proven |
| seq-02-request-0 | 02 | request | B5 1A 02 00 | - | sequence=0 | Proven |
| seq-02-request-255 | 02 | request | B5 1A 02 FF | - | sequence=255 | Proven |
| seq-02-positive-0 | 02 | positive | B5 1A 02 00 | - | sequence=0 | Proven |
| seq-02-positive-255 | 02 | positive | B5 1A 02 FF | - | sequence=255 | Proven |
| seq-03-request-0 | 03 | request | B5 1A 03 00 | - | sequence=0 | Proven |
| seq-03-request-255 | 03 | request | B5 1A 03 FF | - | sequence=255 | Proven |
| seq-03-positive-0 | 03 | positive | B5 1A 03 00 | - | sequence=0 | Proven |
| seq-03-positive-255 | 03 | positive | B5 1A 03 FF | - | sequence=255 | Proven |
| seq-06-request-0 | 06 | request | B5 1A 06 00 | - | sequence=0 | Proven |
| seq-06-request-255 | 06 | request | B5 1A 06 FF | - | sequence=255 | Proven |
| seq-06-positive-0 | 06 | positive | B5 1A 06 00 | - | sequence=0 | Proven |
| seq-06-positive-255 | 06 | positive | B5 1A 06 FF | - | sequence=255 | Proven |
| reset-high | 00 | positive | B5 1A 00 00 02 | - | raw=2;denied=false;unnamed=2 | Proven |
| opaque-02-request | 02 | request | B5 1A 02 07 01 03 34 12 | - | Unknown | Unknown |
| opaque-02-positive | 02 | positive | B5 1A 02 07 02 AA BB | - | Unknown | Unknown |
| opaque-03-request | 03 | request | B5 1A 03 07 00 34 12 78 56 | - | Unknown | Unknown |
| opaque-03-positive | 03 | positive | B5 1A 03 07 00 | - | Unknown | Unknown |
| opaque-06-request | 06 | request | B5 1A 06 FF 09 63 34 12 | - | Unknown | Unknown |
| opaque-06-positive | 06 | positive | B5 1A 06 07 00 34 12 78 56 34 | - | Unknown | Unknown |

## Correlation and remaining evidence

**Unknown:** A sequence matching rule, retry policy and freshness semantics
are not supplied by the starting reference. Equal sequence bytes alone do not
establish correlation or success.

**Unknown:** Supplemental OP02, OP03 and OP06 layouts require an attributable
source before candidate decodings can be restored. The relationship to configured
selectors, physical response adaptation, address bounds, storage durability and
success semantics also need native evidence. The
[family open questions](ebus-vaillant-B51A.md#open-questions) remain unresolved.
Synthetic tuples confer no installed support or authority to send any operation.
