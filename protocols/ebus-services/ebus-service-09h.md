# eBUS Service 0x09 — Memory-service direction alternatives

> Source: eBUS Specification Application Layer (OSI 7) V1.6.1, §3.5 (service naming context).

## Scope and evidence

This bounded declaration covers only `0900`, `0901`, `0902` and `0903`,
matching the finite AE27 companion catalog. It does not imply a complete family
catalog. The historical RAM/EEPROM storage names do not establish a physical
memory space; a storage-name inconsistency must not change PB/SB service identity.
Other vendor variants and requester behavior remain separate and unqualified.

All field declarations below are **Hypothesis**. For these declarations,
**Proven** applies only to the
presence of these finite declarations in the companion, not to native behavior
or installed support. Synthetic examples do not qualify physical behavior.
The specification citation supplies naming and service-mode context; the supplied
direction alternatives and corroborating catalog are not reproducible wire observations.

## Service-mode restriction and security

**Proven:** the eBUS Specification Application Layer (OSI 7) V1.6.1, §3.5
restricts all four `0x09` commands to service/maintenance mode; devices should
not support them during normal operation. `0x0901` and `0x0903` are memory-write
services. Exposing memory writes during normal operation risks uncontrolled
state modification. The hypothetical declarations below do not relax this
restriction or establish execution authority.

## Terminology

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`.
<!-- legacy-role-mapping:end -->

## Bounded direction declarations

Identity is PB `09` plus the SB encoded in the last two digits of the service,
direction and field. An operation discriminator is absent. Request and positive
are abstract directions, not observed peer traffic. A logical position is not a
wire offset. All physical positions are Unknown. In particular, positive-prefix
relevance to PeBUS does not establish physical response positions. `unset` means
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
are unprovided. No request data declaration is supplied by this finite scope.

Positive `0900` and `0903` place opaque `AA 55` at abstract position 2 after
PB/SB; `0902` places the same data at 0 without PB/SB. There is no universal
prefix-stripping rule. Positive `0901` is prefix-only and declares neither a
body nor successful execution. Empty opaque data is preserved without claiming
success or acceptance. The raw counts 0, 10, 11 and 255 remain intact; the
`0902` candidate maximum 10 and formal maximum 255 remain conflicting claims.

[Synthetic direction examples](fixtures/ae28_09_candidates.json) preserve these
alternatives and absent metadata. They are examples of declarations, not packet
captures or evidence of peer effects.

## Vaillant variants

**Hypothesis:** the service catalog records `0x0900`–`0x0902` and the `0x0903`
request as following the standard
layout. Whether the `0x0903` reply is always empty remains **Unknown**.
These historical layout comparisons do not resolve the direction alternatives
or physical positions declared above.

**Hypothesis:** the catalog also records a Vaillant requester issuing `0x0902`
and `0x0903` without a preceding service-mode step. Target acceptance outside
service mode remains **Unknown**; requester behavior does not override the
specification's service-mode restriction.

## Open questions

**Unknown:** physical memory space, peer effects, address equivalence, actual
packet extent, empty-request acceptance and installed support. Unprovided
request positions remain Unknown. Storage names do not resolve these questions.
No service-mode rule or execution authority follows from these declarations.
No memory reader/writer or verification client is defined here.

## Sources

The independently merged [AE27 companion catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/ebus_standard/testdata/ab79_09_candidates.json)
corroborates only the 25 declarations in the table. Catalog presence does not
prove a native wire contract or qualify installed support.

## See Also

- [`ebus-application-layer.md`](./ebus-application-layer.md) — service index
- [`ebus-overview.md`](./ebus-overview.md) — wire-level framing
