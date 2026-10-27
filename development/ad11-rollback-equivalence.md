# AD11 rollback equivalence and retained-state boundaries

> **Narrowed obligation.** The acceptance-index row AD11 no longer covers a
> return to the standalone proxy topology: that target is deprecated and is not
> an accepted rollback target. The supported targets, a direct adapter
> transport and ebusd-tcp, remain in scope; compare B and R for them as
> described below, using the topology-neutral fields and target variants
> defined in the worksheet section; "proxy" in the stage names and examples is
> a historical label for the pre-migration and restored observation.
> Compatibility cells of the gateway transport matrix do not replace this
> transition comparison.

## Status and authority

This is a **proposed offline comparison contract** for the acceptance-index AD11
assertion, “Rollback restores behavior.” It defines evidence to compare a return
from adapter-direct to the pre-migration proxy topology; it does not implement
rollback, certify a run, or prescribe live rollback commands. No behavior is
stable before Helianthus 1.0.

Current public documentation supplies three distinct authorities:

- [AD01–AD12 evidence index](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/development/ad01-ad12-evidence-index.md):
  AD11 requires comparison with the pre-migration baseline, including MCP and
  GraphQL parity. Its topology equivalence test and row-scoped artifacts are
  missing; evidence grade is Unknown and qualification is unassessed.
- [Migration guide](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/deployment/adapter-direct-migration.md):
  rollback restores the previous proxy transport configuration; a restart is
  acceptable. Adapter-direct and proxy-based transports are mutually exclusive.
  The guide's forward-migration semantic checks do not prove rollback equivalence.
- [Multiplexer architecture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/adapter-direct-multiplexer.md):
  active, passive and optional external-client paths have distinct roles and
  reset/disconnect lifecycles. Its architectural decision AD11 is an ownership
  duration guard, a different namespace from acceptance AD11 here.

The worksheet, comparison rules and examples below are proposed future evidence
requirements, not existing API fields, persisted schemas or implemented runtime
transitions. Current sources do not define these interfaces. This page adds no
wire or data-type facts. Any future comparison of native bytes must first use
the applicable public native contract identified by the evidence index; gateway
implementation output alone cannot establish native semantics.

## Three separate observation identities

Use three detached records. The labels are offline evidence identifiers, never
live connection handles or permission to perform a device operation.

| Stage | Identity and content | Comparison purpose |
|---|---|---|
| B: pre-migration baseline | A separately retained pre-migration observation in the target topology, its source identity, effective topology and public fixture conditions; keep original raw evidence and interpretation together. | Defines the behavior to recover. Reconstructing B from a later cache is prohibited. |
| D: post-switch state | An adapter-direct observation with its own topology, source provenance, session epoch and outcomes, or an explicit incomplete record. | Documents what changed and any discontinuity; D is never substituted for B. |
| R: restored observation | A new observation in the target topology after the documented return boundary, with a new session epoch and independently acquired evidence. | Compared with B for the same declared scope and conditions; equality with D is insufficient. |

A proposed worksheet records the following for each stage. Missing fields remain
explicitly unknown; a default value must not manufacture identity or freshness.

| Field group | Required evidence and identity rule |
|---|---|
| Stage and lineage | Stage-local observation label; references to B, D and R where available; completed or interrupted transition; ordered acquisition steps and discontinuities. No capture times or private identifiers in public examples. |
| Source identity | Public fixture/source label, device family, transport/adapter family and relevant firmware context when known. Preserve the original evidence reference and source-to-observation binding. Family name or equal values alone do not establish the same source. Unknown relevant firmware context limits the claim. |
| Topology | Effective transport kind, network kind, and a route role with a public route label, populated per target variant below. Labels describe fixture roles, not network coordinates. A selected configuration and an observed active path are separate facts. |
| Semantic key | Semantic plane, entity/instance scope, property, type, unit and availability meaning, with the native evidence reference when relevant. Preserve every native discriminator rather than collapsing similarly numbered registers or opcodes. |
| Conditions | Fixture revision label and controlled input/state, selected observation scope and expected outcomes. If conditions cannot be matched, do not explain away a value difference as successful restoration. |
| Acquisition | Stage-local session epoch, observation ordering, acquisition outcome, fresh versus retained status, reset/disconnect boundary and raw evidence reference. An ordinal after a boundary alone does not prove a new read. |
| Projection | MCP and GraphQL projections bound to the same stage-local observation, including semantic key, value, type/unit, availability, freshness, source and error meaning wherever exposed. Record an unexposed required dimension as unknown. |
| Result | Per-dimension Equivalent, Different or Unknown; separate evidence grade, execution result and qualification. Record contradictory evidence beside any earlier last-known-good result. |

