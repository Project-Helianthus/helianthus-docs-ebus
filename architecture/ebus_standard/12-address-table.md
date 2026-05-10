# eBUS Address Table

Status: Normative
Milestone: SAS-01 M1 (table v1) + Phase C C0_DOC_SPEC (256-byte taxonomy and frame-type contract)
Table owner: `helianthus-docs-ebus`

<!-- legacy-role-mapping:begin -->
> **Vocabulary note**: this chapter uses the eBUS-spec normative terms
> "Master" and "Slave" verbatim because they are the AddressClass enum
> names defined by the spec. In Helianthus prose outside this chapter,
> "initiator" maps to Master and "target" maps to Slave per the global
> terminology gate. The legacy-role-mapping markers wrap the entire
> chapter to allow spec-faithful vocabulary in the normative content.

## Rename note

This chapter was previously named `12-source-address-table.md` and is renamed
`12-address-table.md` under Phase C of plan
`address-table-registry-w19-26.locked`. The v1 source-address table block
below is preserved byte-for-byte; its hash is unchanged. The new sections are
additive and have their own anchor and hash.

## Purpose

This chapter freezes:

1. The standard eBUS source-address table v1 (25 master rows + companion
   slaves, retained from the original lock).
2. The full 256-byte address taxonomy that classifies every byte value into
   exactly one of `Master | Slave | Broadcast | Reserved`.
3. The frame-type addressing contract that constrains which class is allowed
   in `src` and `dst` for each frame type (`M2S`, `M2M`, `M2BC`).
4. The `ValidateFrameAddressing(frameType, src, dst) error` contract used by
   gateway-side defense-in-depth enforcement.

The table is protocol data and frame-type addressing is protocol semantics:
gateway code may filter or order rows but MUST NOT rewrite standard rows or
weaken the frame-type contract. Tier and role labels (PC, free-use, recommended
for) belong to the upper-layer table v1; the new `AddressClass` enum is the
lower-layer protocol classification only.

> Terminology gate: in all post-Phase-C prose, `initiator` denotes the address
> that started a transaction (frame `src` — equivalent to "Master role" for
> M2S/M2M and "Master role" for M2BC) and `target` denotes the address being
> addressed (frame `dst`). The legacy `Source` and `Companion` columns in the
> v1 table below are retained verbatim and read as "initiator" and "target",
> respectively, for the v1 master/slave companion-pair semantics.

## Official Spec Evidence

This chapter is derived only from local official specifications. In developer
workspaces and local CI, `HELIANTHUS_OFFICIAL_SPEC_DIR` points to the directory
that contains these files. If the variable is unset, the checker tries
`../docs` relative to this repository; repo-only CI falls back to the committed
excerpt fixture below.

- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:28-60`
  for the 25 source-capable address rows and free-use note.
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md:69-305`
  for the slave-address table including reserved companion rows, the
  `A9H`/`AAH` "must not be used" reservation (lines 224-225) and the broadcast
  reservation `FEH` (line 305).
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:170-184`
  for the master/slave companion-address arithmetic and the `0xFF`→`0x04`
  special case.
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:220-244`
  for the broadcast telegram contract (sender Master, dst broadcast, no ACK).
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:248-260`
  for the SYN symbol `0xAA` reservation (lines 250-252) and the source/destination
  semantics.
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:284-286`
  for the ACK byte definition (positive `0x00`, negative `0xFF`).
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:320-349`
  for the priority-class and sub-address split.
- `$HELIANTHUS_OFFICIAL_SPEC_DIR/Spec_Prot_12_V1_3_1_E.en.md:471-478`
  for the ACK/NACK byte context.

The checker in
[`scripts/check_source_address_table_against_official_specs.py`](../../scripts/check_source_address_table_against_official_specs.py)
validates the v1 table rows against the local official specs when
`HELIANTHUS_OFFICIAL_SPEC_DIR` is set. Repo-only CI uses a committed
official-derived fixture with source file hashes and line provenance instead
of comparing the table to itself.

## Semantics (v1 table)

- `Source` is the byte emitted as the source address of an active eBUS frame.
- `Priority index` is the p0..p4 source-address priority class.
- `Arbitration nibble` is the low nibble used for byte-oriented arbitration.
  Lower bus priority class wins on the wire: p0 / `0x0`, then p1 / `0x1`,
  p2 / `0x3`, p3 / `0x7`, and p4 / `0xF`. This does not define Helianthus
  preference order.
- `Official description summary` is a compact summary of the local official
  spec row. It is not an enum.
- `Canonical description` is the stable Helianthus enum-facing description.
- `Free-use` and `Recommended for` are separate fields. A recommendation never
  authorizes gateway startup selection by itself.
- `Companion` is the responder-side address derived by adding `0x05` to the
  source address modulo one byte; `0xFF` therefore maps to `0x04`.
- `0xFF` is valid in the `Source` column. In an ACK/NACK field, `0xFF` is a
  negative acknowledgement. Consumers must keep those contexts separate.

## Gateway Selection Policy

The standard table does not prescribe the Helianthus gateway startup order.
When no source description, priority index, or exact address is configured, the
gateway uses `HelianthusGatewayDefaultPolicy`:

1. p4 candidates: `0xFF`, `0x7F`, `0x3F`, `0x1F`
2. p3 candidates: `0xF7`, `0x77`, `0x37`, `0x17`, `0x07`
3. p1 candidates: `0x11`, `0x31`
4. p0 candidates: `0x00`

This is a Helianthus policy, not an eBUS priority claim. The p4 rows lose to
p0..p3 during bus arbitration; they are tried first because Helianthus wants
free-use or tool-like addresses before preallocated controller identities.

If gateway startup configuration supplies only a priority index, selection
filters `HelianthusGatewayDefaultPolicy`; it does not search every standard
row at that priority. If it supplies a standard source description, selection
uses only rows with that exact canonical description and optionally intersects
them with the configured priority index. Free-use recommendations remain
informational.

An exact source address uses `explicit_validate_only`: candidate search is
bypassed, but the selected source and companion must still pass availability
and active-probe validation before any normal gateway-owned bus-reaching path
can use them.

## Startup Source-Selection Boundary

`helianthus-ebusgo` owns the reusable `SourceAddressSelector` mechanics and
the static table constants. `helianthus-ebusgateway` owns startup
source-selection validation: active probe, retry/quarantine, persistence
metadata, operator recovery surfaces, and source-selection status.
`helianthus-ebusreg` remains source-selection-agnostic and consumes only the
source byte it is given.

Normal gateway-owned operations use only
`SourceAddressSelection.Source` after `active_probe_passed`. This includes MCP,
GraphQL, Portal explorer, semantic pollers/writers, schedulers, NM runtime, and
gateway-internal protocol dispatch. A redundant caller-provided source matching
the active-probe-passed source may be accepted as diagnostic input; a
nonmatching source is rejected on normal gateway-owned paths.

Only transport-specific diagnostic MCP requests may use a non-selected source,
and only for one audited, non-persistent request that does not mutate the
active-probe-passed source.

`DEGRADED_SOURCE_SELECTION` is fail-closed. While it is active, Helianthus
originates no eBUS traffic: no scan, semantic polling, MCP/GraphQL bus invoke,
NM `FF 00`/`FF 02`, `0x07/0xFF`, or companion responder activity.

The only first-implementation pre-discovery validation probe is addressed
`0x07/0x04`, classified as `read_only_bus_load`, against a configured or
current bounded positive target. Startup source-selection validation must not
use broadcast `0x07/0xFE`, `0x0F` test commands, NM services, mutating
services, memory writes, full-range probes, SYN/ESC/broadcast destinations, the
selected source, or the selected companion as a validation target.

The public API migration matrix for these source-selection status and source
authority changes is maintained in
[`api/source-selection-migration.md`](../../api/source-selection-migration.md).

## Hash Contract (v1 table)

Table anchor: `#ebus-source-address-table-v1`

Table version: `ebus-source-address-table/v1`

Hash algorithm: SHA-256 over the exact Markdown table block from the header
row through the last data row, UTF-8 encoded, LF line endings, trailing spaces
stripped per line, and exactly one terminal LF. The heading and surrounding
prose are excluded.

Normalized table hash:
`e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103`

The pre-rename file location was `12-source-address-table.md`. The hash above
is independent of the file name and remains the migration trail anchor.

## eBUS Source Address Table v1

