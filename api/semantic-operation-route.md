# One semantic operation route

Status: proposed ordinary GraphQL target contract for [issue #729](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/729).
This partial slice references Project #2 INT-06 / INT-08; it establishes neither
runtime wiring nor hardware acceptance. No stability claim applies before 1.0.
This is an application API contract, not a native operation definition.

## Owners and existing contracts

The public [SemReg kernel operation contract](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/kernel.md#operations-and-guarded-admission)
owns admission, route identity and execution evidence. Its
[operation types](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/operation/types.go),
[admission implementation](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/operation/admission.go)
and [record validation](https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/operation/record.go)
are implementation corroboration. They do not prove wire behavior.

Read existing opaque identities and revisions through the
[shared snapshot read contract](semantic-snapshot-read.md). Readability,
presentation selection, pack availability and a GraphQL field do not admit an
operation. The native documentation owner must establish native meaning first:

| Native family | Public native contract and execution boundary |
| --- | --- |
| eBUS / HVAC | [Wire transaction and ACK contract](../protocols/ebus-services/ebus-overview.md#acknack-symbols); [B524 native profile evidence](../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md). The qualified native driver owns the exact selector, codec, access, limits, execution and readback. |
| Modbus / PV, storage, EVSE | [Public Modbus documentation](https://github.com/Project-Helianthus/helianthus-docs-modbus). The driver must cite its exact existing family/profile operation contract; this page supplies no register or control mapping. |
| eeBUS | [Public eeBUS documentation](https://github.com/Project-Helianthus/helianthus-docs-eebus). An unresolved native mapping stays unknown and non-actionable; connectivity does not qualify an executor. |

No family is qualified by this table. Evidence conclusions `Proven`,
`Hypothesis` and `Unknown` describe support for a claim; they are separate from
runtime qualification, promotion, freshness and admission. A proven readable
field does not prove writability. Keep raw native evidence beside interpretation
under its owner, exposing only sanitized public references here. For B524,
preserve `(opcode, group, instance, register)`; never substitute another opcode
namespace. No new native operation, range, bypass or live-write recipe is defined.

## One request

Use one additive ordinary GraphQL mutation:
`semanticOperation(input: SemanticOperationInput!): SemanticOperationResult`.
It serves every pack through the same adapter. It does not extend the separate
machine-to-machine schema. The following is the closed input member set:

| Member | Type and meaning |
| --- | --- |
| `assetId` | `String!`; exact existing SemReg `AssetID`. |
| `bindingId` | `String!`; expected existing `NativeBindingID`, checked against the admitted route. It is a match constraint, never a native locator or route override. |
| `capabilityInstanceId` | `String!`; exact existing capability instance, mapped to `Intent.RequiredCapability.InstanceID`. |
| `operation` | `SemanticDefinitionRefInput!`; existing pack-owned operation definition, including `pack { id version }`, `id` and `version`. Maps to `Intent.Kind`. |
| `arguments` | `[SemanticTypedFieldInput!]!`; existing `TypedField` records with `id` and tagged `value`. No free-form native payload. |
| `expectedSemanticRevision` | `String!`; maps to the intent's semantic revision. |
| `expectedCapabilityRevision` | `String!`; complete capability collection revision. |
| `expectedCapabilityInstanceRevision` | `String!`; revision of the one instance, distinct from the collection revision. |
| `expectedSourceEpochId` | `String!`; exact expected source epoch. |
| `expectedDriverGeneration` | `String!`; exact expected driver generation. |
| `preconditions` | `[SemanticPreconditionInput!]!`; existing `Precondition` records: full fact key, candidate ID/revision, operator and expected typed value. Empty only when the pack permits it. |
| `timeoutMs` | `Int!`; request budget, 1–5000 milliseconds, capped by the server's remaining budget. Never extends an owner deadline. |

Referenced input records mirror the existing SemReg records using the recursive
snake_case to camelCase mapping in the shared read contract. Every opaque ID,
including IDs in nested input records, uses string-only GraphQL `String` input
with the existing nullability; numeric inputs are rejected. IDs compare
byte-for-byte, without trimming, case folding, decoding or reconstruction.
Revision/generation values are canonical unsigned decimal strings within the
existing 64-bit type, never GraphQL `Int` or floating-point numbers. Values retain
their one matching tagged arm, exact decimal coefficient/exponent and unit.

Bound this target API before admission: at most one `semanticOperation` field
per GraphQL request, including aliases/fragments; no batched operation requests.
Reject additional input members, null required members and malformed types.
Require a single UTF-8 JSON HTTP request body. Limit that entire body, after
HTTP content decoding and before JSON parsing or GraphQL coercion, to 65,536
bytes (64 KiB), including query text, variables, metadata, whitespace and JSON
escapes. This same byte limit covers inline literals and variable inputs; no
reserialization is measured. Limit each opaque ID to 256 UTF-8 bytes, and
arguments and preconditions to 64 entries each. Existing SemReg
type/collection bounds also apply. Arguments are sorted by field ID; preconditions
by `(canonical fact key, candidate ID, candidate revision)` with no duplicate
tuple. Reject duplicate arguments and unsupported value arms. Overflow and
invalid input fail before any executor invocation; do not truncate or coerce.
These are API resource bounds, not native control ranges.

## Admission and native execution

1. Validate the closed request and resolve the exact pack operation, argument,
   required capability and effect definitions through the existing pack owner.
   `OperationPackValidator.ValidateIntent` validates the unchanged typed
   arguments and pack-owned expected effect. The adapter cannot infer an effect
   from a label or invent a missing operation. The required capability's pack,
   definition and version range come from that exact existing operation contract.
2. Capture one immutable current per-asset snapshot and explicit evaluation
   context. Run SemReg admission against it, preserving expected semantic,
   capability collection and capability instance revisions, source epoch,
   generation, preconditions, deadline and existing causal safeguards. A stored
   publication-time freshness result is insufficient. Missing, stale, conflicted,
   unqualified or unsupported state cannot become an admitted fallback.
3. Require exactly one SemReg route. Match its binding and capability instance
   to the request constraints and its service/source/epoch/generation to the
   current snapshot. All links and instances must satisfy the existing admission
   contract. Ambiguity fails closed; caller selection or a compatibility alias
   cannot select another native endpoint. Unsupported capability, stale epoch
   or generation, and no matching qualified injected executor all mean **no-send**.
4. Dispatch only through the executor injected by the qualified driver owner for
   that admitted route and exact operation. No transport factory, protocol probe,
   global executor discovery or alternate driver fallback is added. Immediately
   before native invocation the owner rechecks `GuardClaims` under its lifecycle
   guard, including capability collection/instance revisions, service, binding,
   source epoch, generation and fences. A concurrent retirement or change causes
   no-send. SemReg admission alone is not an atomic native dispatch guarantee.
5. Preserve the native owner's dispatch, ACK and readback evidence independently.
   Validate any terminal `ExecutionRecord` through `Kernel.Record`; admission
   rejection uses the owning rejection contract. Never synthesize protocol ACK
   from transport completion or readback from a requested value. A generic route
   adds no retry, replay, reroute or write/read sequence. Native mandatory wire
   behavior remains with the existing qualified owner.

The current kernel `Intent` also requires internal identity, authority evidence,
causal context, deadline and replay bookkeeping. Those requirements remain owned
by the existing runtime/kernel contract. This proposal does not expose an
idempotency key, principal, authorization tier or G5 receipt; it adds no
authorization gate before 0.9. It neither fabricates those internal fields nor
relaxes kernel validation. An adapter that cannot construct a valid intent using
its existing owner integration remains unwired and returns `UNAVAILABLE` with
no-send. Resolving that integration is required before runtime acceptance.

## Distinct results

`SemanticOperationResult` has the following closed fields: `status: String!`,
`kernelOutcome: String`, `delivery: String`, `acknowledgement: String`,
`readbackRelation: String`, and `reason: String`. Nullable fields are JSON null
when not evidenced. `reason` preserves a sanitized owner code, with no raw
transport errors. `kernelOutcome` preserves the original SemReg outcome rather
than collapsing conflict or no-effect into success. These are projections, not
new SemReg outcome enum values:

| API `status` | Existing evidence and meaning |
| --- | --- |
| `accepted` | SemReg admission and executor match succeeded. `kernelOutcome`, `delivery`, `acknowledgement` and `readbackRelation` are null. This reports admission only: it never means executed, sent, protocol ACK or readback-confirmed. `Admission` is not a terminal `ExecutionRecord`. |
| `protocol_ack` | `kernelOutcome=acknowledged_unverified`, `delivery=sent`, and native `Acknowledgement.state=accepted` or `provisional`. No confirming readback; `readbackRelation` is `inconclusive` when evidenced, otherwise null. The protocol's accepted ACK is distinct from API admission. |
| `readback_confirmed` | `kernelOutcome=applied`, `delivery=sent`, `readbackRelation=confirms`. A native ACK is retained if supplied, but never invented for a protocol without one. |
| `failed` | Preserve `rejected`, `failed_no_contact`, `no_effect` or `conflict` separately in `kernelOutcome`. Admission rejection has `delivery=not_sent` as an API no-send statement, and no ACK/readback; its kernel record has no route/dispatch. `failed_no_contact` requires dispatch evidence of not-sent and no possible side effect. `no_effect` and `conflict` require their existing post-dispatch evidence, so failed does not generally imply no-send. |
| `unknown` | `kernelOutcome=indeterminate`; dispatch may have occurred and evidence cannot establish effect. Preserve evidenced delivery (`sent` or `unknown`) and ACK/readback relation if present. A timeout or lost response cannot establish not-sent or failure without effect. No blind retry or fallback route is allowed. |

Validated terminal outcomes take precedence over ACK-only classification.
Validated `no_effect` or `conflict` remains `failed` even with an accepted or
provisional native ACK. Only `acknowledged_unverified` with an accepted or
provisional native ACK and no confirming readback maps to `protocol_ack`,
including when the bounded wait expires. Preserve an evidenced `inconclusive`
readback relation on this result. A timeout with ambiguous delivery and
no sufficient ACK evidence is `unknown`. A rejected native ACK is not
`protocol_ack`; classification requires the native owner's failure/effect
evidence, otherwise it remains unknown. An inconclusive readback cannot become
`readback_confirmed`.

For confirming readback, retain the exact later snapshot ID and full revision
vector, candidate ID/revision, complete effect fact key and binding/source/epoch/
generation equal to the admitted route. The candidate must be observed,
qualified, promoted, good, evaluated fresh and available, without open conflict.
Its semantic revision must advance; its receipt must be strictly after completed
dispatch under the kernel's monotonic or uncertainty-aware wall ordering.
`OperationPackValidator.EvaluateReadback` must return `confirms` for the unchanged
intent. An equal cached/pre-dispatch value, another binding, retired generation,
missing snapshot, or overlapping clock uncertainty never confirms execution.

The bounded request may return admission before terminal evidence exists, or the
stronger validated result if already available. This page adds no receipt,
operation polling handle, subscription or persisted execution store. Loss of an
accepted response gives the client no execution proof or replay guarantee.
Ordinary snapshot reads may show current state; they cannot reconstruct causal
execution proof without the existing owner's exact operation evidence.
Reconciliation evidence cannot rewrite the immutable terminal record.

Failed/partial refresh preserves unrelated and last-known-good observations with
their original source, quality and freshness. Retained history cannot qualify a
current executor, satisfy stale preconditions or confirm a new operation.

## Surface compatibility

GraphQL uses its normal `data`/`errors` envelope. Structural errors map to
`INVALID_ARGUMENT`, size overflow to `RESOURCE_EXHAUSTED`, and an unwired
operation provider to `UNAVAILABLE` on `errors[].extensions.code`, with a null
mutation root and no-send. Domain admission failures use the `failed` result
and preserve the owning reason, including stale epoch or unsupported capability.
After possible dispatch, evidence uncertainty must return `unknown` when a
response can still be delivered; a transport error alone proves nothing about
execution. Do not mark errors as safe to resubmit after possible dispatch.

Existing eBUS MCP names, envelopes, errors and behavior remain compatible.
This page registers no new MCP mutation. Any future MCP projection must use the
same admission and evidence result, with the existing envelope and recursive
field-name mapping, and demonstrate GraphQL parity before exposure. All MCP
namespaces remain pre-stable until 1.0; no new namespace is introduced.
The [J16 ordinary runtime tools](driver-runtime-v1.md#error-and-security-boundary)
remain lifecycle tools with their own closed desired-state result. Their
receipt-free result does not become a semantic execution record.

## Synthetic offline examples

The operation definition below is a synthetic fixture contract with no native
mapping, arguments or effect on equipment. It is not a supported operation.
Assume an offline fake pack owner and executor only when checking result shapes.
No sample provides native addressing, control values or capture context.

```graphql
mutation SemanticOperation($input: SemanticOperationInput!) {
  semanticOperation(input: $input) {
    status kernelOutcome delivery acknowledgement readbackRelation reason
  }
}
```

Variables (synthetic):

```json
{
  "input": {
    "assetId": "asset:synthetic",
    "bindingId": "binding:synthetic",
    "capabilityInstanceId": "capability:synthetic",
    "operation": {
      "pack": {"id": "fixture.pack.synthetic", "version": "1.0.0"},
      "id": "fixture.operation.synthetic", "version": "1.0.0"
    },
    "arguments": [],
    "expectedSemanticRevision": "7",
    "expectedCapabilityRevision": "3",
    "expectedCapabilityInstanceRevision": "2",
    "expectedSourceEpochId": "epoch:synthetic",
    "expectedDriverGeneration": "4",
    "preconditions": [],
    "timeoutMs": 1000
  }
}
```

Alternative GraphQL responses for independent offline scenarios, in order:
admission only, native ACK only, confirming readback, absent qualified executor,
stale epoch, unsupported capability, ambiguous delivery, and native ACK with
inconclusive readback. These are projections
of evidence, not complete kernel records or a series rewriting one record.
The `fixture.reason.*` codes are synthetic owner reasons only.

```json
[
  {"data":{"semanticOperation":{"status":"accepted","kernelOutcome":null,"delivery":null,"acknowledgement":null,"readbackRelation":null,"reason":null}}},
  {"data":{"semanticOperation":{"status":"protocol_ack","kernelOutcome":"acknowledged_unverified","delivery":"sent","acknowledgement":"accepted","readbackRelation":null,"reason":null}}},
  {"data":{"semanticOperation":{"status":"readback_confirmed","kernelOutcome":"applied","delivery":"sent","acknowledgement":null,"readbackRelation":"confirms","reason":null}}},
  {"data":{"semanticOperation":{"status":"failed","kernelOutcome":"rejected","delivery":"not_sent","acknowledgement":null,"readbackRelation":null,"reason":"fixture.reason.executor_missing"}}},
  {"data":{"semanticOperation":{"status":"failed","kernelOutcome":"rejected","delivery":"not_sent","acknowledgement":null,"readbackRelation":null,"reason":"stale_source_epoch"}}},
  {"data":{"semanticOperation":{"status":"failed","kernelOutcome":"rejected","delivery":"not_sent","acknowledgement":null,"readbackRelation":null,"reason":"fixture.reason.capability_unsupported"}}},
  {"data":{"semanticOperation":{"status":"unknown","kernelOutcome":"indeterminate","delivery":"unknown","acknowledgement":null,"readbackRelation":null,"reason":"fixture.reason.delivery_uncertain"}}},
  {"data":{"semanticOperation":{"status":"protocol_ack","kernelOutcome":"acknowledged_unverified","delivery":"sent","acknowledgement":"provisional","readbackRelation":"inconclusive","reason":null}}}
]
```

## Rule trace and acceptance boundary

| Rule | Existing owner to check |
| --- | --- |
| Closed, bounded typed input; exact definitions and argument/effect matching | Kernel `Intent`, `Precondition`, `ExpectedEffect`, `OperationPackValidator`; operation `validation.go` and `Kernel.ValidateIntent`. API byte/field/request budgets above are additional surface bounds. |
| Fresh single-snapshot admission; exact capability versions, revisions, epoch and generation | Kernel guarded admission; `Kernel.Admit`, `Route`, `Admission.GuardClaims`. Request binding equality and injected executor match are runtime adapter obligations. |
| No-send under missing executor, unsupported capability, stale epoch or guard change | Kernel route rejection and generation-bound callback contract; qualified native driver owns the final guard and sole native handle. |
| Admission differs from execution and ACK | `Admission` versus `ExecutionRecord`, `DispatchEvidence`, `Acknowledgement`. No terminal accepted outcome exists. |
| ACK differs from applied; failed differs from unknown | Kernel outcome table; `OutcomeAcknowledgedUnverified`, `OutcomeApplied`, `OutcomeRejected`, `OutcomeFailedNoContact`, `OutcomeNoEffect`, `OutcomeConflict`, `OutcomeIndeterminate`. |
| Exact post-dispatch readback and immutable terminal evidence | Kernel `Readback`, `Kernel.Record`, exact pack `EvaluateReadback`; existing native contract supplies observations, never the GraphQL adapter. |
| Partial last-known-good state stays evidence, not current admission | Shared snapshot retained observations and evaluation contract; kernel source retirement/fencing and readback eligibility. |
| Receipt-free lifecycle and MCP compatibility | Shared snapshot surface mapping and J16 runtime tools; neither creates native operation support. |

Offline acceptance must validate every example and trace each rule above. Runtime
acceptance additionally needs real adapter tests for each request identity and
revision independently, ambiguous route rejection, qualified executor absence,
guard changes before invocation, zero native sends on refusal, ACK without
readback, late/foreign/stale readback, unknown delivery, and MCP regression/parity.
Documentation/example validation alone proves no executor wiring, protocol
qualification, transport behavior or physical effect.
