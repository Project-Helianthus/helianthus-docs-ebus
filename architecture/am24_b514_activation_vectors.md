# B514 activation vectors

## Evidence and scope

**Hypothesis:** B514 OP03 is a logical positive vector of ten separate u8
fields, which gives 80 independent bit positions. B514 OP04 is a logical
positive vector of twelve separate scalar enum bytes with 96 declared mappings.
**Unknown:** the exact OP04 labels, every OP03 bit meaning, native support,
physical effects, persistence and delivery. No native codec, mapping table,
polling route, transmit route or admission change follows from this page.

**Proven (software structure):** the pure view below is executable structure
over candidate vectors. Existing shape prose, OP02 row anomalies, OP05 typed
rows and live value methods keep their own responsibilities. The companion
registry build (AM23) holds its merge for this page; this page has no code
dependency.

## Input

The caller supplies, explicitly and unchanged:

| Input | Recognized value |
| --- | --- |
| family | `vaillant` |
| variant | `B514` |
| operation | `3` (OP03) or `4` (OP04) |
| direction | `positive` |
| field bytes | isolated logical field bytes, any length |

The field bytes are the isolated logical vector. Physical offsets and header
adaptation are not selected by this API. The sizes 10 (OP03) and 12 (OP04)
apply only to isolated logical vectors. Each identity axis is compared
independently and exactly; there is no fallback, wildcard or nearest match.

## Output

The view returns, for every input:

| Output | Meaning |
| --- | --- |
| `recognized` | true only when all four identity axes match |
| `grade` | `Hypothesis` when recognized, `Unknown` for raw-only |
| `raw` | an owned copy of all supplied bytes |
| `present_mask` | integer with bit `i` set when field `i` is present; `null` for raw-only |
| `complete` | true only when exactly the declared size is present |
| `remainder` | an owned copy of bytes beyond the declared size |
| `fields` | one entry per declared position; `null` for raw-only |

Missing fields are absent: their entry has `present: false` and no value, never
`false` or zero. A present zero byte is distinct and reports `present: true`.
Short vectors retain every present position. Extra bytes remain raw in
`remainder`, are never interpreted as fields, and make the whole vector not
complete. The returned `raw` and `remainder` do not share storage with the
caller's buffer or with a previous result; mutating a returned value changes
nothing else.

### OP03

Each field entry carries `value` (the raw u8) and `bits`, eight Booleans indexed
0..7 where bit 0 is the least significant bit of the byte. The addressable
position is byte index 0..9 and bit 0..7, so exactly 80 positions exist and no
two alias. `label` is `Unknown` for every position; no semantic label is
invented.

### OP04

Each field entry carries only the raw scalar `value` (0..255) and
`interpretation: Unknown`. The twelve bytes are scalars, not bit flags: the
96 mappings are not 96 bits, no `bits` are exposed and no label is invented.

### Raw-only

An unrecognized operation, family, variant or direction returns
`recognized: false`, grade `Unknown`, the owned raw bytes, an empty remainder,
`complete: false`, and no fields or mask.

## Synthetic cases

The [synthetic package](fixtures/am24_b514_activation_vectors.json) lists the
cases below; the focused test recomputes every expectation independently.

| Case | Operation | Input hex | present_mask | complete | remainder |
| --- | --- | --- | --- | --- | --- |
| op03-empty | 3 | (empty) | 0 | false | (empty) |
| op03-short-zero | 3 | 00 | 1 | false | (empty) |
| op03-short-three | 3 | 8001ff | 7 | false | (empty) |
| op03-full | 3 | 01000000000000000080 | 1023 | true | (empty) |
| op03-extra | 3 | 0100000000000000000080 | 1023 | false | 80 |
| op04-short | 4 | 0003 | 3 | false | (empty) |
| op04-full | 4 | 000380ff0102040810204055 | 4095 | true | (empty) |
| op04-extra | 4 | 000380ff010204081020405500 | 4095 | false | 00 |
| raw-only-operation | 5 | 0003 | null | false | (empty) |

The OP03 walk sets one bit at a time across all 80 positions with all other
bytes zero and requires exactly one true bit. The OP04 vector uses twelve
distinct bytes including 00, 03, 80 and FF.

## Limits

All grades stay independent of physical support, presence, freshness and
execution. Nothing here is stable before Helianthus 1.0. This page adds no
index entry, gate registration or protocol-page claim.
