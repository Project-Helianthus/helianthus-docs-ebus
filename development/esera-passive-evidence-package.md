# ESERA passive evidence handoff worksheet

This is the documentation preparation slice of FOLLOWUP-01, tracked in
[docs issue #640](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/640).
Hardware acceptance stays with
[docs parent #241](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/241)
and [plan parent #7](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/7).
This blank worksheet records no capture, qualification, ESERA support claim,
release result, or completed parent acceptance. Every result starts **Not run**;
every evidence conclusion starts **Unknown**.

## Contract sources and interpretation

Use the public native [ENH contract](../protocols/enh.md) and
[ENS contract](../protocols/ens.md) before interpreting bytes. ENH/ENS transport
prefixes and the firmware data-only escape codec are distinct layers. Record
the actual layer; a prefix or product label does not establish it. Do not infer
adapter control events from a data-only codec.

Use the existing [XR conformance catalog and matrix](../architecture/enh-ens-conformance-tests.md#cross-reference)
for invariant names and documented deviations, and the
[smoke matrix](smoke-matrix.md#matrix-coverage) for topology families. Existing
implementation test status is corroboration, not an ESERA hardware verdict.
Keep conflicting evidence visible and scoped to its family and layer.

The [observe-first transport contract](../deployment/full-stack.md#passive-observe-first-transport-contract)
separately governs application passive capability: direct adapter-class ENH/ENS
and ebusd-tcp paths are unsupported or misconfigured for passive observe-first;
proxy-like ENH/ENS paths require their own evidence. A TCP connection, heartbeat,
healthy process, or INIT response is not bus evidence. Native INIT may proceed
with unknown features after a bounded timeout; this does not admit semantics.

## Capture boundary worksheet

Complete the boundary review before any later operator-controlled session.
This document authorizes no connection, adapter command, scan, poll, write,
arbitration, reset, reconnect experiment, or equipment mutation. In particular,
do not send INIT, INFO, START, SEND, or malformed commands to satisfy a row.
Observe only an independently authorized passive stream; use synthetic offline
replay for injected negative controls. If obtaining evidence requires active
traffic or changing a live setup, retain Not run and refer it to the parents.

| Boundary field | Operator entry | Review result |
|---|---|---|
| Adapter family; public firmware/version context (or unavailable) | Unknown | Not run |
| Bus participant families; public participant firmware context when known (otherwise Unknown); no model or uniquely identifying labels | Unknown | Not run |
| Topology family; direct/proxy; transport and codec layer | Unknown | Not run |
| Existing matrix case selected from its manifest; selection rationale | Unknown | Not run |
| Passive source and direction; any pre-existing active traffic distinguished | Unknown | Not run |
| Planned maximum duration and byte/event bound; relative time origin | Unknown | Not run |
| Stop conditions: bound reached, data loss, unexpected transmission, uncertain isolation | Unknown | Not run |
| Passive-only configuration and absence of observer-originated traffic established | Unknown | Not run |
| Publication review: synthetic excerpts only; observed captures excluded | Unknown | Not run |

Private coordinates, credentials, hostnames, addresses of network endpoints,
serials, contributor identities, absolute capture times, and installation
details stay outside this public package. Observed captures and their raw or
decoded excerpts stay outside it too, even when sanitized. A public-safe
observation report may be referenced by repository-relative link and section,
with family/firmware context, source direction, layer, relative observation
bounds and the basis and limits of each conclusion. It must contain no raw or
decoded capture excerpts, private lookup keys, links to excluded evidence,
Git revision identifiers or pinned-revision links. Public byte and
decoded excerpts must be synthetic, labelled synthetic, and never presented
as observed evidence. Leave a dependent claim Unknown when public evidence
cannot support it; synthetic replay establishes no hardware observation.
Do not generalize a participant observation across a family when the permitted
family/firmware context cannot establish its applicability; retain Unknown.

## Required public-safe artifact fields

Use repository-relative artifact links and family wording. This is a worksheet,
not a new application artifact schema. Keep unavailable fields explicitly
Unknown and unexecuted observations Not run. The excerpt rows below accept
synthetic offline replay only; they do not request publication of captures.

| Artifact | Required fields to fill | Artifact link | Result |
|---|---|---|---|
| Boundary and provenance note | Synthetic replay provenance or public-safe observation report link and section, clearly distinguished; adapter and participant families and public firmware context; topology/layer; passive constraints; duration and byte bounds; omission/redaction reasons | Unknown | Not run |
| Capability record | Synthetic response bytes labelled as replay; direction; negotiated features versus unknown features; application passive-capability state and reason kept separate | Unknown | Not run |
| Synthetic receipt excerpt | Ordered synthetic adapter-to-host bytes/events; offsets and relative elapsed durations; layer; frame boundaries; gaps, truncation, drops and errors; no invented missing bytes | Unknown | Not run |
| Synthetic decoded example | Synthetic receipt-offset references; decoder/version context; direction; source and destination eBUS bus addresses; PB/SB or service; payload/register bytes; CRC/frame validity when determinable; decoded type/unit or Unknown | Unknown | Not run |
| Claim and admission record | Native source link; family scope; evidence grade; independent codec/profile qualification; admitted/withheld reason; last-known-good lineage and freshness where already available | Unknown | Not run |
| Negative-control record | System-under-test component and public release/version (or Unknown; no Git pins); replay tool and version; synthetic input link and exact transformation; referenced XR row or application boundary; expected rejection/withholding; actual output/error and retained state | Unknown | Not run |

An unidentified implementation build or replay tool cannot support a
reproducible replay claim; record that limitation explicitly.

Retain observed raw evidence beside its interpretation outside the public
package. In public synthetic examples, preserve physical wire bytes, transport
control events, logical bytes and semantic values as separate representations
with traceable offsets. For a B524 interpretation retain
the full `(opcode, group, instance, register)` identity; never merge OP=0x02
and OP=0x06. A UI label, decoded value or successful read proves no writability.

## Four independent evidence decisions

Fill these separately for each bounded family/topology and artifact set. The
evidence grade is Proven, Hypothesis, or Unknown; qualification and admission
are separate decisions. A Proven bounded receipt would not qualify a codec,
profile, family-wide support, or semantic mapping automatically. Observed
captures needed below remain outside this public package. Link each recorded
hardware decision to its public-safe observation report and section; retain
Unknown and withhold acceptance when the public report cannot substantiate
the decision independently. Synthetic examples cannot satisfy hardware
evidence decisions.

| Decision | Evidence needed | Evidence grade | Qualification/admission | Result |
|---|---|---|---|---|
| Adapter capability | Native response/provenance for each claimed optional feature; application passive-capability evidence recorded separately | Unknown | Unknown | Not run |
| Raw receipt | Ordered, attributable passive bus bytes, with loss and layer boundaries exposed; heartbeat/TCP/INFO alone insufficient | Unknown | Unknown | Not run |
| Decoded observation | Falsifiable raw-to-decoded mapping and validity/error context; preserve uncertain and partial frames | Unknown | Unknown | Not run |
| Semantic admission | Public native mapping plus the existing family/profile and codec qualification requirements; raw and decoded lineage intact | Unknown | Withheld pending evidence | Not run |

Missing, stale, malformed, contradictory or unqualified evidence must not
create a new semantic admission. Preserve partial last-known-good observations
with their original lineage and freshness/unknown status; do not replace them
with fabricated defaults or relabel old data as newly observed. Capability
withdrawal or a failed decode is recorded independently of retained data.
Follow the native RESETTED cache invalidation rules: retaining historical
evidence never authorizes reusing invalidated INFO as current capability.

## Existing matrix references and negative controls

All injected controls below are synthetic offline exercises for a later
operator to record. Their expected outcomes come from the linked contract;
none is an executed test or a request to inject traffic into hardware.

| Existing XR row or boundary | Planned control and expected observation | Result | Evidence grade |
|---|---|---|---|
| `XR_INIT_TimeoutFailOpen_Bounded` | Replay no RESETTED within the catalog's INIT bound: unknown features, no optional-feature inference; connection continuation alone supplies no receipt proof | Not run | Unknown |
| `XR_UpstreamLoss_GracefulShutdown_NoHang` | End the synthetic stream mid-frame/session: bounded error completion; no invented complete observation | Not run | Unknown |
| `XR_ENH_UnknownCommand_ExplicitError_AdapterToHost` | Replay the catalog's undefined response command: explicit protocol error, not silent discard, timeout or collision | Not run | Unknown |
| `XR_ENH_ParserReset_AfterReadTimeout` | Replay a partial encoded frame across the read timeout, then a valid RECEIVED frame: reset parser and decode the new frame independently | Not run | Unknown |
| `XR_ENH_0xAA_DataNotSYN` | Replay escaped logical data inside a frame versus bare wire SYN: preserve the catalog's data/boundary distinction | Not run | Unknown |
| `XR_INFO_RESETTED_CachePolicy_Explicit` | Replay RESETTED with cached INFO: invalidate current cache; preserve historical raw evidence; retain the catalog's stateless exemption | Not run | Unknown |
| `XR_INFO_FrameLength_AndSerialAccess` | Replay truncated/interleaved INFO and concurrent synthetic requests: exact length and serialize/reject policy; no response stealing or fabricated completion | Not run | Unknown |
| Application boundary: [passive transport contract](../deployment/full-stack.md#passive-observe-first-transport-contract) | Replay heartbeat/connection/capability-only evidence with no bus bytes: raw receipt and semantics remain unproven; unsupported topology stays unavailable | Not run | Unknown |
| Admission boundary: four independent decisions above | Replay an incomplete or unqualified decoded candidate: withhold new admission; retain partial last-known-good lineage without freshness promotion | Not run | Unknown |

The first seven identifiers refer to rows in the
[existing XR matrix](../architecture/enh-ens-conformance-tests.md#cross-reference),
including its partial/alias/deviation notes. Application boundaries are not
new XR rows or native wire claims. Host-to-adapter command rejection,
arbitration, transmission/echo, fairness and ownership tests are outside this
passive worksheet; do not imply that passive receipt covers them.

Select actual case IDs from the existing manifest, without inventing a mapping:
`T01..T04` direct, `T05..T08` via ebusd-tcp, `T09..T24` proxy single-client,
and `T25..T88` proxy dual-client. The
[P03 proof](smoke-matrix.md#observe-first-proof-note) applies only to its stated
proxy-backed ENS family; this worksheet does not execute its canary phases.
The [proxy adjunct](smoke-matrix.md#proxy-semantics-adjunct-gate-px01px12)
retains `PX01..PX12` and its existing scope. No XR implementation status,
synthetic result, P03 artifact shape, or worksheet entry substitutes for the
required hardware matrix or changes its expected-failure inventory.

## Handoff disposition

| Handoff question | Entry | Result |
|---|---|---|
| Public-safe evidence links complete and independently reviewable? | Unknown | Not run |
| Each of the four decisions scoped and supported independently? | Unknown | Not run |
| Negative controls recorded with expected and actual outcomes separate? | Unknown | Not run |
| Conflicts, omissions and remaining hardware work returned to both parents? | Unknown | Not run |

The [deferred FOLLOWUP-01 ownership](smoke-matrix.md#deferred-esera-passive-validation-note)
and [transport runtime gate](contributing.md#transport-runtime-gate-merge-blocking)
remain unchanged. Documentation preparation closes no hardware acceptance.
Any required production transport change is HELD for a separately owned patch
and the applicable `T01..T88` gate, plus `PX01..PX12` when in scope. Ordinary
CI, documentation review and any failing result still gate this docs slice.
