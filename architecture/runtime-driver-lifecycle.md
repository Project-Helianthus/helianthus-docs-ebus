# Runtime driver lifecycle: G5 recovery contract

Status: proposed software 0.7 contract. This page specifies the selected D5
recovery mechanism for gateway issue
[#1032](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1032),
PR 0a and amendment A6, covering S3.7–S3.9. It does not claim that the runtime
control service or durable recovery is implemented. The G4 publication hub has
an in-memory journal; that alone supplies no process-loss recovery.

The companion [gateway runtime/driver contract](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/docs/architecture/runtime-driver-provider-contract-v1.md)
owns the provider SPI and CTL/LIFE vectors. The final G5 operator decisions
select service-side write-ahead persistence and gateway-owned hub export/restore
hooks, using SemReg's existing public `NewPublicationKernel` constructor and
`Apply`. No SemReg API, dependency change or snapshot-import prerequisite is
introduced. Earlier proposals for client command tracking and lifecycle
authorization in that contract must be read with the final D3/D4 decisions below.

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
| Accepted results | Each batch's accepted result, `SnapshotID`, semantic revision, digest and per-key publication cursor; hub commit position including incarnation and `HubSeq` |
| Hub-only history | Admissions, withdrawal rollbacks, activations, asset-less retirements and `RevokedUnpublished` revocations, including results even when no kernel batch exists |
| Control state | Per-asset semantic outcomes and reprojection settled history; source-publication index; epoch and generation reservations with exact per-asset next cursors; withdrawal correlation; retry/deadline budgets and independent native-close obligations |
| Pending work | Complete pending publication envelopes and staged control attempts as exact bytes, their per-source WAL sequences, asset/source ownership, per-asset keys/sequences and monotonic points; no invented accepted result |

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

1. **Intent:** assign the service's per-source WAL sequence before the hub call
   and durably persist the exact pending envelope or control attempt in the
   service transaction. Only then submit it to the hub.
2. **Outcome:** after the hub call returns, durably persist its accepted result,
   commit position, monotonic point, semantic outcome and settled history in a
   second transaction. A rejected operation retains the SemReg error identifier
   verbatim and never enters the accepted replay stream.

A crash between those steps leaves an uncertain pending intent. It is not an
accepted batch merely because submission may have happened. A failed durable
transaction must expose no rejected staging through a later cache flush.

For concurrent service-routed calls, intent order and durable outcome order can
differ. Before replaying a recorded outcome, resolve all pending entries of its
source with lower WAL sequences. A dependent call follows its predecessor's
returned hub call and therefore has a higher WAL sequence. Recorded outcomes
carry hub commit positions so restoration preserves actual commit order,
including per-asset order. An unresolved source WAL gap fails that source
closed; a later recorded activation cannot bypass an uncertain admission.

## Restore before admission

Restoration runs before any source admission in the new incarnation and refuses
an asset that already holds state. A compatible asset identity and validator
set, complete commit order, exact accepted bytes and original monotonic points
are preconditions. Changed validator behavior, including an upgrade that
changes replay acceptance, has no supported migration here and fails closed.

1. Construct each empty asset kernel with `NewPublicationKernel`. Replay every
   accepted publication and control batch through `Apply` in commit order,
   using its persisted monotonic point. Current-process time can change
   retained-observation expiry and must not replace that point.
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
4. Resolve pending exact bytes under the WAL rule before dependent outcomes.
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

## D3 retention and D4/public surface boundary

Final D3 removes client-visible command receipts, idempotency keys,
per-principal key spaces and stored completed-command records. START and STOP are
idempotent by desired state; RESTART executes. Requests return accepted desired
state and revision; completion is read from observed state. Durable lifecycle
scope is desired state, the in-flight operation and D5 recovery material;
completed commands survive only in a short diagnostic log.

Accepted kernel results and cursor replay records above are recovery material,
not the deleted client receipt design. D3 does not delete them. Compact only at
a verified restore point that reproduces snapshots, retained history and
cursors and preserves all reachable pending and cleanup work. No arbitrary
retention duration or capacity is specified here; at a bound, refuse new work
rather than evict material still required for restoration.

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
clocks, IDs and schedules. Destroy both service and hub memory and reconstruct
fresh instances with no shared state. A lifecycle-only empty barrier cannot
satisfy this proof.

| S3.9 case | Required observation after restoration |
|---|---|
| Accepted publications followed by an accepted fence | Replay includes the control batch; retained tombstones and withdrawn history survive |
| One submitted envelope with no outcome, before hub return and after acceptance but before outcome persistence | Only pending intent survives; exact cursor comparison selects exact-byte resubmission or accepted replay/readback without rebuilding bytes |
| Mid-cleanup | Original asset set, budgets, correlation and exact pending attempts survive; native close and semantic cleanup remain independent |
| Unfinished control: one asset accepts and the other rejects | Both affected read gates stay closed initially; the accepted asset opens only after reprojection against its restored snapshot |
| Rejected publication envelope and rejected control attempt | Neither is applied as accepted; each cursor stays at its pre-rejection value and the original error identifier survives |
| WAL gap: A accepted without durable outcome, dependent B accepted and recorded | Resolve A before B; never replay B alone. Removing A's intent must fail the source closed |
| Corrupt replay or incompatible validator, snapshot, revision or cursor | Fail the affected asset closed without damaging an unaffected asset |

For each successful reconstruction, compare `Inspect` snapshot identity,
canonical bytes, revision vector, retained history, per-key cursors and exact
replay results with the pre-loss accepted state. Verify the new barrier retires
prior epochs on both assets and that no old callback or admission becomes
current. Prove another family's admission reads remain responsive during a
blocked durable write, using a stated bound.

This covers S3.7–S3.9/A6 recovery obligations and the recovery aspects of
LIFE-06, LIFE-19, LIFE-21, LIFE-23–LIFE-24 and LIFE-26–LIFE-30. Older
receipt-specific CTL vectors require the D3 amendment; this page does not claim
they pass. LIFE-22 source-isolation acceptance remains a separate prerequisite.
PR 0a provides the prerequisite hooks and hub restoration proof without a
production service caller; PR 1 supplies service persistence and end-to-end
restoration. Neither a hooks-only slice nor this page completes gateway #1032.
