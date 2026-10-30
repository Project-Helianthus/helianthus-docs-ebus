# B51A diagnostic variants and replication flags

## Evidence and scope

This supplement records **Hypothesis** coordinates for the Vaillant mirror and
diagnosis family, PB/SB `B5 1A`, operations `01`, `04`, `05`, `07`, `08`.
The three-position logical prefix is included: sequence is at logical position 3
on each side. These are logical coordinates, not physical telegram lengths.
The [native framing contract](../ebus-services/ebus-overview.md) distinguishes
logical data from wire escaping, framing and CRC8. The candidate mirror CRC below
is separate from that framing CRC8.

The [existing candidate layouts](ebus-vaillant-B51A.md#candidate-mirror-and-diagnosis-layouts)
provide the native context, including distinct configured-register forms. That
older summary suggests DSN/start/offset widths; those suggestions are **Unknown**
in this bounded supplement. No primary capture or vendor specification supporting
these detailed coordinates is supplied here. Presence of the declarations is
**Proven** only as documentation metadata; every field's native interpretation
below remains **Hypothesis**. Physical qualification and invocation are **Unknown**.
The [synthetic tuples](fixtures/aj08_b51a_diagnostic_variants.json) are constructed
examples, not observations from equipment. They contain no source/destination or
firmware claims. A partial tuple preserves raw known positions without filling
missing positions or promoting an interpretation. Nothing is stable before 1.0.

## Field coordinates

Each row has grade Hypothesis. `Unknown` is deliberate, including unspecified
width, byte order, domain or default. Numeric values are unitless unless stated.
`full/Unknown` means full declared domain with numeric bounds still unknown.

| OP | Direction | Alternative | Field | Position | Encoding | Domain | Default | Presence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01,04,05,07,08 | request,positive | common | sequence | 3 | u8 | 0..255 | 0 | always |
| 01 | request | common | flags | 4 | bits8 | 0..255 | 0 | always |
| 01 | request | common | DSN | 5 | Unknown | Unknown | Unknown | always |
| 01 | request | common | start | 7 | Unknown | Unknown | Unknown | always |
| 01 | request | common | offset | 9 | Unknown | Unknown | Unknown | always |
| 01 | request | common | CRC | 10 | LEu16 | 0..65535 | Unknown | always |
| 01 | positive | common | flags | 4 | bits8 | 0..255 | 0 | always |
| 01 | positive | common | DSN | 5 | Unknown | Unknown | Unknown | change=1 |
| 01 | positive | common | start | 7 | Unknown | Unknown | Unknown | change=1 |
| 01 | positive | common | offset | 9 | Unknown | Unknown | Unknown | change=1 |
| 01 | positive | common | family-code | 10 | u8 | 0..255 | Unknown | always |
| 04 | request | common | level | 4 | u8 | 0..255 | 0 | always |
| 04 | positive | common | enable-bits | 4 | 13 bytes | 104 bits | disabled | always |
| 05 | request | common | level | 4 | Unknown | Unknown | 0 | always |
| 05 | request | common | point | 5 | Unknown | 0..99 | 0 | always |
| 05 | positive | common | flags | 4 | bits8 | 0..255 | 0 | always |
| 05 | positive | range | display-type | 5 | Unknown | Unknown | 0 | disabled=0 |
| 05 | positive | range | value | 6 | LEu16 | 0..65535 | 0 | disabled=0 |
| 05 | positive | range | minimum | 8 | Unknown | Unknown | 0 | disabled=0 |
| 05 | positive | range | maximum | 10 | Unknown | Unknown | 0 | disabled=0 |
| 05 | positive | range | step | 12 | u8 | 0..255 | 0 | disabled=0 |
| 05 | positive | enum | alternatives-1..6 | 6..11 | six u8 | each 0..255 | 0 | disabled=0 |
| 05 | positive | four-byte | additional-value | 6 | LEu32 | 0..4294967295 | 0 | disabled=0,bit3=1 |
| 05 | positive | four-byte | reserved | 10..12 | three u8 | each 0..255 | 0 | disabled=0,bit3=1 |
| 07 | request | common | flags | 4 | bits8 | 0..255 | 0 | always |
| 07 | positive | common | replication-status | 4 | u8 | 0..255 | 0 | always |
| 08 | request | common | target-written | 4 | LEu16 | 0..65535 | 0 | always |
| 08 | request | common | initiator-to-write | 6 | LEu16 | 0..65535 | 0 | always |
| 08 | request | common | configuration | 8 | u8 | 0..255 | 0 | always |
| 08 | request | common | target-version | 9 | u8 | 0..255 | 0 | always |
| 08 | request | common | initiator-version | 10 | u8 | 0..255 | 0 | always |
| 08 | positive | common | initiator-written | 4 | Unknown | full/Unknown | 0 | always |
| 08 | positive | common | target-to-write | 6 | Unknown | full/Unknown | 0 | always |
| 08 | positive | common | target-version | 8 | u8 | 0..255 | 0 | always |
| 08 | positive | common | initiator-version | 9 | u8 | 0..255 | 0 | always |

## Flag declarations

All bit defaults are false. Reserved bits remain raw. No flag exclusivity is
established, including valid/invalid and normal/inverted combinations.

| OP | Direction | Bit | Meaning | Grade |
| --- | --- | --- | --- | --- |
| 01 | request | 0 | power-on/start | Hypothesis |
| 01 | request | 1 | change | Hypothesis |
| 01 | request | 2 | CRC-support | Hypothesis |
| 01 | request | 3..7 | reserved | Hypothesis |
| 01 | positive | 0 | valid | Hypothesis |
| 01 | positive | 1 | invalid | Hypothesis |
| 01 | positive | 2 | blocked | Hypothesis |
| 01 | positive | 3 | change | Hypothesis |
| 01 | positive | 4 | denied | Hypothesis |
| 01 | positive | 5 | invalid-range | Hypothesis |
| 01 | positive | 6 | not-user-adjustable | Hypothesis |
| 01 | positive | 7 | reserved | Hypothesis |
| 05 | positive | 0 | disabled; following data omitted | Hypothesis |
| 05 | positive | 1 | writable | Hypothesis |
| 05 | positive | 2 | enum-vs-range | Hypothesis |
| 05 | positive | 3 | additional-four-byte/no-range; read-only over writable | Hypothesis |
| 05 | positive | 4..5 | reserved | Hypothesis |
| 05 | positive | 6 | text alternative 6 | Hypothesis |
| 05 | positive | 7 | text alternative 7 | Hypothesis |
| 07 | request | 0 | normal-replication | Hypothesis |
| 07 | request | 1 | inverted-replication | Hypothesis |
| 07 | request | 2 | refresh | Hypothesis |
| 07 | request | 3..7 | reserved | Hypothesis |

## Interpretation boundaries

| Topic | Preserved interpretation | Unresolved boundary | Grade |
| --- | --- | --- | --- |
| OP01 CRC | mirror candidate; unsupported CRC-support flag is 0 | replacement number Unknown; no TTL or polling suppression | Hypothesis |
| OP04 enable bits | 0 disabled, 1 enabled; all default disabled; 13 bytes = 104 independent bits | logical footprint 17 and separate tail (0,13,0) do not establish physical length | Hypothesis |
| OP05 disabled | bit0=1 omits all following data | raw partial positions remain preserved | Hypothesis |
| OP05 enum | six independent alternatives; repeat last when fewer; no separate current-value field | alternative selection Unknown | Hypothesis |
| OP05 bit3 | additional-four-byte/no-range competes with read-only over writable | retain both; no selection by length or adaptation | Hypothesis |
| OP05 range | candidate min+n*step with n*step<=max | enforcement Unknown | Hypothesis |
| OP07 status | whole byte: 0 false, 1 true, default false; nonzero-truth competes with unlabeled 2..255 | raw 02 unresolved; replication algorithms Unknown | Hypothesis |
| OP08 configuration | 1 initiator-spare, 2 target-spare; named default initiator-spare conflicts with raw default 0 | 0 and 3..255 unmapped | Hypothesis |
| OP08 ownership | cross-device ownership | identity and persistence Unknown | Hypothesis |

<!-- legacy-role-mapping:begin -->
Role terminology follows the native framing contract: initiator corresponds to
legacy master; target corresponds to legacy slave. Thus target-written and
target-version preserve the slave-written/slave-version roles, and
initiator-to-write and initiator-version preserve master-to-write/master-version.
<!-- legacy-role-mapping:end -->
The positive direction carries initiator-written and target-to-write instead.
Configured-register forms and previously allocated storage/save forms remain
outside this slice; sharing an operation byte does not merge their variants.
