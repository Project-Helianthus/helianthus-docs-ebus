# Vaillant B50E — logger service

`PB=0xB5`, `SB=0x0E`.

This document specifies the candidate wire contract for the Vaillant `B5 0E` data-logger service: a rule table that selects values to record, a log buffer, an information block and two control operations. It does not define client lifecycle, deployment policy, or consumer presentation.

## Status

Every layout on this page is **Hypothesis**, unconfirmed on the wire. No capture of a `B5 0E` request or reply is recorded here. Device coverage, write effects and the record format of the log buffer remain `Unknown`.

Profile availability: each `B5 0E` operation (`00` to `07`) is available under both the eBUS and the PeBUS profiles (candidate). No service of this family is available only on PeBUS (candidate, unconfirmed on the wire). This statement covers `B5 0E 00..07`. The 19 data types of the rule-read reply (below) are the same under the eBUS and the PeBUS profiles (candidate, unconfirmed on the wire).

The sibling diagnostic services are on [ebus-vaillant-B503.md](ebus-vaillant-B503.md): `B5 03` codes and histories, and `B5 09 18` sensor and block bit maps.

## Wire shape

The request prefix is `B5 0E <operation>`. Offsets below count from the first byte of the service prefix: the prefix occupies offsets 0 to 2, so the first argument byte is at offset 3. By the same convention as the other `B5` services the request data field starts with the operation byte. How reply offsets map onto the data bytes of a bus reply is unconfirmed; do not apply them to a bus reply without a qualified capture. Multi-byte integers are little-endian unless stated.

## Sub-command catalog

| Operation | Name | Direction (candidate) | Request layout | Reply layout |
|---|---|---|---|---|
| `00` | write rule entry | write | 17 bytes: rule index `uint16` at offset 3, type flag at 5, compare flag at 6, time base at 7, address `uint32` at 8, data type at 12, four opaque compare bytes at 13 | echoes the rule index; 5 bytes |
| `01` | clear rule entry | write (candidate) | rule index; request sentinel semantics Unknown | positive response may echo a `uint16` index; see bounded candidates below |
| `02` | read rule entry | read | rule index `uint16` at offset 3 | rule fields; data-type key at offset 12; a value row selected by the key from offset 13 |
| `03` | read log buffer | read | buffer offset `uint32` at offset 3, length `uint16` at offset 7 (default 8) | echoes offset at 3 and length at 7; data from offset 9 |
| `04` | clear log buffer | write | reset `uint8` at offset 3; `1` resets all | feedback: `1` accepted; `0` and `2` to `255` not accepted |
| `05` | read information block | read | no argument | 11 bytes: build at offset 3, release at 4, rule capacity `uint16` at 5, buffer size `uint32` at 7 |
| `06` | built-in rules | not classified | active rules, 2 bytes at offset 3 | supported rules at offset 3, active rules at offset 5 |
| `07` | operating mode | not classified | mode `uint8` at offset 3 | mode at offset 3, status at offset 4 |

Operations `00`, `01` and `04` are candidate state-changing operations (rule table or buffer), and operations `06` and `07` can change the logger's active rules or operating mode (candidate). None of them is classified under a safety class, and none is documented as safe to send; a separately established safety procedure and target-specific qualification are required. Operations `02`, `03` and `05` are candidate reads; that does not establish that a target answers them.