| Source | Priority index | Arbitration nibble | Official description summary | Canonical description | Free-use | Recommended for | Companion |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `0x00` | p0 | `0x0` | PC/Modem | PC/Modem | no | none | `0x05` |
| `0x10` | p0 | `0x0` | Heating controller | Heating regulator | no | none | `0x15` |
| `0x30` | p0 | `0x0` | Heating circuit controller 1 | Heating circuit regulator 1 | no | none | `0x35` |
| `0x70` | p0 | `0x0` | Heating circuit controller 2 | Heating circuit regulator 2 | no | none | `0x75` |
| `0xF0` | p0 | `0x0` | Heating circuit controller 3 | Heating circuit regulator 3 | no | none | `0xF5` |
| `0x01` | p1 | `0x1` | Hand programmer / Remote control | Handheld programmer / remote | no | none | `0x06` |
| `0x11` | p1 | `0x1` | Bus interface / Climate controller | Bus interface / climate regulator | no | none | `0x16` |
| `0x31` | p1 | `0x1` | Bus interface | Bus interface | no | none | `0x36` |
| `0x71` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0x76` |
| `0xF1` | p1 | `0x1` | Heating controller | Heating regulator | no | none | `0xF6` |
| `0x03` | p2 | `0x3` | Burner controller 1 | Combustion controller 1 | no | none | `0x08` |
| `0x13` | p2 | `0x3` | Burner controller 2 | Combustion controller 2 | no | none | `0x18` |
| `0x33` | p2 | `0x3` | Burner controller 3 | Combustion controller 3 | no | none | `0x38` |
| `0x73` | p2 | `0x3` | Burner controller 4 | Combustion controller 4 | no | none | `0x78` |
| `0xF3` | p2 | `0x3` | Burner controller 5 | Combustion controller 5 | no | none | `0xF8` |
| `0x07` | p3 | `0x7` | empty | Not preallocated | yes | none | `0x0C` |
| `0x17` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x1C` |
| `0x37` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x3C` |
| `0x77` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0x7C` |
| `0xF7` | p3 | `0x7` | Heating controller recommendation | Not preallocated | yes | Heating regulator | `0xFC` |
| `0x0F` | p4 | `0xF` | Clock module / Radio clock module | Clock/radio-clock module | no | none | `0x14` |
| `0x1F` | p4 | `0xF` | Burner controller 6 recommendation | Not preallocated | yes | Combustion controller 6 | `0x24` |
| `0x3F` | p4 | `0xF` | Burner controller 7 recommendation | Not preallocated | yes | Combustion controller 7 | `0x44` |
| `0x7F` | p4 | `0xF` | Burner controller 8 recommendation | Not preallocated | yes | Combustion controller 8 | `0x84` |
| `0xFF` | p4 | `0xF` | PC | PC | no | none | `0x04` |

---

## 256-Byte Address Taxonomy

Anchor: `#ebus-256-byte-address-taxonomy-v1`

Taxonomy version: `ebus-address-taxonomy/v1`

The full 256-byte address space is partitioned by lower-layer eBUS protocol
classification into exactly four classes. Tier (p0..p4), free-use status, and
upper-layer role recommendations belong to the v1 table above; this taxonomy
is purely about which raw byte values are valid in `src`, in `dst`, and in
which frame type.

```text
type AddressClass uint8

const (
    AddressClassReserved  AddressClass = iota // 0
    AddressClassMaster                        // 1
    AddressClassSlave                         // 2
    AddressClassBroadcast                     // 3
)
```

### Class definitions

- `AddressClassMaster`: any byte that satisfies the eBUS initiator
  bit-pattern rule — high nibble AND low nibble both in `{0x0, 0x1, 0x3,
  0x7, 0xF}`. Spec_Prot_7 Anhang §1 (`Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md`
  lines 28-58) enumerates exactly **25 master addresses** (`00H`, `10H`,
  `30H`, `70H`, `F0H`, `01H`, `11H`, `31H`, `71H`, `F1H`, `03H`, `13H`,
  `33H`, `73H`, `F3H`, `07H`, `17H`, `37H`, `77H`, `F7H`, `0FH`, `1FH`,
  `3FH`, `7FH`, `FFH`). The arbitration nibble allocation that produces
  this set is described in Spec_Prot_12 §6.2.2 (`Spec_Prot_12_V1_3_1_E.en.md`
  lines 320-349).
- `AddressClassSlave`: every byte that is NOT `AddressClassMaster`, NOT
  `AddressClassBroadcast`, and NOT `AddressClassReserved`. This is the
  taxonomy-by-elimination class. Cardinality is `256 - 25 - 1 - 2 = 228`
  bytes. NOTE: this number is the **lower-layer protocol** count and
  intentionally diverges from the **enumerated** slave count in the Anhang
  (see "Reconciliation with Anhang slave enumeration" below).
- `AddressClassBroadcast`: exactly one byte, `0xFE`. Spec_Prot_7 Anhang §2
  line 305: "`FEH` ... Reserved for broadcast messages". Spec_Prot_12 §4.3
  (lines 220-244) defines the broadcast telegram form.