Target variants for the Topology group. Record only the fields of the
rollback target actually exercised; a field that does not exist for that target
is recorded as not applicable, never filled with proxy provenance:

| Rollback target | Route role and label | Target-specific field |
|---|---|---|
| Direct adapter transport | Direct adapter route (the adapter-direct southbound transport and its framing family) | Southbound transport and framing label; no proxy profile |
| ebusd-tcp | ebusd-tcp route (gateway as client of an ebusd endpoint) | ebusd endpoint role label; no proxy profile |

The stages named B and R keep their roles: B is the separately retained
pre-migration observation and R is the restored observation, each in the
topology of the chosen target. The synthetic examples below are written with
`route-A` as the route label of that target; read it as the direct adapter
route or the ebusd-tcp route, with the target-specific field from this table.

These labels form a deterministic comparison envelope: the same detached inputs
and declared scope must yield the same ordered dimension results and reasons.
They do not introduce a namespace, endpoint or gateway-to-driver binding.

## Recover, re-observe, retain and discard

The proposed AD11 comparison separates restored topology behavior from semantic
cache retention and transport lifetime. No session splicing is allowed.

| Boundary | Must recover or be re-observed for the claimed scope | What can remain as history; what cannot carry forward as current proof |
|---|---|---|
| Proxy selection and routing | Recover B's transport/network/route roles and the target-specific field of the chosen rollback target. Independently observe that R uses that topology, with only one gateway transport active. | Saved configuration is historical intent until effective selection and path evidence exist. The integrated compatibility listener alone does not prove a return to B's route. |
| Semantic behavior | Re-observe B's semantic keys, types, units, availability/error meanings and controlled-condition outcomes through R. Value equality is required only for matched deterministic fixture conditions. | Retain B and D caches with original provenance and stale/last-known-good status. Cached equality cannot replace a fresh R observation. Do not erase partial last-known-good state because newer evidence is missing or different. |
| Source binding | Re-observe a compatible source binding for R and match it to B's declared source and conditions. Any replacement or identity conflict needs an explicit limitation. | Neither a shared family label nor a copied identity label from an earlier session proves continuity. Incompatible sources are not admissible comparison pairs. |
| Session lifecycle | R has a distinct newly established transport-session epoch and fresh acquisition evidence after the return boundary. Record interruption or disconnect as such. | Old live handles, sockets, ownership grants, pending requests/responses, echo/phase state and old “connected” flags cannot be reused or counted as R proof. Historical handle labels may explain provenance only. Late D completions remain D evidence. |
| Passive and external-client behavior | If claimed in B's scope, re-observe the corresponding restored path, discontinuities and outcomes; otherwise leave that dimension unassessed. | Pre-switch passive bytes and external-session success do not establish restored continuity. No replay or concatenation across epochs may fill the gap. |
| Adapter INFO and reset evidence | Obtain independent relevant restored identity evidence; unresolved reset policy limits the comparison. | The evidence index identifies a conflict between architecture INFO retention and native reset invalidation. Cached INFO cannot resolve that conflict or prove a new source binding; this page changes neither policy. |
| Public projections | Compare MCP and GraphQL for the same R observation and compare that normalized semantic result with B. Preserve existing eBUS MCP compatibility. | A new MCP result paired with an old GraphQL cache is not parity. A transport change grants no authority to change either public semantic contract. |

This is an evidence-admission boundary: when required provenance or observation
is absent or contradictory, admission of an AD11 equivalence claim fails closed.
It does not add a runtime authentication, principal, credential or permission
check, profile-admission rule or authorization gate.

