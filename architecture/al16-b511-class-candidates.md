# B511 positive-class candidate representation

Read the public [native B511 contract](../protocols/vaillant/ebus-vaillant-b511.md#operating-data-classes-candidate)
first. That contract retains conflicting community and candidate interpretations,
including the unresolved relationship between the two OP07 reply descriptions.
This finite architecture contract follows the catalog prerequisite, which must
merge before this page. Its merge status is not established by these examples.
Refs [parent #736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736)
and [child #1025](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1025).

This page describes required library behavior, not an observed companion code
result. Candidate interpretations are **Hypothesis**. **Proven** is limited to
synthetic arithmetic and the explicitly declared representation shape; neither
proves a native meaning. Physical qualification, presence, freshness and execution
remain **Unknown**, independently of grade. No native effect or full parity is
claimed before its own checks. Nothing is stable before Helianthus 1.0.

## Library boundary

```go
func Ab50Entries() ([]Ab50Entry, error)
func Ab50Lookup(ab50Key Ab50Key) (Ab50Entry, bool, error)
```

`Ab50Entries` enumerates finite metadata, not installed devices or supported
profiles. `Ab50Lookup` compares the entire exact key. The representation retains
these identity axes without normalization, wildcarding, variant fallback or
inferred direction. Optional coordinates distinguish absence from explicit zero.

| Key field | Type | Identity rule |
| --- | --- | --- |
| Ab50Family | string | exact family |
| Ab50Variant | string | exact variant |
| Ab50Primary | uint8 | exact primary service |
| Ab50Secondary | *uint8 | absent differs from explicit zero |
| Ab50Operation | *uint8 | absent differs from explicit zero |
| Ab50Direction | *string | absent differs from a supplied direction |
| Ab50Field | string | exact field |
| Ab50Group | *uint8 | absent differs from explicit zero |
| Ab50RequestedInstance | *uint8 | absent differs from explicit zero |
| Ab50Register | *uint16 | absent differs from explicit zero |
| Ab50CommandRole | *string | absent differs from a supplied role |

For these examples family is `vaillant`, primary is `0xB5`, secondary is `0x11`,
direction is `positive`; group, requested instance, register and command role
are absent. Variant identifiers in the examples are synthetic controls, not
companion catalog names or native profile identifiers. OP00 is present zero,
never an absent operation. List order is not an offset or a lookup coordinate.

A well-formed absent key returns `Ab50Entry{}, false, nil`. Invalid catalog data
returns an error: enumeration yields no usable collection and lookup yields
`Ab50Entry{}, false, error`. Empty data, malformed or trailing JSON, unknown
fields, incomplete keys, invalid metadata and duplicate exact keys fail closed.
An admission failure must not replace a caller's independently retained
last-known-good result. Retained knowledge does not become fresh or authorize
execution. Unknown semantics alone do not erase raw evidence or independent
useful fields.

Every successful enumeration and lookup returns independent memory, including
key pointers, optional scalar pointers, slices, maps and nested contents. A
mutation cannot affect the catalog, another held result or a later call.
Grade, metadata presence, physical qualification, presence, freshness and
execution stay separate. This declaration does not establish runtime conformance.

## Bounded positive-class summaries

Every row below is **Hypothesis**. These are class-local field summaries, not a
second dictionary. Unprovided individual labels, widths, absolute positions and
per-variant defaults remain absent. The known LEu16 energy widths and explicitly
named flag-byte cardinalities do not supply offsets for any field.

| OP (hex) | Candidate field set and cardinalities |
| --- | --- |
| 00 | three flag bytes; optional second modulation |
| 01 | separate handshakes and forced-mode guards; warm-start bit5 only in applicable variants |
| 02 | status domain 0/1; DHW-enabled covers tank-loading/warm-start while tapping remains enabled |
| 03 | basic-state domain 0..6; two flag bytes; message domain 0..3; other labels Unknown |
| 04 | status and two temperatures |
| 05 | four setpoints and two status bytes |
| 06 | CH/DHW/pressure/cooling limits; raw status values 4/9/16 remain unlabelled |
| 07 | power percent; LEu16 energy kWh 0..9999; pump/status flags |
| 08 | volume percent and pump/status |
| 09 | LEu16 yield kWh 0..65535; power percent; activity/display/day-night |
| 0A | error/loading |
| 0B | fan/radiator/bypass/error/maintenance/assistant |
| 0C | operation domain 0..3 and switch-on flags |
| 0D | status/configuration |

Handshakes do not imply forced-mode guards, and neither establishes warm-start
applicability. Bit5 supplies no semantics in an inapplicable variant. Domain
membership supplies no individual label. In particular OP06 statuses 4, 9 and 16
have no invented text. OP03 message 3 differs from unlabelled 4; basic-state 6
differs from unlabelled 7. OP09 does not inherit OP07's 9999 bound or a sentinel.
Preserve unlabelled raw values without clipping or replacement.

## Synthetic controls

The [small JSON example set](fixtures/al16_b511_class_candidates.json) is not a
native profile or a full catalog. Each input is an explicitly supplied field
slice, not bytes located by a telegram parser. Scalar controls are synthetic
observations, not claims about field widths. Every `offset` is null; unspecified
`width_bits` and `default` are null. A supplied slice does not locate its field.

| Control | Field slice / scalar | Independent expected result |
| --- | --- | --- |
| OP07 energy upper | 0F 27 | 9999 kWh; inside candidate domain |
| OP07 energy outside | 10 27 | 10000 kWh; outside candidate domain; raw retained |
| OP09 yield maximum | FF FF | 65535 kWh; inside candidate domain; no sentinel |
| OP06 status controls | 4 / 9 / 16 | raw retained; each label Unknown |
| OP03 message controls | 3 / 4 | inside / outside; both labels Unknown |
| OP03 basic-state controls | 6 / 7 | inside / outside; both labels Unknown |
| OP01 applicability controls | bit5 set in applicable / inapplicable variant | candidate warm-start true / Unknown |
| OP07 incomplete energy | 0F | partial; no candidate number; raw retained |
| OP07 extra energy | 0F 27 00 | extra; no candidate number; raw retained |

The complete synthetic energy 9999 can remain a last-known-good candidate when
the next slice is incomplete or extra. The current slice and independently useful
power percent 25 survive separately; retained energy is not current evidence.
Out-of-domain 10000 remains a raw arithmetic value, never an admitted energy
candidate. An unknown label is not a missing raw observation. Fail-closed semantic
admission does not suppress evidence or grant write admission.

The [scoped unittest](../tests/test_al16_b511_class_candidates.py) checks these
declarations and synthetic controls without importing another repository. Its
local identity and arithmetic oracles do not execute the companion API. Physical
qualification, transport conformance and device smoke testing remain unverified.
Independent committed-change review, full Gate D and publication checks remain
later shipping requirements.

Existing request declarations, OP0F special-function membership, overlapping
positive extents and cache policies are outside this residual scope. No parser,
cross-repository runtime import, transmit route, polling default, automatic native
qualification or application integration is added. Existing eBUS MCP compatibility
and GraphQL parity remain requirements for later integration. No new major or
experimental namespace or authorization gate before 0.9 is introduced; roadmap
wording remains 0.11. Navigation and runtime integration are carried separately.