- `AddressClassReserved`: bytes that the eBUS spec excludes from address use
  because of conflicts with the symbol layer:
  - `0xAA` — SYN symbol. Spec_Prot_12 §5.1 lines 250-252: "The SYN-symbol
    has bit sequence `10101010` (`0xAA`). This bit sequence is reserved
    for the SYN symbol and may not occur in any other symbol or
    character." Spec_Prot_7 Anhang line 225: "`AAH` ... Must not be used
    as a master or slave address — used as synchronisation symbol!"
  - `0xA9` — escape byte for the SYN/escape expansion rule. Spec_Prot_12
    §5.1 lines 250-252: "value `0xAA` has to be converted into two data
    bytes and expanded to sequence `0xA9` + `0x01` ... `0xA9` is expanded
    to `0xA9` + `0x00`." Spec_Prot_7 Anhang line 224: "`A9H` ... Must not
    be used as a master or slave address — used as synchronisation
    symbol!" (the Anhang text reuses the SYN footnote for both reserved
    rows).

> Implementation note: `AddressClassReserved` MUST be the zero value of the
> enum so that any uninitialized `AddressClass` field fails closed.

### 256-byte mapping rules

Algorithmic resolution per byte `b`:

```text
1. if b == 0xAA or b == 0xA9 -> AddressClassReserved
2. else if b == 0xFE         -> AddressClassBroadcast
3. else if isMasterBitPattern(b) -> AddressClassMaster   (25 bytes)
4. else                      -> AddressClassSlave        (228 bytes)
```

Where `isMasterBitPattern(b)` returns true iff `(b >> 4) ∈ {0,1,3,7,F}` AND
`(b & 0x0F) ∈ {0x0, 0x1, 0x3, 0x7, 0xF}`. This is the existing
`helianthus-ebusgo/protocol.IsInitiatorCapableAddress` predicate.

Cardinality check: `1 (broadcast) + 2 (reserved) + 25 (master) + 228 (slave)
= 256`. The taxonomy partitions the full byte space; every byte has exactly
one class.

### Reconciliation with Anhang slave enumeration

Spec_Prot_7 Anhang §2 (lines 69-305) is a **device-allocation table**, not the
lower-layer taxonomy. Two distinct counts coexist and must not be confused:

- **Anhang named slaves**: 203 rows labelled `Slave 1` (line 75, address
  `02H`) through `Slave 203` (line 304, address `FDH`). These are the
  spec's allocated/recommended slave slots and the only slave addresses
  the Anhang assigns a sequential slave number to.
- **Anhang reserved-companion slaves**: 25 rows of the form "Reserved for
  slave address of master address `XXH`" (e.g. line 76 `04H` reserved for
  master `FFH`; line 77 `05H` reserved for master `00H`; ...). These are
  slave-class addresses by protocol classification, but the Anhang does
  not give them a sequential slave number because they are pre-allocated
  to a master companion. There are exactly 25 such rows (one per master).
- **Lower-layer Slave class total**: 203 + 25 = 228 bytes.

The 228 figure is the protocol classification used by `AddressClassSlave`.
The 203 figure is the Anhang's sequential `Slave NNN` label range and is
not used by the validator. ebusd's "203 pure slaves" reference matches the
Anhang label count, not the taxonomy class.

There is no `[SPEC-AMBIGUOUS]` flag here: the two figures answer different
questions. The validator only ever asks "is this byte slave-class" and
that is `256 - 25 master - 1 broadcast - 2 reserved = 228`.

### Pinned classification cases

Operator-confirmed and spec-pinned (line cites refer to
`Spec_Prot_7_V1_6_1_Anhang_Ausgabe_1.en.md` unless noted):

- `0x00` — Master. Anhang line 34 (Master 1, PC/Modem).
- `0xFF` — Master. Anhang line 58 (Master 25, PC). NOT a Slave: the slave
  table ends at `FEH` (line 305) and never lists `FFH`. PC reserved-use
  note: the Anhang has no special "PC reserved" rule; `0x00` and `0xFF`
  are ordinary masters of priority `p0` and `p4` respectively per their
  rows. Spec_Prot_12 §5.4 (line 264) caps total primary-command codes at
  254 because `0xAA` and `0xA9` are excluded — that rule applies to PB,
  not addresses.
- `0x04` — Slave. Anhang line 76: "Reserved for slave address of master
  address `FFH`". Slave-class because it is neither initiator bit-pattern
  nor broadcast nor reserved.
- `0x05` — Slave. Anhang line 77: "Reserved for slave address of master
  address `00H`".
- `0x08` — Slave. Anhang line 79: "Reserved for slave address of master
  address `03H`".
- `0x15` — Slave. Anhang line 88: "Reserved for slave address of master
  address `10H`".
- `0x26` — Slave. Anhang line 103: `26H | Slave 18`. No master companion
  (`0x21` fails initiator bit-pattern: low nibble `0x2` not in
  `{0,1,3,7,F}`). Operator-pinned `Companion(0x26) = (0, false)` case.
- `0xEC` — Slave. Anhang line 291: `ECH | Slave 194`. No master companion
  (`0xE7` fails high-nibble `0xE`). SOL00 in Vaillant deployments; locked
  plan AD03 pins it.
