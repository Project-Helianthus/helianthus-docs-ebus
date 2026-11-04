# Local-worker qualification decisions

Status: **Unknown — owner acceptance choices incomplete; every physical profile
remains unqualified and off.** This record is a partial slice of
[docs issue #1132](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1132).
Refs [Project-Helianthus/helianthus-ebusgateway#991](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/991),
which remains open. Recording requirements does not authorize physical-backend
activation, arming, deployment or a real-bus response.

## Evidence and software boundary

Native facts must come first from the public
[eBUS wire contract](../protocols/ebus-services/ebus-overview.md) and the
[identification service contract](../protocols/ebus-services/ebus-service-07h.md#service-0x07-0x04--identification).
This application qualification record does not set native timing or change
framing, CRC, escaping or response phases.

**Proven** describes a statement supported by its cited public evidence;
**Hypothesis** describes a proposal; **Unknown** describes missing or unverified
evidence. These grades are separate from qualification and authority. A proposed
contract, synthetic pass or finite zero-error run does not qualify a platform.
Nothing here is stable before Helianthus 1.0.

AA20's [registration contract](../api/ebus-local-responder.md) and
[offline transport contract](../architecture/local-worker-transport.md) settle
the software reference choices below as proposed contracts (**Hypothesis**),
without proving their runtime implementation or physical suitability:

- Exact registration and wire identities; duplicate rejection; immutable bounded
  plans; destination-time provisional selection followed by native validation.
- Pointer-free, fixed-width serialized ABI; bounded SPSC lanes with independent
  control; checked nonwrapping counters and release/acquire publication rules.
- Exclusive expiry boundaries and per-symbol authority checks; exact retirement
  acknowledgement, or original finite lease expiry plus proven reader quiescence
  before reclamation. A paused reader's storage stays quarantined.
- Synthetic directed identification reads only; existing eBUS MCP compatibility
  and equivalent detached GraphQL/MCP ordering, loss reasons and evidence labels.

These choices do not supply platform atomics, physical budgets, an in-flight
hardware cancellation policy or production profile admission. Missing companion
implementation evidence remains unverified.

## Owner acceptance table

The local-worker design's section-11 topics are covered individually below.
The design and the Orchestrator notes establish direction, not measured results.
No accepted numeric product budgets or qualified platform profile were supplied.
All unchosen physical rows remain **Unknown** and block physical-backend
qualification; proposals in the third column are **Hypothesis**, not owner answers.

| Decision | Actual accepted choice / evidence | Proposed conservative disposition and required owner answer |
| --- | --- | --- |
| Timing, errors and tail acceptance | **Unknown**; no accepted values or measurement record | Specify every edge, deadline, percentile, maximum lateness, allowed miss/error rate and recovery threshold, with units and denominator. Keep off until measured against the accepted contract. |
| Board, kernel and toolchain profile | **Unknown**; no qualified profile | Select a board/frontend family and separately qualified revision/configuration, kernel/configuration, toolchain/build, runtime, scheduling, memory, clock, load, power and thermal envelope. No transfer of qualification between platforms. |
| Counter and MMIO primitives | **Unknown**; no qualified counter or MMIO access profile | Require monotonic counter resolution, access/rollover behavior and clock comparability evidence; audit MMIO mapping attributes, access widths, ordering/barriers and exclusive ownership. Select primitives only after evidence; no hardware addresses or setup recipe here. |
| Shared-memory ABI and cross-process atomics | Software reference specified by AA20; physical proof **Unknown** | Retain the reference layout and ownership rules. Require aligned atomic-width and release/acquire proof across processes for the exact architecture/kernel/toolchain, including publication, reclamation and paused readers. Same-process tests and serialization are insufficient. |
| Leases, revocation and in-flight output | Software expiry/reclamation rules specified by AA20; physical bounds and policy **Unknown** | Accept finite arm, registration, plan, command and control-service budgets under parent pauses. Require exact acknowledgement or original lease expiry for admission closure, plus quiescence for reuse. Choose a native-phase-safe finish/abort policy for output already in flight; absent that policy, physical admission stays closed. |
| Registration API | Software reference specified by AA20; physical integration **Unknown** | Preserve exact-key lifecycle, duplicate refusal, cleanup, single wire authority and fresh identities after restart. Require evidence that physical conflicts, disconnect/reset and delayed cleanup cannot retain or revive admission. Registration alone grants no live transmit authority. |
| Minimal read-only virtual-device admission | Synthetic identification reference specified by AA20; physical profile acceptance **Unknown** | Owner must accept the exact supported read-only request/response scope, native evidence, source/freshness constraints, finite limits and unavailable behavior. Unsupported or invalid authority stays silent; no invented universal NACK, stateful command or write support. |
| Fault containment | **Unknown**; no accepted electrical containment requirement or proof | Owner must define the allowed fault envelope and independent containment needed for stuck drive, process pause/death, abnormal stop and recovery. Supervision, heartbeat, process kill or software cleanup cannot bound a stuck electrical pulse. |

The first candidate is the **10x GPIO bit-level engine**, not a qualified backend.
The abstraction and acceptance contract stay engine-independent; sampling rate
is a measurable candidate choice, not a product threshold. Alternative engines
need their own evidence and cannot inherit this candidate's prospective result.
No board, Linux arm64, latency, power or thermal suitability is established.

## Required acceptance detail

The timing answer must distinguish the end of the final request character on
the wire to the first permitted response start edge from the request-CRC-to-ACK
metric. Define the exact physical edges and their relationship to native phase
completion for each metric. Enqueue, callback, write completion and delivery time
are not wire timestamps. Specify RX observation-gap tolerance, TX bit/edge error,
turnaround, higher-tail and worst-observed limits separately. Do not adopt the
design's feasibility objective as product acceptance or add percentiles to infer
an end-to-end distribution.

Require a declared load envelope, measurement method and uncertainty, duration,
sample count, failed attempts and counts of misses, corruptions and absent
responses. Define each rate's denominator and recovery acceptance, including
saturation, clock regression, expired plans and parent stalls. Finite success
cannot establish a hard worst-case bound.

The platform answer must bind counter/MMIO and atomic proofs to the same profile
as timing evidence. Include the frontend's propagation/settling assumptions,
runtime allocation bounds and relevant scheduling, throttling and thermal
conditions. Readiness or a retained last-known-good profile is not qualification
of a changed configuration. Preserve raw public-safe evidence beside its
interpretation; preserve unaffected last-known-good state with provenance and
aging while affected output remains fenced.

The revocation answer must state where each bound starts and ends, including
parent publication, worker observation, output fencing, acknowledgement and
reader quiescence. Parent pauses must not renew authority indefinitely. Unknown
worker progress or a lost acknowledgement does not permit address, plan or
mapping reuse. A safe in-flight policy must cover physical output buffering and
already-driven levels without relaxing AA20's per-symbol authority contract.
Any asynchronous hardware mechanism needs separate proof; the synchronous offline
model proves no cancellation or cessation bound for it.

## Evidence closure and carried gates

An owner answer must name the accepted requirement, its scope and units, the
public evidence artifact, review outcome and remaining Unknowns. Requirements
chosen by the owner and measurements satisfying them are separate records. No
row becomes qualified merely because it has an answer or this page is merged.
Absent an answer, retain Unknown, keep the profile off and withhold dependent
physical-backend authoring. This document is a reviewable requirements record,
not closure of the owner-decision hold.

Parent criterion 5 needs accepted timing/error budgets and on-wire evidence;
criterion 6 needs bounded invalidation, revocation and safe retirement evidence;
criterion 8 needs measured qualification for each adapter/transport/profile
combination. AA20's software contracts do not discharge these physical edges.

Hardware gates start only after the operator adapter mount and separate explicit
action-time authorization: passive bench, isolated TX bench, autonomous read-only
responder timing, conformance, endurance and faults. Even a responder answer on a
real bus is a live write. This dossier authorizes none of those actions.

Only synthetic/public fixtures, in-memory loopback and injected time belong to
the software evidence scope. No new real-bus transmit path is reachable in default
configuration, and this record introduces no production arming switch. Manual
local-link and publication review establish document properties only; no
transport, passive-observation, hardware, hosted/SDK, Matter conformance or
certification pass follows. Physical profiles remain unqualified and off until
all applicable owner requirements and separately authorized evidence are met.
