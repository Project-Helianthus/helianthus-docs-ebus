# Bidirectional driver registration boundary

Status: proposed architecture extension, tracked by
[docs issue #715](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/715).
This is a partial contract slice advancing
[gateway issue #1125](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1125);
it does not close that parent. Output registration and hooks below are proposed,
not implemented or wired by this page. No operation router or Portal selection
persistence owner is selected here. All public interfaces remain pre-stable
until Helianthus 1.0.

## Sources and authority

The [runtime driver lifecycle](runtime-driver-lifecycle.md) owns G5 registration
and final D1–D5 decisions. Its final decisions supersede older receipt,
idempotency-key and lifecycle authorization proposals in the
[gateway provider contract](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/architecture/runtime-driver-provider-contract-v1.md).
That companion owns the provider SPI and causal processing rules. The
[shared snapshot read](../api/semantic-snapshot-read.md) owns the target detached
semantic read and ordinary GraphQL/MCP parity. A source's documented internal
implementation is not evidence of public endpoint exposure.

**Proven** here means supported by those supplied public contracts, not device
qualification or executed runtime acceptance. **Hypothesis** denotes proposed
extension behavior in this page. **Unknown** covers unsupported native mappings,
production output-hook wiring and the selection persistence owner. These labels
are independent of qualification, freshness, runtime readiness and physical
acceptance; registration changes none of those dimensions.

Native meaning must first be established by the corresponding public native
documentation, including the [eBUS references](../protocols/) and
[eeBUS documentation](https://github.com/Project-Helianthus/helianthus-docs-eebus).
Driver-native acquisition, decode, qualification, retry/reconnect, raw evidence,
ACK/readback and close proof stay with their native drivers. Protocol-neutral
facts and projection loss stay with
[SemReg's public kernel](https://github.com/Project-Helianthus/helianthus-docs-semantic/blob/main/api/v1/kernel.md).
eeBUS output implementation belongs to
[helianthus-eebusreg](https://github.com/Project-Helianthus/helianthus-eebusreg).
A family-local provider port is neither the common production Provider
interface nor a live gateway integration. This page adds no native semantics.

## Descriptors and proposed output declarations

The existing S0 descriptor format already declares exactly one direction per
instance. Direction describes roles, never automatic forwarding or authority.

| Direction | Role | Does not imply |
| --- | --- | --- |
| `southbound` | Acquires native evidence and can publish admitted semantic observations | Native write support or a public output endpoint |
| `northbound` | Consumes admitted semantic snapshots for an explicit output target | Source acquisition, qualification or automatic publication |
| `both` | Declares both roles with separate source and sink identities | Reflection of output into acquisition or a second semantic authority |

Keep the existing immutable `DriverID`, disposition, `NativeContractRef`, typed
lifecycle adapter, owned `SourceID` set and hook declarations. Source ownership
is exclusive across the complete registry and hub. An output-only descriptor
may have an empty source set; do not fabricate an acquisition source or semantic
asset to register a sink. Driver, asset, source, source epoch, driver generation,
native connection generation and target binding identities are distinct.

The following **proposed declaration concepts** describe future obligations only.
The existing descriptor and public API remain unchanged:

| Proposed concept | Boundary to preserve |
| --- | --- |
| Output binding identity and target contract | Stable configured sink identity and exact target profile/version; no endpoint coordinates or credentials in public metadata |
| Projection declaration | Exact semantic pack definitions and target mapping version, with per-item loss/withholding accounting |
| Output lifecycle contribution | Typed preparation, activation, withdrawal, drain and retirement obligations correlated to the owning runtime incarnation |
| Causal participation | Target processor identity, ancestry preservation and bounded echo handling under the semantic owner |

Validate the complete set, disabled entries included, and freeze detached copies
before factories, semantic declarations or endpoint effects. Duplicate driver or
source ownership, conflicting sink ownership, unsupported target contracts and
unsupported hooks must refuse before effects. Rejection installs no partial
registry and preserves unaffected last-known-good state and provenance. A sink
collision is about the same configured output binding, not merely two outputs
projecting the same fact.

Today's host requires an empty hook set: every hook declaration fails, including
the reserved `mcp`, `setup`, `portal`, `semantic` and `evidence` names. Output
concepts above cannot bypass that refusal. A future implemented hook schema needs
separate review and acceptance before registration can admit it. O8 compiled
driver packages remain the delivery boundary; this proposal adds no dynamic
plugin loading, parallel control service or alternate lifecycle owner.

## Output lifecycle and retirement

All proposed contributions use the existing gateway lifecycle serialization,
desired-state service and DriverManager boundary. Registration and cached
list/get perform no endpoint I/O. Native output setup and resource closing remain
owned by the target implementation, with one retry owner.

| Transition | Proposed output obligation and existing invariant |
| --- | --- |
| Inactive registration or completed STOP | Store detached declarations only; no endpoint open, subscription activation or publication. Desired STOPPED alone does not prove shutdown completion |
| START preparation | Restore required D5 material and complete the epoch barrier before preparation; prepare inert target resources, keeping publication admission closed |
| Activation | Admit only the exact current generation after lifecycle readiness and valid projection input; readiness alone publishes nothing |
| Partial update or rejected input | Retain omitted last-known-good facts with their original aging policy; rejected publication changes nothing. Retained audit observations never become current output input |
| STOP | Fence callbacks and output admission immediately, withdraw active contributions, cancel/drain work and prove native close independently of semantic cleanup; report STOPPED only after both obligations settle |
| Explicit RESTART or START after completed STOP | D1 retires the predecessor and proves close before one successor epoch and generation-1 reservation; repeated reconciliation reuses the recorded successor |
| Automatic replacement or native reconnect | Preserve D1 distinctions: replacement advances driver generation within the epoch; an internal connection retry need not replace the driver |
| Failure, uncertain close or incomplete recovery | Keep affected admission closed and quarantine intact; do not reopen through a new epoch or cached projection. Unaffected assets retain their valid state |

An output-only runtime can have an empty semantic barrier/cleanup set, but still
owes cancellation, target withdrawal and independent close proof. A queued
projection or callback must carry its owning incarnation and target binding;
late work from a retired incarnation cannot publish, mutate a successor or
remove a successor's contribution. Retirement retains causal tombstones for
their required lifetime rather than clearing them on reconnect.

The existing Portal contribution key omits the source epoch while generation
restarts in each epoch. As the lifecycle source states, DM-HOOKS must provide
an epoch-aware key or a per-driver monotonic contribution generation before
cross-epoch contributions are safe. This page does not choose or implement that
mechanism.

D2 bootstrap, corrupt-load refusal and explicit repair rules remain intact.
D3 START/STOP are idempotent by desired state with optimistic expected revisions;
START while already desired RUNNING does not reset backoff or allocate an epoch.
RESTART keeps desired RUNNING. Lost responses use list/get readback, not client
receipts or idempotency keys. D4 uses ordinary MCP without a new lifecycle
principal or authorization gate; native-write safety and unrelated safeguards
remain. D5 exact-byte recovery, pending work and tombstones must restore before
admission. This design changes none of G5 D1–D5/O8.

## Snapshot reads, selection and explicit publication

SemReg snapshots are the sole semantic read source for outputs and public
semantic views. Capture detached state coherently, then evaluate and project
against the same per-asset snapshot identity, full revision vector, candidate
revisions, evaluation context and captured mapping definitions. Do not splice
live driver reads, older facts or newer capability records into that view.
Acquisition never occurs as a side effect of selection, preview or reading.

Preserve alternatives, conflicts, provenance, exact zero/false values, absent
values, freshness and qualification independently. Unknown native mappings stay
Unknown; candidate evidence never becomes admitted support through projection.
A closed read gate cannot be bypassed by exporting cached last-known-good data
as current. Projection accounts explicitly for unsupported, withheld, unknown
and lossy items, preserving owner reasons and public-safe evidence references.

Portal selection is presentation intent: choosing an asset, candidate or target
can produce a preview, but cannot start a driver, acquire facts, grant native
write authority or activate publication. Explicit publication is a separate
request to the existing composition boundary, bound to the selected target and
validated current snapshot/projection. No request payload or persistence owner
is defined here. Changing or losing a selection must not implicitly publish or
replay a previously queued request. Stale input requires reevaluation; it cannot
silently switch candidate or target. A preview is not publication completion.

Existing eBUS MCP names, envelopes and behavior remain compatible. The shared
read's ordinary MCP and GraphQL adapters must expose equivalent detached data,
canonical ordering and loss accounting under their documented field mapping.
Deterministic data/envelope hashes do not prove acquisition or qualification.
This extension introduces no lifecycle GraphQL surface, new major namespace or
stability promise. VRC Explorer remains a standalone community tool.

## Source/sink conflicts and echo loops

| Condition | Required boundary |
| --- | --- |
| Two drivers claim one source | Refuse registration before effects; do not merge ownership |
| Two owners claim one output binding | Refuse conflicting registration; never pick the last registrant |
| Independent candidates disagree | Preserve candidates and conflict evidence; presentation policy cannot choose a native route or qualify a candidate |
| Multiple sinks consume one admitted fact | Allow independent explicit projections with separate target identities and loss reports; consuming adds no source ownership |
| Both-role driver sees its own exported value | Preserve truthful native observation evidence, but never treat an echo as independent corroboration or automatically derive another intent |
| Returned ancestry re-enters a target | Reject derived intent as `echo_suppressed` before I/O; preserve original correlation |
| Expired ancestry or exhausted hop budget | Withhold derived intent; a truthful observation may still publish with its actual evidence and quality |
| Equal values with independent ancestry | Equality alone is not loop detection and grants no authority; evaluate the separate intent under the existing rules |

Use the provider contract's `CausalContext`, not a new output-local loop service.
Preserve origin, correlation, parent correlation and entered-target path. An
external context starts empty at hop zero; locally created context starts with
its target at hop one. Egress changes neither path nor count. Ingress validates
count/path/expiry, rejects receiver re-entry before hop-budget exhaustion, then
atomically appends the receiver and increments the count. Rejection mutates
neither context nor correlation. Maximum hops remain 8; operation echo windows
are positive and at most 300 seconds. Keep correlation tombstones through the
later of the operation deadline or dispatch plus echo window, including clock
uncertainty. Duplicate correlation/operation admission and reflected ancestry
are suppressed without I/O. No missing ancestry may be fabricated as proof of
an independent operation.

## Synthetic-peer acceptance obligations

These are proposed implementation tests, not executed runtime results. Use
synthetic family peers and detached fixtures only, without native equipment.

| Case | Required observation |
| --- | --- |
| Registration and freeze | Exercise all three directions and disabled entries; invalid ownership, missing references and every unsupported hook yield zero factory/endpoint/publication calls. Caller mutation cannot change frozen registration |
| Source/sink conflict | Vary source owner and target binding independently; reject actual collisions while distinct sinks and unaffected sources remain usable |
| Lifecycle and D1 | START, same-desired START, STOP, START after STOP and RESTART; assert one successor per accepted replacement, old retirement and close before successor preparation, and no epoch allocation for a no-op |
| Late work and retirement | Hold an old callback and queued projection across epoch succession and generation reuse; neither can publish nor retire the new contribution. Unconfirmed close blocks replacement |
| Partial state and loss | Omit one field, reject another batch and make one sibling unavailable; retain the correct original value/aging/provenance, preserve zero/false versus absent, and withhold gated current output with explicit loss |
| Selection versus publication | Preview and change selection without output; explicit publication uses only validated detached input. Stale selection and lost response cannot silently republish or reroute |
| Loop and tombstones | Pass A to B to A, duplicate a correlation/operation, overlap re-entry and exhausted budget, expire ancestry and reconnect; assert correct refusal, unchanged rejected context and zero output I/O. Independent equal values are not suppressed merely for equality |
| Recovery and isolation | Destroy service/hub memory, restore D5 pending work, retirement and tombstones before admission; corrupt affected material fails closed without erasing unrelated last-known-good state |
| Ordinary surfaces and O8 | Preserve eBUS regression behavior and shared MCP/GraphQL detached-view parity; compiled registration remains the only package delivery path and no parallel service is constructed |

Future identity tests must vary driver, source, epoch, driver generation, output
binding and causal correlation/operation independently where claimed, with
independent expected values and a named production mutation each variant catches.
No mutation kills, native qualification, runtime integration, transport, passive
capture or physical acceptance are claimed by this documentation review.

Reconcile this page and the independently authored gateway bidirectional design
when that design merges. No sibling proposal or unmerged implementation is a
prerequisite or current implementation reference here. Parent integration,
independent review and committed-head gates remain separate acceptance work.