- `0xF6` — Slave. Anhang line 298: "Reserved for slave address of master
  address `F1H`". Companion of v1 row `0xF1` (Master 10). NETX3 primary
  slave.
- `0xA9` — Reserved (escape byte; Anhang line 224, Spec_Prot_12 §5.1
  lines 250-252).
- `0xAA` — Reserved (SYN symbol; Anhang line 225, Spec_Prot_12 §5.1
  lines 250-252).
- `0xFE` — Broadcast (Anhang line 305).

### What this taxonomy is NOT

- It is NOT the upper-layer tier classification (p0..p4). Tier lives in the
  v1 table above. A Master with priority class `p4` is still
  `AddressClassMaster`.
- It is NOT a device role enum (PC, Heating Regulator, Burner, etc.). Roles
  live in the v1 `Canonical description` column and in upper-layer device
  registry types.
- It is NOT a free-use marker. Free-use lives in the v1 `Free-use` column.
- It is NOT a verification-state field. Verification state lives in the
  registry `AddressSlot` (plan `address-table-registry-w19-26.locked`).

### Wire-level vs gateway-side enforcement

Operator-declared exception: the eBUS spec does NOT constrain the FROM address
on the wire by frame type. There is no "you must always emit M2BC from a
Master" rule enforced at the bit level; the wire accepts arbitrary bytes and
the receiver discriminates by header position and frame structure. The
classification above is therefore *gateway-side discipline*, not a bus
hardware invariant. Helianthus refuses ill-typed frames at the transport
boundary as defense in depth, not because the bus rejects them.

The Anhang silently confirms this: every slave row gives a recommended
device role (Mixer, Pump, Outdoor temperature, ...) but never says "the
slave must validate the sender class". Sender-class enforcement is
upper-layer policy.

## Frame-Type Addressing Contract

Anchor: `#ebus-frame-type-addressing-contract-v1`

Contract version: `ebus-frame-type-addressing-contract/v1`

eBUS defines three frame types in Spec_Prot_12 §4.1-§4.3:

| Frame type | Spec section | Spec name | Sender role | Receiver role |
| --- | --- | --- | --- | --- |
| `M2M` | §4.1 (lines 148-184) | Master-Master Telegram | Master | Master |
| `M2S` | §4.2 (lines 186-218) | Master-Slave Telegram | Master | Slave |
| `M2BC` | §4.3 (lines 220-244) | Broadcast Telegram | Master | Broadcast (`0xFE`) |

Helianthus wraps these as `protocol.FrameType` values. The mapping unifies the
parser-side reconstructor enum and the emitter-side `Frame` field into a
single source of truth (Phase C AD27).

| `protocol.FrameType` | Wire frame | Allowed `src` class | Allowed `dst` class | Notes |
| --- | --- | --- | --- | --- |
| `FrameTypeM2S` | Master-Slave | Master | Slave | Per spec §4.2. Receiver acknowledges via ACK byte. |
| `FrameTypeM2M` | Master-Master | Master | Master | Per spec §4.1. Receiver acknowledges via ACK byte. |
| `FrameTypeM2BC` | Broadcast | Master | Broadcast (`0xFE` only) | Per spec §4.3. NOT acknowledged. |
| `FrameTypeUnknown` | — | n/a | n/a | Zero value. Caller may leave it unset; validator falls back to `FrameTypeForTarget(dst)`. INVALID after fallback only when target is reserved. |

### Frame.FrameType field and FrameTypeForTarget fallback

Phase C extends `protocol.Frame` with an optional `FrameType` field. The
existing central inference function `protocol.FrameTypeForTarget(target byte)
FrameType` (defined in `helianthus-ebusgo/protocol/protocol.go`) remains
authoritative for the *derived* mapping `dst → frame type`:

```text
FrameTypeForTarget(0xFE)  -> FrameTypeBroadcast        (== FrameTypeM2BC)
FrameTypeForTarget(b) where b is master bit-pattern    -> FrameTypeM2M
FrameTypeForTarget(b) where b is slave-class           -> FrameTypeM2S
FrameTypeForTarget(0xAA|0xA9)                          -> FrameTypeUnknown
```

When the caller leaves `Frame.FrameType` at the zero value, `Frame.Validate`
substitutes `FrameTypeForTarget(Frame.Target)`. This means the additive
`FrameType` field is **back-compat** — every existing caller continues to
work unchanged, and the validator still rejects all post-Phase-C
ill-formed cases.

