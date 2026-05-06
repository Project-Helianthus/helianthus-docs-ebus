# Startup Admission and Discovery Pipeline

Status: Normative; source-selection semantics superseded by SAS-01
Plan reference:
[startup-admission-discovery-w17-26.locked/00-canonical.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/00-canonical.md)
(`Canonical-SHA256:
345445f1cedfc21e6c35d6e0f21513979fbf7ff3a520978932f0dd82e65c1b3d`)

SAS-01 update:
`source-address-selection-admission.locked` supersedes this document wherever
it describes `JoinBus`, `Joiner`, `JoinConfig`, `JoinResult`,
`admission_path_selected`, forced selection, or fixed-source override as current
startup authority. Those terms remain here only as history for the W17-26
startup plan. Current startup admission is:

```text
observe -> source_address_select -> active_probe
  -> persist/scan only on active_probe_passed
  -> quarantine/exclude/reselect on probe failure
  -> DEGRADED_SOURCE_SELECTION with zero Helianthus-originated eBUS traffic
     when no candidate can be admitted
```

The admitted `SourceAddressSelection.Source` is the sole normal source
authority for gateway-owned MCP, GraphQL, Portal, semantic, scheduler, poller,
NM, and protocol-dispatch traffic. Exact operator source configuration maps to
`explicit_validate_only`; it bypasses candidate search but not active
validation. Persisted raw `source_addr.last` is migration input only and cannot
override explicit configuration or current validation.

The only first-implementation pre-discovery source-validation probe is a
bounded addressed `0x07/0x04` read-only request against a configured or current
positive target. Broadcast `0x07/0xFE`, `0x07/0xFF`, `0x0F`, NM, mutating
services, memory writes, and full-range probes are not admission-validation
traffic.

## Purpose

This document freezes the normative startup-admission and
passive-first discovery pipeline for Helianthus on non-ebusd-tcp
direct transports. It ratifies the M0 doc-gate for cruise-run
meta-issue `#20` and extracts the startup-admission portion of
`ISSUE-GW-JOIN-01` from the parent maintenance plan into a transport-
specific contract that implementation PRs can consume without
reopening the already locked design questions.

This document is intentionally narrow. It governs how the gateway
acquires or overrides its local initiator identity, how warmup and
directed discovery are ordered, how passive evidence is promoted, how
degraded mode is surfaced, and how the machine-readable admission
artifact is shaped. It does NOT redefine the broader NM model, the
broader discovery model, or the B524 semantic root-discovery rules.
Those documents remain authoritative where they already apply.

The keywords MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, and
MAY are normative in this document.

The implementation scope of this document is ENH, ENS, UDP-plain, and
TCP-plain. `ebusd-tcp` is included only as a contrast case for
transport-class selection, static-source fallback, and the sanctioned
full-range retry guard. The startup-admission artifact specified here
is not emitted for `ebusd-tcp` in this plan.

<a id="introduction-and-scope"></a>
## 1. Introduction and Scope

### 1.1 Problem Statement

The observed startup scan storm had two coupled root causes and must be
treated as a two-layer defect, not as an isolated scan-logic bug.

At the admission layer, the gateway could emit active frames using a
static or prematurely assumed local initiator before a direct transport
had established a valid `JoinResult`. At the discovery layer, the
gateway could still behave like a probe-centric scanner and drive
full-range address work before a passive topology picture had formed.
Fixing either layer alone would leave the other capable of producing
the same bus-disturbance pattern under a different trigger.

This document therefore specifies a single startup pipeline with four
required properties:

1. passive observation begins first;
2. admission selects or overrides the active initiator before
   non-override active traffic;
3. discovery promotion is passive-first and bounded;
4. degraded mode is explicit rather than silently falling through to a
   probe-heavy fallback.

### 1.2 Scope Boundary

This document applies only to non-ebusd-tcp direct transports:

- ENH
- ENS
- UDP-plain
- TCP-plain

For these transports, the startup pipeline is:

1. passive reconstructor started;
2. `JoinBus` subscription established;
3. Joiner warmup executed unless operator override bypasses gating;
4. admission path selected;
5. directed probe phase entered if and only if directed confirmation is
   needed;
