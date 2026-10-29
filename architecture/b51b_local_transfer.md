# B51B local transfer budgets and independent local CRC

This is a bounded candidate software behavior contract for the Vaillant family.
The [public native family contract](../protocols/vaillant/ebus-vaillant.md#open-questions)
leaves the B5 1B wire layout Unknown. That native boundary takes precedence:
none of the local predicates here establishes native wire semantics, installed
support, freshness, qualification, or execution authority. Nothing is stable
before Helianthus 1.0.

Proven means only independently checked synthetic representation or arithmetic.
Hypothesis marks each supplied local behavior candidate. Unknown marks an
unprovided branch; it cannot admit a transfer. The source of these candidates
is the bounded functional specification in issue #817, a partial slice of #736,
not a capture or vendor wire specification. All tuples in the
[synthetic fixture](fixtures/ai26_b51b_local_transfer.json) are synthetic;
the [standard-library oracle](../tests/test_ai26_b51b_local_transfer.py)
checks both publications against independent constants and arithmetic.

Configuration backup and program contents remain distinct (Hypothesis).
Application-start completion supplies no version result (Unknown). The ordered
roles below distinguish selection, data, write, CRC, status and application;
they do not prescribe an executor or prove a successful device transition.

The grouped procedure has five chunks, not retries. Only its first group is
bounded here; later groups are conditional and Unknown. The cap205 alternative
remains separate: its rejection of 206 does not change the grouped procedure.
Progress is credited only after acceptance and by actual length. Pending or
rejected steps credit zero. An unprovided status yields Unknown. A byte counter
never supplies a buffer offset. Only absence plus a valid default materializes
00 00; a later setter supersedes it. No supplied fact assigns peer append or
offset semantics. These local behavior statements are Hypothesis.

The default CRC candidate uses polynomial 1021, initialization FFFF, MSB-first,
no reflection and no final XOR. Coverage is exactly the call input. Custom
initialization and custom tables can differ; an unprovided table is Unknown.
The synthetic numeric vectors are Proven arithmetic, independently checked with
standard-library CRC arithmetic. They establish no block or transport CRC.
Local, block and transport CRC remain distinct (Hypothesis). Numeric OP0B
fields remain LE16 with no added swap (Hypothesis); B1 29 is the LE16 encoding
of 29B1, independently Proven as a representation.

Forwarding has two distinct Hypothesis alternatives: `filtered` rejects every
selector 06..0E; `unfiltered` lacks that selector predicate. Both retain
`framing`, `address_role`, `state`, `capacity` and `routing` gates. Each gate must
be satisfied; a failed gate rejects and an unprovided gate yields Unknown in
this bounded oracle. Missing selector filtering never means accept-all. The
fixed NN shapes below belong to the second local route. For OP09, NN=3+k and
envelope=8+k, with structural k=0..13. A route rejection at k=14 does not assign
a general protocol or physical limit. The 200/205/206 transfer caps are separate
from this structural route bound. Other selectors and route variants are Unknown.

Raw alternatives remain visible in separate rows rather than reconciled into
one cap or one route. Their applicability to a real implementation is unresolved.
No identity, raw cached bytes, status or failure is converted into qualification.
Rejected or Unknown candidate steps supply no replacement for partial last-known-good
state. Cache freshness, timers, publication policy and failure recovery beyond
these injected predicates are Unknown. There are no sleeps, transport calls,
programming executor, device operations or runtime changes. Existing eBUS MCP
and GraphQL behavior is outside this page's claims and unchanged.

## Checked synthetic tables

Each row carries its own evidence grade. Hex values have no implicit byte swap.
In offset rows, `none` means no later setter; `absent` means no current value.
In CRC rows, `empty` means zero input bytes; other inputs are exact hex spans.

### sequence

| Field | Role | Grade |
|---|---|---|
| 08 | block/segment selection | Hypothesis |
| 09 | data | Hypothesis |
| 0A | write | Hypothesis |
| 0B | CRC | Hypothesis |
| 0C | status | Hypothesis |
| 0E | application | Hypothesis |

### budgets

| Field | Chunks in order | Budget or cap | Result | Grade |
|---|---|---|---|---|
| grouped | 206,206,206,206,200 | 1024 | accept | Hypothesis |
| grouped | 206,206,206,206,201 | 1024 | reject | Hypothesis |
| cap205 | 205 | 205 | accept | Hypothesis |
| cap205 | 206 | 205 | reject | Hypothesis |

### progress

| Field | Status | Credited bytes | Grade |
|---|---|---|---|
| 200 | rejected | 0 | Hypothesis |
| 17 | accepted | 17 | Hypothesis |
| 17 | pending | 0 | Hypothesis |
| 17 | unprovided | Unknown | Unknown |

### offset

| Field | Default validity | Later setter | Result | Grade |
|---|---|---|---|---|
| absent | valid | none | 00 00 | Hypothesis |
| absent | invalid | none | absent | Hypothesis |
| absent | valid | 34 12 | 34 12 | Hypothesis |
| 78 56 | valid | none | 78 56 | Hypothesis |

### crc

| Field | Initialization | Numeric CRC | LE16 | Grade |
|---|---|---|---|---|
| 313233343536373839 | FFFF | 29B1 | B1 29 | Proven |
| empty | FFFF | FFFF | FF FF | Proven |
| 313233343536373839 | 0000 | 31C3 | C3 31 | Proven |
| 31323334 | FFFF | 5349 | 49 53 | Proven |
| 3536373839 | FFFF | 5EB6 | B6 5E | Proven |

### crc_parameters

| Field | Value | Grade |
|---|---|---|
| polynomial | 1021 | Hypothesis |
| initial | FFFF | Hypothesis |
| bit_order | MSB-first | Hypothesis |
| reflection | false | Hypothesis |
| final_xor | 0000 | Hypothesis |
| coverage | exact call input | Hypothesis |

### shapes

| Field | NN | Grade |
|---|---|---|
| 06 | 1 | Hypothesis |
| 07 | 1 | Hypothesis |
| 08 | 9 | Hypothesis |
| 0A | 1 | Hypothesis |
| 0B | 1 | Hypothesis |
| 0C | 1 | Hypothesis |
| 0D | 2 | Hypothesis |
| 0E | 2 | Hypothesis |

### route_data

| Field | NN | Envelope | Result | Grade |
|---|---|---|---|---|
| 0 | 3 | 8 | accept | Hypothesis |
| 13 | 16 | 21 | accept | Hypothesis |
| 14 | 17 | 22 | reject | Hypothesis |

### unknowns

| Field | Grade |
|---|---|
| session initiator | Unknown |
| virtual block size | Unknown |
| peer append/offset behavior | Unknown |
| application-start version result | Unknown |
| conditional later groups | Unknown |
| custom CRC table | Unknown |
| programming executor | Unknown |
| transport implementation | Unknown |
| physical maximum | Unknown |
| installed support | Unknown |
| freshness | Unknown |
| qualification | Unknown |