Frame size: the eBUS application layer limits a manufacturer-specific telegram to 14 data bytes (see [ebus-application-layer.md](../ebus-services/ebus-application-layer.md#communication-rules)). The candidate request of operation `00` (15 data bytes including the operation byte) and a log-buffer read of operation `03` with a length above the remaining reply space exceed that limit. How such requests and replies are carried on eBUS (segmentation, a smaller length, or another bus profile) is unresolved.

### Rule flags

Candidate interpretation, unconfirmed on the wire.

- Type flag: bits 0 to 1 give the address type (`0` unused, `1` symbolic, `2` absolute, `3` internal event); bits 6 to 7 give the status (`0` unused, `1` stop, `2` start). The meaning of bits 2 to 5 is not established.
- Compare flag: see the bounded comparison candidate below; its logical position is Unknown. The offset 6 in the operation `00` layout above is an unqualified layout proposal, not an established location for this candidate.
- Time base: bits 0 to 1 give the unit (`0` once, `1` second, `2` minute, `3` hours); bits 2 to 7 are a 6-bit multiplier.
- Address: `uint32` interpreted in the context of the address type.

### Bounded rule comparison and clear-index candidates

The following two declarations are **Hypothesis**, not native qualification.
They cover only the finite comparison and OP01 positive-index candidates;
other variants and other rule fields remain separate. Logical positions are
Unknown; a logical position is not a wire offset. Extents describe candidate
field carriers, not complete frames. Missing operation or direction metadata
is explicitly Unknown, not a wildcard or evidence of applicability.

| Grade | Identity | Direction | Logical position / extent | Raw type / domain | Scale / unit | Sentinel / default / conflict | Unresolved properties |
|---|---|---|---|---|---|---|---|
| Hypothesis | vaillant / B50E / PB=B5 / SB=0E / OP=Unknown / rule_comparison | Unknown | Unknown / 8 bits | uint8; full byte 00..FF; scalar bits 0..2, modes 0..7; bit 7 independent stop-override-FIFO on match | 1 / none | No sentinel or default established; high flag applies across all modes, not only mode 7 | Bits 3..6 (mask 78) unresolved; preserve full raw byte; physical prefix adaptation Unknown |
| Hypothesis | vaillant / B50E / PB=B5 / SB=0E / OP=01 / clear_rule_positive_index | response (positive candidate) | Unknown / 16 bits | uint16 unsigned little-endian; 0..65535; optional echo | 1 / none | FFFF (65535) may mean all rules cleared only in this OP01 positive echo form; no default established; other operations have no clear meaning here | One-byte echo incomplete/raw; echo presence does not establish physical deletion or persistence; physical prefix adaptation Unknown |

Scalar comparison candidates: `0` time only, `1` equal, `2` not equal,
`3` less than, `4` less than or equal, `5` greater than,
`6` greater than or equal, `7` change. Bit 7 is independent of that scalar:
when set it is a candidate to stop override FIFO when a rule matches. Bits
3..6 do not establish additional modes and must remain raw.

The following are synthetic arithmetic examples, not observations of a device.
Every semantic interpretation remains Hypothesis; physical behavior is Unknown.
The [synthetic examples](fixtures/ae10_b50e_candidates.json) preserve the raw
bytes and explicit absent metadata. Their correctness establishes no native
recording, physical support, freshness or execution authority. Native recording,
other rule fields and checksum/stuffing semantics remain Unknown. Rule-table
declarations are separate from active rule execution.

| Raw comparison byte | Scalar mode candidate | High flag candidate | Unresolved bits retained | Grade |
|---|---|---|---|---|
| 00 | 0 | false | 00 | Hypothesis |
| 07 | 7 | false | 00 | Hypothesis |
| 80 | 0 | true | 00 | Hypothesis |
| 87 | 7 | true | 00 | Hypothesis |
| 88 | 0 | true | 08 | Hypothesis |

| Operation | Direction | Raw echo | Index candidate | All-rules candidate | Completeness | Grade |
|---|---|---|---|---|---|---|
| 01 | positive response | 34 12 | 4660 | false | complete candidate carrier | Hypothesis |
| 01 | positive response | FF FF | 65535 | true | complete candidate carrier | Hypothesis |
| 01 | positive response | FF | Unknown | Unknown | incomplete/raw | Unknown |
| 02 | positive response | FF FF | Unknown | Unknown | raw; outside clear candidate | Unknown |

### Built-in rules and operating mode

Candidate interpretation, unconfirmed on the wire.

- Operation `06` bit map (byte 0: bit 0 power-on, bit 1 status, bit 2 error; byte 1: bit 7 target answer). The request carries the active rules in 2 bytes; the reply carries the supported rules and the active rules.
- Operation `07` mode values: `0F` read, `E1` activate, `F0` deactivate, `FF` do not care. Status values: `0` power-on delay, `1` check rule, `2` write memory, `3` clear memory, `4` read memory.

## Decoding as candidate

### Data types of the rule-read reply

In the reply of operation `02`, the data-type key at offset 12 selects one of 19 value rows from offset 13. Candidate layout, unconfirmed on the wire:

| Key | Value row (starts at row offset 0) | Companion field |
|---:|---|---|
| 0 | opaque | none |
| 1 | boolean, `uint8` | none |
| 2 | `uint8` | none |
| 3 | `int8` | none |
| 4 | `uint16` | none |
| 5 | `int16` | none |
| 6 | `uint32` | none |
| 7 | `int32` | none |
| 8 | secure boolean, `uint8`: `0F` true, `F0` false | none |
| 9 | `uint8` | 1 inverse byte at row offset 1 |
| 10 | `int8` | 1 inverse byte at row offset 1 |
| 11 | `uint16` | 2 inverse bytes at row offset 2 |
| 12 | `int16` | 2 inverse bytes at row offset 2 |
| 13 | `uint32` | 4 inverse bytes at row offset 4 |
| 14 | `int32` | 4 inverse bytes at row offset 4 |
| 15 | opaque | none |
| 16 | opaque | none |
| 17 | `int16` divided by 16, degrees Celsius (range -2048.0 to 2047.9375) | state `uint8` at row offset 2: `00` ok, `55` short circuit, `AA` interrupted |
| 18 | `int16` divided by 16, degrees Celsius (range -2048.0 to 2047.9375) | 2 inverse bytes at row offset 2 |

Inverse bytes are carried raw. The value width of the opaque keys `0`, `15` and `16` is not established.

### Log buffer

The reply of operation `03` is an opaque buffer: the requested offset (`uint32`) at offset 3, the length (`uint16`) at offset 7 and the data from offset 9. No record stride, timestamp layout or integrity check is established, and the rule-read type table does not apply to the buffer.

Candidate interpretation, unconfirmed on the wire: a requester separates buffer entries at the byte `AA` and reverses byte stuffing before interpreting an entry. The stuffing rule itself is not established.

## Open questions

- The record stride of the log buffer is not established.
- The timestamp layout of the log buffer is not established.
- The integrity contract (checksum or sequence check) of the log buffer is not established.
- The stuffing rule and the entry separator `AA` for the log buffer are a candidate interpretation, unconfirmed on the wire.
- The mapping of the layout offsets above to the data bytes of a bus telegram is unconfirmed for every operation.
- How the operation `00` request (15 data bytes) and long operation `03` replies fit the 14-data-byte limit of a manufacturer-specific eBUS telegram is unresolved.
- Operation `01` has only the bounded optional positive-index echo candidate above; its physical placement, presence on a target, deletion and persistence remain Unknown. Request sentinel semantics are Unknown.
- Whether any target answers a `B5 0E` operation, and with which operations, is unconfirmed; the safety class of each operation is unassigned.
- The widths of the opaque value rows (keys `0`, `15`, `16`) are not established.

## References

- [Finite B50E candidate catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab61_b50e_candidates.json) — corroborating declaration metadata for the two bounded candidates only; not native wire evidence.

- [Vaillant B503 diagnostic and service selectors](ebus-vaillant-B503.md)
- [Vaillant B509 register access](ebus-vaillant-B509.md)
- [Vaillant family index](ebus-vaillant.md)
