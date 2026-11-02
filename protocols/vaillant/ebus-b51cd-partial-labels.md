# B51C and B51D partial testing labels

## Native contract and evidence

The public starting contract is [header-only service identities](ebus-vaillant.md#header-only-service-identities)
and its [native label inventory](fixtures/b5-header-only-service-labels.csv).
That contract leaves the wire layout and individual meanings Unknown and states
that these identities are not one-byte eBUS requests. The partial declarations
below retain only the supplied candidate constants; they do not fill that gap.

**Hypothesis:** Eleven B51C names and twelve B51D names have partial forms
consisting only of request B5 and positive F5, each one coded eight-bit constant
at logical byte zero, bit zero. B51C and B51D are lexical name groups here;
the suffix is a label identifier only. Neither group nor suffix establishes
secondary 1C/1D, an opcode, a body, an enum, a constructor or a decoder.
No suffix is a wildcard or an encoded byte. All 23 identities remain separate
even though their constants coincide. Uninterpreted controls remain opaque.

**Unknown:** Matching eBUS/PeBUS declarations do not establish physical
equivalence or installed support. A logical positive F5 is not an established
physical reply header. Body layout, codec, gating, confirmation, effect and
physical framing remain unresolved. The starting contract and this partial
Hypothesis are retained side by side; neither resolves the missing wire evidence.
No complete alternative wire layout is supplied, so none is synthesized.

## Synthetic partial tuples

All rows in the [synthetic fixture](fixtures/ai18_b51cd_partial_labels.json)
are synthetic declarations, without device observations. The two constants in
each row describe separate partial forms, never a combined packet. Logical byte,
bit and width apply independently to each constant. `absent` corresponds to
null in the fixture and differs from numeric zero; it supplies no coordinate
or body bytes. An Unknown body is never an empty encodable packet. No test
command or partial-form emitter is defined.

**Proven:** Only the local representation arithmetic in the final table is
established. This proves neither the Hypothesis nor a native wire contract. Synthetic checks confer no physical qualification, freshness,
persistence or execution permission.

| Group | Label suffix | Request constant | Positive constant | Logical byte | Bit | Width bits | Secondary | Operation | Body | Grade |
|---|---|---|---|---|---|---|---|---|---|---|
| B51C | 00 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 01 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 02 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 03 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 10 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 13 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 14 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 19 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 1B | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 1C | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51C | 1D | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 00 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 01 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 02 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 03 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 10 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 11 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 12 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 13 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 14 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 15 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 16 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |
| B51D | 17 | B5 | F5 | 0 | 0 | 8 | absent | absent | absent | Hypothesis |

## Unresolved declarations

Each grade is independent of the representation arithmetic and of physical
qualification. Partial constants remain available as partial knowledge; they
cannot admit a complete encodable form. No inference is made from a readable
value to writable behavior or from one device family to another.

| Claim | Grade |
|---|---|
| body-layout | Unknown |
| codec | Unknown |
| gating | Unknown |
| confirmation | Unknown |
| effect | Unknown |
| physical-framing | Unknown |
| physical-equivalence | Unknown |
| installed-support | Unknown |
| freshness | Unknown |
| persistence | Unknown |
| execution-permission | Unknown |
| uninterpreted-controls | Unknown |

## Local representation arithmetic

The unsigned range and absolute bit interval describe each isolated constant,
not a complete body or physical packet length.

| Side | Constant | Decimal | Minimum | Maximum | Start bit | End bit | Grade |
|---|---|---|---|---|---|---|---|
| request | B5 | 181 | 0 | 255 | 0 | 7 | Proven |
| positive | F5 | 245 | 0 | 255 | 0 | 7 | Proven |