When the caller explicitly sets `Frame.FrameType`, the validator MUST
cross-check against `FrameTypeForTarget(Frame.Target)`. Mismatch is
`ErrInvalidFrameAddress`. This protects services like `03h 10h` (see
"Service 03h 10h runtime-target branching" below) where the caller knows
something the central inference cannot know — for those, the caller MUST
declare the actual frame type and the dst byte must be consistent with
that declaration.

### Self-addressing rule

For any frame type, `src != dst` MUST hold. The bus has no architecturally
meaningful self-addressed frame; an emitter cannot acknowledge or arbitrate
against itself. The validator rejects `src == dst` regardless of frame type.

### Sender constraint scope

Per spec §4.1-§4.3, the *sender* role for every defined frame type is Master.
The contract above therefore requires `src == AddressClassMaster` in all
three frame types. There is no spec-defined frame whose sender is a Slave
or a Broadcast byte; a Slave participant only emits the post-ACK reply
segment of an M2S transaction (Spec_Prot_12 §4.2.1, lines 216-218), which
is part of the same telegram, not an independently addressed frame.

### Per-application-layer-service frame-type mapping

The following table records, per spec line, the frame type each
application-layer service emits. Values are derived directly from the `ZZ`
column of the corresponding `Spec_Prot_7_V1_6_1_E.en.md` Requirement table.
Where the spec uses an unconstrained `ZZ` (e.g. "Target address / Slave"),
the cited section indicates the only legal target class; where the spec
admits both master and slave targets, the row is flagged
**runtime-target-branching**.

| Service code | Spec section (line) | `ZZ` declaration | Frame type at the wire | Runtime branching? |
| --- | --- | --- | --- | --- |
| `03h 04h` | §3.1.1 (line 320) | `ZZ` Target address (single response form) | M2S | no |
| `03h 05h` | §3.1.2 (line 344+) | same as `03h 04h` (single response form) | M2S | no |
| `03h 06h` | §3.1.3 | single response form | M2S | no |
| `03h 07h` | §3.1.4 | single response form | M2S | no |
| `03h 08h` | §3.1.5 | single response form | M2S | no |
| `03h 10h` | §3.1.6 (lines 510, 518, 525) | `ZZ` Target address / Slave; spec contains explicit "If target == master" (line 518) and "If target == slave" (line 525) branches | M2S OR M2M (caller declares) | **YES — runtime-target-branching** |
| `08h 00h` | §3.4.1 (line 1190) | `ZZ = FEh` Broadcast | M2BC | no |
| `08h 01h` | §3.4.2 (line 1213) | `ZZ = FEh` Broadcast | M2BC | no |
| `08h 02h` | §3.4.3 (line 1236) | `ZZ = FEh` Broadcast | M2BC | no |
| `08h 03h` | §3.4.4 (line 1259) | `ZZ = FEh` Broadcast | M2BC | no |
| `08h 04h` | §3.4.5 (lines 1283, 1293) | `ZZ` Target address; ACK at byte 16; note "Controller 0, HK-controller" | M2S | no |
| `FEh 01h` | §3.7.1 (line 1580) | `ZZ = FEh` Target address (broadcast) | M2BC | no |
| `FFh 00h` | §3.8.1 (line 1602) | `ZZ = FEh` Target address (broadcast) | M2BC | no |
| `FFh 01h` | §3.8.2 (line 1620) | `ZZ = FEh` Target address (broadcast) | M2BC | no |
| `FFh 02h` | §3.8.3 (line 1638) | `ZZ = FEh` Target address (Broadcast) | M2BC | no |
| `FFh 03h` | §3.8.4 (line 1656) | `ZZ` Target address (slave address of master to be interrogated) | M2S | no |
| `FFh 04h` | §3.8.5 (line 1678) | `ZZ` Target address (slave address of to be interrogated master) | M2S | no |
| `FFh 05h` | §3.8.6 (line 1706) | `ZZ` Target address (slave address of to be interrogated master) | M2S | no |
| `FFh 06h` | §3.8.7 (line 1733) | `ZZ` Target address (slave address of to be interrogated master) | M2S | no |

NM rows (`FFh 00h..FFh 06h`) split cleanly: the three reset/failure
broadcasts (`FFh 00h`, `FFh 01h`, `FFh 02h`) are M2BC because their
`ZZ = FEh` is hard-coded in the spec table; the four interrogations
(`FFh 03h..FFh 06h`) are M2S because their `ZZ` field is "slave address
of master to be interrogated" — i.e. they unicast at the slave companion
of the master they query and receive an ACK + S-block reply. There is no
mixed-frame NM service in the spec.

Service 08h is uniformly M2BC for sub-codes `00h..03h` (the spec hardcodes
`ZZ = FEh` in every Requirement table) and M2S for `04h` (System Remote
Control, single-target unicast to a controller; ACK byte 16).

