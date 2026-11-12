# B531 local power projection boundary

The [native B531 candidate contract](../protocols/vaillant/ebus-vaillant-b531-hem-power-limit.md)
comes first. The finite companion scope is the AE23 minimum and maximum OP02
catalog declarations only; this page assumes no broader completed catalog.
OP02 is the B531 sub-command token, not a B524 opcode. The scope is the
heat-pump family, with no model or endpoint qualification.

This page describes representation and pure synthetic arithmetic only.
Nothing here is stable before 1.0. It adds no namespace or authorization gate.
The [synthetic numerical examples](../protocols/vaillant/fixtures/ae24_b531_candidates.json)
preserve both raw words independently, and the
[local projected values](fixtures/ae24_b531_local_projection.json) hold the
multiplied results outside the protocol tree. They are examples, not an artifact
schema or a decoder implementation.

## Local declarations

Hypothesis is the claim grade for the local projection and slot association.
Proven describes only the checked arithmetic of the synthetic examples below;
it never qualifies a native claim. W is metadata on a projected value only.

| Grade | Identity | Direction | Logical position / extent | Raw type / domain | Local transform / result domain | Projected metadata / native unit | Sentinel / default / conflict | Unresolved |
|---|---|---|---|---|---|---|---|---|
| Hypothesis | B531 OP02 minimum | local representation of candidate reply | first quantity / 2 octets; wire offset Unknown | unsigned LE16 / 0..65535 | multiply by 10 into u32 / 0..655350 | W / Unknown | FFFF remains numeric; default absent; no ordering rejection | endpoint support; native units; correlation; reply adaptation; cache freshness; target eligibility; applied limits: Unknown |
| Hypothesis | B531 OP02 maximum | local representation of candidate reply | second quantity / 2 octets; wire offset Unknown | unsigned LE16 / 0..65535 | multiply by 10 into u32 / 0..655350 | W / Unknown | FFFF remains numeric; default absent; no ordering rejection | endpoint support; native units; correlation; reply adaptation; cache freshness; target eligibility; applied limits: Unknown |

Each word is independent. Minimum greater than maximum remains in its
original order. FFFF has no established native sentinel and converts to
655350 locally; it is not treated as unavailable. The local transform
multiplies rather than divides by ten and does not use signed16.

## Synthetic arithmetic acceptance

These are independently stated expected results, with no physical observation.
Native unit remains Unknown in every case. Raw bytes are preserved beside
unsigned values and arithmetic results. No missing unit is filled from W.

| Case | Minimum raw | Maximum raw | Minimum unsigned | Maximum unsigned | Minimum local u32 | Maximum local u32 | Native unit | Arithmetic grade | Native grade |
|---|---|---|---|---|---|---|---|---|---|
| endpoints | 00 00 | FF FF | 0 | 65535 | 0 | 655350 | Unknown | Proven | Hypothesis |
| independent-order | 02 00 | 01 00 | 2 | 1 | 20 | 10 | Unknown | Proven | Hypothesis |
| minimum-only | 02 00 | FF FF | 2 | 65535 | 20 | 655350 | Unknown | Proven | Hypothesis |
| maximum-only | 00 00 | 01 00 | 0 | 1 | 0 | 10 | Unknown | Proven | Hypothesis |

Relative to endpoints, minimum-only varies only the minimum word;
maximum-only varies only the maximum word. The independent-order case
combines those alternatives to expose ordering enforcement.

## Separate local maximum-table declaration

Only the projected maximum is associated with a separate local per-slot
table. Its index domain is 0..8 inclusive. Nine is not an installed count;
this declaration establishes neither installed endpoints nor eligibility.
Minimum has no association with this table. No actual table or cache is
written by this slice.

| Grade | Example index | Index domain | Associated quantity | Value source | Default | Unresolved |
|---|---|---|---|---|---|---|
| Hypothesis | 0 | 0..8 inclusive | maximum only | projected maximum u32 | absent | endpoint support; cache freshness; target eligibility; applied limits: Unknown |
| Hypothesis | 8 | 0..8 inclusive | maximum only | projected maximum u32 | absent | endpoint support; cache freshness; target eligibility; applied limits: Unknown |

The two declaration examples vary only the index. Neither is a table write,
and neither establishes a cache entry's presence or freshness. Absent
metadata remains absent; no default, pair correlation or supported mapping
is inferred. No failed or partial observation is admitted as a fresh pair;
this slice adds no replacement path for prior last-known-good state.

## Applicability

Unknown: actual endpoint support, native units, correlation, reply adaptation,
cache freshness, target eligibility and applied limits. Synthetic correctness
cannot qualify physical behavior. No native quantity becomes supported merely
because its arithmetic fits u32.

This slice adds no poll, capability predicate, cache writer, publication path,
active executor or runtime API. Existing eBUS MCP compatibility and GraphQL
parity gain no new behavior from these declarations. Runtime adoption,
transport validation and independent physical qualification remain separate.