6. semantic polling gate released only under the contract in
   [§2](#startup-ordering-contract).

`ebusd-tcp` remains out of this pipeline's active admission scope. It
does not run Joiner in this plan, does not emit the admission artifact
defined here, and continues to use configured static-source fallback as
described in
[nm-participant-policy.md](./nm-participant-policy.md#local-address-pair-authority).

### 1.3 Relationship to Existing Normative Docs

This document augments, but does not rewrite:

- [nm-model.md](./nm-model.md)
- [nm-discovery.md](./nm-discovery.md)
- [nm-participant-policy.md](./nm-participant-policy.md)
- [b524-semantic-root-discovery.md](./b524-semantic-root-discovery.md)
- [protocols/ebus-services/ebus-overview.md](../protocols/ebus-services/ebus-overview.md)

The existing documents remain the normative source for:

- the NM state machine and service classification;
- the general passive-first discovery philosophy;
- local address-pair authority and frozen NM-class load numbers;
- the B524 startup recovery rule;
- wire-level transaction semantics and inferred target attribution.

This document adds the missing cross-document contract for startup
ordering, admission selection, degradation, and the discovery-class
startup burst band.

### 1.4 Parent-Plan Relationship

This plan package is the narrow-scope execution of `ISSUE-GW-JOIN-01`
from the maintenance plan
`ebus-good-citizen-network-management.maintenance`. The parent remains
authoritative for the broader NM initiative. This document extracts the
startup-admission and discovery-specific subset needed by this cruise
run and makes it independently reviewable under the docs gate for issue
`Project-Helianthus/helianthus-docs-ebus#286`.

This relationship is additive:

- parent-plan intent remains authoritative;
- this document does not reopen parent-plan settled decisions;
- M0 ratifies the direct-transport startup pipeline so downstream
  gateway milestones can proceed under AD18 Tier 1.

### 1.5 Hard Out-of-Scope Guards

The following remain out of scope for this document and for the
implementation work it gates:

- new `FF 00`, `FF 01`, or `FF 02` emission semantics;
- active `07 FF` broadcast discovery;
- active `07 FE` broadcast discovery as a general startup scan;
- responder-lane `07 04`, `FF 03`, `FF 04`, `FF 05`, or `FF 06`
  implementation;
- peer-NM interrogation as a topology source;
- passive transaction reconstructor refactoring;
- semantic poller internals refactoring;
- firmware or adapter-proxy protocol changes;
- any non-additive Home Assistant API surface changes.

### 1.6 Terms Used Here

For the purposes of this document:

- **admission** means selecting the active local initiator and
  companion-target provenance for startup;
- **warmup** means the default `JoinConfig` listen-first window of at
  least `5s`;
- **directed probe** means an explicit-target `07 04` confirmation sent
  through the new `helianthus-ebusreg` directed scan API;
- **startup window** means the first `60s` over which the discovery-
  class startup burst budget is measured;
- **degraded mode** means admission is not active and the gateway keeps
  retrying on backoff while active semantic polling remains gated.

<a id="startup-ordering-contract"></a>
## 2. Startup Ordering Contract

### 2.1 Contract Summary

On join-capable direct transports, the gateway MUST complete passive
startup admission before it emits any non-override active frames.

The required order is:

```text
INIT / INFO
  -> PassiveTransactionReconstructor started
  -> JoinBus subscribed
  -> Joiner warmup (>= 5s, default JoinConfig)
  -> admission path selected
  -> first active directed probe, if any
  -> semantic polling gate closes
```

This sequence is a startup invariant, not a best-effort preference.

### 2.2 Default Path When Override Is Unset

When `StartupSource.Override` is unset, the gateway SHALL perform the
following sequence.

#### 2.2.1 Passive First

The passive reconstructor MUST start before Joiner warmup begins. The
Joiner consumes reconstructed traffic through `JoinBus`; therefore a
warmup window without an already-running reconstructor is not a valid
warmup window.

#### 2.2.2 JoinBus Before Warmup

`JoinBus` MUST subscribe to the reconstructor before Joiner warmup
begins. The subscription point defines the earliest admissible event
boundary for warmup evidence.

#### 2.2.3 Warmup Duration and Default JoinConfig

The default warmup MUST be at least `5s`.

The default `JoinConfig` is:

- warmup enabled with duration `5s`;
- inquiry disabled;
- persist-last-good enabled.

The contract frozen here assumes `InquiryEnabled=false`. Under that
setting:

- `JoinBus.InquiryExistence` MUST return an explicit not-supported
  sentinel;
- it MUST NOT return `nil`;
- it MUST NOT emit `07 FE`.

#### 2.2.4 Admission Completes Before Active Frames

The first non-override active frame MUST NOT be emitted until a valid
`JoinResult` exists.

Valid here means:

- `JoinResult.Initiator` is present and transport-consistent;
- `JoinResult.CompanionTarget` is present and transport-consistent;
- the admission path is `join`.

Before those conditions hold:

- `probe_count` MUST remain `0`;
- active semantic polling request count MUST remain `0`.

#### 2.2.5 Directed Probes Follow Admission

In the historical W17-26 wording, the directed-probe phase could begin only
after the `join` path was selected, and directed probes used
`JoinResult.Initiator` as their source.

In current SAS M4 terms, directed probes MAY begin only after source selection
and active probe validation admit a source. Directed probes use the admitted
`SourceAddressSelection.Source` as their source.

No directed probe MAY be used to bootstrap admission itself.

### 2.3 Historical Override Carve-Out

The old override path was an explicit W17-26 carve-out from the
warmup-before-active-frame invariant: when `StartupSource.Override` was set,
the operator override acted as the active source and warmup did not gate
emission on that historical path.

SAS M4 supersedes that carve-out. Exact source configuration now maps to
`explicit_validate_only`: candidate search is bypassed, but the configured
source still requires active validation before any normal Helianthus-owned
traffic uses it. It does not create a general allowance for static-source
fallthrough on source-selection-capable direct transports.

### 2.4 Historical Override Branches

#### 2.4.1 Historical `Override` Set and `Validate=false`

The old `StartupSource.Override.Validate=false` branch is historical W17-26
wording only. Current SAS M4 implementations SHALL NOT emit immediate normal
Helianthus-owned active traffic from this branch. Exact configured source input
SHALL be represented as `admission.source_selection.mode =
explicit_validate_only`, SHALL set
`startup_source_selection_explicit_source_active=1`, and SHALL pass active
validation before normal gateway-owned MCP, GraphQL, Portal, semantic,
scheduler, poller, NM, or protocol-dispatch traffic uses the source.

Diagnostic transport-specific MCP calls remain outside this normal-operation
authority and may use a caller-supplied source for that one diagnostic request.

#### 2.4.2 Historical `Override` Set and `Validate=true`

The old `StartupSource.Override.Validate=true` advisory-Joiner branch is also
historical. Current SAS M4 implementations use source-address selection plus
active probe validation; they SHALL NOT emit the removed `override` value and
SHALL NOT keep an advisory Joiner as current source authority.

If exact source validation fails, normal gateway-owned traffic remains blocked
and the admission state transitions to degraded source selection rather than
falling back to unvalidated static-source operation.

### 2.5 Semantic Polling Gate

The existing `semanticBarrier` closure predicate in
`cmd/gateway/main.go:194-202` SHALL be extended so that the barrier
closes only when BOTH of the following are true:

1. `startupScanSignals.semanticBootstrapReady` has fired; and
2. admission is either:
   - Joiner-success with a valid `JoinResult`, or
   - override-set.

The barrier MUST remain open when:

- admission is degraded without override;
- warmup observed no valid admission outcome;
- Joiner has not yet succeeded;
- the transport has not recovered after rejoin failure.

The semantic polling change above is a signal-source change only. The
implementation MUST reuse the existing poller-internal barrier wait and
change only the outer closure predicate. It MUST NOT refactor poller
internals or add a second admission gate inside the poller.

### 2.6 Failure Cases Under the Ordering Contract

If Joiner fails and no override is configured:

- the selected admission path SHALL be degraded;
- `probe_count` SHALL remain `0`;
- active semantic polling request count SHALL remain `0`;
- passive observation MAY continue;
- rejoin backoff MAY continue;
- no active admission-bootstrapping traffic may be emitted.

This is an explicit degraded state, not a permission to fall back to a
full-range scan or to static-source operation.

<a id="admission-path-selection"></a>
## 3. Admission Path Selection

### 3.1 Enum

For the current SAS M4 source-selection surface, startup source selection SHALL
be emitted and reasoned about using:

`admission.source_selection.mode ∈ {source_selection, explicit_validate_only,
degraded_transport_blind, degraded_no_events}`

No other value is valid under the current source-selection artifact contract.

### 3.2 Value Definitions

| Value | Triggering Condition | Meaning | Active Traffic Allowed |
|---|---|---|---|
| `source_selection` | source-selection-capable direct transport produced a valid source before first non-explicit-source active frame | direct source selection succeeded | yes, using selected source |
| `explicit_validate_only` | exact source configuration is set, regardless of `Validate` branch | operator supplied exact source, still actively validated | yes, using explicitly configured source after validation rules |
| `degraded_transport_blind` | warmup window observed zero passive events and admission could not establish a valid source | silent-bus or transport-blind startup | no |
| `degraded_no_events` | transport is observable enough to run warmup, but no admissible `JoinResult` exists by warmup end and no override is set | admission degraded after observable but insufficient or conflicting evidence | no |

Subsections 3.3 through 3.6 retain the historical W17-26 wording. Current SAS
M4 consumers use the mapped labels in the table above.

### 3.3 `join`

`join` is a historical W17-26 artifact label. Current SAS M4 artifacts SHALL
emit `source_selection` instead.

The old `join` label was selected only when all of the following were true:

- the transport is one of ENH, ENS, UDP-plain, or TCP-plain;
- Joiner was wired through `JoinBus`;
- Joiner completed with a valid `JoinResult`;
- the first non-override active frame, if any, uses
  `JoinResult.Initiator`.

The current high-confidence non-explicit-source path on source-selection-
capable direct transports is `source_selection`, not `join`.

### 3.4 `override`

`override` is a historical W17-26 artifact label. Current SAS M4 artifacts SHALL
emit `explicit_validate_only` for exact configured source input, and that source
still requires active validation before normal Helianthus-owned traffic may use
it. Current artifacts SHALL NOT emit `override`.

### 3.5 `degraded_transport_blind`

`degraded_transport_blind` is selected when the warmup interval
observes zero passive events and therefore cannot support admission.

This value is specific to a startup condition where the transport path
is blind or the bus is silent enough that warmup cannot produce any
usable observations.

The required degraded reason log for this case is:

`startup admission degraded reason=transport_blind`

### 3.6 `degraded_no_events`

`degraded_no_events` is selected when the transport is active enough to
produce warmup observation, but startup still cannot establish a valid
direct admission result and no override is set.

This bucket includes, at minimum, join-attempt outcomes where:

- warmup produced observation but no usable local initiator candidate;
- the join process did not converge to a valid pair;
- passive evidence did not justify any active source selection.

This value intentionally does NOT authorize fallback to configured
static-source operation on direct transports.

### 3.7 Transport Classification Cross-Reference

Transport capability classification is defined operationally in
[nm-participant-policy.md §Transport Capability Matrix](./nm-participant-policy.md#transport-capability-matrix)
and restated as a focused startup matrix in
[§10](#transport-capability-matrix).

The path-selection implications are:

- ENH, ENS, UDP-plain, TCP-plain:
  `source_selection` or `explicit_validate_only`, otherwise degraded;
- `ebusd-tcp`:
  static configured fallback remains the default path outside the
  artifact scope of this plan.

The selected enum value SHALL drive the admission artifact field
`admission.source_selection.mode`, degraded-mode log classification, and
observability review of startup behaviour. It SHALL NOT by itself change
discovery promotion rules.

<a id="evidence-pipeline-and-promotion"></a>
## 4. Evidence Pipeline and Promotion

### 4.1 Pipeline Summary

Discovery in this plan is passive-first. It does not begin with a
broadcast sweep and it does not assume that startup must establish
identity for every device before semantic readiness can advance.

The pipeline is:

```text
passive reconstructor
  -> evidence buffer
  -> suspect promotion
  -> directed confirmation only when needed
  -> startup-directed probe phase
  -> normal steady-state discovery maintenance
```

### 4.2 Source of Admission Warmup Evidence

`JoinBus` SHALL subscribe to `PassiveTransactionReconstructor`.

The admissible event classes forwarded to Joiner are constrained by the
plan and by the reconstructor contract:

- broadcast events: request-only;
- initiator/initiator events: request-only;
- initiator/target events with response: request plus inferred
  response;
- abandoned transactions: not forwarded;
- discontinuity events: not forwarded.

Warmup evidence seeds the evidence buffer but MUST NOT directly promote
devices solely by virtue of being observed during warmup.

### 4.3 Passive-First Principle

Before any directed confirmation occurs, the gateway MUST accumulate
passive evidence.

Passive evidence is preferred because it:

- adds zero startup bus load;
- reflects the real bus population instead of a synthetic probe
  population;
- aligns discovery with the NM model's observe-first philosophy.

Directed confirmation is allowed only after passive evidence has
created or promoted suspects that justify explicit target work.

### 4.4 Promotion Rule

Promotion follows AD03.

A suspect SHALL be promoted when either of the following is true:

- the suspect has at least two observations; or
- the suspect has any single strong evidence signal.

No weaker rule is permitted.

### 4.5 Evidence Classification Table

The classification below is normative.

| Evidence Source | Strength | Address Confirmed | Notes |
|---|---|---|---|
| CRC-valid `07 04` request + response pair | strong | both initiator and target | strongest targeted identity signal in scope |
| Request-only `07 04` | weak | requester only | does not confirm target |
| Passive `FF 00` broadcast | strong | originator | startup-presence evidence |
| Passive `FF 01` broadcast | strong | originator | presence evidence even if Helianthus does not emit it |
| New-source CRC-valid cyclic application traffic | strong | sender | catch-all passive source |
| Inferred target response from reconstructed initiator/target exchange | strong | target | target inferred from direct-mode transaction semantics |

The target inference rule above depends on the direct-mode transaction
shape in
[protocols/ebus-services/ebus-overview.md](../protocols/ebus-services/ebus-overview.md).
The target response does not repeat addressing bytes on the wire, so
target identity is inferred from the initiating request context.

### 4.6 Evidence Buffer

The evidence buffer SHALL be present and SHALL be bounded.

The required baseline contract is:

- `max_entries=128`;
- LRU eviction;
- baseline-topology protection;
- configurable seed list.

The buffer is not a best-effort cache. It is a normative retention
contract used to prevent startup floods from evicting addresses that
are already known to be structurally important for the observed
topology.

### 4.7 Baseline Topology Protection

The evidence buffer SHALL protect the configured baseline topology seed
from ordinary LRU eviction pressure.

The seed is configurable at:

`startup_admission.baseline_topology_seed`

The Vaillant default seed is:

`{0x08, 0x15, 0x26, 0x04, 0xF6, 0xEC}`

This set corresponds to the currently observed baseline topology and
serves as the first lock's protected address set.

### 4.8 Baseline Seed Validation

Each configured baseline seed address MUST be validated at config load.

Validation rules are:

- address must be within the eBUS target-capable address range;
- address MUST NOT be `0xFE` broadcast;
- address MUST NOT be `0xAA` SYN;
- invalid seed configuration is a startup error.

### 4.9 Retention Behaviour Under Flood

Under startup evidence flood conditions:

- total buffer length MUST remain `<= 128`;
- baseline-protected entries MUST survive;
- non-protected entries MAY be evicted by LRU.

This retention behaviour is part of the plan's required regression
surface.

### 4.10 Directed Confirmation Input Set

Directed probes SHALL draw their target set from promoted suspects
without identity, not from the full legal address range.

This means:

- no nil target list;
- no empty target list;
- no `0x01..0xFD` sweep;
- no use of directed confirmation to manufacture suspects out of thin
  air.

### 4.11 Rejoin Backoff

Admission degradation does not end the startup logic. It enters rejoin
retry on bounded backoff.

The rejoin backoff contract is:

- `Base=5s`;
- `Max=60s`;
- exponential growth (`Base`, `2*Base`, `4*Base`, ...);
- cap persists until rejoin success.

This backoff aligns with the ebusgo defaults named in the plan and is
part of the degraded-mode recovery contract.

### 4.12 What Evidence Does Not Do

Evidence accumulation MUST NOT:

- close the semantic barrier by itself;
- authorize active semantic polling without admission success or
  override;
- justify full-range active scanning on direct transports;
- treat decode faults or discontinuities as promotion evidence.

Decode faults and discontinuity events are observability-loss signals,
not positive presence evidence.

<a id="startup-directed-probe-phase"></a>
## 5. Directed Probe Phase and Bus-Load Budget

### 5.1 Glossary Definition

`startup_directed_probe_phase` is the post-admission, startup-bounded
interval during which the gateway may send explicit-target `07 04`
probes against promoted suspects that still lack identity, using the
selected active initiator.

This term replaces the older and misleading idea of a generic "startup
scan pass" for adapter-direct transports.

### 5.2 Entry Conditions

The startup-directed probe phase MAY begin only when all of the
following are true:

- the transport is source-selection-capable direct transport;
- the admission mode is `source_selection` or `explicit_validate_only`;
- the target set is explicit and non-empty;
- each target is target-capable and valid for directed scan;
- the startup rate limiter allows the next probe.

### 5.3 Zero Intersection With Legacy Full-Range Scan

The startup-directed probe phase has ZERO intersection with the legacy
full-range `0x01..0xFD` scan.

For the avoidance of doubt:

- the startup-directed probe phase is explicit-target only;
- it is driven by promoted suspects, not by raw address enumeration;
- it is allowed on direct transports under this document;
- the legacy full-range retry remains a distinct mechanism;
- that full-range retry remains sanctioned only for `ebusd-tcp` under
  the guarded conditions in [§9](#full-range-retry-guard) and
  [b524-semantic-root-discovery.md](./b524-semantic-root-discovery.md).

### 5.4 Startup Burst Budget

The discovery-class startup burst limit is:

`discovery_class_startup_burst_pct_limit = 2.0`

This limit is measured over a startup window of:

`window_s = 60`

This discovery-class burst band is NEW in this M0 doc-gate. It does
not modify the frozen NM-class sustained and burst numbers; it governs
only the startup-directed probe phase.

### 5.5 Post-Startup Rate Limit

After the startup window ends, directed confirmation returns to a
steady-state rate limit of:

`1 probe per 15s`

This is expressed as:

`post_startup_sustained_rate_probes_per_15s = 1`

The steady-state rate is an invariant, not a tuning suggestion.

### 5.6 Wire Capacity Derivation

The frozen bus math used here is:

- eBUS baud rate: `2400`;
- framing cost: `10 bits` per byte;
- useful wire capacity: `240 bytes/s`.

At `2.0%` of capacity, the startup discovery-class burst ceiling is:

`240 B/s * 0.02 = 4.8 B/s`

The plan rounds the operational envelope to approximately `5 B/s` for
the purpose of the startup `probe_count` acceptance rule.

### 5.7 `probe_count <= 15` Derivation

A full directed `07 04` transaction is treated as approximately
`18-22 wire bytes` before escape expansion.

At the hard acceptance bound of `15` probes over `60s`:

- low estimate: `15 * 18 = 270 bytes`;
- high estimate: `15 * 22 = 330 bytes`.

Per second, this is:

- low estimate: `270 / 60 = 4.5 B/s`;
- high estimate: `330 / 60 = 5.5 B/s`.

The plan's ratified operational shorthand is:

- `probe_count <= 15` satisfies the intended startup burst budget at
  approximately `5 B/s`;
- the acceptance gate remains `startup_burst_pct <= 2.0` over the
  `60s` window;
- `probe_count <= 15` is a hard companion limit and a startup
  behavioural guard.

### 5.8 Probe Ceiling

The following hard ceilings apply during the startup window:

- `probe_count <= promoted_suspects_without_identity`;
- `probe_count <= 15`.

The second ceiling is absolute. Any startup run with `probe_count > 15`
fails acceptance regardless of why extra probes were emitted.

### 5.9 Probe Source

The source address used for directed probes SHALL be the admitted
`SourceAddressSelection.Source`, regardless of whether the mode is
`source_selection` or `explicit_validate_only`.

No other source is valid on direct transports in this plan.

### 5.10 Probe Purpose

Directed probes exist to confirm or identify promoted suspects that
remain identity-pending.

Directed probes SHALL NOT be used:

- as a general liveness sweep;
- as a replacement for admission warmup;
- as a way to force topology population on a silent bus;
- as a substitute for the deprecated full-range scan behaviour.

### 5.11 Full-Range Separation Statement

The direct-transport startup pipeline specified here and the bounded
full-range retry described in the B524 document are mutually distinct
mechanisms.

The direct-transport startup pipeline:

- uses explicit promoted-suspect targets;
- is allowed on ENH, ENS, UDP-plain, TCP-plain;
- never performs a full-range pass.

The sanctioned full-range retry:

- exists only for `ebusd-tcp` in this plan;
- is guarded by the B524 startup recovery rule;
- is disabled by default on non-ebusd-tcp transports.

<a id="degraded-mode-surface"></a>
## 6. Degraded Mode Surface

### 6.1 Purpose

Degraded mode exists to make admission failure explicit. It is not a
silent fallback and it is not a hidden retry loop.

When admission is degraded:

- the gateway keeps retrying on bounded backoff;
- passive observation continues when available;
- active semantic polling remains gated unless override is active;
- observability surfaces show the degraded state.

### 6.2 Required Degraded Log Line

On entry to degraded mode, the gateway SHALL emit:

`startup admission degraded reason=<reason>`

This is the primary operator-facing degraded admission line.

The reason value MUST be structured enough to distinguish at least:

- `transport_blind`;
- join-attempt degradation with observed traffic but no admissible
  result.

### 6.3 Admission States

For observability purposes, the state machine exposed here is:

- `0 = pending`
- `1 = active`
- `2 = degraded`

This is an admission-surface state model, not a replacement for the
NM state machine.

### 6.4 Required Expvars

The implementation SHALL expose exactly these admission-related
expvars:

| Expvar | Type / Domain | Required Semantics |
|---|---|---|
| `startup_source_selection_degraded_total` | monotonic counter | count of degraded transitions |
| `startup_source_selection_state` | enum `{0,1,2}` | current source-selection state |
| `startup_source_selection_explicit_source_active` | boolean-like gauge | `1` when exact source configuration is active |
| `startup_source_selection_warmup_events_seen` | per-cycle gauge | reset each warmup interval |
| `startup_source_selection_warmup_cycles_total` | monotonic counter | increments per source-selection warmup entered |
| `startup_source_selection_explicit_validate_only_total` | monotonic counter | increments per exact-source validation cycle |
| `startup_source_selection_explicit_source_conflict_detected` | boolean-like gauge | exact-source validation conflict detected |
| `startup_source_selection_degraded_escalated` | latched flag | `1` while escalation latch active |
| `startup_source_selection_degraded_since_ms` | unix-ms gauge | timestamp of current envelope-visible degraded state entry |
| `startup_source_selection_consecutive_failures` | gauge | reset on source-selection success |
| `startup_source_selection_degraded_cumulative_ms` | rolling gauge | 15-minute in-process cumulative degraded time |

### 6.5 `bus_admission` Envelope Field

The observability envelope
`ebus.v1.bus_observability.data` SHALL include an additive
`bus_admission` field in the data body.

The required addition is additive only. It SHALL NOT create a separate
top-level envelope or a separate hash field.

### 6.6 `data_hash` Behaviour

The existing `data_hash` naturally covers `bus_admission` because
`bus_admission` is part of the existing data body.

Therefore:

- no new `admission_hash` field is allowed;
- when `bus_admission` changes after surviving the stability window,
  `data_hash` changes naturally;
- when `bus_admission` does not change, `data_hash` remains stable.

### 6.7 Envelope Stability Window

Admission state changes SHALL be reflected into the envelope body only
after the new state is stable for:

`state_min_stability_s = 30`

This value is operator-tunable only within:

`[5, 60]`

and remains subject to the AD22 invariant:

`state_min_stability_s * 5 <= continuous_threshold_s`

With the frozen `continuous_threshold_s=300`, any configured stability
value above `60` is invalid and MUST be rejected at config load.

### 6.8 Escalation Threshold

Escalation SHALL trigger when either threshold fires first:

- `K = 5` consecutive rejoin failures; or
- `T = 5 min` cumulative degraded time within a rolling `15 min`
  window.

This is the AD17 contract.

### 6.9 Escalation Signal

On the first unlatched-to-latched escalation transition, the gateway
SHALL:

- emit one structured WARN line;
- set `startup_source_selection_degraded_escalated=1`.

The WARN line is:

`startup admission degraded escalated threshold=<failures|duration> value=<N>`

No repeated WARN is emitted while already latched.

### 6.10 Latch Clear

The escalation latch clears only after:

- admission has returned to active state; and
- active state has remained continuous for
  `state_min_stability_s` seconds.

There is no WARN on latch clear.

### 6.11 Cumulative Window Algorithm

The cumulative degraded-time window algorithm is fixed as:

`cumulative_window_algorithm = fixed_bucket_1s`

The implementation is defined as:

- `900` slots;
- one slot per second;
- rolling window length `900s` (`15 min`);
- each slot stores degraded milliseconds in that second;
- sum over all slots produces
  `startup_source_selection_degraded_cumulative_ms`.

With `900` buckets at `4 bytes` each, the memory bound is
approximately `3.6 KB` per admission instance.

### 6.12 Restart Semantics

The cumulative degraded-time accumulator is in-process only.

It SHALL NOT persist across process restart.

On process start the gateway SHALL emit:

`startup admission escalation accumulator zeroed reason=process_start`

<a id="operator-override"></a>
## 7. Operator Override

### 7.1 Status

Operator override is opt-in and default-off.

Historically it let an operator force the local initiator selection on
join-capable direct transports. SAS M4 supersedes that behavior: the operator
may configure an exact source, but the gateway treats it as
`explicit_validate_only` and still requires active validation before normal
Helianthus-owned traffic uses it.

### 7.2 Configuration Surface

The override surface is:

- `StartupSource.Override`
- `StartupSource.Override.Validate`

Persistence is config-only. There is no runtime auto-lift and no
automatic conversion from override to join on later Joiner success.

### 7.3 Unset Branch

When override is unset:

- Joiner warmup gates active traffic;
- warmup-before-active-frame invariant applies;
- directed probes await successful admission;
- semantic barrier closes only on
  `semanticBootstrapReady AND Joiner-success`.

This is the default and preferred branch.

### 7.4 Exact Source Set

When exact source configuration is set:

- candidate search is bypassed;
- active probe validation remains mandatory;
- normal gateway-owned active traffic waits for validation success;
- the selected mode is `explicit_validate_only`;
- `startup_source_selection_explicit_source_active=1`;
- `startup_source_selection_explicit_validate_only_total` increments for the
  admission cycle.

### 7.5 Exact Source Validation Failure

If exact source validation fails:

- normal gateway-owned active traffic remains blocked;
- the gateway records a degraded source-selection state;
- the selected mode remains `explicit_validate_only` for the attempted
  exact-source cycle;
- the failed source may be reported under `source_selection.failed_source`;
- automatic fallback to unvalidated static-source operation is forbidden.

### 7.6 No Auto-Lift

The override SHALL remain in effect until the operator removes it from
configuration and restarts.

The implementation MUST NOT:

- auto-clear override on later Joiner success;
- silently rewrite the configured source;
- promote advisory Joiner output into runtime configuration.

<a id="admission-artifact-schema-key-paths"></a>
## 8. Source-Selection Artifact Schema Key-Paths

### 8.1 Status and Scope

This section is the normative SAS M4 key-path listing for the source-selection
artifact. The JSON schema file itself lives in
`helianthus-ebusgateway` at
`docs/schemas/source-selection-artifact.schema.json`. This document authorizes
the schema semantics and field
set; it does not move schema-file authorship into this repository.

Artifact scope is:

- non-ebusd-tcp;
- adapter-direct startup validation.

### 8.2 Admission Object

| Key Path | Required | Meaning |
|---|---|---|
| `admission.state` | yes | admission runtime state as emitted by the artifact |
| `admission.source` | yes | selected active initiator source |
| `admission.companion_target` | yes | companion target associated with the selected source |
| `admission.warmup_duration_s` | yes | effective warmup duration used for the admission cycle |
| `admission.reason_if_degraded` | yes | structured degraded reason, empty or null-equivalent only when not degraded |
| `admission.transport_kind` | yes | classified transport kind for the run |
| `admission.source_selection.mode` | yes | enum in `{source_selection, explicit_validate_only, degraded_transport_blind, degraded_no_events}` |

### 8.3 Discovery Object

| Key Path | Required | Meaning |
|---|---|---|
| `discovery.wire_bytes` | yes | measured discovery-class startup wire bytes |
| `discovery.window_s` | yes | measurement window in seconds |
| `discovery.startup_burst_pct` | yes | measured startup discovery-class burst percent over the startup window |
| `discovery.post_startup_sustained_rate_probes_per_15s` | yes | post-startup directed-probe steady-state rate |
| `discovery.probe_count` | yes | number of directed probes emitted in the measured startup window |
| `discovery.promoted_suspects_without_identity` | yes | promoted suspects that still lacked identity and therefore justified directed confirmation |
| `discovery.per_baseline_address_evidence_counts` | yes | per-seed evidence counts for the configured baseline topology |

### 8.4 Enum Constraint

The schema SHALL enforce:

`admission.source_selection.mode ∈ {source_selection, explicit_validate_only,
degraded_transport_blind, degraded_no_events}`

Any out-of-range value is invalid and SHALL be treated as a failure by
consumers and by CI validation.

### 8.5 Discovery Budget Coupling

The discovery fields are not informational-only. They are coupled to
the startup load contract in [§5](#startup-directed-probe-phase).

At minimum, the emitted values must support validation that:

- `startup_burst_pct <= 2.0`;
- `probe_count <= 15`;
- post-startup rate `<= 1 probe per 15s`.

### 8.6 Artifact Scope Limitation

This admission artifact is outside `ebusd-tcp` scope in this plan.
`ebusd-tcp` is referenced in the transport matrix and in the guarded
full-range retry rule, but does not emit `admission.source_selection.mode`
within this plan's adapter-direct acceptance surface.

<a id="full-range-retry-guard"></a>
## 9. Full-Range Retry Guard

### 9.1 Guard Statement

The sanctioned bounded full-range retry from
[b524-semantic-root-discovery.md](./b524-semantic-root-discovery.md)
remains `ebusd-tcp`-only in this plan.

It is not part of the direct-transport startup-directed probe phase.

### 9.2 Non-ebusd-tcp Default

On ENH, ENS, UDP-plain, and TCP-plain:

- full-range retry is disabled by default;
- it MUST NOT run as an implicit fallback when admission degrades;
- it MUST NOT run merely because passive evidence is incomplete.

### 9.3 Diagnostic Re-Enable Gate

On non-ebusd-tcp transports, full-range retry may be re-enabled only
when BOTH of the following are true:

1. the operator has explicitly enabled a diagnostic flag; and
2. the evidence buffer has already produced at least one Vaillant root
   candidate.

If either prerequisite is missing, full-range retry remains forbidden.

### 9.4 Reason for the Gate

This guard exists because a direct-transport fallback to full-range
scan would collapse the distinction between the new passive-first
startup pipeline and the old scan-storm-producing behaviour.

The evidence-buffer prerequisite ensures that even the diagnostic
escape hatch is anchored in observed topology, not in blind address
enumeration.

### 9.5 B524 Relationship

The B524 startup recovery rule remains:

- if narrowed or preloaded startup inventory does not produce a
  coherent B524 root, one bounded full-range discovery retry may be
  required before closing startup scan;
- within this plan, that sanctioned retry belongs to `ebusd-tcp`;
- it is not generalized to direct transports.

### 9.6 Guard Summary Table

| Transport Class | Full-Range Retry Default | Re-Enable Conditions |
|---|---|---|
| ENH | disabled | diagnostic flag AND `>= 1` Vaillant root candidate |
| ENS | disabled | diagnostic flag AND `>= 1` Vaillant root candidate |
| UDP-plain | disabled | diagnostic flag AND `>= 1` Vaillant root candidate |
| TCP-plain | disabled | diagnostic flag AND `>= 1` Vaillant root candidate |
| `ebusd-tcp` | sanctioned bounded retry remains available under B524 rule | transport-specific existing path |

<a id="transport-capability-matrix"></a>
## 10. Transport Capability Matrix

### 10.1 Startup-Admission Reference Table

This startup-focused matrix is a reference extract from the broader
transport capability discussion in
[nm-participant-policy.md](./nm-participant-policy.md#transport-capability-matrix).

| Transport | Join wired | Static-source fallback |
|---|---|---|
| ENH | Y | Override-only |
| ENS | Y | Override-only |
| `ebusd-tcp` | N | default |
| UDP-plain | Y | Override-only |
| TCP-plain | Y | Override-only |

<a id="references"></a>
## 11. References

### 11.1 Primary Plan Artifacts

- [startup-admission-discovery-w17-26.locked/00-canonical.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/00-canonical.md)
- [startup-admission-discovery-w17-26.locked/10-scope-and-problem.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/10-scope-and-problem.md)
- [startup-admission-discovery-w17-26.locked/11-milestones-and-coordination.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/11-milestones-and-coordination.md)
- [startup-admission-discovery-w17-26.locked/12-decision-matrix.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/12-decision-matrix.md)
- [startup-admission-discovery-w17-26.locked/13-configuration-and-acceptance.md](../../helianthus-execution-plans/startup-admission-discovery-w17-26.locked/13-configuration-and-acceptance.md)

### 11.2 Existing Normative Docs

- [nm-model.md](./nm-model.md)
- [nm-discovery.md](./nm-discovery.md)
- [nm-participant-policy.md](./nm-participant-policy.md)
- [b524-semantic-root-discovery.md](./b524-semantic-root-discovery.md)
- [protocols/ebus-services/ebus-overview.md](../protocols/ebus-services/ebus-overview.md)

### 11.3 Specific Reference Anchors

The following existing sections are especially authoritative for this
document:

- `protocols/ebus-services/ebus-overview.md`, join strategy section;
- `protocols/ebus-services/ebus-overview.md`, direct transaction flow;
- `protocols/ebus-services/ebus-overview.md`, inferred target response
  address semantics;
- `nm-participant-policy.md`, local address-pair authority;
- `nm-participant-policy.md`, transport capability matrix;
- `nm-participant-policy.md`, bus-load policy;
- `nm-discovery.md`, passive evidence sources and discovery-to-NM
  pipeline;
- `b524-semantic-root-discovery.md`, startup recovery rule.

### 11.4 Normative Summary

This document freezes the direct-transport startup contract as:

- passive reconstructor and `JoinBus` before warmup;
- Joiner warmup before non-override active traffic;
- override as explicit opt-in carve-out only;
- passive-first evidence promotion;
- explicit-target directed confirmation only;
- discovery-class startup burst budget of `2.0%` over `60s`;
- degraded mode with explicit logs, expvars, envelope surfacing, and
  AD17 escalation;
- AD23 key-path listing for the admission artifact;
- full-range retry guarded away from direct transports by default.