### Service 03h 10h runtime-target branching

Spec_Prot_7 §3.1.6 (`Spec_Prot_7_V1_6_1_E.en.md` line 497 onward) is unique
in §3.1: it declares two response forms based on the runtime target byte:

- Lines 518-523: "If target address == master-address then" — response is
  a follow-on master telegram (`ZZ 9 ACK`, `M 10 SYN`). This is M2M-shaped
  at the wire.
- Lines 525-540: "If target address == slave-address then" — response is
  a slave block (`S 1 ACK ... S 9 CRC`, `M 9 ACK`, `M 10 SYN`). This is
  the standard M2S form.

The other 03h sub-codes (§3.1.1–3.1.5) only document one response form
and so map deterministically to M2S.

For 03h 10h the caller MUST set `Frame.FrameType` explicitly to either
`FrameTypeM2S` or `FrameTypeM2M`, and the validator cross-checks that the
declared `FrameType` matches `FrameTypeForTarget(Frame.Target)`. The
validator does not "guess" between branches; the caller's runtime
knowledge is authoritative, and `FrameTypeForTarget` is the central
consistency check.

## Validator Contract

Anchor: `#ebus-validate-frame-addressing-v1`

Contract version: `ebus-validate-frame-addressing/v1`

The validator is invoked through `Frame.Validate` (a method on the existing
`protocol.Frame` struct). The legacy stand-alone signature
`ValidateFrameAddressing(ft, src, dst byte) error` is provided as a
private helper for unit testing and the `Frame.Validate` body; the
public surface is the method form.

```text
package protocol

var ErrInvalidFrameAddress = errors.New("ebus: invalid frame addressing for frame type")

// Validate reports whether the frame is well-typed.
// If FrameType is the zero value, FrameTypeForTarget(Target) is substituted
// and the result is also cross-checked: a non-zero FrameType set by the
// caller MUST match FrameTypeForTarget(Target).
func (f Frame) Validate() error
```

Bus.Send (in the eventbus / RawTransport adapter layer) MUST invoke
`frame.Validate()` at the top of its body, before any byte is committed
to the wire. On a non-nil error, Bus.Send returns it without writing to
the bus.

The validator MUST return `ErrInvalidFrameAddress` (or an `errors.Is`-wrapped
form thereof) when ANY of the following hold (with `ft` resolved as either
the explicit `Frame.FrameType` or `FrameTypeForTarget(Frame.Target)`):

1. `ft == FrameTypeUnknown` after fallback (i.e. `Target` is reserved
   `0xAA`/`0xA9`).
2. `src == dst` (`Frame.Source == Frame.Target`).
3. `ft == FrameTypeM2S` AND (`AddressClass(src) != Master` OR
   `AddressClass(dst) != Slave`).
4. `ft == FrameTypeM2M` AND (`AddressClass(src) != Master` OR
   `AddressClass(dst) != Master`).
5. `ft == FrameTypeM2BC` AND (`AddressClass(src) != Master` OR
   `dst != 0xFE`).
6. `Frame.FrameType` is non-zero AND `Frame.FrameType !=
   FrameTypeForTarget(Frame.Target)` (caller-vs-central-inference
   mismatch). EXCEPTION: for the runtime-target-branching service `03h
   10h`, this clause is the load-bearing check that the caller's branch
   choice (M2S vs M2M) is consistent with the actual target byte; both
   branches still pass clauses 3 and 4 individually because the dst byte
   is in the corresponding class.

The function MUST return `nil` when none of the rejection clauses hold AND
`ft` resolves to one of `{FrameTypeM2S, FrameTypeM2M, FrameTypeM2BC}`.

The validator MUST NOT consult the v1 source-address table tier or
free-use columns. It MUST NOT consult the gateway's admitted source. Both
those concerns are upper-layer policy, not protocol classification.

The validator MUST be a pure function of `(Frame.FrameType, Frame.Source,
Frame.Target)`: no state, no logging, no metrics. Bus.Send is responsible
for emitting `ErrInvalidFrameAddress` audit records on rejection.

### Test surface

`Frame.Validate` operates over the implicit space `4 (FrameType including
zero) × 256 × 256 = 262 144 cases`. Sampling per Phase C M-C4 covers:

- Boundary classes for each `ft`: at least one (`Master`, `Slave`,
  `Broadcast`, `Reserved`) `src` × each `dst` class.
- Pinned cases from the v1 table: `(M2S, 0x71, 0x08)` accept,
  `(M2S, 0x71, 0x10)` reject (dst is Master), `(M2M, 0x10, 0xF1)` accept,
  `(M2BC, 0x71, 0xFE)` accept, `(M2BC, 0x71, 0x08)` reject (dst is Slave).
