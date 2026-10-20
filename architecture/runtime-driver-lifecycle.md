# Runtime driver lifecycle: G5 registration, epoch and recovery contract

Status: proposed software 0.7 contract. This page specifies the selected D5
epoch policy D1/A2 and D5 recovery mechanism for gateway issue
[#1032](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1032),
PRs 0a/0b and amendments A1–A6, covering S0/S5, S1/S2, S3, S4/S6/S7 and CTL-01–CTL-19.
A5 is implemented as an internal service for lifecycle-only `ebus.primary` only by
[gateway PR #1241](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1241).
The first external ordinary-MCP contract below is pending gateway PR 2.
Internal service/write-ahead recovery exists; direct G4 publishers still have
an in-memory journal, which alone supplies no process-loss recovery. This page
claims no hardware validation or universal provider SPI.

The companion [gateway runtime/driver contract](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/architecture/runtime-driver-provider-contract-v1.md)
owns the provider SPI and CTL/LIFE vectors. The final G5 operator decisions
select service-side write-ahead persistence and gateway-owned hub export/restore
hooks, using SemReg's existing public `NewPublicationKernel` constructor and
`Apply`. No SemReg API, dependency change or snapshot-import prerequisite is
introduced. Earlier proposals for client command tracking and lifecycle
authorization in that contract must be read with the final D3/D4 decisions below.
The companion's historical idempotency key,
receipt, `IDEMPOTENCY_CONFLICT`, `PERMISSION_DENIED` and persistent idempotency
lookup are superseded by this page; the amended control error enum includes
`TRANSITION_BUSY`, `RESOURCE_EXHAUSTED` and `COUNTER_EXHAUSTED`.

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

### First production registration and historical dispatch evidence

`ebus.primary` is the only production registration in this slice. It is
southbound, configured/enabled and lifecycle-only. It owns one stable configured
source and declares no hooks, semantic assets, bindings, capability instances or
semantic publications. Native invocation capabilities remain separate from
semantic capability instances. The empty barrier and cleanup set are valid;
never fabricate semantic material to satisfy a binding-bearing provider SPI.

The following paragraph preserves the original registration dispatch evidence,
before production composition landed; its Unknown/blocker statements describe
that earlier supplied material. Current A5 composition status follows it.

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

Current A5 composition derives the configured source from DriverID and the
persisted instance GUID before endpoint work. Its native reference names the
public transport module, `transport.DriverRuntime` and the exact linked module
version; a workspace/replacement build reports `devel` verbatim. A missing GUID
withholds the driver as FAILED without a placeholder. This is software
composition evidence from the companion's S4/S6/S7 section, not native wire
proof, profile qualification or a concrete device identity published here.

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

## S4/A3/A4: lifecycle-only eBUS bridge

This bridge companion is the partial slice tracked by
[docs issue #692](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/692).
Publish A3/A4 and S4/S6/S7 before gateway manager/composition changes. Final
D1/D2/D3/D5 are settled as described on this page; they are not open choices
from the earlier issue draft. **A5 is implemented internally** for
`ebus.primary` by the merged gateway composition. Public lifecycle tools remain
pending PR 2 under [the D4 MCP contract](../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4).
That status supplies no universal provider SPI or hardware-validation claim.

### Source ownership without semantic assets

The bridge adapts the existing DriverManager and native runtime. The manager
is the sole owner of native attempts, reconnect/backoff scheduling and native
retry budgets; the control service owns durable decisions and ordered
reconciliation. Semantic control retries keep their separate finite budgets
and never start a second native retry loop. Admission-hold and close-result
hooks must release manager locks before hub work, persistence or native I/O.

A3 separates the companion's semantic `ObservedRecord.EffectiveCapabilities`
(`CapabilityInstance` values) from a typed native effective-capability field.
For `ebus.primary`, semantic effective capabilities remain empty until the
family's semantic migration. Native effective capabilities report only the
currently admitted native invocation gates and are withdrawn with native
admission. In particular, the manager's `SEMANTIC_PROJECTION` gate for legacy
consumers is a native invocation capability, not a semantic capability instance
or a hub publication. The historical `DriverSnapshotV1` proposal's
`effective_capabilities` field in the [retired driver API](../api/driver-runtime-v1.md#field-invariants)
retains that native meaning; it must not be populated with semantic instances.
The first external five-tool [G5 MCP contract](../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4)
uses its closed driver projection without capability fields; the historical
snapshot is not an implementation or acceptance target.

A4 is a bounded lifecycle-only exception to the companion's binding-bearing
SPI. An asset-free source needs no semantic binding, capability instance,
binding-bearing `ActivationProof`, or fabricated admission capability/binding.
Do not manufacture an asset, validator or observation to fill those shapes.
The bridge still requires exact lifecycle correlation, current native readiness,
the source barrier and native admission checks. This exception confers no
qualification, native write permission or semantic publication authority;
a later family migration must satisfy its full semantic activation contract.

### Shell and preparation order

Compose the frozen registration and control service before eBUS reconciliation.
Start HTTP, health, MCP, GraphQL and status independently of a driver reaching
RUNNING; STOPPED, a slow/failing START or corrupt control state must not park
shell startup behind `WaitRunning` or terminate the shared process. Stable
process-owned active/passive handles survive stopped periods and expose truthful
unavailability. Close mutation admission first on process exit, retaining reads
until shell teardown. Shutdown does not rewrite durable desired intent.

For a valid configured source, even when initially desired STOPPED, establish
the stable `SourceID`, persist the lifecycle correlation, admit the inert source
without declaring an asset, and complete its empty epoch barrier/reservation
before any endpoint construction. This is hub source ownership, not current
native I/O admission or observed RUNNING. Restore retained D5 material first
when present. A control-load failure withholds preparation and admission rather
than inventing a fresh source or RUNNING decision; the shell remains available.
Persistent desired state, cached addresses and historical RUNNING are never
current admission. The first START claims the initial inert reservation; later
succession follows A2, including retirement before start and no overlapping
native owner.

### STOP and generation task ownership

At the STOP/RESTART fence boundary immediately revoke new native leases, B503
issuance, proxy readiness, the admitted bus source and old callback authority.
Previously issued B503/proxy calls cannot retain old-generation authority.
Then reconcile two independent obligations: fence the exact semantic generation
and retire/settle its epoch, and cancel/drain/close native work. Semantic failure
or blocked reprojection cannot delay native cancellation and close work; proven
native close cannot erase unfinished semantic cleanup. STOPPED requires both
obligations complete, including the asset-free source's retirement. Read the
hub view for that source's lifecycle truth; its bounded, overflow-capable
source-level retirement event is notification, not completion proof.

Use the native close classification, not a nil manager return, as evidence.
An independently proven close after drain timeout may be restartable;
unconfirmed close retains quarantine, reports FAILED/CLOSE_UNCONFIRMED and
blocks replacement preparation, activation and admission. An internal error is
not close proof. Preserve exact pending cleanup, accepted prefixes, original
correlation and budgets when either obligation fails. No epoch change or
same-desired START clears uncertainty.

Move the post-`WaitRunning` source validation, scan, semantic polling,
revalidation and promotion orchestration into tasks owned by the full admitted
generation correlation, including its explicit native-generation mapping.
Cancel **and join** all such work before replacement; cancellation alone is not
completion. A task that cannot join within its bound keeps replacement blocked
and status truthful. Late callbacks, provider/health results and publications
remain fenced at the serialization boundary. Do not install their results into
a successor or relabel retained data as a current observation.

Run current-session source validation and each configured startup task once per
admitted generation, including a later START from STOPPED and a manager-driven
replacement. Repeated wakes do not duplicate tasks, and admission is required
before capture/acquisition tasks run. Polling loops may iterate within that one
generation-owned task; once per generation describes task startup, not one poll.
Keep stable process handles and reuse native scan/poll/revalidate/promote
functions. This orchestration neither transfers their protocol ownership nor
adds a retry owner. Native reconnect does not rotate the epoch; replacement
within that epoch still fences and joins predecessor work.

## S6: shell status and public parity

Daemon status continues to describe the process. Adapter status must use current
native admission, so retained firmware or cached identity cannot make a STOPPED
or FAILED adapter appear running. Preserve readiness field names and the proxy
DISABLED/DEGRADED/READY vocabulary, deriving proxy READY only from live
admission. HTTP/process readiness remains available with intentionally stopped
eBUS; no generic driver collection or eeBUS replacement is added to readiness.
Status/list/get use cached coherent views, perform no endpoint I/O and stay
responsive throughout preparation, backoff, cleanup and control-load failure.

Full desired/observed lifecycle views use the ordinary MCP service surface;
there is **no lifecycle GraphQL API**, resolver, mutation or subscription.
Existing daemon/adapter MCP and GraphQL status remain equivalent, including
unavailable cases. The intended payload differences are truthful gating of
existing adapter running/admitted-address fields and proxy readiness after
withdrawal, and retained evidence with original provenance/age while capture is
paused. They are not evidence of new semantic capabilities or a new status
schema. Document each actual difference and update deterministic envelope and
schema/output goldens, with the reason in the implementation PR. Every MCP
namespace is pre-stable before 1.0; neither an existing name nor a golden gives
a stability promise, and no new major or experimental namespace is introduced.
Final D4 removes lifecycle principal/authorization checks only; native-write
safety and unrelated eeBUS safeguards keep their owners.

## S7: retained eBUS evidence and deferred store move

Bus observability, identification evidence and the active/passive deduplicator
remain process-scoped. STOP, START and RESTART do not move, clear or reset those
stores. Capture pauses while no generation is admitted; existing records and
partial last-known-good state retain their native identity, provenance and age.
A later START resumes capture under the new admitted correlation without
rewriting old records as fresh or granting I/O from a cache. Evidence grades
`Proven`, `Hypothesis` and `Unknown` remain separate from codec/profile
qualification and current admission. G5 changes neither evidence semantics nor
retention policy and supplies no new native wire claim.

Characterize bus/identification-evidence MCP tools and GraphQL fields across
STOP→START, preserving shapes, retained-record meaning and classification.
There is no bus-tool reclassification or closure of
[gateway #1020](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1020).
The reserved `evidence` hook remains unimplemented and declaring it fails
registration. This contract does not turn process stores into driver hooks.

[gateway #1021](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1021)
and DM-RAW retain the later move of stores, observers and deduplicator behind
the eBUS driver, observer rewiring, contributed read views and metrics split.
LEGACY-IDENTITY G2/G2c retains native raw identification acceptance and its
passive/live evidence obligations before that move. G5 absorbs neither owner's
implementation or acceptance evidence; filename gate classification does not
waive those later behavior obligations.

### S4/S6/S7 synthetic acceptance obligations

These are gateway implementation vectors, not passing runtime tests from this
prose-only slice. Use synthetic/public fixtures with fixed clocks and explicit
barriers; keep native wire facts under their public native documentation owner.

| Case | Required observation |
|---|---|
| Initially STOPPED; slow/failing START; corrupt/unreadable/unsupported control | HTTP/health/status and MCP/GraphQL reads stay responsive within a stated bound. Valid STOPPED prepares the inert source/barrier with zero endpoint construction; control failure stays FAILED without RUNNING fallback |
| Lifecycle-only activation | No invented asset, binding, semantic capability or binding-bearing ActivationProof; semantic capabilities empty and native gates separately reported; no native admission before readiness |
| STOP during STARTING, RUNNING or BACKOFF | Leases, B503, proxy and callbacks lose authority immediately; no stale-generation I/O. Block semantic cleanup and prove native cancellation progresses; then block close and prove semantic retirement progresses. STOPPED requires both |
| Close uncertainty and late results | FAILED/CLOSE_UNCONFIRMED blocks replacement even after semantic success; late provider/health/publication results never install; proven close alone does not bypass pending cleanup |
| STOP→START, RESTART and same-epoch manager replacement | All predecessor scan/poll/revalidate/promote tasks are cancelled and joined before replacement; current-session validation and configured tasks start once per admitted generation, with repeated wakes unable to duplicate them; manager remains sole native retry owner |
| Cached status and retained evidence | STOPPED/FAILED has no admitted address or proxy READY and retained firmware cannot imply running. MCP/GraphQL daemon/adapter unavailable cases agree; evidence stores retain identity/provenance/age and partial last-known-good values with capture paused while unadmitted |

Apply these alongside the amended A2 LIFE vectors, CTL-17/18 bootstrap/config
vectors and the companion's applicable LIFE-01–LIFE-10 and LIFE-14–LIFE-32
obligations. No close, replay, isolation or native-write safeguard is weakened.
Intended output changes need characterization/goldens in the gateway slice;
this page changes no executable payload, schema or golden. The docs gate checks
documentation only; protocol/transport execution and physical acceptance are
not supplied by this page.

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
A5 is implemented as an internal service for `ebus.primary` only, not a
universal provider SPI; the external ordinary-MCP slice remains pending.
The choices below are
selected implementation bounds, with no remaining operator checkpoint.

Desired state has exactly two values: `RUNNING`, `STOPPED`. Observed state has
exactly eight: `DISABLED`, `STOPPED`, `STARTING`, `RUNNING`, `DEGRADED`, `BACKOFF`,
`STOPPING`, `FAILED`. Desired state is intent; observations are runtime facts.
The namespace holds one issued-revision high-water mark: the highest desired
revision ever issued under this GUID, starting at 0 on bootstrap. Every
accepted decision (including each bootstrap seed) and every repair writes the
mark in the same atomic transaction as the records it changes. Each accepted
decision takes mark + 1 as its driver's new desired revision and stores that
value as the new mark, so desired revisions are unique across all drivers and
all time within the namespace, and a driver's current desired revision is
simply the number of its last accepted decision. A driver with no record has
never been decided: reads return desired `STOPPED` with `desired_revision` equal to the
current mark, which a client echoes, and its first accepted decision must carry
`ExpectedRevision` equal to that mark, compared exactly like any other
optimistic comparison, and takes mark + 1. Revision 0 is not a sentinel for "no
record"; it is the mark only in a namespace where nothing has ever been
decided. Removing a driver is a durable decision recorded as a mark-only write
(the mark becomes mark + 1) in the same atomic transaction that deletes the
driver's record, once it holds no in-flight work or reachable D5 material.
Registering a driver into an existing namespace, on first appearance or
re-add, is likewise a mark-only write in the same transaction that makes the
driver visible, before any read of it returns the mark. A re-added ID therefore
continues above every earlier revision, and a request held before a removal or
a re-add always carries a mark lower than the current one and is refused with
`REVISION_CONFLICT`, even when no other decision happened in between. Bootstrap
seeds configured drivers as decisions, so registration there is not a separate
mark-only write.

Catalog revision starts at 1, advances once per accepted decision and once per
externally visible observed-view transaction, and is distinct from desired,
native and semantic revisions, lifecycle sequence and publication cursors. It
is a view counter only: it orders cached list/get views, is never compared with
a desired revision and is never used for optimistic control. Persist every catalog advance before exposing the new view;
the durable catalog revision bounds every view issued under this GUID, survives
restart and is never reused. Repair preserves it and advances it exactly once,
from validated `C` to `C + 1`; it never regresses.
List/get return coherent cached views; historical observations grant no startup or
native admission authority.

This durable write is not deferred to the periodic cadence of the
[runtime state](runtime-state.md) page: every accepted decision with its mark
advance, every mark-only write and every repair is written durably and
atomically before the decision is acknowledged or its view exposed, and every
catalog advance is written before its view is exposed, so a crash cannot lose
an acknowledged intent or an issued revision.

Durability here includes the rename: the parent-directory fsync error
tolerance of the generic runtime-state namespaces does not apply to control
transactions. If parent-directory durability cannot be established, the
transaction fails closed: nothing is acknowledged, no view is exposed and no
mark or catalog revision is issued, so recovery can never load an older desired
state while a revision believed issued is reused. A failure before the rename
is a pre-commit failure refused with `UNAVAILABLE`; a failed directory fsync
after a successful rename is ambiguous persistence, handled below.

Directory durability is established, never inferred. A failed parent-directory
fsync after a successful rename leaves the rename not durable even though a
readback observes the new bytes. Until directory durability is established
(the directory fsync retried to success, or the namespace rewritten durably by
temporary file, file fsync, rename and directory fsync) the new view is not
exposed, nothing is acknowledged and admission stays closed. Readback agreement
between the stored bytes and the cached view alone never reopens admission,
because a power loss can still restore the previous mark and let a revision
that was exposed be issued again after restart.

In JSON, every revision in responses (desired revision, catalog revision and
the current view returned with a refusal) is a canonical decimal string: ASCII
digits only, no sign, no leading zero except `"0"`, at most the unsigned 64-bit
maximum. `ExpectedRevision` in a request is stricter: a canonical decimal
string of a nonzero unsigned 64-bit value, so `"0"`, leading zeros, signs,
whitespace and non-digits fail shape validation with `INVALID_ARGUMENT` before
any other check. Zero never needs to be sent: bootstrap seeds every configured
driver as a decision at mark + 1, so the mark is at least 1 whenever any driver
exists, and a driver with no record reads the nonzero mark, which is what its
first decision must carry. Responses may show `"0"` only as the mark of a
namespace in which nothing was ever decided (no driver configured), which no
request can target. Internally revisions are unsigned 64-bit values; an
increment that would exceed that maximum refuses with `COUNTER_EXHAUSTED`.

### Validate, decide and commit

The request contains only `DriverID` and `ExpectedRevision`; the method
selects START, STOP or RESTART. This page supersedes the request-member rules
of `api/driver-runtime-v1.md`: `idempotency_key`, `request_id` and any receipt
or completed-operation member are not accepted, and a request carrying them is
refused as `INVALID_ARGUMENT` like any additional member. A finite caller deadline comes from the call
context. Closed decoding rejects unknown/missing fields, duplicate members,
malformed revisions. No lifecycle principal, authority,
idempotency key, canonical request digest, key lookup, receipt or completed-
operation record exists. Semantic replay digests remain D5 recovery material.

1. Validate shape, canonical ID and registered identity, usable control state
   for that driver, configured/enabled eligibility, then the finite unexpired
   deadline, in the check order of the refusal table below. No validation
   invokes a factory or endpoint.
2. Take the single namespace-wide serialization point (the sole writer of the
   control namespace, which is the shared-mark lock) for every request, never a
   serializer scoped to one driver. The checks that do not need the point
   (refusal-table rows 1-5: request shape, driver existence, control state,
   configuration eligibility and the deadline) are completed in step 1 before
   and independently of the wait. The wait is bounded and never outlasts the
   deadline; a request whose deadline expires during the wait is refused with
   `DEADLINE_EXCEEDED` (row 5). Immediately after acquiring the point, a
   request first confirms that admission is open (a readback after ambiguous
   persistence still pending refuses with `UNAVAILABLE`, row 3) and then
   rechecks the deadline: an expired deadline is refused with
   `DEADLINE_EXCEEDED` (row 5) before the revision comparison and before the
   same-desired no-op path, so neither `REVISION_CONFLICT` nor a no-op success
   is returned past the deadline. Under it, read the mark, compare expected
   revision with the current durable desired revision (the mark itself for a
   driver with no record), allocate the next revision and durably write the
   decision with the advanced mark (steps 3-5), without releasing it. A request
   that waited for the point re-reads the mark after acquiring it for allocation,
   never using an earlier read. Compare against the driver's own durable desired
   revision when its record exists; only a driver with no record compares against
   the re-read mark. Another driver's acceptance advances the allocator but does
   not change an existing record's comparison revision. Concurrent changing
   requests for different drivers may both be accepted, each allocating from the
   mark current under the point; CTL-19 specifies both orderings. Mismatch
   returns `REVISION_CONFLICT` and the current cached view without mutation,
   including for a would-be no-op. Recheck deadline before commit. Expiry before the commit point refuses the
   request; cancellation after commit cannot retract accepted intent.
   If the bounded wait ends without acquiring the point, the request makes no
   durable change and, after the same admission confirmation, performs one
   read-only load of the current desired revision of its driver (the mark
   itself for a driver with no record). An `ExpectedRevision`
   below that value is conclusively stale, because desired revisions and the
   mark only advance, and is refused with `REVISION_CONFLICT` and the current
   cached view; otherwise it is refused with `TRANSITION_BUSY`. `TRANSITION_BUSY`
   never reports an outcome of the revision comparison.
3. After the step 2 deadline recheck and revision comparison, START while
   desired RUNNING and STOP while desired STOPPED return the current
   desired state/revision without writing, waking reconciliation or allocating
   correlation. They do not reset retries/backoff, heal degraded generations,
   clear quarantine, change observations or bump either revision or the mark.
   A STOP for a driver with no record is such a no-op, returning STOPPED at the current mark.
   START while desired RUNNING is a no-op even when the driver is observed
   FAILED, quarantined or in BACKOFF: recovering a FAILED driver is the
   reconciler's job under its native retry and recovery rules, and a manual
   START is not a recovery path. This test
   precedes capacity checks, so repeated same-desired requests remain no-ops
   while bounded work or cleanup is outstanding.
4. RESTART requires desired RUNNING. Every accepted RESTART keeps RUNNING and
   takes a new desired revision (mark + 1), even if the observed driver is STARTING,
   BACKOFF or FAILED. Quarantine or unresolved recovery refuses only a
   changing request whose work would require unsafe admission (refusal-table
   order 7); it is never cleared by a request.
5. Still under the step 2 serialization point, check transition capacity,
   storage and all required counter increments.
   Atomically persist desired/revision, the advanced mark, typed in-flight work,
   its internal sequence/correlation and reservation before exposing acceptance
   or waking reconciliation; a driver's first accepted decision creates its
   record in that transaction. Pre-commit failure exposes no staged decision;
   periodic or cache/meta writes cannot later flush rejected staging.
   A control transaction that fails before the commit point (marshal, write,
   file fsync, rename refused) is discarded rather than retried: staging is
   dropped, the decision is refused with `UNAVAILABLE` (retryable by the
   client) and the revision and mark are unchanged; the generic runtime-state
   retry-on-next-trigger behaviour does not apply to this namespace.
   Ambiguous persistence (a failure after the rename was issued but before
   confirmation, including a failed parent-directory fsync after a successful
   rename) fails admission closed: the control service itself
   reads back the committed namespace before admitting any further decision,
   for every driver because the mark is shared. Admission reopens only after
   readback establishes whether the transaction committed, the cached views
   and mark match the durable state and, when the new bytes are present,
   parent-directory durability of them is established as the durability rules
   above require; readback agreement alone never reopens admission. A failed
   readback applies the load-failure rules below.

Every refusal leaves durable state, the mark, both revisions and observations
unchanged. Checks run in this fixed order and the first failing check decides:

| Order | Refusal | Code | Retryable |
|---|---|---|---|
| 1 | Unknown, missing or duplicate member, malformed revision string (including `"0"`, leading zeros, signs, whitespace, non-digits) | `INVALID_ARGUMENT` | No |
| 2 | `DriverID` noncanonical or not registered | `NOT_FOUND` | No |
| 3 | Driver record malformed or `runtime_control` failed to load; the driver reports `FAILED` | `FAILED_PRECONDITION` | No, until offline repair |
| 3 | Readback after ambiguous persistence still pending | `UNAVAILABLE` | Yes |
| 4 | Driver disabled by configuration | `FAILED_PRECONDITION` | No |
| 5 | Call context has no finite deadline | `INVALID_ARGUMENT` | No |
| 5 | Deadline expired, at validation, during the bounded serialization wait, immediately after acquiring the serialization point or at the pre-commit recheck | `DEADLINE_EXCEEDED` | Yes, with a new deadline |
| 6 | `ExpectedRevision` differs from the current desired revision | `REVISION_CONFLICT` with current view | Yes, after readback |
| 6 | RESTART while desired `STOPPED` (checked after the same-desired no-op test) | `FAILED_PRECONDITION` | No |
| 7 | Quarantine or unresolved recovery blocks work that would require admission | `FAILED_PRECONDITION` | No, until recovery resolves |
| 8 | The decision path is busy: the typed transition slot is full or the namespace-wide decision serialization point was held beyond the bounded wait | `TRANSITION_BUSY` | Yes |
| 9 | Record limit, byte limit or bounded-outcome reservation cannot fit | `RESOURCE_EXHAUSTED` | Yes |
| 10 | A required counter or mark increment would exceed the unsigned 64-bit maximum | `COUNTER_EXHAUSTED` | No |

Two outcomes sit outside the ordered checks. A pre-commit write failure
(step 5) follows every row above and returns `UNAVAILABLE`, retryable, with the
revision and mark unchanged. A bounded-wait timeout at the serialization point
(step 2) follows rows 1-5, which are completed without the point, and returns
`REVISION_CONFLICT` (row 6) when the expectation is conclusively stale and
otherwise `TRANSITION_BUSY` (row 8); `TRANSITION_BUSY` never reports an outcome
of the revision comparison, and the request made no durable change.

Both accepted and no-op responses contain **desired state and desired revision
only**, as the two members `desired_state` and `desired_revision`. They contain no operation ID, sequence, disposition or completion claim.
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

From stable STOPPED, a changing START occupies the current slot as typed START
work, and the reserved slot stays free; that typed START persists so recovery
resumes it. From a stable driver, STOP or RESTART occupies the current slot.
During STOPPING (desired STOPPED, typed STOP in the current slot), a changing
START takes the reserved slot as a typed START replacement when that slot is
empty; it executes only after the STOP's cleanup and native close settle. During
STARTING or BACKOFF, accept STOP or RESTART only if the reserved slot is empty and no
accepted RESTART is still executing. The new request always takes the reserved
slot. When the STARTING or BACKOFF attempt has no typed current operation (bootstrap
or process-start reconciliation of stored RUNNING, or a manager retry), the
acceptance transaction synthesizes the cancellation of that untyped attempt as
the current slot, with its correlation, cleanup obligations and budgets. Acceptance immediately fences the old
attempt's callbacks, publications and admission, cancels its preparation or
scheduled retry, and retains the old correlation for late-result cleanup.
The old START may terminate as canceled; its cleanup is never discarded. The
reserved STOP completes only after cleanup and native close; reserved RESTART
executes its own stop-then-start after those obligations settle. It cannot be
replaced by a later STOP or RESTART. An accepted RESTART is never coalesced away.

Precedence while a STOP is in flight: desired is already STOPPED, so STOP is a
same-desired no-op, RESTART returns `FAILED_PRECONDITION` (desired RUNNING
required) before capacity is checked, and START takes the reserved slot as
above. After all earlier refusal checks and the same-desired no-op test pass,
a changing request arriving during an executing RESTART or with both slots
occupied returns retryable `TRANSITION_BUSY`, with no revision or state
change. The caller reads current state and retries with its current revision
after work settles; there is no server retry queue. This deliberately bounded
refusal is separate from the same-desired no-op rule.
List/get and observations of unrelated drivers remain responsive; the namespace-wide decision serialization point never holds hub or manager locks over disk
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
and atomic rename, then expose committed state; for this namespace the parent-directory fsync must succeed (no tolerated errors) before acknowledgment.
No cross-filesystem fallback and no GUID generation/replacement is allowed.

A fresh, readable, valid base whose GUID has no control material at all gets
exactly one atomic seed. No control material means: no `runtime_control`
namespace or part of one, no mark, no D5 recovery material and no quarantine
copy for this GUID (the existence of a copy counts, never its content). The
seed starts the mark at 0 and records each configured driver, in bytewise
`DriverID` order, as one accepted decision at mark + 1: enabled drivers
RUNNING, disabled drivers STOPPED and observed DISABLED. A missing namespace
or mark while any such material exists is a load failure that requires repair,
never a fresh start. A driver added to configuration after bootstrap has no
record and stays STOPPED until its first accepted START; bootstrap never
repeats. Bootstrap is not a user START; its
RUNNING reconciliation happens despite subsequent START being a no-op. Once
seeded, stored STOPPED survives restart with no endpoint opened. Disabled
configuration always wins over stored RUNNING and prevents admission; it does
not silently rewrite durable intent or permit START/RESTART to enable a driver.

Missing, corrupt, unreadable and unsupported are distinct load dispositions.
This fail-closed rule applies to the `runtime_control` namespace only; other
namespaces keep the [runtime-state](runtime-state.md#failure-modes) cache
behaviour (corrupt file renamed and loaded empty, unsupported plugin namespace
dropped from the in-memory load). Corrupt/unreadable/unsupported control state
starts the HTTP/API/health shell but withholds affected eBUS as FAILED; no
empty-state or RUNNING fallback is allowed. Preserve bad bytes and quarantine
before any repair. A malformed known
driver record fails that driver closed while valid independent records remain
usable. A malformed or missing mark or catalog revision fails the whole namespace
closed, because decisions and coherent views depend on these durable bounds.
Whole-file corruption/unreadability withholds all dependent drivers and must
never create a new GUID or overwrite the unreadable bytes as a fresh base: the
runtime-state `.corrupt-<ISO8601>` rename keeps the exact original bytes and
counts as a quarantine copy, so control is unreadable, never missing, and no
bootstrap seed follows.

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
namespace records within an otherwise valid base may be reset only when the
mark, durable catalog revision and the D5 recovery stream can be validated.
First preserve an exclusive, non-overwriting quarantine copy of the exact original bytes and
fsync it. Failure to preserve that copy aborts reset. Existing quarantine copies
are never deleted or replaced. Copy GUID, meta and all other opaque namespaces
unchanged. Quarantine copies are unvalidated diagnostics only; they never
supply a revision bound, records or recovery material. Before replacement, read
`H` from the validated mark: it bounds every desired revision previously issued
under this GUID, including removed driver IDs and earlier repairs. Cross-check
it against the verified D5 recovery stream; any desired revision recorded there
above `H`, or a D5 stream that cannot be verified, refuses reset. If the mark
cannot be validated, refuse. Read `C` from the validated durable catalog
revision; if it cannot be validated, refuse. If `H + N` for `N` configured IDs
or `C + 1` cannot be represented, refuse with `COUNTER_EXHAUSTED` before
replacement; never wrap or choose a lower value. Every reset refusal exits nonzero with its named reason
(`COUNTER_EXHAUSTED` for overflow, `FAILED_PRECONDITION` otherwise) and replaces
nothing.

Atomically replace only the desired, in-flight and catalog records: one
version-1 STOPPED record per configured ID at desired revisions `H + 1` through
`H + N` in bytewise `DriverID` order, the mark set to `H + N` in the same
transaction, catalog revision `C + 1`, and no active operation. Resolve IDs
from the installation’s existing read-only configuration; if that configuration cannot
be validated, refuse rather than guess IDs. Subsequent changing decisions take
mark + 1. `ExpectedRevision` remains the same single unsigned 64-bit value, with
no additional request field. Every pre-repair expected revision therefore
conflicts, including a stale START at revision 1 after all recovery gates clear.
A fresh process incarnation separately fences old callbacks and reservations.

Reset leaves the verified D5 recovery stream in place and untouched. It supplies
no replay, semantic cleanup or native-close proof of its own; on the next start
the ordinary restore path replays that stream and fences historical correlations.
The reset durably cancels the admission-producing portion of every retained
in-flight START or RESTART: the replayed stream resumes only cleanup and close
obligations, and nothing admits or starts a driver after a reset until a new
decision carries a post-reset revision. The unproven-close quarantine flag is a
process-epoch value and is not restored as such; a new process starts without
it, but an unresolved retained close obligation still blocks replacement
admission until that obligation completes. A source with
unresolved retained/indexed semantic state stays read-gated and FAILED until
that restore resolves it; resetting cannot manufacture an empty successful
snapshot. The lifecycle-only empty asset set may remain STOPPED after reset.
No native start occurs as part of this command.

## S3/D3: finite retention and D5 preservation

Durable minimum is desired/revision, catalog revision, the bounded typed
in-flight work and the complete D5 replay/recovery material specified above. Version 1 permits at most
129 records (the one issued-revision mark plus at most 128 driver records) and a
64 MiB encoded control namespace, including the mark, pending work and restore
material. Mark-only writes count against these limits and follow the same readback rule as decisions. Reject registration beyond the driver limit before
effects. Reserve space before accepting work for its bounded outcomes/cleanup;
if the full reservation cannot fit, return retryable `RESOURCE_EXHAUSTED` before
acceptance. Never evict reachable recovery material to admit a new request.
Per-operation semantic attempts are limited to 8 and a 30-second overall budget;
activation staging remains at most 128 unique-asset batches/8 MiB. Persist budgets
and do not renew them on wakes, no-ops or component recovery. These service
bounds do not change native retry, drain or close defaults, and expiry never
asserts close or erases unfinished cleanup.

The mark, desired/catalog revision, internal lifecycle sequence, WAL sequence,
asset ordinal, epoch ordinal and generation counters are unsigned 64-bit values;
the mark starts at 0, so the first issued desired revision is 1, and the others
are initially 1 when first allocated. Check every increment and clock arithmetic;
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
| CTL-04 | Lose an accepted START response, restart the process and read back durable desired/revision; same-desired START is a no-op, without any key/receipt lookup. A changing START from stable STOPPED persists typed START in the current slot, which recovery resumes. Fail the temporary-file fsync and fail a rename before the commit point: the decision is refused with UNAVAILABLE, nothing is acknowledged, no mark or catalog revision is issued, staging is discarded and no later trigger flushes it. Fail the parent-directory fsync after a successful rename with a generic-tolerated error (for example ENOTSUP): the error is not tolerated, nothing is acknowledged and the case enters readback as ambiguous persistence; an unconfirmed rename never acknowledges and never issues a revision |
| CTL-05 | Accept only `DriverID` and `ExpectedRevision` (a canonical decimal string); reject every additional request member as invalid shape; valid control uses only the validation and atomic decision steps defined above |
| CTL-06 | START in desired RUNNING across DEGRADED/BACKOFF/FAILED (including quarantined FAILED) is a no-op and not a recovery path, and STOP in desired STOPPED with unconfirmed close preserve retry budget, quarantine, observations and both revisions |
| CTL-07 | RESTART in desired STOPPED refuses; each accepted RESTART in RUNNING advances revision and executes one replacement; RESTART during STOPPING with desired STOPPED returns FAILED_PRECONDITION before TRANSITION_BUSY; STOP during STOPPING is a no-op; START during STOPPING takes the reserved slot as a typed START replacement that executes after the STOP's cleanup and native close, and a further changing request then gets TRANSITION_BUSY |
| CTL-08 | Pause STARTING and separately BACKOFF, each with a typed current START and with an untyped attempt (bootstrap reconciliation or manager retry); STOP/RESTART fence/cancel the old attempt, retain cleanup correlation and always take the reserved slot with one exact next kind, the untyped case synthesizing the cancellation as the current slot; another changing request that passes earlier refusal checks gets TRANSITION_BUSY; no accepted RESTART disappears |
| CTL-09 | Lose process memory during active RESTART; D5 restores pending work and the new incarnation performs its retained replacement before dropping the slot |
| CTL-10 | Lost RESTART response is resolved by readback; old-revision retry conflicts and a fresh-revision retry after settlement executes another restart |
| CTL-11 | Same-desired requests during occupied slots remain no-ops with only desired/revision returned; no new durable record, wake or counter allocation |
| CTL-12 | Hold a pre-repair START with `ExpectedRevision=1`; offline-reset with verified bound `H >= 1`, restart and clear recovery gates. Read back STOPPED at its repaired revision (`H + 1` for a single configured ID); submit the held two-field request and require REVISION_CONFLICT with no mutation, reconciliation wake or native open. With a retained in-flight START or RESTART in D5 at reset time, the first restart resumes only its cleanup and close obligations and performs no admission or native open until a post-reset decision is accepted. A fresh START using the read-back revision can proceed. Repeat repair after further decisions and with removed IDs in the revision coverage; all earlier revisions still conflict. An unvalidated mark, a D5 revision above the mark, an unverifiable D5 stream or `H + N` above the unsigned 64-bit maximum refuses reset without replacing any record; a successful reset leaves the D5 stream byte-identical. After visible observations and decisions, repair advances validated durable catalog revision `C` to `C + 1`; an invalid `C` or overflowing `C + 1` refuses without replacement |
| CTL-13 | Two drivers A and B: accepted decisions interleave and each takes mark + 1, so no revision repeats across drivers. Remove B (record deleted, mark + 1 in the same transaction), then re-add B (mark + 1 again) with no decision for A in between: reads return STOPPED with `desired_revision` equal to the current mark, and a request held before the removal, carrying B's old revision or the mark current at that time, is refused with REVISION_CONFLICT with no mutation. Second line: repeat with an accepted decision for A between removal and re-add; the held request is refused likewise. START with `ExpectedRevision` equal to the read-back mark is accepted at mark + 1, above every earlier revision; a first START for a driver with no record whose `ExpectedRevision` differs from the mark conflicts, and a STOP carrying the mark is a no-op. Remove the namespace, or only its mark, while other control records, D5 material or a quarantine copy exist: load fails closed and nothing is seeded; only a GUID with no control material bootstraps at mark 0. All revisions encode as canonical decimal strings |
| CTL-14 | Drive one request per refusal row, plus requests failing several checks at once; each returns the code of the earliest failing check in the refusal table with no mutation. A malformed driver record returns FAILED_PRECONDITION with that driver FAILED while an independent driver stays usable; ambiguous persistence returns UNAVAILABLE for every driver until the service's readback completes and directory durability is established |
| CTL-15 | START carrying `ExpectedRevision` `"0"` is refused with INVALID_ARGUMENT; repeat with `"01"` (leading zero), `"+1"`, `" 1"` and `"1x"`. Each refusal is the first refusal-table row, with no mutation, no readback and no reconciliation wake |
| CTL-16 | Fail the parent-directory fsync after a successful rename of an accepted START: no acknowledgment, no exposed view and admission closed with UNAVAILABLE for every driver. A readback that observes the new bytes matching the cached view does not reopen admission. After a simulated power loss that restores the previous mark, the revision first believed issued is issued again and a request holding it is not accepted on the strength of the earlier exposure. Admission reopens only after the directory fsync is retried to success or the namespace is rewritten durably (temporary file, file fsync, rename, directory fsync). A lost acknowledgment after a durable commit reopens by readback |
| CTL-17 | Store desired STOPPED for a configured-enabled driver, restart the process: the driver starts in STOPPED with no endpoint opened and no provider call until a new START is accepted. A configured-enabled driver with stored desired RUNNING, or seeded RUNNING by first bootstrap, starts in STARTING. A driver added to configuration after bootstrap has no record and starts in STOPPED |
| CTL-18 | START and RESTART for a configured-disabled driver are refused with FAILED_PRECONDITION under refusal-table order 4, with no mutation. The transition list has no start transition out of DISABLED; the driver leaves DISABLED only through a configuration change or reload
| CTL-19 | Two drivers A and B, A with a STOPPED record at desired revision `H` and B without a record, begin with namespace mark `H`, where `H <= 2^64 - 3` leaves room for two increments, and concurrent changing START requests each carrying `ExpectedRevision=H`, with both requests past validation before either commits. If A commits first, A is accepted at `H + 1` and B is refused with REVISION_CONFLICT and no mutation. If B commits first, B is accepted at `H + 1` and A still compares against its own durable desired revision `H` and is accepted at `H + 2`. The recorded driver's request is accepted in either order; the no-record request conflicts when it loses the race. Accepted revisions remain unique and the mark advances once per accepted changing decision; no request persists a precomputed revision after waiting. Repeat from the same initial state with each request first. For two concurrent START requests for the same absent-record driver carrying `H`, the first creates its RUNNING record at `H + 1`; the second compares against that record, conflicts before the same-desired no-op check and makes no mutation. Hold the point beyond the bounded wait with the holder's write blocked before its commit: a waiting request whose expectation is below its driver's current desired revision (the mark for a driver with no record) is refused with REVISION_CONFLICT, and one whose expectation is current is refused with TRANSITION_BUSY, each with no durable change and no mark advance, TRANSITION_BUSY never reporting a revision-comparison outcome. A request that acquires the point only after its deadline expired is refused with DEADLINE_EXCEEDED, whether its expectation would have conflicted or matched and whether it would have been a same-desired no-op, with no mutation. The comparison, mark read, allocation and durable write happen under one namespace-wide serialization point, never a per-driver serializer alone |

Also prove disabled/deadline/shape refusals, storage exhaustion, every counter's
overflow refusal, quarantine retention, offline-reset refusal on an active writer
or invalid base, exact quarantine preservation, GUID/meta/opaque round trips,
and corrupt/unsupported loads without empty fallback. Two-driver fixtures must
show B's reads and list/get remain responsive while A blocks in persistence or cleanup;
a B decision waits at the namespace-wide serialization point and is never decided against a mark read before the wait.
The committed `scripts/check_runtime_control_contract.py` gate and its mutation
tests protect these documentation obligations and the closed API examples.
They do not execute service/store/MCP behavior or prove recovery; implementation
tests and payload goldens must independently meet the vectors above.

## S2/D4: ordinary MCP external control

[The exact wire contract](../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4)
selects `helianthus.runtime.list`, `helianthus.runtime.get`,
`helianthus.runtime.start`, `helianthus.runtime.stop` and
`helianthus.runtime.restart` for PR 2. It replaces revision 9's S2 kernel
operator boundary and experimental-tool proposal. The five tools delegate to
one ControlService: cached List/Get and Decide with the exact START/STOP/RESTART
method. They never bypass durable decisions through DriverManager.

Discover and dispatch all five through every ordinary MCP transport the gateway
offers (HTTP today) with eeBUS disabled or absent, and retain registration while
eBUS is STOPPED or FAILED.
There is no lifecycle principal/authority adapter, authorization check before
0.9, new socket or operator-only registration. Closed two-field mutations,
canonical IDs/revisions, duplicate member rejection and finite context
deadlines retain S1/D3's ordered refusals. Whole-body trailing data is rejected
by the transport as an invalid request before any tool or service call; it is
outside the service refusal sequence and never produces the lifecycle
`INVALID_ARGUMENT` envelope. Accepted/no-op data contains only
desired state and revision; results are observed through coherent sorted
list/get, never a receipt. After a lost RESTART response, read back: an
old-revision retry conflicts, while a fresh-revision retry after settlement
requests another restart.

The MCP adapter must preserve amended CTL-01–CTL-19 above, the existing
deterministic meta/data/error envelope and data_hash, and A2 LIFE fencing and
independent-close obligations. PR 2 owns synthetic transport-dispatch coverage
and schema/output goldens; this documentation does not claim those tests pass.
No public lifecycle GraphQL fields are added. Existing eBUS status parity,
partial last-known-good evidence/provenance and fail-closed admission remain.

## D4/public surface boundary

Final D4 removes G5 lifecycle principal/authorization checks and the proposed
kernel operator boundary; lifecycle tools use ordinary MCP. It does not remove
native-write safety or unrelated eeBUS safeguards. Every MCP namespace is
pre-stable until 1.0, including existing eBUS namespaces: no new major or
experimental namespace is introduced. Intentional payload changes require
documentation, deterministic envelopes, schema/output goldens and PR
explanation. Preserve existing eBUS MCP/GraphQL parity; this recovery seam adds
no lifecycle GraphQL surface. The S2/D4 contract above defines the first public
lifecycle tool payloads without claiming their implementation.

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
