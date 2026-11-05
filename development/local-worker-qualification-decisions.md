# Local-worker qualification decisions

Status: **Hypothesis: acceptance requirements decided 2026-11-03 under delegated
owner authority; every physical profile remains unqualified and off until a
recorded run makes a requirement Proven for that profile.** This record is a
partial slice of
[docs issue #1132](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/1132).
Refs [Project-Helianthus/helianthus-ebusgateway#991](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/991),
which remains open. Recording requirements or evidence does not authorize
physical-backend activation, arming, deployment, device access, a bench run, a
live write or a real-bus response.

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

The [registration contract](../api/ebus-local-responder.md) and
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

## Qualification requirements and source basis

The planning inputs titled *eBUS northbound local-worker design* (section 11,
"Decisions still needed") and *Orchestrator notes for Astra batch 19* establish
proposal direction. They are not public evidence artifacts; the qualification
requirements are restated here so no private input is needed to read this record.
The eight decision areas are timing/error acceptance, platform profiles,
counter/MMIO primitives, shared-memory ABI/atomics, leases/revocation,
registration API, minimal read-only scope and fault containment. The table below
gives each area's required owner answer; the software reference contracts linked
above define the proposed software choices, not physical acceptance.
The owner's decided answers are recorded in the next section and cited by number
in the second column. They are requirements graded **Hypothesis**; no measurement
record or qualified platform profile exists.
All physical suitability and every row without a decided answer remain **Unknown**
and block physical-backend qualification; proposals in the third column are
**Hypothesis**, not evidence.

| Decision | Actual accepted choice / evidence | Proposed conservative disposition and required owner answer |
| --- | --- | --- |
| Timing, errors and tail acceptance | Requirement decided 2026-11-03 (**Hypothesis**): rows 1-3 and 5-7 below; measurement record **Unknown** | Specify every edge, deadline, percentile, maximum lateness, allowed miss/error rate and recovery threshold, with units and denominator. Keep off until measured against the accepted contract. |
| Board, kernel and toolchain profile | Requirement decided 2026-11-03 (**Hypothesis**): row 8 below; qualified profile **Unknown** | Select a board/frontend family and separately qualified revision/configuration, kernel/configuration, toolchain/build, runtime, scheduling, memory, clock, load, power and thermal envelope. No transfer of qualification between platforms. |
| Counter and MMIO primitives | Requirement decided 2026-11-03 (**Hypothesis**): row 10 below; qualified counter or MMIO access profile **Unknown** | Require monotonic counter resolution, access/rollover behavior and clock comparability evidence; audit MMIO mapping attributes, access widths, ordering/barriers and exclusive ownership. Select primitives only after evidence; no hardware addresses or setup recipe here. |
| Shared-memory ABI and cross-process atomics | Offline transport contract specifies the software reference; requirement decided 2026-11-03 (**Hypothesis**): row 11 below; physical proof **Unknown** | Retain the reference layout and ownership rules. Require aligned atomic-width and release/acquire proof across processes for the exact architecture/kernel/toolchain, including publication, reclamation and paused readers. Same-process tests and serialization are insufficient. |
| Leases, revocation and in-flight output | Offline transport contract specifies software expiry/reclamation; requirement decided 2026-11-03 (**Hypothesis**): row 12 below; physical bounds and policy proof **Unknown** | Accept finite arm, registration, plan, command and control-service budgets under parent pauses. Require exact acknowledgement or original lease expiry for admission closure, plus quiescence for reuse. Choose a native-phase-safe finish/abort policy for output already in flight; absent that policy, physical admission stays closed. |
| Registration API | Registration contract specifies the software reference (**Hypothesis**); owner acceptance **Unknown**: row 4 decides responder-only scope and defers arbitration, but does not accept the registration lifecycle or its integration requirements; physical integration **Unknown** | Preserve exact-key lifecycle, duplicate refusal, cleanup, single wire authority and fresh identities after restart. Require explicit owner acceptance of these choices and evidence that physical conflicts, disconnect/reset and delayed cleanup cannot retain or revive admission. Registration alone grants no live transmit authority. |
| Minimal read-only virtual-device admission | Registration contract specifies synthetic identification; requirement decided 2026-11-03 (**Hypothesis**): row 13 below; physical profile acceptance **Unknown** | Owner must accept the exact supported read-only request/response scope, native evidence, source/freshness constraints, finite limits and unavailable behavior. Unsupported or invalid authority stays silent; no invented universal NACK, stateful command or write support. |
| Fault containment | Requirement decided 2026-11-03 (**Hypothesis**): rows 14-15 below; electrical containment proof **Unknown** | Owner must define the allowed fault envelope and independent containment needed for stuck drive, process pause/death, abnormal stop and recovery. Supervision, heartbeat, process kill or software cleanup cannot bound a stuck electrical pulse. |

**Hypothesis**: the first engine to qualify is the **10x GPIO bit-level
engine**: GPIO observation at 10 observations per nominal bit period, with
bit-level receive/transmit handling. Decided requirement 2 below accepts it as
the first engine; that acceptance is a requirement, not evidence. No public
measurement artifact is supplied for this engine; its physical suitability
remains **Unknown**. The designated second engine, tried only when the first
fails qualification or cannot hold the 41.7 µs edge budget, is a dedicated
PL011 kernel-driver path. This record supplies no such driver; its existence
and physical suitability are **Unknown**.
The abstraction and acceptance contract stay engine-independent; sampling rate
is a measurable engine choice, not a product threshold. Each engine needs its
own evidence and cannot inherit another engine's prospective result.
No board, Linux arm64, latency, power or thermal suitability is established.

## Decided acceptance requirements (2026-11-03)

The owner delegated the fifteen qualification choices to the project
orchestrator, who adopted every proposed default. These are accepted
**requirements**. Meeting them needs separate evidence (next section). Every
answer stays **Hypothesis** until a run on the chosen profile makes it Proven.

| # | Accepted requirement | Grade |
| --- | --- | --- |
| 1 | Budgets are measured against nominal 2400 baud (bit 416.7 µs, character 4.167 ms), anchored at the observed start edge. Only external bus-side timing qualifies. | **Hypothesis** |
| 2 | First engine: the 10x GPIO bit-level userland engine. RX uses three central samples; TX edge error ≤ 41.7 µs, abort beyond. Designated second engine, tried only if the first fails qualification or cannot hold the 41.7 µs edge budget: a dedicated PL011 kernel-driver path. One engine is qualified per profile at a time. | **Hypothesis** |
| 3 | A SYN is a framed, unescaped 0xAA and ends any wait. 100 ms with neither SYN nor character withdraws admission until a fresh SYN. | **Hypothesis** |
| 4 | Responder-only first. Physical arbitration stays Unknown and initiator traffic stays on the existing adapter path. The later arbitration budget is start-bit jitter ≤ 10 µs. | **Hypothesis** |
| 5 | Inter-character abort gap 10 ms; our responses are contiguous. | **Hypothesis** |
| 6 | Turnaround ≤ one bit; never start beyond one character (4.167 ms); final-ACK wait 200 ms; one NACK retransmit. | **Hypothesis** |
| 7 | Passive and responder runs are zero-defect, with maximum edge lateness ≤ 41.7 µs. Collision-rate budgets are set at the arbitration stage. | **Hypothesis** |
| 8 | Exactly one profile: the bench host generation, the adapter board family in raw mode, one recorded kernel, one exact toolchain. Every other combination is Unknown and off. | **Hypothesis** |
| 9 | Passive, isolated-TX and responder stages, each ≥ 90 min under load, plus a 24 h passive run and a 24 h responder run. Tails and failed attempts are reported. | **Hypothesis** |
| 10 | Userland engine: architecture monotonic counter plus descriptor-validated MMIO, with the descriptor owner-provisioned per profile and no guessed or looked-up addresses. PL011 kernel-driver path: driver interface, no user-space MMIO. | **Hypothesis** |
| 11 | A cross-process aligned-u64 acquire/release proof on the exact profile before any shared mapping. MMIO is ordered by explicit barriers. | **Hypothesis** |
| 12 | 5 s non-extendable lease; revocation before the next symbol; immediate single release on echo mismatch, late edge or foreign start; parent death withdraws admission at once. | **Hypothesis** |
| 13 | Arm only the synthetic identification read at a device-free address; silence (no ACK, no NACK) otherwise; selectors are added one at a time. | **Hypothesis** |
| 14 | Worker faults stay in the child process. The gateway, other transports and mux sessions see "backend unavailable"; restart is passive with no re-arm. | **Hypothesis** |
| 15 | TX only in attended, action-authorized bench runs. Independent hardware containment is required before any unattended arming. | **Hypothesis** |

Two clarifications apply to the table:

- Row 2: the first engine is the 10x GPIO bit-level userland engine. The
  designated second engine is the dedicated PL011 kernel-driver path, tried when
  the first fails qualification or cannot hold the 41.7 µs edge budget. Only one
  engine is qualified per profile at a time.
- Row 10: counter plus descriptor-validated MMIO applies to the userland engine.
  On the PL011 kernel-driver path the driver owns the UART registers and the user
  side sees timestamps and bytes through the driver's interface, so no MMIO
  descriptor is provisioned for that engine and row 10 reads "driver interface,
  no user-space MMIO" there.

This page authorizes no device access, bench run or live write. Every hardware
stage needs its own action-time authorization from the owner.

## Qualification evidence

One row per run, including failed and aborted runs. Each row must cite a
public redacted raw artifact or an exact durable public reference to it, plus
a public profile manifest; an opaque profile label alone is insufficient.
Record the UTC capture interval, board/frontend family and revision/configuration,
kernel/configuration, toolchain and build content digests, engine configuration,
load, power and thermal conditions, measurement method and uncertainty, and
capture provenance. Preserve raw bus bytes, direction, source/destination,
service and external edge timestamps needed to reproduce the row's aggregates
and falsify its claims. Identify the reference capture used for loss/corruption
comparisons and explain redactions and their effect on verification.

Redact credentials, private network details and personally identifying device
data before publication; retain the technical configuration and capture context
needed to distinguish the tested setup. Missing public evidence or context keeps
the affected claim **Unknown** and the profile unqualified and off. A row grades
only its own profile and stage. A finite zero-defect run is evidence for that run,
not a bound.

| Run | Stage | Profile (label) | Public evidence / profile manifest | UTC capture interval | Engine | Duration | Samples / symbols / segments | Gaps | Framing faults (bus-confirmed) | Lost or corrupted vs reference | Lateness p99 / p99.9 / max | Failed attempts | External timing | Grade and remaining Unknowns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| — | — | — | — | — | — | — | — | — | — | — | — | — | — | No run recorded. Every requirement above remains a requirement; qualified external timing (`AA22QualifiedTiming`) is Unknown for every profile. |

## Required acceptance detail

The timing answer must distinguish the end of the final request character on
the wire to the first permitted response start edge from the request-CRC-to-ACK
metric. Define the exact physical edges and their relationship to native phase
completion for each metric. Enqueue, callback, write completion and delivery time
are not wire timestamps. Specify RX observation-gap tolerance, TX bit/edge error,
turnaround, higher-tail and worst-observed limits separately. Do not adopt the
proposal's feasibility objective as product acceptance or add percentiles to infer
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
already-driven levels without relaxing the offline transport contract's
per-symbol authority checks.
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

For the linked gateway parent, the relevant obligations are restated here:
Deadline handling must be independent of observer queues, using prepared local
plans without a subscriber callback or IPC round trip in the response path.
Stale responses and slots must not survive invalidation, revocation or restart;
retirement needs acknowledgement or finite expiry with reader quiescence.
Finally, each adapter/transport/profile combination needs external on-wire
qualification against accepted timing/error budgets. Exact matching to the
parent's numbered acceptance criteria remains unverified, as the registration
contract's acceptance trace also states. The software contracts do not discharge
these physical edges.

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
