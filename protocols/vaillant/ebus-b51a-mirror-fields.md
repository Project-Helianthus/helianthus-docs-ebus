# B51A mirror storage and diagnostic save candidates

## Scope and evidence

**Hypothesis:** The Vaillant B51A mirror/diagnosis forms are separate from
configured-register tables. The public native starting contract is
[candidate mirror and diagnosis layouts](ebus-vaillant-B51A.md#candidate-mirror-and-diagnosis-layouts).
The supplemental field declarations below remain candidate interpretations,
not wire-confirmed mappings. The [configured-register forms](ebus-vaillant-B51A.md#wire-shape)
retain their separate identity; a configured IDX is not established as a
candidate sequence byte. The overlap with the backup-heater OP06 form remains
unresolved. No address dictionary from another form is imported.

Positions are logical offsets counting PB at 0, SB at 1 and operation at 2:
`B5 1A OP sequence ...`. The sequence on each side is its own u8 field.
A positive tuple below includes a **synthetic logical prefix**, not a physical
response header. Actual eBUS response data has no such service prefix; physical
adaptation of these logical response positions is **Unknown**.

Every field and named interpretation is graded individually below. **Proven**
on a synthetic tuple means only its byte representation or local arithmetic
under the declared candidate layout. It does not promote that layout to a
Proven native contract. **Unknown** includes installed family support, physical
qualification, freshness, durability and success semantics. No tuple establishes
receipt, acceptance, execution permission or a resulting device state.
Unprovided properties, units and broader operation coverage remain **Unknown**.

## Candidate fields

Only the listed operations are covered. Width `end` means all remaining opaque
bytes, with minimum length zero and no declared maximum. Width `conditional`
preserves the formal two-byte description and the display-type alternatives;
no unconditional one-byte narrowing is justified. Defaults `Unknown` are unset.
Logical address limits do not follow merely from formal u16 representability.

| Op | Side | Field | Position | Width | Encoding | Default | Formal domain | Logical limit | Grade |
|---|---|---|---|---|---|---|---|---|---|
| 00 | request | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 00 | positive | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 01 | request | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 01 | positive | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 02 | request | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 02 | positive | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 03 | request | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 03 | positive | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 06 | request | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 06 | positive | sequence | 3 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 00 | positive | acknowledgement | 4 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 02 | request | flags | 4 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | request | length | 5 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | request | mirror_address | 6 | 2 | LE u16 | Unknown | 0..65535 | 0..mirror-length-1 | Hypothesis |
| 02 | positive | positive | 4 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 02 | positive | data | 5 | end | opaque | Unknown | not scalar | length 0..unset | Hypothesis |
| 03 | request | flags | 4 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 03 | request | mirror_address | 5 | 2 | LE u16 | 0 | 0..65535 | independent mirror limit Unknown | Hypothesis |
| 03 | request | symbol_address | 7 | 2 | LE u16 | 0 | 0..65535 | independent symbol limit Unknown | Hypothesis |
| 03 | request | data | 9 | end | opaque | Unknown | not scalar | length 0..unset | Hypothesis |
| 03 | positive | flags | 4 | 1 | u8 | 0 | 0..255 | Unknown | Hypothesis |
| 06 | request | level | 4 | 1 | u8 | Unknown | 0..255 | Unknown | Hypothesis |
| 06 | request | point | 5 | 1 | u8 | Unknown | 0..255 | 0..99 | Hypothesis |
| 06 | request | value | 6 | 2 | LE u16 | Unknown | 0..65535 | Unknown | Hypothesis |
| 06 | positive | save_status | 4 | 1 | u8 | 0 | 0..255 | 5..255 unlabeled; no implicit success | Hypothesis |
| 06 | positive | mirror_address | 5 | 2 | LE u16 | Unknown | 0..65535 | independent mirror limit Unknown | Hypothesis |
| 06 | positive | symbol_address | 7 | 2 | LE u16 | Unknown | 0..65535 | independent symbol limit Unknown | Hypothesis |
| 06 | positive | value | 9 | conditional | LE u16 | Unknown | 0..65535 | display type selects width | Hypothesis |

## Interpretations and unknowns

The reset acknowledgement is a whole u8; only bit 0 has a candidate name.
Raw `02` therefore changes an unnamed high bit, not denied bit 0. The OP02
whole-u8 false/true reading competes with the out-of-area bit-0 reading;
neither alternative resolves raw values 2..255. Preserve the whole raw byte.
For OP03 the declared whole flags default to zero and named/reserved bits to
false; zero flags and empty data still do not establish acceptance.
OP06 save status is a scalar, not a success bitmask. Status zero explicitly
means value-not-saved; unlisted codes do not imply success.

| Rule | Declaration | Grade |
|---|---|---|
| correlation | 00,01 only: equal sequence is candidate correlation; no retry or freshness policy | Hypothesis |
| reset-bit | 0:denied:false | Hypothesis |
| reset-other | 1..7:unnamed; defaults Unknown | Unknown |
| read-flags | 0:triple-storage; default Unknown; bits 1..7 Unknown | Hypothesis |
| read-positive | 0:false;1:true | Hypothesis |
| read-unresolved | 2..255:unresolved | Unknown |
| read-alternative | bit 0:out-of-area; conflicts with whole-u8 interpretation | Hypothesis |
| read-length | requested and returned lengths independent | Hypothesis |
| write-request-bits | 0:triple-storage:false;1:direct-update:false;2..7:reserved:false | Hypothesis |
| write-positive-bits | 0:not-written:false;1:invalid-symbol:false;2:invalid-parameter:false;3:storage-error:false;4..7:reserved:false | Hypothesis |
| opaque-data | end-delimited; minimum 0; maximum unset; empty does not prove acceptance | Hypothesis |
| save-status | 0:value-not-saved;1:point-not-found;2:write-protected;3:range-violation;4:misconfiguration | Hypothesis |
| save-widths | formal-u16:2;display-one-byte:1;display-two-byte:2 | Hypothesis |
| address-limits | mirror and symbol logical limits independent; no other address dictionary | Hypothesis |
| physical-adaptation | Unknown | Unknown |
| storage-durability | Unknown | Unknown |
| success-semantics | Unknown | Unknown |

## Synthetic logical tuples

All tuples are synthetic, without endpoints or device observations. The
[companion native tuples](fixtures/ai16_b51a_mirror_fields.json) retain raw bytes
beside declared results, in the same order as this page. A result is conditional
on the Hypothesis layout; its Proven grade applies only to the local predicate.
The read pair retains requested length 3 and returned length 2 independently.
The write tuple preserves distinct mirror and symbol addresses and empty opaque
data. The save tuples retain point 99 versus 100 independently of sequence,
and one-byte versus two-byte values with the same low byte.

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
| read-request | 02 | request | B5 1A 02 07 01 03 34 12 | - | requested=3;mirror=4660 | Proven |
| read-short | 02 | positive | B5 1A 02 07 01 AA BB | - | positive=true;actual=2;data=AA BB | Proven |
| read-false | 02 | positive | B5 1A 02 07 00 | - | positive=false;actual=0;data= | Proven |
| read-raw-two | 02 | positive | B5 1A 02 07 02 | - | positive=unresolved;actual=0;data= | Proven |
| write-empty | 03 | request | B5 1A 03 07 00 34 12 78 56 | - | mirror=4660;symbol=22136;actual=0;acceptance=Unknown | Proven |
| save-point-99 | 06 | request | B5 1A 06 FF 09 63 34 12 | - | sequence=255;level=9;point=99;fits=true;value=4660 | Proven |
| save-point-100 | 06 | request | B5 1A 06 00 09 64 34 12 | - | sequence=0;level=9;point=100;fits=false;value=4660 | Proven |
| save-zero | 06 | positive | B5 1A 06 07 00 34 12 78 56 34 | display-one-byte | status=value-not-saved;mirror=4660;symbol=22136;value=52;width=1 | Proven |
| save-one | 06 | positive | B5 1A 06 07 01 34 12 78 56 34 12 | display-two-byte | status=point-not-found;mirror=4660;symbol=22136;value=4660;width=2 | Proven |
| save-five | 06 | positive | B5 1A 06 07 05 34 12 78 56 34 12 | formal-u16 | status=unmapped;mirror=4660;symbol=22136;value=4660;width=2 | Proven |

## Correlation and remaining evidence

**Hypothesis:** Equal sequence bytes for reset/00 and OP01 are candidate
correlation only. Requests with sequence 0 and positives with sequence 255
(and the reverse) are not correlated by that rule. Equal bytes do not establish
fresh success. Other operations inherit no sequence matching rule. This is not
a retry policy.

**Unknown:** The relationship to configured selectors, physical response
adaptation, address bounds where not provided, storage durability and success
semantics need native evidence. The [family open questions](ebus-vaillant-B51A.md#open-questions)
remain unresolved. Synthetic ranges and predicates confer no installed support,
freshness, persistence or authority to send any operation. Raw alternatives and
partial information must remain available when an interpretation is unresolved.
