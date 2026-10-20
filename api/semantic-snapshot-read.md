# Shared SemReg snapshot read

Status: target contract for the ordinary GraphQL and MCP surfaces; runtime
exposure and parity tests remain separate implementation work. All MCP
namespaces are pre-stable until 1.0 under [the MCP policy](mcp.md#current-status).
This page defines a Helianthus API projection, not native protocol semantics.

## Ownership and entry points

The one shared read view serves PV, Storage, EVSE, Thermal and Infrastructure.
It reads existing SemReg state without acquisition, publication, native decoding
or operation dispatch. These additive entry points use the same detached view:

| Surface | Target entry point | Selection |
| --- | --- | --- |
| Ordinary GraphQL | `semanticSnapshot(assetIds: [ID!]!): SemanticSnapshotRead` | Required opaque asset IDs. |
| MCP | `semantic.v1.snapshot.get` | Required `asset_ids` array. |

`semantic.v1.*` already contains the SemReg-backed
`semantic.v1.pv.current.get`. The new cross-pack tool belongs there rather than
reusing the legacy `ebus.v1.semantic.snapshot.get`. No new namespace is needed.
The ordinary GraphQL root is camelCase and additive to the schema described in
[graphql.md](graphql.md). It does not broaden the separate
[machine-to-machine contract](../docs/platform/public-graphql-m2m-v1.md).
Neither new entry point is implemented merely by publishing this page.

The existing SemReg-backed tools are `semantic.v1.pv.current.get`,
`semantic.v1.evse.current.get` and `semantic.v1.storage.growatt.current.get`
(PV/inverter, EVSE and Growatt storage/BMS families). Their names are established
by the gateway's [PV registration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/modbus_v1.go),
[EVSE registration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/tesla_gen3_evse_semantic.go)
and [storage registration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/growatt_storage_semantic.go).
These tools and the legacy eBUS semantic tools, their envelopes, names and
behavior remain until their separately reviewed migration. This inventory does
not establish exposure through the shared endpoint. The inventory and
`EVALUATED_SEMREG_PUBLICATION` are not yet documented in api/mcp.md; that page's
inventory integration is separate work. This contract introduces no
authorization gate, namespace graduation or stability promise.

The semantic owner is the public
[kernel contract](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/kernel.md)
and its
[serialization contract](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/serialization.md).
The concrete member names and types used here follow
[SemReg types](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/types.go)
and
[projection types](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/projection/types.go).
Native meaning must first be supported by the corresponding public native
documentation; these API records neither decode nor strengthen it.

## Selection and one request read point

1. Require 1–32 distinct asset IDs, each at most 256 UTF-8 bytes and valid as
   SemReg `AssetID`. Reject duplicates, nulls, unknown arguments, wildcards,
   native locators and empty selection as `INVALID_ARGUMENT`. IDs are compared
   byte-for-byte, without trimming, case folding or protocol interpretation.
2. Detach the selected state once from the shared hub at one coherent read
   point. All GraphQL aliases in one operation share that capture and one
   evaluation context; take the union of their selected IDs before capture.
   The operation-wide union also has the 32-asset bound. MCP captures once per
   tool call. Separate requests can legitimately observe later publications.
3. A SemReg `Snapshot` is complete **per asset**, not a global revision. Each
   returned asset therefore carries its own `snapshot_id` and all five
   `revisions` components. Never invent a global SemReg revision or require
   different assets' revision numbers to match. Capture publication pointers
   coherently; sequential independent reads that can straddle a publication
   boundary do not meet this contract.
4. Evaluate each captured snapshot with the same explicit `EvaluationContext`.
   Serialize this immutable result, not resolver-time clock reads. Capture the
   pack-definition catalog used for projection with the view too. The detached
   objects cannot observe later hub, registry or caller mutation.
5. Return one entry for every selected asset, including an unknown or
   unavailable asset. An unavailable sibling does not erase a readable
   last-known-good asset. No on-demand native probe repairs a missing asset.
6. Bound the complete serialized shared view to 4 MiB, before GraphQL field
   selection or MCP wrapping. Kernel and projection collection limits also
   apply, including 32 source keys per disposition. Overflow
   fails the whole read with `RESOURCE_EXHAUSTED`; no truncation, pagination
   across changing snapshots or successful partial dump is allowed. Clients
   can explicitly request fewer assets in a new request.

The 32-source-key limit is the present bounded **all-or-error** contract, even
when only one disposition exceeds it. The complete accounting must fit the
projection contract; returning the first 32 keys would hide alternatives or
join dimensions incorrectly. An asset-unavailable entry or `INTERNAL` would be
a different wire error policy, not a clarification. Reducing selected assets
can resolve aggregate size overflow but cannot repair one over-bound asset.

Within one asset, snapshot, evaluation, projection and any selection must bind
the identical snapshot ID and complete revision vector. Candidate references
also bind exact candidate revisions. Validate this before exposure. A mismatch
fails the entire read with `CONFLICT`; never splice an older fact, newer
capability or a cached evaluation into a superficially consistent response.

The read does not change publication rules: an omitted field in a valid partial
publication retains its prior value and original aging policy; a rejected
publication changes nothing. Reading must preserve that state, alternatives,
conflicts, generation fences and source-retirement tombstones. Historical
retained observations remain separate from current facts and never become
selection input, capability admission, route authority or operation evidence.

## Shared view records

The transport-neutral view has one required member, `assets`, an array of
`AssetSnapshotRead`. The following are API wrapper members; they are not new
members of SemReg `Snapshot`:

| Member | Type and presence | Meaning |
| --- | --- | --- |
| `asset_id` | `AssetID`, required | The selected opaque asset identity, including on failure. |
| `snapshot` | `Snapshot`, optional | Complete, unchanged public-safe source snapshot. Never a filtered object labeled as a kernel snapshot. |
| `evaluation` | `EvaluationView`, optional | Complete pure time evaluation of that snapshot. |
| `projection` | `ProjectionReport`, optional | Explicit per-item accounting for this read target. |
| `selections` | `Selection[]`, required | Presentation-only results, or `[]` when no existing selection policy is configured. |
| `unavailable_reason` | string code, optional | Why the asset cannot supply a snapshot read; never a native locator or raw error text. |

A readable entry has `snapshot`, `evaluation` and `projection` together, and no
`unavailable_reason`. A missing asset has none of those three, `selections: []`
and `unavailable_reason: "semantic.read.reason.asset_unknown"`. An asset with no
accepted publication uses `semantic.read.reason.snapshot_unavailable`. A read
gate closed by source lifecycle controls uses
`semantic.read.reason.source_unavailable`; do not bypass it using cached state.
An unwired provider fails the whole request with `UNAVAILABLE`, rather than
fabricating empty snapshots. These `semantic.read.reason.*` codes belong to
this API wrapper, not to the native owner or SemReg family catalog. The
surface-owned codes are exactly: `asset_unknown`, `snapshot_unavailable`,
`source_unavailable`, `publication_withheld`, `capability_unqualified`,
`capability_unknown`, `capability_unavailable`, `fact_unavailable` and
`value_unknown`; any other reason is the owning contract's code, preserved
verbatim.

Opaque `AssetID`, `NativeBindingID`, `SnapshotID`, candidate, source, epoch and
instance IDs are references, not addresses or routing instructions. The view
preserves `snapshot.bindings`, `identity_links`, `sources`, `facts`, `services`,
`capabilities`, `fences` and `cursors` using the SemReg types verbatim.
`Snapshot.Retained` and `EvaluationView.Retained` both serialize under
`retained_observations` when present; use their current Go types
`RetainedObservationRecord` and `EvaluatedRetainedObservation`, respectively.

No raw native locator, private symbol/text, credential, serial, address or
private evidence body may cross this surface. `EvidenceRef` preserves `owner`,
`kind`, `digest`, `contract`, `access` and `redaction`; it is not permission to
dereference evidence. Preserve access/redaction markers without disclosing the
underlying material. Native raw evidence stays with its owner beside the
interpretation. Opaque identifiers and dimensions must themselves be public-safe.

Validate the whole source snapshot for public exposure before serializing it.
Apply the [kernel snapshot rules](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/kernel.md#type-snapshot)
(`Snapshot.Validate()`), including references, revisions, evidence access and
redaction; in particular, restricted evidence with `redaction: "none"` cannot
appear in a public snapshot. Then check every opaque ID and dimension for
public safety: syntactic validity alone does not prove that a string conceals
no serial, private address or private text. The provider must establish these
checks before capture; the pure shared-view builder assumes public-safe input.
This is an exposure requirement, not a claim that the builder discovers secrets.
If it cannot be exposed intact, withhold the **whole asset entry** with
`semantic.read.reason.publication_withheld`, the same shape as other unavailable
entries. Do not strip records, rewrite evidence or recompute an ID and claim it
is the source snapshot. Other public-safe asset entries remain readable. This
conservative boundary avoids silently leaking an unsafe candidate through an
otherwise withheld projection. It adds no consumer authorization mechanism.

## Scalars, presence and quality

Use `Value.kind` as the discriminator. Exactly its matching member is present:
`quantity`, `boolean`, `text`, `symbol`, `symbols` or `time`. Pack validators
still determine which kind is legal for a particular fact. Status symbols must
not be relabeled as booleans for convenience.

| Case | Required representation and interpretation |
| --- | --- |
| Quantity | `Quantity.number` is `Decimal` with string `coefficient` and integer `exponent10`; `unit` is a definition ID. No floating-point intermediate or display-unit conversion. |
| Zero | Canonical decimal `{"coefficient":"0","exponent10":0}` is a present exact value. Nonzero coefficients have no leading or trailing zero; exponent is in -18 through 18. |
| False | `{"kind":"boolean","boolean":false}` is present, where the pack admits a boolean. |
| Empty text | `{"kind":"text","text":""}` is present, where admitted. It is not an absent pointer. |
| Empty collection | Required record arrays use `[]` for a known empty collection. `Value.symbols` requires 1–64 entries; an empty symbol value is invalid, not unknown. |
| Absent value | `FactCandidate.value` is omitted in MCP; requested nullable GraphQL `value` resolves to `null`. Preserve quality and reasons. Never substitute zero, false, empty text or an empty array. |
| Unknown symbol | Keep `Symbol.namespace`, `token` and `known: false` where public-safe and admitted. Unknown native tokens do not become known pack symbols. |
| Integer/time | `Uint64`, `Int64`, all revisions, generations and `TimePoint` nanoseconds/uncertainty are decimal strings. Preserve `clock_id` and monotonic `clock_epoch_id`; no RFC3339 replacement inside SemReg records. |

SemReg records reject explicit JSON null; optional MCP members are omitted.
GraphQL nullable object fields use GraphQL null semantics, while a field not
selected by the query is simply absent from the GraphQL response. A consumer
must request quality, evaluation and projection metadata to distinguish unknown,
withheld, unsupported and unavailable values. A transport failure is not an
unknown fact. Required arrays and quality axes must never default on decode.

Copy all `Quality` axes independently: `assertion` (`observed`, `inferred`),
`qualification` (`candidate`, `qualified`, `unsupported`, `unknown`, `rejected`),
`promotion`, `validity`, `availability`, `freshness` and `reasons`. The documentary
evidence labels **Proven**, **Hypothesis** and **Unknown** are separate from
these machine fields. Neither an observed assertion nor a fresh value proves
qualification, promotion or write authority.

Keep original candidate `quality`, `times` and `freshness_policy` immutable.
Current freshness and effective availability come from
`evaluation.facts[].freshness` and `effective_availability`, joined by
`candidate_id` and `candidate_revision`. Preserve the evaluation context, digest
and original deadlines. Freshness can change without changing publication
revisions. Incomparable clocks yield the kernel's conservative unknown result;
the adapter must not reset receipt time or make stale evidence fresh.

## Projection accounting and deterministic order

For each readable asset construct a SemReg `ProjectionReport` with
`contract: "helianthus.semantic.projection/v1"`. Its manifest uses
`target_id: "target:semantic-snapshot-read"`, `target_version: "1"`,
`kernel_version: "helianthus.semantic.kernel/v1"`, the exact applicable
`pack_versions`, and decimal-string `mapping_revision: "1"` for this mapping.
Applicability comes from pack references in the captured facts, service and
capability definitions, not a guessed protocol/model name.

`requested` includes each declared fact and capability definition from those
packs once as `(kind,item_id)`, including definitions absent from the snapshot.
It also accounts for any source fact/capability definition not understood by the
target. It does not assert that every asset implements every pack. Services,
identity and lifecycle records are copied intact with the source snapshot;
this read target performs no service/relation or operation mapping.

Every requested tuple has exactly one `ProjectionDisposition` with the same
`kind`, `item_id`, `source_keys`, `outcome`, `loss` and optional `reason` member
names as SemReg. `source_keys` contains all matching complete `FactKey` values,
including dimensions; absent definitions have `[]`. Capability dispositions
reference supporting facts only when they exist in this same snapshot. Different
dimensions or alternatives must never be collapsed into one chosen scalar.

| `outcome` | Rule |
| --- | --- |
| `exact` | Exact representation, `loss: []`; does not imply qualified or actionable. |
| `transformed` | At least one loss detail; never conceal rounding, unit, time, symbol or provenance changes. This target does not transform source records. |
| `withheld` | Explicit reason for a target item intentionally not projected. Source candidate evidence may still be readable as audit state, never as the withheld capability. |
| `unrepresentable` | Explicit reason why the target cannot represent the item. |
| `unsupported` | Explicit supported evidence of non-support, not mere absence. |
| `unknown` | Explicit reason; absence alone cannot prove non-support. Use `semantic.read.reason.value_unknown` for an absent fact with no stronger supported reason. |

`LossDetail` uses `kind`, `source_items`, `description`, `reversible`; kinds are
`unit`, `range`, `precision`, `time`, `symbol`, `provenance`, `identity`,
`capability`, `operation`, `policy`. Reasons preserve the owning contract's
code. Loss descriptions must be public text. Every omitted target capability,
unavailable item or unsupported sibling remains visible in its disposition.
Unknown fields never acquire a synthetic fact or capability. Validate report
completeness and references against the captured snapshot. Missing capability
instances are `unknown` unless the owner supplies stronger evidence of
non-support or withholding. Unqualified instances cannot be projected as
admitted capabilities: use `withheld` for candidate, `unknown` for unknown,
and `unsupported` for explicitly unsupported state, retaining the owner's
reason. If none is supplied, use the surface-owned
`semantic.read.reason.capability_unqualified` for withheld capabilities and
`semantic.read.reason.capability_unknown` for absent/unknown capabilities.
Unavailable or withdrawn capabilities use `withheld` with the owner's reason,
or `semantic.read.reason.capability_unavailable` when no reason is supplied.
If every candidate for a fact is effectively unavailable or withdrawn in the
evaluation, use `withheld` with the owner's reason, or
`semantic.read.reason.fact_unavailable`. A still-retained value remains visible
only as original audit evidence, not as a currently available measurement.
A fact can be represented exactly as candidate audit evidence without
claiming that it satisfies a capability. If no candidate has a value, use
`unknown`, or the stronger explicitly evidenced unsupported/withheld outcome.
Preserve all reason codes in source quality. For `fact_unavailable`,
`capability_unavailable` and `capability_unqualified`, first identify the exact
source keys that causally withhold this item. Intersect native reasons across
all candidates of all those causal keys, not across every supporting key.
An available sibling key is non-causal and cannot erase the explanation of an
unavailable key. Every candidate on a causal key must itself explain the
selected outcome through its original quality: unavailable/withdrawn for
availability, or candidate/rejected qualification for unqualified capability
support (a fact's admission also considers promotion and validity). A candidate
on a causal key without explanatory quality or without the common reason
prevents a fabricated native explanation; keep the surface fallback instead.
Never join candidates using a fact ID alone: match the complete `FactKey`,
including pack ID/version and every dimension ID, value kind and value.
Expiry-only evaluation cannot manufacture a native availability reason, and an
instance-only qualification/availability failure cannot borrow unrelated fact
reasons. With no causal fact explanation, retain the existing surface fallback.
When that intersection contains several codes, use the lexically first one for
the disposition's single `reason`. For other outcomes retain the applicable
owner reasons with the same lexical tie-break.
The STD-01 rule below takes precedence for affected eeBUS items.
Selections, when
supplied by an existing policy, preserve their policy ID/version, exact key,
candidate revision, snapshot/revisions, evaluation digest/context and
`presentation_only: true`; they never replace alternatives or confer authority.

Sort assets by `asset_id`, not request order. Preserve the kernel's canonical
array orders: facts by canonical `FactKey` bytes; candidates by `candidate_id`;
conflicts by `conflict_id`; bindings/instances by primary ID; source paths by
source/epoch/generation/binding; evidence by owner/kind/contract/digest; reasons
by definition ID. Use the serialization contract's full ordering rules,
including the retained tuple and numeric generation comparison. Sort projection
requests/dispositions by `(kind,item_id)`, loss by its canonical key, and
selections by `(canonical key,policy_id,policy_version)`. Reject duplicates.
Object field order is not semantic. The same capture, evaluation context and
mapping/policy versions produce the same shared-view data and array order on
both surfaces after the field-name mapping below.

The [derived five-pack availability view](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/pack-availability-view.md)
and [`DerivePackAvailability`](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/projection/availability.go)
provide the smaller underlying pure view: five pack rows with separate services,
capabilities, current fact alternatives/evaluations and retained observations,
joined to the exact snapshot and evaluation. The shared read is a superset in
scope: it also preserves the complete source snapshot, per-target projection
accounting, selections and per-asset unavailability across the selected assets.
It is not a serialization of that helper's rows, and the helper establishes no
pack endpoint exposure, runtime qualification or operation admission.

## GraphQL and MCP mapping

The ordinary GraphQL root returns the shared view directly; the normal GraphQL
`data`/`errors` response envelope remains. Use typed objects for the referenced
SemReg records, string scalars for 64-bit values/IDs/digests, `Boolean` for
booleans and `Int` for `Decimal.exponent10`. All matching `Value` arms are
nullable; `kind` determines the one present arm. Required record members and
arrays stay non-null. Optional MCP fields are nullable in GraphQL. Enum/code
string values, contract identifiers and units are unchanged.
The response contains only selected GraphQL fields; an incomplete selection is
not canonical kernel JSON and cannot be validated as a complete snapshot or
used to recompute its digest. Full reconstruction first restores all fields
and SemReg member names; source IDs/digests are never recomputed from a
GraphQL selection or a transport envelope.

Convert snake_case member names recursively to camelCase on GraphQL, leaving
already single-word members unchanged. Representative normative mappings:

| MCP / SemReg | GraphQL |
| --- | --- |
| `asset_ids`, `asset_id`, `binding_id`, `snapshot_id` | `assetIds`, `assetId`, `bindingId`, `snapshotId` |
| `unavailable_reason`, `identity_links` | `unavailableReason`, `identityLinks` |
| `candidate_id`, `candidate_revision`, `source_epoch_id` | `candidateId`, `candidateRevision`, `sourceEpochId` |
| `driver_generation`, `retained_observations` | `driverGeneration`, `retainedObservations` |
| `evaluated_at`, `evaluate_monotonic`, `freshness_policy` | `evaluatedAt`, `evaluateMonotonic`, `freshnessPolicy` |
| `unix_nanoseconds`, `clock_id`, `uncertainty_ns` | `unixNanoseconds`, `clockId`, `uncertaintyNs` |
| `effective_availability`, `evaluation_digest` | `effectiveAvailability`, `evaluationDigest` |
| `pack_id`, `pack_version`, `fact_id`, `item_id` | `packId`, `packVersion`, `factId`, `itemId` |
| `source_keys`, `source_items`, `presentation_only` | `sourceKeys`, `sourceItems`, `presentationOnly` |
| `exponent10`, `known`, `revisions.semantic` | `exponent10`, `known`, `revisions.semantic` |

The supplied [GraphQL adapter](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/graphql/semantic_snapshot.go)
constructs object names as `Semantic` plus the concrete Go struct name, with
two wrapper exceptions. This is the source-derived type-name mapping for schema
selection and fragments; it does not establish current public root wiring:

| Go record | GraphQL object name |
| --- | --- |
| `semanticview.View`, `semanticview.Asset` | `SemanticSnapshotRead`, `AssetSnapshotRead` |
| `Snapshot`, `RevisionVector` | `SemanticSnapshot`, `SemanticRevisionVector` |
| `EvaluationView`, `EvaluationContext`, `EvaluatedFact` | `SemanticEvaluationView`, `SemanticEvaluationContext`, `SemanticEvaluatedFact` |
| `FactEnvelope`, `FactKey`, `FactCandidate`, `Conflict` | `SemanticFactEnvelope`, `SemanticFactKey`, `SemanticFactCandidate`, `SemanticConflict` |
| `Value`, `Quantity`, `Decimal`, `Symbol`, `Dimension` | `SemanticValue`, `SemanticQuantity`, `SemanticDecimal`, `SemanticSymbol`, `SemanticDimension` |
| `Quality`, `Times`, `TimePoint`, `MonotonicPoint`, `FreshnessPolicy` | `SemanticQuality`, `SemanticTimes`, `SemanticTimePoint`, `SemanticMonotonicPoint`, `SemanticFreshnessPolicy` |
| `RetainedObservationRecord`, `EvaluatedRetainedObservation` | `SemanticRetainedObservationRecord`, `SemanticEvaluatedRetainedObservation` |
| `ProjectionReport`, `ProjectionManifest`, `RequestedItem`, `ProjectionDisposition`, `LossDetail` | `SemanticProjectionReport`, `SemanticProjectionManifest`, `SemanticRequestedItem`, `SemanticProjectionDisposition`, `SemanticLossDetail` |
| `Selection` | `SemanticSelection` |

Other reachable struct records follow the same prefix rule; ID, digest,
revision and code aliases are string scalars, not object types.

MCP returns the existing Helianthus envelope described in
[mcp.md](mcp.md#shared-request-and-envelope-rules):
`meta.contract` is `{name: "helianthus-ebus-mcp", major: 1, minor: 0}`;
`meta.consistency.mode` is `EVALUATED_SEMREG_PUBLICATION`, as on the existing
SemReg-backed PV tool. This tool takes only `asset_ids`: it does not accept the
legacy `LIVE`/`SNAPSHOT` consistency selector or a replay snapshot ID. Do not
put a per-asset ID into envelope `meta.consistency.snapshot_id` for a multi-asset
read. The per-asset identities live inside `data.assets[].snapshot`.

Only the consistency mode is shared with those existing tools. The proposed
shared envelope deliberately uses `helianthus-ebus-mcp` and error
`source_layer: "gateway"`, without Modbus `meta.limits`. The existing siblings
use `helianthus-modbus-mcp`, error `source_layer: "modbus"`, and `meta.limits`
from [their envelope constructor](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/mcp/modbus_v1.go).
Do not migrate or relabel those envelopes through this contract.

`meta.data_timestamp` is the request evaluation wall time in RFC3339Nano;
SemReg `TimePoint` remains exact inside `data`. `meta.data_hash` is computed by
the existing envelope algorithm over the serialized data; it is not a snapshot
ID or proof of acquisition/qualification. `data` contains the shared view and
`error` is null on successful reads, including explicit unavailable entries.
Request failures have null `data` and the existing error object members
`code`, `message`, `retriable`, `source_layer`; messages are sanitized and
`source_layer` is `gateway`. Invalid input, conflict and overflow are not
retriable; provider unavailability and timeout are retriable. GraphQL maps the
same request failures to `errors[].extensions.code` with a null root, without
inventing an MCP-shaped GraphQL envelope.

## Synthetic examples and five-pack parity

All examples are synthetic. This MCP tool-call payload is JSON; it is not a
native locator request or the full JSON-RPC message:

```json
{
  "name": "semantic.v1.snapshot.get",
  "arguments": {
    "asset_ids": ["asset:evse", "asset:infrastructure", "asset:pv", "asset:storage", "asset:thermal"]
  }
}
```

An ordinary GraphQL operation can request both identity and accounting without
a domain-specific root. Other typed snapshot members remain selectable:

```graphql
query SharedSemanticRead($assetIds: [ID!]!) {
  semanticSnapshot(assetIds: $assetIds) {
    assets {
      assetId unavailableReason
      snapshot {
        snapshotId
        revisions { semantic identity facts services capabilities }
        facts {
          key {
            packId packVersion factId
            dimensions { id value { kind text } }
          }
          candidates {
            candidateId revision
            value {
              kind
              quantity { number { coefficient exponent10 } unit }
              boolean text symbol { namespace token known }
            }
            quality {
              assertion qualification promotion validity availability freshness reasons
            }
          }
        }
      }
      evaluation {
        snapshotId
        revisions { semantic identity facts services capabilities }
        facts { candidateId candidateRevision freshness effectiveAvailability }
      }
      projection {
        snapshotId
        revisions { semantic identity facts services capabilities }
        dispositions {
          kind itemId outcome reason
          sourceKeys {
            packId packVersion factId
            dimensions { id value { kind text } }
          }
          loss { kind sourceItems description reversible }
        }
      }
    }
  }
}
```

Its variables select exactly the same assets:

```json
{
  "assetIds": ["asset:evse", "asset:infrastructure", "asset:pv", "asset:storage", "asset:thermal"]
}
```

This **RevisionVector fragment** demonstrates that every component remains a
decimal string, including components that did not change with the latest fact:

```json
{"semantic":"7","identity":"2","facts":"5","services":"1","capabilities":"1"}
```

This **ProjectionDisposition fragment** accounts for a requested but absent
Thermal fact without fabricating a value or an unsupported-device claim:

```json
{
  "kind": "fact",
  "item_id": "thermal.measurement.humidity_relative",
  "outcome": "unknown",
  "source_keys": [],
  "loss": [],
  "reason": "semantic.read.reason.value_unknown"
}
```

This complete shared-view `data` example shows an explicitly unavailable asset,
not a successful empty snapshot or a zero-valued device:

```json
{
  "assets": [
    {
      "asset_id": "asset:missing",
      "selections": [],
      "unavailable_reason": "semantic.read.reason.asset_unknown"
    }
  ]
}
```

The following are **scalar fragments**, not complete facts, snapshots or
envelopes. Their parent fact supplies identity, quality, time and evidence:

```json
[
  {"kind":"quantity","quantity":{"number":{"coefficient":"0","exponent10":0},"unit":"unit.watt"}},
  {"kind":"boolean","boolean":false},
  {"kind":"text","text":""}
]
```

Use these pack definitions through the same records and entry points. The
zero examples do not qualify a family or prove a live reading:

| Device family / semantic pack | Example fact ID | Exact zero unit / dimension ID |
| --- | --- | --- |
| PV/inverter / `helianthus.pack.pv` | `pv.ac.active_power` | `unit.watt` / `pv.dimension.phase` |
| Storage/BMS / `helianthus.pack.storage` | `storage.state.soc` | `unit.percent` / `storage.dimension.pack` |
| EVSE / `helianthus.pack.evse` | `evse.ac.active_power` | `unit.watt` / `evse.dimension.phase` |
| Thermal/HVAC / `helianthus.pack.thermal` | `thermal.measurement.air_temperature` | `unit.celsius` / `thermal.dimension.temperature` |
| Infrastructure / `helianthus.pack.infrastructure` | `infrastructure.ac.voltage` | `unit.volt` / `infrastructure.dimension.phase` |

Their public contracts are
[PV](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/packs/pv-inverter-v1.md),
[Storage](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/packs/storage-bms-v1.md),
[EVSE](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/packs/evse-v1.md),
[Thermal](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/packs/thermal-hvac-v1.md)
and
[Infrastructure](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/packs/infrastructure-v1.md).
Use each exact captured pack version, not one assumed common version. Unknown
instead has absent value plus its supported quality/reason and an explicit
projection disposition; no pack-specific zero/false/empty fallback is allowed.

## eeBUS inbound and acceptance boundary

Native wire semantics belong to the
[eeBUS protocol documentation](https://github.com/Project-Helianthus/helianthus-docs-eebus).
Unresolved STD-01 revisions do not establish native mappings. The SemReg
[family-catalog fixture](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/fixtures/v1/family-catalog-v1.json)
keeps `eebus-inbound` at `unknown` with reason `unknown_pending_std_01`.

The current [shared-view source](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/semanticview/view.go)
recognizes an affected item by the exact `unknown_pending_std_01` token in a
contributing candidate's `quality.reasons`; it gives that signal precedence and
sets the disposition to `unknown` with that reason. The catalog is provenance
for the family state, not an observation lookup or an automatic protocol/name
heuristic. How an inbound producer assigns that token without it already being
present is **Unknown** here; no new signal or decoder is defined.

Affected inbound observations remain `candidate` or `unknown`, unpromoted and
non-actionable, preserving that reason and native evidence references. Expose
an `unknown` or `withheld` disposition as appropriate, never qualified support,
a normative mapping or an invented value. Native and family reason codes are
preserved verbatim; do not prefix or reinterpret `unknown_pending_std_01` as an
API-owned reason. A readable candidate and a transport connection cannot
establish capability admission or conformance. No eeBUS payload is decoded here.

Runtime acceptance must exercise both real surface adapters over the same
synthetic detached read: all five packs, shuffled input ordering, distinct
asset/binding/candidate identities, every revision component, exact scalars,
absent values, stale/unknown freshness, losses, unavailable siblings, mixed
revision rejection and private-data withholding. Multiple GraphQL aliases must
capture once, and a concurrent publication must not change that detached view.
Legacy tool compatibility requires separate regression coverage. Publishing
this contract proves neither that runtime parity nor hardware acceptance.

## Complete MCP envelope examples

These are complete tool-result envelope bodies, before MCP text-content or
JSON-RPC wrapping. The epoch timestamp is a synthetic evaluation constant,
not a capture time. The success includes two sorted unavailable entries; it is
success at the request level, not evidence of a readable or qualified device.
Readable entries instead carry all three snapshot/evaluation/projection members
as defined above; these unavailable entries must omit all three.

```json
{
  "data": {
    "assets": [
      {
        "asset_id": "asset:missing",
        "selections": [],
        "unavailable_reason": "semantic.read.reason.asset_unknown"
      },
      {
        "asset_id": "asset:withheld",
        "selections": [],
        "unavailable_reason": "semantic.read.reason.publication_withheld"
      }
    ]
  },
  "error": null,
  "meta": {
    "contract": {
      "name": "helianthus-ebus-mcp",
      "major": 1,
      "minor": 0
    },
    "consistency": {
      "mode": "EVALUATED_SEMREG_PUBLICATION"
    },
    "data_timestamp": "1970-01-01T00:00:00Z",
    "data_hash": "<computed-data-hash>"
  }
}
```

A whole-read overflow error has no partial asset data and is not retriable:

```json
{
  "data": null,
  "error": {
    "code": "RESOURCE_EXHAUSTED",
    "message": "semantic snapshot read exceeds bounds",
    "retriable": false,
    "source_layer": "gateway"
  },
  "meta": {
    "contract": {
      "name": "helianthus-ebus-mcp",
      "major": 1,
      "minor": 0
    },
    "consistency": {
      "mode": "EVALUATED_SEMREG_PUBLICATION"
    },
    "data_timestamp": "1970-01-01T00:00:00Z",
    "data_hash": "<computed-data-hash>"
  }
}
```

The `data_hash` values are publication placeholders, not wire values. Validation
replaces them in memory with hashes derived from each example's synthetic `data`;
no concrete digests are published. Use the existing envelope algorithm (SHA-256
of compact JSON; object keys sorted for these map values), not SemReg canonical
snapshot hashing. The hashes can be derived with the Python
standard library: `hashlib.sha256(json.dumps(data, sort_keys=True,
separators=(",", ":")).encode("utf-8")).hexdigest()`. Error hashing includes
JSON `null`. No `snapshot_id` or Modbus limits are added to consistency metadata.