- Zero-FrameType fallback cases: `(zero, 0x71, 0x08)` resolves to M2S
  accept; `(zero, 0x71, 0xF1)` resolves to M2M accept; `(zero, 0x71,
  0xFE)` resolves to M2BC accept; `(zero, 0x71, 0xAA)` resolves to
  Unknown reject.
- Caller-vs-central mismatch: `(M2BC, 0x71, 0x08)` rejects via clause 6
  AND clause 5 (dst is not 0xFE).
- Reserved-byte rejections: any case with `src == 0xAA`, `src == 0xA9`,
  `dst == 0xAA`, or `dst == 0xA9`.
- `FrameTypeUnknown` rejection AFTER fallback (only when `dst ∈
  {0xAA, 0xA9}`).
- Self-addressing rejection: `src == dst` for every `ft`.

## Hash Contract (taxonomy + frame-type contract)

Anchor: `#ebus-address-taxonomy-and-frame-type-contract-v1`

Hash algorithm: SHA-256 over the byte sequence formed by concatenating, in
order, the Markdown content of:

1. The `## 256-Byte Address Taxonomy` H2 heading line and all content up to
   (and not including) the `## Frame-Type Addressing Contract` H2 heading.
2. The `## Frame-Type Addressing Contract` H2 heading line and all content up
   to (and not including) the `## Validator Contract` H2 heading.
3. The `## Validator Contract` H2 heading line and all content up to (and not
   including) the `## Hash Contract (taxonomy + frame-type contract)` H2
   heading.

UTF-8 encoded, LF line endings, trailing spaces stripped per line, exactly one
terminal LF after the last included line.

Operator-runnable verification snippet (mirrors the shape of the existing
`scripts/check_source_address_table_against_official_specs.py`; lives at
`helianthus-docs-ebus/scripts/check_address_table_taxonomy_hash.sh` after
Phase C M-C0):

```bash
#!/usr/bin/env bash
# Recomputes the taxonomy + frame-type-contract hash from this file.
# Block boundaries: from `## 256-Byte Address Taxonomy` (inclusive) to
# `## Hash Contract (taxonomy + frame-type contract)` (exclusive),
# matching the prose algorithm above.
set -euo pipefail
file="${1:-architecture/ebus_standard/12-address-table.md}"
awk '
  /^## Hash Contract \(taxonomy \+ frame-type contract\)[[:space:]]*$/ {
    inblock = 0
  }
  inblock { print }
  /^## 256-Byte Address Taxonomy[[:space:]]*$/ { inblock = 1; print }
' "$file" | sed -E 's/[[:space:]]+$//' | shasum -a 256 | cut -d' ' -f1
```

The block hash is computed *post-edit* (i.e. when the three sections above
this one are frozen for a release). Phase C M-C0 acceptance requires the
hash recorded here to match the script output bit-for-bit.

Normalized hash:
`c19124aca8b42c1dcae659c37e7b21b20a4538dc7bc2bd785b5643b3f70503cc`

Computed from this file post-operator-freeze (Phase C M-C0 close;
hash recomputed under PR #297 thread `PRRT_kwDORGW9z86ATOzD`
follow-up after the awk extractor was corrected so the
`## Hash Contract` heading is excluded — matching the prose
algorithm above).
The validator CI script (post-M-C0) hard-fails if the script's
recomputed hash does not match this value — any subsequent edit
to the taxonomy / frame-type-contract / validator-contract blocks
above this one MUST be accompanied by a recompute + pin update.

Migration trail:

- v1 table hash (unchanged):
  `e78954445087f63064818ab60a2739b9a6b9bf0ae0147fbe92aac5ac76592103`.
- Taxonomy + frame-type-contract hash: NEW, computed at Phase C M-C0 close.

The two hashes are independent: amendments to the taxonomy section do NOT
invalidate the v1 table hash, and vice versa. CI MUST verify both hashes
independently against this file.

## Cross-References

- `helianthus-execution-plans/address-table-registry-w19-26.locked/14-phase-c-frame-type-transport.md`
  for the milestone breakdown that delivers `AddressClass`, `FrameType`,
  `RawTransport.Send(ft, ...)`, and `ValidateFrameAddressing`.
- `helianthus-docs-ebus/architecture/atr/03-ack-nack-insertion-rules.md` for
  the dual-meaning context of `0xFF` (Master at frame start vs NACK in ACK
  position) referenced by AD04.
- `helianthus-docs-ebus/architecture/atr/01-address-table-model.md` for the
  `AddressSlot` data model that consumes this taxonomy at the registry
  layer.

<!-- legacy-role-mapping:end -->