## Proposed comparison and parity decision

1. Declare scope before comparison: source binding, fixture conditions, semantic
   keys, topology roles and any passive/external paths claimed. Preserve B as an
   independent baseline. Missing B produces Unknown, never a baseline from D.
2. Record D and the return boundary separately. An interrupted transition stays
   incomplete until a distinct R observation exists. A configuration edit alone
   cannot promote a stage to observed behavior.
3. Check B/R source and condition compatibility. An incompatible source is a
   recorded identity mismatch; baseline equivalence remains Unknown. Do not
   remap a family, instance or native key to make values match.
4. Require a fresh R acquisition and topology evidence in its new epoch. Retain
   partial older results without making them current. Insufficient provenance
   produces Unknown for affected dimensions and for overall equivalence.
5. Normalize MCP and GraphQL only using their documented semantic meanings:
   serialization/order differences may be normalized; source, instance, units,
   freshness, absence, null, unsupported and errors must not be silently equated.
   Both views must bind to the same R observation. If that binding or a required
   dimension is unavailable, parity is Unknown. Different projections of the
   same comparable observation are a parity discrepancy, not successful restore.
6. Compare each declared B/R dimension. A fresh disagreement under matched
   conditions is Different; retain both observations and raw evidence. Overall
   Equivalent requires every required dimension to be Equivalent and parity to
   hold. A known discrepancy prevents Equivalent even if other dimensions are
   Unknown; report the discrepancy and the unknown dimensions separately.

Equivalent is a proposed offline comparison outcome, not qualification or runtime
admission. Proven means only that a specified claim has sufficient scoped
evidence; Hypothesis means a supported candidate without complete proof; Unknown
means required evidence is absent or inconclusive. These grades are independent
of executed PASS/FAIL/Not run/Unverified and of qualification. None of the cases
below is an executed test, a Proven restored topology or a qualified family.

## Synthetic three-stage acceptance examples

All labels below are invented, public fixture roles. There are no device models,
network coordinates, live handles or device actions. The detached baseline is a
controller-family fixture `source-A`, adapter-family `adapter-A`, firmware-context
label `fixture-firmware-A`, condition `steady-A`, and semantic key
`heating / zone-A / temperature`, numeric degrees Celsius, available, value 20.
The fixture reference `raw-B` binds that interpretation to B's synthetic raw
record; it is not a real capture or a claim about wire encoding. MCP/GraphQL
entries are conceptual projections, not new API field names.

Each row resets to its own independent B. Epoch labels distinguish lifetimes,
not persistent handles. Unless explicitly changed, source and controlled fixture
conditions match; B and fresh R each have their own evidence bindings. D records
adapter-direct operation, never a substitute comparison baseline.

| Case | B: pre-migration proxy | D: post-switch adapter-direct | R: restored proxy | Required proposed outcome |
|---|---|---|---|---|
| Successful restore | `B-ok`, epoch `b-ok`, observed proxy route `route-A`; raw-B and MCP/GraphQL both bind to B and yield 20, available. | `D-ok`, epoch `d-ok`, independently observed adapter-direct path; retain D evidence separately. | `R-ok`, new epoch `r-ok`; independently observed route-A and fresh `raw-R-ok` yield 20 under steady-A. MCP and GraphQL bind to R-ok and agree in every required dimension. | Equivalent for the declared topology/semantic scope. This is an expected synthetic outcome only; passive/external paths absent from the scope remain unassessed. Qualification remains unassessed. |
| Missing baseline | `B-missing`: no detached baseline artifact or B source binding. | `D-only` has value 20 and a complete direct-path record. | `R-no-B`, new epoch, fresh proxy observation is 20; MCP and GraphQL agree on R. | Unknown baseline equivalence despite R parity. D's cache cannot be backfilled into B. Preserve R as scoped evidence without a restoration claim. |
| Incompatible source identity | `B-source` is source-A under steady-A, value 20. | `D-source` records source-B in the same controller family; retain that mismatch. | `R-source`, new epoch, freshly observes source-B, value 20; MCP and GraphQL agree on R-source. | Source mismatch; B/R equivalence Unknown. Equal family/value and local parity cannot establish restored source identity. |
| Interrupted transition | `B-interrupt` is complete, value 20. | `D-interrupt` records a discontinuity; the return boundary is incomplete. | `R-interrupt` contains only intended proxy configuration, no new epoch/path acquisition. Both surfaces still show a retained B value. | Unknown topology, freshness and parity binding. Preserve B as last-known-good history and D as incomplete; never splice a late D response into R or operate a device automatically. |
| Stale cache looks equal | `B-stale` is complete, value 20. | `D-stale` retains B's semantic cache with its original binding. | `R-stale`, new proxy epoch/path observed, but no fresh semantic read; MCP and GraphQL both display retained 20 from B. | Topology may be Equivalent within its observed scope; semantic equivalence and fresh R parity are Unknown. Identical stale output is insufficient. Preserve its stale status and original evidence. |
| Fresh read disagreement | `B-different` is complete, value 20 under steady-A. | `D-different` records a direct-path value 20 independently. | `R-different`, new epoch/path, fresh `raw-R-different` yields 21 under the same fixture conditions. MCP and GraphQL both bind to R and yield 21. | Semantic Different with R parity satisfied; overall equivalence is not established. Keep B and the new disagreement; do not overwrite B or use D's equal value to suppress the contradiction. |

