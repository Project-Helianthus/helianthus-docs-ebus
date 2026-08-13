# Promoted Semantic Consumers V1

Status: unreleased V1 contract for MSP-09A through MSP-09D.

## Scope

This contract exposes the eighteen semantic leaves locked by the final
MSP-085 live campaign. It does not reopen promotion, evaluate new candidates,
or make raw SHIP/SPINE data public. The canonical leaf inventory is
[`manifests/promoted-semantic-consumers-v1.json`](./manifests/promoted-semantic-consumers-v1.json).

Consumer rollout remains ordered:

1. gateway GraphQL parity;
2. gateway Portal rendering;
3. Home Assistant integration;
4. add-on packaging and live acceptance.

All eighteen rows remain read-only in V1. A promoted setpoint or operating
mode is observable data, not permission to add a mutation or command route.

## Projection Boundary

The gateway projects eeBUS values into the existing typed zone, DHW, and
system GraphQL objects. It does not add a parallel eeBUS object tree. The
projection is constrained to the exact manifest paths and value kinds.

The coexistence rule is `FILL_MISSING_ONLY`:

- an existing non-null eBUS semantic value is returned byte-for-value as
  before M9;
- eeBUS may fill only an absent field listed in the manifest;
- eeBUS-native capability and metadata rows fill fields that have no eBUS
  producer;
- the rule does not compare timestamps, choose the freshest source, retain a
  stale value, or define platform-wide source precedence;
- a failed or disconnected eeBUS refresh clears the eeBUS overlay. It never
  erases a value owned by the existing eBUS provider.

This narrow compatibility rule preserves the established eBUS API while a
future protocol-neutral semantic owner may define general freshness and
source-selection policy.

## GraphQL Contract

Existing query roots remain unchanged: `zones`, `dhw`, and `system`. Existing
fields carry the eleven cross-protocol leaves. M9A adds only these fields:

| GraphQL field | Type | Nullability | Semantic path |
|---|---|---|---|
| `dhw.state.overrun_active` | `Boolean` | nullable | `/dhw/overrun_active` |
| `dhw.config.operation_mode_changeable` | `Boolean` | nullable | `/dhw/operation_mode_changeable` |
| `zones[].config.operation_mode_changeable` | `Boolean` | nullable | zone-specific capability path |
| `system.gateway_brand` | `String` | nullable | `/system/gateway_brand` |
| `system.gateway_vendor` | `String` | nullable | `/system/gateway_vendor` |

The zone rows share schema fields and are bound by a closed identity map:
semantic `zone_1` targets the existing GraphQL id `zone-1`, and semantic
`zone_2` targets `zone-2`. The projection must not rename or duplicate a zone.
Code tests and GraphQL snapshots must prove that the pre-M9 ids remain exact.

The two promoted eeBUS `userLabel` leaves do not replace the existing non-null
`zones[].name`. They project to nullable `zones[].config.source_label` only
after the transform `STABLE_ZONE_PSEUDONYM`. The transform ignores the raw
label bytes and emits `Zone 1` for `zone-1` and `Zone 2` for `zone-2`; no
caller-selected salt, hash, or label text participates. This preserves the
fact that an eeBUS label exists for the promoted semantic path without
disclosing household naming. The raw `userLabel` remains owner-only MCP data.
All new names are snake_case only because this is an initial, unreleased
surface; no compatibility aliases are needed.

Null means no current producer supplied the field. Numeric values use GraphQL
`Float` after the exact decimal normalization already locked by MSP-085.
Temperature units remain `degC`; GraphQL field names carry the public Celsius
unit convention used by the existing semantic API.

## Public Safety

GraphQL, Portal, and Home Assistant may contain semantic paths, normalized
values, units, and deterministic zone pseudonyms. They must not contain:

- candidate ids, dossier hashes, `candidate_ref`, or promotion internals;
- SKI, SHIP id, certificate material, or trust-store bytes;
- SPINE device/entity/feature addresses, raw `userLabel`, or function payloads;
- eBUS selectors, source addresses, or raw frames;
- private keys, tokens, or other cryptographic secrets.

The owner-only raw MCP remains the inspection surface for protocol identity
and raw evidence. Public consumer payloads are semantic projections only.

## Portal And Home Assistant

Portal renders the same typed GraphQL values and distinguishes unavailable
fields from false, zero, or an empty string. It may link an authorized operator
to the raw MCP workbench, but it does not embed raw identity in public HTML or
REST payloads.

Home Assistant preserves existing config-entry, device, zone, climate, water
heater, and sensor unique ids. Cross-protocol leaves enrich existing semantic
entities through `FILL_MISSING_ONLY`; they do not create protocol-prefixed
duplicates. Gateway brand/vendor and the deterministic source-label pseudonym
are metadata, not standalone entities; the existing zone `name` and identity
remain unchanged. Capability booleans are diagnostic attributes until a separately
approved command contract exists. `overrun_active` may be a read-only binary
sensor because it is an observed state, not a command.

Zone-parent resolution preserves device continuity across a temporarily sparse
eBUS radio inventory. A live radio match is authoritative. If no live match is
available for a zone whose mapping selects a radio controller, Home Assistant
may retain only a persisted binding for that same config entry, climate unique
id, Helianthus radio identifier, and validating radio mapping. The unreleased
pre-V1 migration may seed this binding once from an existing association because
the prior implementation could attach a climate to a radio device only after a
live match. Later reloads must use the persisted mapping rather than infer a new
one from registry attachment. Retention is allowed only when the coordinator
explicitly marks the current inventory snapshot incomplete; a complete snapshot
with no match leaves the zone unresolved. The fallback cannot create a parent
for a new unresolved zone, use a non-radio device, or override a changed mapping.
When a later live radio match resolves a different physical parent, the live
mapping replaces and persists over the retained one before the config entry
reloads for re-parenting.

## Acceptance

M9 is complete only when:

- schema and value snapshots cover all eighteen paths;
- no retired, candidate, conflicted, withheld, or unlisted path is exposed;
- eeBUS disconnect removes only overlay-owned values;
- pre-M9 eBUS GraphQL, Portal, and Home Assistant snapshots remain unchanged
  where eBUS already supplied a value;
- `zone-1` and `zone-2` remain the only two target identities, and raw
  `userLabel` values are absent from every public snapshot;
- Portal and Home Assistant consume GraphQL, never owner-only MCP;
- add-on restart preserves eeBUS trust and restores the promoted projection;
- code-repository tests enforce the manifest and public anti-leak boundary.
