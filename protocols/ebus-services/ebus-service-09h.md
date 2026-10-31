# eBUS Service 0x09 — Memory Server (Application Layer)

## Scope and evidence

The standard command layouts below are **Proven**. The separate bounded
synthetic candidate inventory covers only `0900`, `0901`, `0902` and `0903`.
It does not imply a complete family catalog. The historical RAM/EEPROM storage names do not establish a physical
memory space; a storage-name inconsistency must not change PB/SB service identity.
Other vendor variants and requester behavior remain separate and unqualified.

All field declarations in the bounded synthetic inventory are **Hypothesis**.
These 25 candidate declarations do not establish native behavior or installed
support. Synthetic examples do not qualify physical behavior or replace the
standard layouts. Provenance is not published.

## Service-mode restriction and security

**Proven:** all four `0x09` commands are restricted to service/maintenance mode;
devices should not support them during normal operation. `0x0901` and `0x0903` are memory-write
services. Exposing memory writes during normal operation risks uncontrolled
state modification. The hypothetical declarations below do not relax this
restriction or establish execution authority.

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`.
<!-- legacy-role-mapping:end -->

## Standard command layouts

**Proven:** these are the service-only Memory Server layouts. Offsets below are
zero-based within the payload, excluding PB/SB, length, CRC and ACK.

| Service | Standard name | Request payload | Response payload |
|---|---|---|---|
| `0x0900` | Read RAM | 0: address low; 1: address high; 2: count DN | 0..DN-1: data (DN bytes) |
| `0x0901` | Write RAM | 0: address low; 1: address high; 2..: data | Empty (response NN=0) |
| `0x0902` | Read EEPROM | 0: address low; 1: address high; 2: count DN | 0..DN-1: data (DN bytes) |
| `0x0903` | Write EEPROM | 0: address low; 1: address high; 2..: data | Empty (response NN=0) |

**Proven:** read requests have NN=3; DN has nominal range 0..10, with DN>10
permitted in service mode. Addresses are low-byte-first, 16-bit; device-specific
address meanings and physical storage remain **Unknown**.

**Unknown:** write-data count: NN counting from M7 (high address byte),
bounded 1..8, conflicts with data rows enumerating Data Byte 0 through NN-1. These imply NN-1 versus NN data bytes; the ambiguity is retained.
The final EEPROM write block may have NN<10. An empty standard write response
alone does not prove persistence or execution on a device.

## Bounded direction declarations

Identity is PB `09` plus the SB encoded in the last two digits of the service,
direction and field. An operation discriminator is absent. Request and positive
are abstract directions, not observed peer traffic. A logical position is not a
wire offset. All physical positions in this inventory are Unknown. In particular,
an abstract positive prefix does not establish physical response positions. `unset` means
metadata is absent, not zero, a sentinel, a default or an inferred scale.

| Grade | Service | Direction | Field | Logical position | Extent (bytes) | Raw type / domain | Scale | Sentinel / default / conflict | Unresolved |
|---|---|---|---|---|---|---|---|---|---|
| Hypothesis | 0900 | request | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0900 | request | SB | 1 | 1 | byte / SB=00 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0900 | request | address | Unknown | 2 | unsigned LE16 / 0..65535 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0900 | request | count | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0900 | positive | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0900 | positive | SB | 1 | 1 | byte / SB=00 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0900 | positive | data | 2 | to end-of-data; min 0; max unset | opaque / no defined unit or enum | unset | sentinel unset; default unset; conflict unset | physical position and packet extent Unknown; empty does not establish success |
| Hypothesis | 0901 | request | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0901 | request | SB | 1 | 1 | byte / SB=01 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0901 | request | address | Unknown | 2 | unsigned LE16 / 0..65535 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0901 | positive | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown; prefix-only; no body or success claim |
| Hypothesis | 0901 | positive | SB | 1 | 1 | byte / SB=01 | unset | sentinel unset; default unset; conflict unset | physical position Unknown; prefix-only; no body or success claim |
| Hypothesis | 0902 | request | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0902 | request | SB | 1 | 1 | byte / SB=02 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0902 | request | address_low | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0902 | request | address_high | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0902 | request | count | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; candidate max 10 conflicts with formal 255 | logical and physical positions Unknown |
| Hypothesis | 0902 | positive | data | 0 | to end-of-data; min 0; max unset | opaque / no defined unit or enum | unset | sentinel unset; default unset; conflict unset | physical position and packet extent Unknown; empty does not establish success |
| Hypothesis | 0903 | request | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0903 | request | SB | 1 | 1 | byte / SB=03 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0903 | request | address_low | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0903 | request | address_high | Unknown | 1 | u8 / 0..255 | unset | sentinel unset; default 0; conflict unset | logical and physical positions Unknown |
| Hypothesis | 0903 | positive | PB | 0 | 1 | byte / PB=09 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0903 | positive | SB | 1 | 1 | byte / SB=03 | unset | sentinel unset; default unset; conflict unset | physical position Unknown |
| Hypothesis | 0903 | positive | data | 2 | to end-of-data; min 0; max unset | opaque / no defined unit or enum | unset | sentinel unset; default unset; conflict unset | physical position and packet extent Unknown; empty does not establish success |

The `0900` and `0901` address example `34 12` denotes 4660 in the unsigned
LE16 alternative. For `0902` and `0903`, it retains independent low=52 and
high=18 bytes; address equivalence is Unknown. Request positions beyond PB/SB
are unprovided in this inventory. Its omission of request data is not an
address-only standard write layout; both standard write requests include data
as shown above. The fixture represents only these bounded alternatives.

Positive `0900` and `0903` place opaque `AA 55` at abstract position 2 after
PB/SB; `0902` places the same data at 0 without PB/SB. There is no universal
prefix-stripping rule. Positive `0901` is prefix-only and declares neither a
body nor successful execution. Empty opaque data is preserved without claiming
success or acceptance. The raw counts 0, 10, 11 and 255 remain intact; the
`0902` candidate maximum 10 and formal maximum 255 remain conflicting claims.

[Synthetic direction examples](fixtures/ae28_09_candidates.json) preserve these
alternatives and absent metadata. They are examples of declarations, not packet
captures or evidence of peer effects.

## Vaillant family variants

**Hypothesis:** candidate layouts for `0x0900`–`0x0902` and the `0x0903`
request follow the standard layout. Whether the `0x0903` reply is always empty
remains **Unknown**.
These candidate layout comparisons do not resolve the direction alternatives
or physical positions declared above.

**Hypothesis:** candidate requester contexts without a preceding service-mode
step are `0x0902` with `NN=3`, address `0x0000` and count 9 toward a remote
room-control family, and `0x0903` with `NN=3` and one data byte toward a
system-control family. Target acceptance outside service mode remains
**Unknown**; these candidates do not override the service-mode restriction.
Provenance is not published.

## Open questions

**Unknown:** physical memory space, peer effects, address equivalence, actual
packet extent, empty-request acceptance and installed support. Unprovided
request positions in the synthetic inventory remain Unknown. Storage names do
not resolve these questions.
No service-mode rule or execution authority follows from these declarations.
No memory reader/writer or verification client is defined here.

## See Also

- [`ebus-application-layer.md`](./ebus-application-layer.md) — service index
- [`ebus-overview.md`](./ebus-overview.md) — wire-level framing
