# Runtime driver lifecycle: G5 registration, epoch and recovery contract

Status: proposed software 0.7 contract. This page specifies the selected D5
epoch policy D1/A2 and D5 recovery mechanism for gateway issue
[#1032](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1032),
PRs 0a/0b and amendments A1/A2/A6, covering S0/S5, S1, S3, S4 and CTL-01–CTL-11. It does not claim
that the runtime control service or durable recovery is implemented. The G4 publication hub has
an in-memory journal; that alone supplies no process-loss recovery.

The companion [gateway runtime/driver contract](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/architecture/runtime-driver-provider-contract-v1.md)
owns the provider SPI and CTL/LIFE vectors. The final G5 operator decisions
select service-side write-ahead persistence and gateway-owned hub export/restore
hooks, using SemReg's existing public `NewPublicationKernel` constructor and
`Apply`. No SemReg API, dependency change or snapshot-import prerequisite is
introduced. Earlier proposals for client command tracking and lifecycle
authorization in that contract must be read with the final D3/D4 decisions below.

## S0/A1: typed compiled-driver registration

This registration companion is the partial slice tracked by
[docs issue #652](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/652).
It must merge before or with gateway PR 1. Compiled driver packages live in the
gateway repository. The gateway owns descriptor format `v1`; DM-HOOKS owns
future hook schemas and implementations. This is a gateway-internal typed
registration boundary, not delivery of a universal public provider SPI.

Every descriptor contains the following immutable registration material:

| Field | Contract |
|---|---|
| `DriverID` | Canonical, unique, nonempty UTF-8 ID matching `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`, at most 128 bytes; stable across restart and gateway rename |
| Direction | Exactly `southbound`, `northbound` or `both`, explicitly selected per instance |
| Disposition | Explicit configured/enabled disposition; configuration eligibility is separate from durable desired state and current observed state |
| `NativeContractRef` | Nonempty `Owner`, `Contract` and `Version`, naming the public native owner, owner-defined contract and exact supported version/revision; sanitized, with no endpoint, credential, raw payload or handle |
| Lifecycle adapter | Typed factory plus Runtime binding over DriverManager; registration stores the adapter without invoking it |
| Owned `SourceID` set | Stable configured source identities, each exclusively owned by one driver across the entire descriptor set and existing hub ownership |
| Hook declarations | Optional versioned declarations; an empty set is required by this first host |

Direction expresses supported roles. It grants no forwarding, native operation,
publication, write permission, profile qualification or evidence grade.
`DriverID`, `SourceID`, semantic asset/binding identity and lifecycle correlation
remain distinct. A source derives from DriverID plus configured owner identity,
never an endpoint, connection handle, path or discovery result. Reconnecting or
changing an endpoint cannot silently change ownership.

### Validate and freeze before effects

Validate the **complete** descriptor set, including disabled entries, and freeze
detached copies before any factory invocation, semantic declaration or endpoint
call. Validate IDs, directions, dispositions, native references, adapters and
source ownership against both all other descriptors and the hub. Duplicate or
noncanonical driver IDs, duplicate source ownership and hub-source collisions
refuse registration before effects. Failure installs no partial registry and
mutates no hub ownership. Retain unaffected last-known-good state and provenance;
rejected registration never grants admission.

Recognize only hooks implemented by this host at their supported versions.
Unknown hook names and unsupported versions fail explicitly. The reserved
future names are `mcp`, `setup`, `portal`, `semantic` and `evidence`; **all hook
declarations currently fail**, including these names, because none is
implemented. Reserving a name is not accepting a nonfunctional control.
Registration and common lifecycle control contain no protocol, vendor or family
switch and perform no endpoint I/O or semantic declaration.

List/get read only the frozen registry and cached lifecycle state. List returns
all configured drivers sorted bytewise by `DriverID`, independent of registration
order. Entries and catalog revision come from one coherent read transaction;
get returns the corresponding coherent cached entry and `NOT_FOUND` for an
unknown ID. Neither operation constructs a driver, probes an endpoint, refreshes
native state or performs discovery.

### First production registration and dispatch evidence

`ebus.primary` is the only production registration in this slice. It is
southbound, configured/enabled and lifecycle-only. It owns one stable configured
source and declares no hooks, semantic assets, bindings, capability instances or
semantic publications. Native invocation capabilities remain separate from
semantic capability instances. The empty barrier and cleanup set are valid;
never fabricate semantic material to satisfy a binding-bearing provider SPI.

The native owner is
[`github.com/Project-Helianthus/helianthus-ebusgo`](https://github.com/Project-Helianthus/helianthus-ebusgo),
with the transport API exposed by
[`transport/driver_runtime.go`](https://github.com/Project-Helianthus/helianthus-ebusgo/blob/main/transport/driver_runtime.go).
These branch links identify the public owner and file, not a frozen dependency
version or native eBUS wire proof. The dispatch-pinned source provides
`transport.DriverRuntime`; the supplied material does not establish an
owner-defined contract identifier/version or the exact configured `SourceID`.
Those values are **Unknown** and remain dispatch acceptance blockers. Gateway
descriptor `v1` must not substitute for a native contract version. Do not install
a placeholder reference, derive identity from an endpoint or admit this driver
until the exact supported native contract and configured source are supplied
and validated. This page does not claim that production registration has passed.

### S0/CTL-01 synthetic acceptance obligations

Use synthetic southbound, northbound and both-role descriptors. Require zero
factory calls, semantic declarations, endpoint calls and state mutation for
noncanonical or duplicate DriverID, invalid direction/disposition, missing native
reference fields or adapter, duplicate sources, hub ownership collision, unknown
hook and unsupported hook version. Mutating caller-owned descriptors after freeze
must not alter the registry. Permute registration order and assert sorted,
coherent list/get views, including disabled entries, with no provider calls.
Prove registration/control packages import no protocol package and that the
production composition registers only `ebus.primary`. These are gateway test
obligations, not executed tests or wire-evidence claims in this prose slice.

The repository check `python3 scripts/check_runtime_driver_registration.py`
guards the registration documentation clauses above. It does not execute the
gateway acceptance obligations or establish native wire behavior.

## S5: deferred managed adapters and DM-HOOKS

Later managed sidecars must use this same validated registration path with their
own direction, native contract and exclusively owned sources. Each migration
owns durable intent/recovery, exact lifecycle correlation, pre-open barrier and
admission, activation proof, write-ahead publication/index, read-gated
reprojection, independent native-close proof, restart non-overlap, one native
retry owner and truthful status. Remove direct start/close ownership atomically
when its managed adapter takes over; never create a dual-owner window or register
a placeholder accepting controls it cannot execute. No family mutates another
family's state. Synthetic isolation fixtures use separate assets under the
current one-source-per-asset constraint.

The existing Portal contribution key is `{DriverID, Generation}` with no source
epoch, while driver generation restarts in each epoch. DM-HOOKS must supply a
per-DriverID monotonic contribution generation or an epoch-aware key before
contributions can safely span epoch succession. G5 registration does not solve
that limitation or implement Portal, MCP, setup, semantic or evidence hooks.
S5 sidecar migrations, shared-asset source isolation/LIFE-22 and the universal
public SPI remain deferred; this slice closes none of them.

## A2: explicit restart and start after stop

Final D1 selects a new source epoch for every accepted RESTART and START after
a completed STOP, as well as on process start. Final N1 requires this public
A2 companion to merge before or with gateway PR 0b; registration and service
documentation is a separate prerequisite of PR 1. This is the partial slice
tracked by [docs issue #650](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/650),
not completion of gateway #1032.

The stable `SourceID` derives from `DriverID` plus configured owner identity.
It never derives from an endpoint, path, connection handle or discovery result.
Changing a connection does not change source ownership. Keep source identity,
process incarnation, source epoch, driver generation, native generation,
lifecycle sequence and publication cursor distinct.

| Trigger | Epoch and reservation rule |
|---|---|
| Process start, including desired STOPPED | Create a new epoch and its inert generation-1 barrier reservation before provider work; historical admission is never current |
| First START from an initially STOPPED process, with no intervening completed STOP | Claim the existing inert generation-1 reservation at its persisted per-asset next cursors; do not allocate a second epoch |
| STOP of a started driver | Fence callbacks and admission immediately; retire the current epoch and finish semantic cleanup independently of native cancellation/drain/close. Publish STOPPED only after both obligations complete; STOP does not admit a successor |
| START after completed STOP | Allocate exactly one successor epoch/reservation after old-epoch retirement, settled control and proven native close; complete its barrier before preparation |
| RESTART | Require desired RUNNING and keep it RUNNING throughout the serialized stop-then-start operation. Retire and close the predecessor before admitting exactly one successor epoch/reservation; intermediate observed STOPPING is not a durable desired STOPPED decision |
| Manager-driven retry or failure replacement | Retain the epoch and advance driver generation through the existing Fence/Activate path; never turn an automatic retry into explicit epoch succession |
| Native reconnect | Retain the epoch. A reconnect that admits a replacement driver instance advances driver generation; an internal connection retry without replacement stays under the existing driver generation and native retry owner |

START and STOP remain idempotent by desired state under D3. A START while desired
RUNNING neither resets backoff nor allocates an epoch. Repeated reconciler wakes
for one accepted operation reuse its persisted successor and reservation; a new
accepted RESTART is a new operation, not a client-key replay.

### Publication-free hub-native succession

The new hub-native succession seam is allowed only after the old epoch is
retired and its control work, including reprojection, is settled. The service
also requires independent native-close proof before replacement. A nil manager
return or a semantic retirement alone is not that proof. Uncertain close retains
quarantine and prevents successor preparation, activation and admission; changing
epochs cannot clear it.

Derive the successor epoch from `(process incarnation, SourceID, admission
ordinal)`, with a strictly advancing per-source ordinal, and start its driver
generation at 1. Journal the succession and ordinal/reservation transition as
one all-or-none hub operation: journal failure exposes no successor handle,
consumes no usable reservation and cannot permit a parallel admission. Preserve
the predecessor's retirement history. Concurrent or repeated attempts for the
same accepted lifecycle operation resolve to that one recorded successor; they
must not allocate multiple ordinals, epochs or reservations. The service's
durable intent/outcome protocol below records the hub-only transition outside
hub and manager locks; an ambiguous result blocks replacement until resolved.

This operation requires no asset declaration or publication. The lifecycle-only
empty asset set remains valid and its generation-1 next cursor stays at 1.
For a nonempty source, carry the indexed and incomplete-cleanup asset set into
the successor barrier, retain old tombstones and history, and settle each
affected asset before provider work or admission. Each cursor is scoped to
`(asset, SourceID, epoch, driver generation)` as specified below; accepted
barrier work advances only that asset's cursor. Never reset a consumed cursor
or use a larger driver generation as a substitute for retiring an old epoch.

Do not borrow legacy `BeginEpoch`, legacy successor admission or `Withdraw`
rollback. `Withdraw` is a pre-publication rollback, not STOP or succession;
`Activate` cannot revive a retired epoch. Existing legacy identity regimes and
error behavior remain owned by their existing paths. A same-epoch cleanup
generation used to retire old work is not the new epoch's provider reservation.

Persist exactly one pending successor epoch and generation-1 reservation for
the accepted replacement, then its barrier results and exact claim before
`Prepare`. Claim, consume and activation retain their existing write-ahead and
readiness rules. Component recovery resumes the same claim and per-asset next
cursors, including uncertain exact bytes; process-loss recovery uses the new
incarnation and restoration rules below, never an old live handle.

### Generation mapping and late work

Map each full driver `GenerationKey` (source, epoch, driver generation, with
driver/operation correlation) explicitly to its process-monotonic native
generation before accepting native callbacks or admission. Persist the mapping
with the lifecycle correlation; after process loss it is historical only.
Driver generation resets to 1 in a successor epoch, while native generation
continues increasing within the process. Never compare a bare driver-generation
counter to a native generation or route a callback by generation number alone.

Fence old handles, staged publications, callbacks and late preparation/activation
results at the admission/publication serialization boundary using incarnation,
source, epoch, generation, admission identity and operation correlation. A late
result is never installed or published; abort or fence/stop it on its independent
bounded cleanup deadline, retaining quarantine without close proof. Native
retry, reconnect, lease drain and close ownership and budgets do not change;
the service supplies ordered intent, not a second native retry or drain owner.

### Amended LIFE expectations

These A2 expectations replace the companion's older same-epoch replacement
wording for LIFE-05/25/31/32. They are synthetic implementation acceptance
obligations, not claims that implementation tests have passed. A6's per-asset
cursors apply rather than an older shared sequence across assets.

| Vector | Required A2 observation |
|---|---|
| LIFE-05: successful close-before-Prepare RESTART | Desired stays RUNNING. Fence old callbacks/admission, retire and settle the old epoch, prove native close, then journal one ordinal-derived successor at generation 1. Complete its barrier and claim its exact persisted reservation before preparation/publication; no overlapping native owner |
| LIFE-25: initially STOPPED process, two barrier assets, first START, then RESTART | First START uses the initial inert epoch's existing generation-1 reservation and each asset's next cursor after its own accepted barrier. RESTART retires that epoch and claims one new epoch at generation 1 after cleanup and close proof; it never claims an old same-epoch cleanup generation or carries an old cursor into the new epoch |
| LIFE-31: START, completed STOP, second START with duplicate wakes and component recovery before Prepare | STOP permanently retires the first epoch. The second START and every wake/recovery reuse exactly one recorded successor epoch, generation-1 reservation and per-asset next cursors. No extra ordinal or epoch is allocated; old callbacks and handles stay rejected |
| LIFE-32: RESTART has uncertain/conflicting semantic withdrawal but native close succeeds | Preserve exact pending semantic bytes, accepted prefix, budgets and independent close proof. Desired remains RUNNING; no successor admission or preparation until old retirement/control settles. Resolve uncertain work first, then journal and claim exactly one new epoch/reservation without resetting any accepted cursor |

Also require synthetic negative cases for succession before retirement, pending
control/reprojection, journal rejection, concurrent duplicate succession and
unconfirmed native close. Assert zero replacement provider calls on refusal,
unchanged last-known-good identity/provenance on unaffected assets, old-handle
rejection after success, same-epoch manager retry with increasing native
generation, and a generation-1 successor mapped to a strictly later native
generation. LIFE-07–LIFE-10 late-result safeguards remain in force.

## Ownership and durable scope

The control service owns durable intent and outcome transactions. The hub owns
publication, its memory journal, and export/restore hooks. Hooks never persist
or fsync. Disk I/O occurs outside both hub and manager locks; a slow durable
write must not hold another family's admission read behind an fsync.

Every publication and control mutation of a registered, service-routed writer
uses this durable path. Direct G4 publishers in the storage, EVSE and PV
families remain memory-only until their managed adapters route every mutation
through the service. G5 grants them no durable-replay claim.

The first production registration, `ebus.primary`, is lifecycle-only. Its owned
asset set, barrier set and semantic cleanup set are empty. Do not invent an
asset, validator, binding, capability or provider observation to exercise
recovery. Nonempty restoration requires synthetic qualified publishers and is
mandatory when a managed publishing adapter is introduced.

This is a Helianthus platform contract, not native eBUS evidence or new device
write authority. [Native wire contracts](../protocols/) remain the
first authority for protocol facts. Preserve raw evidence and provenance beside
interpretation, with `Proven`, `Hypothesis` and `Unknown` distinct from codec,
profile and publication qualification. Recovery does not upgrade any evidence
grade, establish compatibility with another family, or reconstruct evidence
from a rescan.

## Complete recovery material

IDs and digests can verify a replay; they cannot reconstruct a kernel. For
every managed asset, retain the following material until a verified restore
point makes it unnecessary:

| Material | Required contents |
|---|---|
| Kernel inputs | Compatible asset identity and validator set; complete accepted publication **and control** batches as exact canonical bytes, in per-asset commit order, with each original monotonic point and publication instant |
| Clock continuity | Per-asset durable monotonic high-water mark, clock unit and mapping, and a restart-comparable elapsed-time anchor for that mark; cover every reserved point, including pending and rejected attempts |
| Accepted results | Each batch's accepted result, `SnapshotID`, semantic revision, digest and per-key publication cursor; hub commit position including incarnation and `HubSeq` |
| Hub-only history | Admissions, withdrawal rollbacks, activations, asset-less retirements and `RevokedUnpublished` revocations, including results even when no kernel batch exists |
| Control state | Per-asset semantic outcomes and reprojection settled history; source-publication index; epoch and generation reservations with exact per-asset next cursors; withdrawal correlation; retry/deadline budgets and independent native-close obligations |
| Pending work | Complete pending publication envelopes and staged control attempts as exact bytes, their per-source WAL sequences and per-asset intent ordinals, asset/source ownership, per-asset keys/sequences and monotonic points; no invented accepted result |

Fences, source retirements, withdrawals and generation-transition fences that
reach a kernel are accepted `PublicationBatch` inputs too. Exporting only
provider publications or epoch events loses retained tombstones and withdrawn
history. Publication cursors are scoped to asset, source, epoch and generation;
the first sequence of an unseen key is 1. `HubSeq`, lifecycle sequence and
publication cursor are distinct. Assets commit separately; no cross-asset
atomicity or shared publication sequence is implied.

## Export and two durable steps

Export supplies detached copies of staged bytes before submission and accepted
results after the hub call. Copying must not expose mutable aliases. The
service consumes those copies outside hub and manager locks; export itself
does no persistence and does not turn staging into an accepted result.

1. **Intent:** assign the service's per-source WAL sequence and, for each affected
   asset, a per-asset intent ordinal before the hub call. Durably persist them
   with the exact pending envelope or control attempt in the service transaction.
   Reserve its monotonic point under the same asset gate and atomically persist
   the advanced clock high-water mark and elapsed-time anchor with the intent.
   Only then submit it to the hub.
2. **Outcome:** after the hub call returns, durably persist its accepted result,
   commit position, monotonic point, semantic outcome and settled history in a
   second transaction. A rejected operation retains the SemReg error identifier
   verbatim and never enters the accepted replay stream.

A crash between those steps leaves an uncertain pending intent. It is not an
accepted batch merely because submission may have happened. A failed durable
transaction must expose no rejected staging through a later cache flush.

For each source, serialize WAL sequence assignment, durable intent persistence
and hub submission through completion of the hub call. A later WAL sequence must
not enter the hub before the preceding call completes; an ambiguous completion
blocks further submissions for that source until resolved. This serialization
uses a service-side per-source gate, never a hub or manager lock across disk
I/O. Sources that share an asset also obey the per-asset rule below; unrelated
sources remain independent. Outcome persistence may overlap a
later call, so durable outcome order can still differ. Before replaying a
recorded outcome, resolve all pending entries of its source with lower WAL
sequences. A dependent call follows its predecessor's returned hub call and
therefore has a higher WAL sequence. Recorded outcomes
carry hub commit positions so restoration preserves actual commit order,
including per-asset order. An unresolved source WAL gap fails that source
closed; a later recorded activation cannot bypass an uncertain admission.

For each asset, serialize intent ordinal assignment, durable intent persistence
and hub submission through completion of the hub call across **all** sources,
including control mutations. Use a service-side per-asset gate, never a hub or
manager lock across disk I/O. An ambiguous completion blocks further submissions
to that asset until resolved. The durable ordinal therefore orders uncertain
intents relative to later outcomes from any source, even when the earlier
outcome was never persisted. It is not a publication cursor or `HubSeq`, and a
rejected intent consumes its ordinal without becoming an accepted batch.
Outcome persistence may overlap later calls, but restoration must resolve every
earlier uncertain ordinal before applying a later outcome on that asset. Missing
or incompatible ordering material fails the affected asset closed. Multi-asset
operations retain an ordinal for each asset; this adds no cross-asset atomicity.

Acquire the per-source gate first, then all affected per-asset gates in one
canonical total order by stable asset identity, independent of caller enumeration
order. Acquire the complete asset gate set before assigning any intent ordinal,
persisting intent or entering the hub; never acquire a source gate while holding
an asset gate. Hold the gates through hub completion and release them in reverse
order, preserving the source and asset blocks for ambiguous completion above.

## Restore before admission

Restoration runs before any source admission in the new incarnation and refuses
an asset that already holds state. A compatible asset identity and validator
set, complete commit order, exact accepted bytes and original monotonic points
are preconditions. Changed validator behavior, including an upgrade that
changes replay acceptance, has no supported migration here and fails closed.

1. Construct each empty asset kernel with `NewPublicationKernel`. Replay every
   accepted publication and control batch through `Apply` in commit order,
   using its persisted monotonic point. Current-process time can change
   retained-observation expiry and must not replace that point. Restore the
   durable clock mapping below before allocating any new point, including for
   the new epoch barrier; pending exact-byte resubmission keeps its original point.
2. Verify every replayed result against its stored snapshot identity, semantic
   revision, digest and cursor. Any mismatch fails the affected asset closed:
   its reads remain closed and the affected driver reports `FAILED`. Preserve
   unaffected assets and their last-known-good identity, provenance and history;
   do not fabricate an empty successful snapshot or silently select a fallback.
3. Reinstate hub-only transitions, control gates, reservations and outcomes.
   Prior-incarnation admissions, activations, retirements and revocations are
   historical; no old epoch, callback, route or native-close claim is current
   merely because it survived on disk. A persisted settled flag never opens
   reads. Reprojection against the restored exact snapshot must acknowledge
   settlement before an affected read gate can reopen.
4. Resolve pending exact bytes under both the source WAL and per-asset ordinal
   rules before dependent outcomes, including outcomes from another source.
   Compare the exact asset/key cursor: a matching accepted sequence and digest
   permits exact replay/readback; an unchanged cursor permits exact-byte
   resubmission; an incompatible cursor fails closed. Never rebuild uncertain
   evidence or replay a rejected entry as accepted. Hub-only uncertain entries
   are reinstated as uncertain history, not current admission.
5. Only after reconstruction and gap resolution may the new epoch barrier
   retire prior epochs on every restored/indexed or incomplete-cleanup asset.
   New process epochs and the selected new epoch on RESTART or START after STOP
   fence prior work. Restore does not replace semantic cleanup, current
   admission/readiness checks or independent native-close proof/quarantine.

Steps 1–4 obey dependency order together: step 4's gap resolution precedes any
dependent accepted result, even when that result is listed in step 1. A corrupt
asset record closes that asset; a source-level unresolved gap closes that
source. Healthy unrelated paths remain available with unchanged provenance.

### Clock continuity after replay

Persisted points belong to an asset's durable logical timeline, not directly to
one process's clock origin. Let `H` be its durable high-water mark, `m0` the new
process's monotonic sample at restore, and `d` the verified elapsed duration from
the persisted anchor for `H` to `m0`, in the same unit. After historical replay
and pending gap resolution, allocate each new point as
`max(H + d + (m - m0), last + tick)`, where `m` is the current process sample,
`last` initially equals `H`, and `tick` is one representable clock unit. Keep
`H`, `d` and `m0` fixed for this process mapping. Advance `last` and durably reserve the new high-water mark with its corresponding anchor
before submission. Include pending and rejected reservations when recovering
`H`; never lower it on rejection, compaction or a second restart.

The elapsed-time anchor must remain comparable across the relevant restart,
including host restart if supported. Do not subtract samples from different
process clock origins or infer elapsed duration from an unverified wall clock.
Missing continuity, a backward clock, incompatible units or arithmetic overflow
fails the affected asset closed before new operations or reads resume. Downtime
therefore counts toward retained-observation age; restore never renews retention
or changes original publication instants. Historical replay still reproduces the
pre-loss state; the first new `Apply`, including the epoch barrier, evaluates
expiry at the advanced point using the existing kernel rules.

## S1/D3: minimal durable control decisions

This amendment is the partial slice tracked by
[docs issue #660](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/660).
It replaces the companion's unimplemented receipt and idempotency-record design,
including its request/result types, S1/S3 rules and CTL-03–CTL-11 expectations.
It is the public prerequisite for the durable store, service and MCP slices;
it does not claim those implementations have shipped. The choices below are
selected implementation bounds, with no remaining operator checkpoint.

Desired state has exactly two values: `RUNNING`, `STOPPED`. Observed state has
exactly eight: `DISABLED`, `STOPPED`, `STARTING`, `RUNNING`, `DEGRADED`, `BACKOFF`,
`STOPPING`, `FAILED`. Desired state is intent; observations are runtime facts.
Desired revision starts at 1 and advances only on accepted changing requests.
Catalog revision starts at 1, advances once per accepted decision and once per
externally visible observed-view transaction, and is distinct from desired,
native and semantic revisions, lifecycle sequence and publication cursors.
List/get return coherent cached views; historical observations grant no startup
or native admission authority.

### Validate, decide and commit

The request contains only `DriverID` and nonzero `ExpectedRevision`; the method
selects START, STOP or RESTART. A finite caller deadline comes from the call
context. Closed decoding rejects unknown/missing fields, duplicate members,
malformed revisions and trailing JSON. No lifecycle principal, authority,
idempotency key, canonical request digest, key lookup, receipt or completed-
operation record exists. Semantic replay digests remain D5 recovery material.

1. Validate shape, canonical ID and registered identity, configured/enabled
   eligibility, then the finite unexpired deadline. Unknown IDs return
   `NOT_FOUND`; disabled drivers return `FAILED_PRECONDITION` for mutations.
   No validation invokes a factory or endpoint.
2. Under the per-driver decision serializer, compare expected revision with
   current durable desired revision. Mismatch returns `REVISION_CONFLICT` and
   the current cached view without mutation, including for a would-be no-op.
   Recheck deadline before commit. Expiry before the commit point refuses the
   request; cancellation after commit cannot retract accepted intent.
3. START while desired RUNNING and STOP while desired STOPPED return the current
   desired state/revision without writing, waking reconciliation or allocating
   correlation. They do not reset retries/backoff, heal degraded generations,
   clear quarantine, change observations or bump either revision. This test
   precedes capacity checks, so repeated same-desired requests remain no-ops
   while bounded work or cleanup is outstanding.
4. RESTART requires desired RUNNING. Every accepted RESTART keeps RUNNING and
   increments desired revision, even if the observed driver is STARTING,
   BACKOFF or FAILED. Quarantine or unresolved recovery blocks changing work
   that would require unsafe admission; it is never cleared by a request.
5. Check transition capacity, storage and all required counter increments.
   Atomically persist desired/revision, typed in-flight work, its internal
   sequence/correlation and reservation before exposing acceptance or waking
   reconciliation. Pre-commit failure exposes no staged decision; periodic or
   cache/meta writes cannot later flush rejected staging. Ambiguous persistence
   fails admission closed until readback resolves the committed state.

Both accepted and no-op responses contain **desired state and desired revision
only**. They contain no operation ID, sequence, disposition or completion claim.
The ordinary deterministic MCP envelope remains; completion and failure are
observed through list/get. A lost response is resolved by readback. A repeated
RESTART with an updated expected revision is another requested restart; it is
never deduplicated by a fabricated key. Retrying the old revision conflicts.
Readback can show later intervening decisions and does not promise attribution
of a completion to a particular client call.

### Bounded typed transition and truthful completion

Each driver has at most two typed work slots: one current transition (including
its outstanding cancellation/native close and semantic cleanup), and one reserved
next transition. The reserved slot holds at most one replacement and never a
queue. Store the exact kind, accepted desired revision, lifecycle sequence,
phase, full lifecycle correlation, old attempt, cleanup obligations and budgets;
a replacement also retains its exact successor reservation. Internal sequences
are not client operation handles and survive only while recovery needs them.
No wake or recovery infers work from desired state alone.

From a stable driver, STOP or RESTART occupies the current slot. During STARTING
or BACKOFF, accept STOP or RESTART only if the reserved slot is empty and no
accepted RESTART is still executing. Acceptance immediately fences the old
attempt's callbacks, publications and admission, cancels its preparation or
scheduled retry, and retains the old correlation for late-result cleanup.
The old START may terminate as canceled; its cleanup is never discarded. The
reserved STOP completes only after cleanup and native close; reserved RESTART
executes its own stop-then-start after those obligations settle. It cannot be
replaced by a later STOP or RESTART. An accepted RESTART is never coalesced away.

A changing request arriving during STOPPING, an executing RESTART, or with both
slots occupied returns retryable `TRANSITION_BUSY`, with no revision or state
change. The caller reads current state and retries with its current revision
after work settles; there is no server retry queue. In particular, START after
a pending STOP waits for completed STOP. This deliberately bounded refusal is
separate from the same-desired no-op rule. Unrelated drivers and list/get remain
responsive; decision serialization never holds hub or manager locks over disk
I/O, native calls, cancellation or drain.

Persist phase/observation updates before releasing the next slot. Native close
and semantic cleanup are independent obligations. Publish STOPPED only when
both complete; nil manager return alone proves neither. A proven drain timeout
with subsequent close may be restartable; unconfirmed close reports
`FAILED/CLOSE_UNCONFIRMED`, retains quarantine and blocks replacement. Semantic
conflict/exhaustion preserves exact pending work and closed affected read gates
regardless of native-close success. Late preparation/activation is never
installed; independently bounded cleanup retains its original correlation.
Retry ownership stays native; control no-ops cannot renew its budget.

On component recovery resume exact work and reservations. After process loss,
restore D5 first, fence historical correlations and reconcile each retained
kind in order under the new incarnation. An unfinished RESTART still performs
one replacement even though desired already says RUNNING; no old native-close
proof authorizes current admission. Only after terminal obligations are durable
may their operation slot be removed. Retain recovery-reachable correlation in
D5, not in a completed-command record.

## S3/D2: bootstrap, load failures and explicit repair

Use the independently versioned `runtime_control` namespace, format version 1,
under the sole runtime-state writer. Preserve GUID ownership, top-level/meta
versions and unknown namespaces. Stage privately, serialize with all other
runtime-state writes, use same-directory temporary output, required file fsync
and atomic rename, then expose committed state; directory fsync is best effort.
No cross-filesystem fallback and no GUID generation/replacement is allowed.

A fresh, readable, valid base with a genuinely missing namespace gets exactly
one atomic seed: enabled drivers RUNNING/revision 1, disabled drivers
STOPPED/revision 1 and observed DISABLED. Bootstrap is not a user START; its
RUNNING reconciliation happens despite subsequent START being a no-op. Once
seeded, stored STOPPED survives restart with no endpoint opened. Disabled
configuration always wins over stored RUNNING and prevents admission; it does
not silently rewrite durable intent or permit START/RESTART to enable a driver.

Missing, corrupt, unreadable and unsupported are distinct load dispositions.
Corrupt/unreadable/unsupported control state starts the HTTP/API/health shell
but withholds affected eBUS as FAILED; no empty-state or RUNNING fallback is
allowed. Preserve bad bytes and quarantine before any repair. A malformed known
driver record fails that driver closed while valid independent records remain
usable. Whole-file corruption/unreadability withholds all dependent drivers and
must never create a new GUID or overwrite the unreadable file as a fresh base.

### Offline namespace-only reset

The selected maintenance interface for the later store implementation is the
standalone command below (a specified deliverable, not a shipped executable):

```text
gateway-runtime-control-reset --state-file <runtime-state-file> --namespace runtime_control --desired STOPPED
```

Run it only with the gateway process stopped. It takes the same exclusive store
lock and refuses if a process/writer still owns the file. The namespace and
STOPPED value are fixed accepted choices; there is no whole-file reset mode,
gateway startup flag, MCP repair tool or online bypass.

Validate readability, the entire base structure and the existing valid GUID
before touching anything. Whole-file corruption/unreadability is refused until
a valid GUID-preserving base is restored externally. Unsupported or malformed
namespace bytes within an otherwise valid base may be reset, but first preserve
an exclusive, non-overwriting quarantine copy of the exact original bytes and
fsync it. Failure to preserve that copy aborts reset. Existing quarantine copies
are never deleted or replaced. Copy GUID, meta and all other opaque namespaces
unchanged; atomically replace only `runtime_control` with version-1 STOPPED
records at revision 1 for the configured IDs, catalog revision 1, and no active
operation. Resolve IDs from the installation’s existing read-only configuration;
if that configuration cannot be validated, refuse rather than guess IDs. The stopped-process reset starts a new control history and cannot be
mistaken for an online revision rollback; old client revisions are invalid
across repair. A fresh process incarnation fences old callbacks and reservations.

Reset deliberately discards the active namespace, including its D5 recovery
stream; the quarantined original remains available for recovery investigation.
It supplies no replay, semantic cleanup or native-close proof. A source with
unresolved retained/indexed semantic state stays read-gated and FAILED until
valid D5 recovery material is restored and verified; resetting cannot manufacture
an empty successful snapshot. The lifecycle-only empty asset set may remain
STOPPED after reset. No native start occurs as part of this command.

## S3/D3: finite retention and D5 preservation

Durable minimum is desired/revision, the bounded typed in-flight work and the
complete D5 replay/recovery material specified above. Version 1 permits at most
128 driver records and a 64 MiB encoded control namespace, including pending
work and restore material. Reject registration beyond the driver limit before
effects. Reserve space before accepting work for its bounded outcomes/cleanup;
if the full reservation cannot fit, return retryable `RESOURCE_EXHAUSTED` before
acceptance. Never evict reachable recovery material to admit a new request.
Per-operation semantic attempts are limited to 8 and a 30-second overall budget;
activation staging remains at most 128 unique-asset batches/8 MiB. Persist budgets
and do not renew them on wakes, no-ops or component recovery. These service
bounds do not change native retry, drain or close defaults, and expiry never
asserts close or erases unfinished cleanup.

Desired/catalog revision, internal lifecycle sequence, WAL sequence, asset
ordinal, epoch ordinal and generation counters are unsigned 64-bit values,
initially 1 when first allocated. Check every increment and clock arithmetic;
refuse before mutation at overflow with `COUNTER_EXHAUSTED`, never wrap or reuse.
No-ops allocate no counters. Counter exhaustion does not prevent already
reserved cleanup or falsify its status; if its next required increment cannot
be represented, retain work and fail the affected path closed.

Completed operations have no durable record. Diagnostics keep only a sanitized
in-memory ring of at most 32 terminal summaries per driver, at most 512 bytes
each, dropped on process exit and never used for admission, deduplication or
recovery. No principal, request digest, endpoint or raw error is logged.
Accepted kernel results and cursor replay records are recovery material, not
client receipts. Compact only at a verified restore point that reproduces
snapshots, retained history, cursors, ordering and clock continuity and preserves
all reachable pending/cleanup work. Verify the new restore point before atomic
replacement; failed verification preserves the old recovery stream.

Process shutdown preserves desired intent and recovery material. Cleaning native
resources is not an accepted STOP, desired-revision change or deletion of pending
work; never copy the manager's shutdown-local STOPPED back into durable intent.
A downgrade preserves the namespace opaquely but ignores intent and may start
eBUS even when stored desired is STOPPED. Re-upgrade restores intent and D5
recovery, not receipts; test that round trip with an unknown namespace and an
unchanged GUID. D5 exact-byte write-ahead, two-step outcomes, gap resolution,
verified compaction and independent cleanup remain mandatory.

### Amended CTL acceptance vectors

These replace receipt-specific expectations, not passing implementation results.
Use synthetic IDs, fixed deadlines and explicit scheduling barriers.

| Vector | Required D3 observation |
|---|---|
| CTL-01 / CTL-02 | Coherent sorted cached list/get; unknown ID returns NOT_FOUND with no factory calls |
| CTL-03 | Stale expected revision conflicts even for a same-desired request; no mutation |
| CTL-04 | Lose an accepted START response, restart the process and read back durable desired/revision; same-desired START is a no-op, without any key/receipt lookup |
| CTL-05 | Accept only `DriverID` and nonzero `ExpectedRevision`; reject every additional request member as invalid shape; valid control uses only the validation and atomic decision steps defined above |
| CTL-06 | START in desired RUNNING across DEGRADED/BACKOFF/FAILED and STOP in desired STOPPED with unconfirmed close preserve retry budget, quarantine, observations and both revisions |
| CTL-07 | RESTART in desired STOPPED refuses; each accepted RESTART in RUNNING advances revision and executes one replacement |
| CTL-08 | Pause STARTING and separately BACKOFF; STOP/RESTART fence/cancel the old attempt, retain cleanup correlation and reserve one exact next kind; another changing request gets TRANSITION_BUSY; no accepted RESTART disappears |
| CTL-09 | Lose process memory during active RESTART; D5 restores pending work and the new incarnation performs its retained replacement before dropping the slot |
| CTL-10 | Lost RESTART response is resolved by readback; old-revision retry conflicts and a fresh-revision retry after settlement executes another restart |
| CTL-11 | Same-desired requests during occupied slots remain no-ops with only desired/revision returned; no new durable record, wake or counter allocation |

Also prove disabled/deadline/shape refusals, storage exhaustion, every counter's
overflow refusal, quarantine retention, offline-reset refusal on an active writer
or invalid base, exact quarantine preservation, GUID/meta/opaque round trips,
and corrupt/unsupported loads without empty fallback. Two-driver fixtures must
show B and list/get remain responsive while A blocks in persistence or cleanup.
These are service/store/MCP test obligations; this prose slice executes none of
them and changes no schema/output golden. Later payload goldens must remove
receipt/key fields and record only the amended desired/revision response.

## D4/public surface boundary

Final D4 removes G5 lifecycle principal/authorization checks and the proposed
kernel operator boundary; lifecycle tools use ordinary MCP. It does not remove
native-write safety or unrelated eeBUS safeguards. Every MCP namespace is
pre-stable until 1.0, including existing eBUS namespaces: no new major or
experimental namespace is introduced. Intentional payload changes require
documentation, deterministic envelopes, schema/output goldens and PR
explanation. Preserve existing eBUS MCP/GraphQL parity; this recovery seam adds
no lifecycle GraphQL surface and no new public tool payload.

## Required synthetic restoration proof

These are implementation acceptance obligations, not passing test claims for
this documentation slice. Use a synthetic two-asset publisher with fixed
clock inputs, IDs and schedules, with a reset process clock on restart rather
than one continuous process-clock schedule. Destroy both service and hub memory
and reconstruct fresh instances with no shared state. A lifecycle-only empty barrier cannot
satisfy this proof.

| S3.9 case | Required observation after restoration |
|---|---|
| Accepted publications followed by an accepted fence | Replay includes the control batch; retained tombstones and withdrawn history survive |
| One submitted envelope with no outcome, before hub return and after acceptance but before outcome persistence | Only pending intent survives; exact cursor comparison selects exact-byte resubmission or accepted replay/readback without rebuilding bytes |
| Mid-cleanup | Original asset set, budgets, correlation and exact pending attempts survive; native close and semantic cleanup remain independent |
| Unfinished control: one asset accepts and the other rejects | Both affected read gates stay closed initially; the accepted asset opens only after reprojection against its restored snapshot |
| Rejected publication envelope and rejected control attempt | Neither is applied as accepted; each cursor stays at its pre-rejection value and the original error identifier survives |
| WAL gap: A accepted without durable outcome, dependent B accepted and recorded | Resolve A before B; never replay B alone. Removing A's intent must fail the source closed |
| Cross-source asset gap: source A commits to an asset without a durable outcome; source B then commits to the same asset and persists its outcome | After memory loss, use durable per-asset ordinals to resolve A before replaying B and reproduce the pre-loss snapshot, retained history and both source cursors. Missing A's intent or ordering material fails that asset closed; an unrelated asset remains recoverable |
| Concurrent same-source callers: A holds the lower WAL sequence and is paused before hub completion while B is ready | B cannot enter the hub until A completes; delay A's outcome persistence until after B's, then lose memory and verify recovery resolves A before replaying B with matching snapshots |
| Concurrent different-source operations enumerate the same assets as A then B and B then A; pause the first after acquiring the first canonical asset gate and start the second | The second cannot hold B while waiting for A; neither assigns ordinals, persists intent or enters the hub before acquiring both asset gates. Release the pause and require both calls to complete within a stated bound; then lose memory and verify restoration preserves per-asset commit order and both source cursors |
| Reset process clock below all persisted points, including an uncertain intent above the last accepted point; repeat restart after a new operation | Replay at original points; each new publication and control point exceeds all prior reservations. Verify remaining retention with known downtime both shorter and longer than the expiry interval; missing or backward elapsed-time continuity fails only the affected asset closed |
| Corrupt replay or incompatible validator, snapshot, revision or cursor | Fail the affected asset closed without damaging an unaffected asset |

For each successful reconstruction, compare `Inspect` snapshot identity,
canonical bytes, revision vector, retained history, per-key cursors and exact
replay results with the pre-loss accepted state. Verify the new barrier retires
prior epochs on both assets and that no old callback or admission becomes
current. Prove another family's admission reads remain responsive during a
blocked durable write, using a stated bound.

This covers S3.7–S3.9/A6 recovery obligations and the recovery aspects of
LIFE-06, LIFE-19, LIFE-21, LIFE-23–LIFE-24 and LIFE-26–LIFE-30. The amended
CTL vectors above replace receipt-specific expectations; this page does not claim
they pass. LIFE-22 source-isolation acceptance remains a separate prerequisite.
PR 0a provides the prerequisite hooks and hub restoration proof without a
production service caller; PR 1 supplies service persistence and end-to-end
restoration. Neither a hooks-only slice nor this page completes gateway #1032.
