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

The existing typed zone, DHW, and system GraphQL objects are eBUS-typed
native views. The gateway does not add a parallel eeBUS object tree, and these
objects are not the common model. The projection is constrained to the exact
manifest paths and value kinds.

### One Resource Per Target Object

Each target object stands for one canonical resource of the common model. The
manifest member `resources` records, for each target, the common resource kind,
the candidate sources from both protocols with the public document that holds
their native evidence, and the identity basis:

| Target | Common resource kind | eBUS candidate | eeBUS candidates |
|---|---|---|---|
| `zones[id=zone-1]`, `zones[id=zone-2]` | `resource.zone` | the B524 zone instance behind the row (`OP=0x02 GG=0x03`) | the SPINE `HVACRoom` entity and the SPINE `HeatingZone` entity |
| `dhw` | not decided | the B524 native hot-water group (`OP=0x02 GG=0x01 II=0x00`) | the SPINE `DHWCircuit` entity |
| `system` | `resource.thermal_system` | the system group of the B524 semantic root (`OP=0x02 GG=0x00 II=0x00`) | the SPINE `TemperatureSensor` entity with outside-air scope and the SPINE `DeviceInformation` entity |

Each candidate keeps its own binding and provenance. Neither protocol's value
replaces the other's inside the resource.

The two protocols' views are one resource only when the mapping records an
accepted identity basis (manifest member `identity_bases`):

- `operator_declaration`: the operator gives both views one shared parent and
  slot; for a zone, the same operator-declared thermal system and the same
  slot;
- `shared_native_anchor_key`: both views carry the same native anchor key; the
  mapping records the identification scheme, the issuer and the shared key
  value, so a validator can tell one shared key from two keys of a
  compatible format.

An ordinal, a shared digit in a path or label, a bundle-local slot label, a
similar name, and a bus or network address are never a basis. A mapping
without an accepted basis is `unresolved`, and its candidates are not merged:
the two views stay separate resources.

Every mapping in this manifest is `unresolved`. No published evidence shows a
native anchor key shared by the B524 resource and the eeBUS entities; the
eeBUS slot labels are local to their bundle; no observed relation joins a
`HeatingZone` entity to an `HVACRoom` entity; and an operator declaration
belongs to one installation, not to this contract. Each leaf row carries the
basis of its target in `identity_basis`. The semantic path segment `zone_1` and
the GraphQL id `zone-1` are public names of two views; their shared digit is
not an identity link.

Which common resource kind a hot-water value describes is not decided here:
the element inventory holds the hot-water kind as `unknown`. A mapping decides
identity only. This page places no leaf value, and no thermal quantity, on a
common resource; the subject of each value is decided by the element inventory
and the native owners.

### Target Policy `FILL_MISSING_ONLY`

`FILL_MISSING_ONLY` is the policy that one named target, the eBUS-typed
GraphQL roots `zones`, `dhw`, and `system`, declares over the candidates of one
resource (manifest members `projection_policy_target` and
`projection_policy_scope`). It is not the internal merge: the resource keeps
every candidate with its binding and provenance, and another target may declare
another policy over the same candidates.

For a resource whose identity basis is accepted, the target presents:

- a non-null value of the eBUS candidate byte-for-value as before M9;
- a value of an eeBUS candidate only for an absent field listed in the
  manifest;
- eeBUS-native capability and metadata rows for fields that have no eBUS
  producer.

For an `unresolved` resource the target presents no eeBUS candidate value.
The policy does not compare timestamps, choose the freshest source, retain a
stale value, or define platform-wide source precedence. A failed or
disconnected eeBUS refresh withdraws the eeBUS candidates' values from the
target. It never erases a value of the eBUS candidate.

The policy keeps the established eBUS API unchanged. General freshness and
source selection belong to the common model, not to this target. The gateway's
present overlay still joins the two views by the zone ordinal; this contract
does not accept that join, and the gateway slice that replaces the overlay
follows this page.

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

The zone rows share schema fields. A zone leaf's GraphQL path names the
eBUS-typed row it fills, `zones[id=zone-1]` or `zones[id=zone-2]`, and it fills
that row only when the row's zone mapping records an accepted identity basis.
The projection must not rename or duplicate a zone. Code tests and GraphQL
snapshots must prove that the pre-M9 ids remain exact.

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
heater, and sensor unique ids. Cross-protocol leaves reach existing semantic
entities only through the GraphQL target and its `FILL_MISSING_ONLY` policy,
and only for a resource with an accepted identity basis; they do not create
protocol-prefixed duplicates. Gateway brand/vendor and the deterministic source-label pseudonym
are metadata, not standalone entities; the existing zone `name` and identity
remain unchanged. Capability booleans are diagnostic attributes until a separately
approved command contract exists. `overrun_active` may be a read-only binary
sensor because it is an observed state, not a command.

Zone-parent resolution preserves device continuity across a temporarily sparse
eBUS radio inventory. A live radio match is authoritative. If no live match is
available for a zone whose mapping selects a radio controller, Home Assistant
may retain only a persisted binding for that same config entry, climate unique
id, Helianthus radio identifier, and validating radio mapping. The unreleased
pre-V1 registry attachment is not sufficient provenance and must not bootstrap
the binding automatically. A lab or operator migration must write a binding only
from separately archived live evidence. Later reloads use the persisted mapping
rather than infer a new one from registry attachment. Retention is allowed only
when the coordinator explicitly marks the current inventory snapshot incomplete;
a complete snapshot with no match leaves the zone unresolved. The fallback
cannot create a parent for a new unresolved zone, use a non-radio device, or
override a changed mapping. When a later live radio match resolves a different
physical parent, the live mapping replaces and persists over the retained one
before the config entry reloads for re-parenting.

## Acceptance

M9 is complete only when:

- schema and value snapshots cover all eighteen paths;
- no retired, candidate, conflicted, withheld, or unlisted path is exposed;
- eeBUS disconnect removes only values of eeBUS candidates;
- pre-M9 eBUS GraphQL, Portal, and Home Assistant snapshots remain unchanged
  where eBUS already supplied a value;
- `zone-1` and `zone-2` remain the only two target identities, and raw
  `userLabel` values are absent from every public snapshot;
- every target maps to one resource whose identity basis is recorded, and no
  eeBUS value reaches a target whose mapping is `unresolved`;
- Portal and Home Assistant consume GraphQL, never owner-only MCP;
- add-on restart preserves eeBUS trust and restores the promoted projection;
- code-repository tests enforce the manifest and public anti-leak boundary.

Any live re-validation of these mappings belongs to an owner-approved hardware
session; this page asks for no device action.