For every row, a projection variant in which MCP reports R while GraphQL reports
B or D makes parity Unknown because the observations differ. A variant in which
both are bound to R but disagree on a value, unit, instance, availability or
error is a parity discrepancy. Neither variant can become Equivalent. Unknown
source/acquisition provenance remains Unknown even if serialized payloads match.

## Source review and remaining evidence gaps

| Proposed element | Current source support | Gap or limit retained |
|---|---|---|
| B/D/R worksheet and deterministic comparison envelope | Evidence index: AD10, AD11 and conflicts/carry-forward. | No current worksheet schema, snapshot-binding interface or comparator is specified. All worksheet fields and decision transitions here are future work. |
| D to R topology boundary and new observation epoch | Migration guide: rollback and notes; architecture: topology, reset propagation and connection management. | Sources allow restart and distinguish paths; they do not supply a rollback execution artifact or prove restored session isolation. No new runtime recovery transition is asserted. |
| Cache, raw evidence and old-handle boundaries | Evidence index: result discipline and conflicts/carry-forward; architecture: INFO cache, reset propagation and passive delivery. | INFO reset conflict remains unresolved. Proposed epoch isolation is an acceptance requirement, not proof of current implementation. G5 recovery is unchanged. |
| Successful-restore example and fresh-disagreement example | Evidence index: AD11 baseline comparison and parity; migration guide: semantic verification. | Synthetic equal/different outcomes illustrate the proposed comparison only. Neither source supplies these detached observations. |
| Missing-baseline and incompatible-source examples | Evidence index: scoped provenance, family conditions and fail-closed carry-forward. | A compatible live source binding and sufficient baseline artifacts remain absent; no identity API is assumed. |
| Interrupted-transition and stale-cache examples | Evidence index: no session splicing or stale admission; architecture: disconnect/reset boundaries. | No completed restored observation is inferred; no cache invalidation implementation or interrupted-rollback recovery is added. |
| MCP/GraphQL normalization and projection variants | Evidence index: AD11 parity requirement. | Exact projection-to-observation bindings and normalization mechanics need implementation evidence and independent review; no public API change is specified here. |

This AD11 contract is independent of X28 and W28 add-on rollback and consumes no
unmerged implementation or specification. It does not change G5 D1–D5/O8 or claim
add-on configuration rollback acceptance. It adds no automatic device operation,
new major/experimental namespace, transport production change or output binding.

Parent acceptance under docs-ebus #250 and gateway #476 remains open, and
must itself record the retirement of the proxy return target made by the operator decision on
helianthus-ebusgateway#1378: row-scoped
offline comparison artifacts, independent review, complete committed-head gates,
separately authorized live topology/semantic observations and hardware acceptance
are still needed. Other AD rows remain unresolved on their own evidence. Document
readability and offline link checking establish neither semantic correctness nor
runtime success, profile admission, hardware qualification or parent closure.
