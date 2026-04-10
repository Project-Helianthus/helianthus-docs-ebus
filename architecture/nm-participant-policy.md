# Local Participant Behavior and Bus-Load Policy

Status: Normative
Plan reference: ebus-good-citizen-network-management.locked (M0/ISSUE-DOC-02)

## Purpose

This document freezes the numeric bus-load bounds, transport capability
expectations, and local participant behavior that govern Helianthus NM
runtime compliance. It is the third and final M0 normative document and
must be satisfied before any NM runtime code that originates bus traffic
lands in `helianthus-ebusgateway`.

Implementation work references this document for local address-pair
authority, transport blindness semantics, broadcast gating rules, and the
frozen bus-load budget.

## Local Address-Pair Authority

Helianthus NM runtime requires a canonical local address pair: one
initiator address and one companion target address. The pair is runtime
state with provenance, not a literal constant. Provenance indicates how
the pair was selected and from which source.

### Preferred Source: JoinResult

On transports that support a join handshake, the canonical source is the
transport join result:

- **Initiator:** `JoinResult.Initiator`
- **Companion target:** `JoinResult.CompanionTarget`

A completed join that yields a valid pair is the highest-confidence
source. The ENH, ENS, UDP-plain, and TCP-plain transports are expected
to support this path once their join protocols are implemented.

### Fallback Source: Configured Policy

On transports that do not support a join handshake (notably ebusd-tcp),
the canonical source is operator configuration:

- **Initiator:** configured local initiator address
- **Companion target:** derived from the initiator per the eBUS
  companion-address derivation rule (initiator + `0x05`)

This path carries lower confidence because the configured address is not
validated against the live bus before use.

### Provenance

The active local address pair carries a provenance tag that records:

- The source class (join-result or configured-fallback)
- The transport identity that produced the pair
- A monotonic sequence number incremented on each address-pair change

Provenance enables runtime code to distinguish high-confidence pairs
from configured fallbacks and to detect stale references after a rejoin.

## Init_NM and Transport Events

### Init_NM Triggers

Helianthus enters the NMInit state on exactly these events:

1. **Process start.** Gateway process begins execution.
2. **First valid address pair.** First successful acquisition of a valid
   local address pair after process start.
3. **Completed join or rejoin after transport recovery.** Transport
   reconnects and a join handshake completes successfully.
4. **Explicit operator-triggered NM reset.** An operator command
   requests NM reinitialization.
5. **Configuration change invalidating the target configuration.**
   Any configuration mutation that invalidates the current address pair
   or monitored-node set.

Cross-reference: [nm-model.md](./nm-model.md) defines the NMInit,
NMReset, and NMNormal state machine transitions.

### Rejoin Semantics

A rejoin that changes the active local address pair is NM-relevant. The
transition sequence is:

    NMInit --> NMReset --> NMNormal

The previous address pair is discarded. All NM state derived from the
old pair (including monitored-node timers) is invalidated.

A rejoin that preserves the same address pair is NOT NM-relevant and
does not trigger a state transition.

Joiner warmup observations seed evidence but do not promote devices
directly into the monitored-node set.

### Transport Blindness

When the transport disconnects without a completed rejoin:

- **self status:** transitions to NOK immediately.
- **Remote-node cycle-time timers:** freeze. Timers do not advance
  during transport blindness because no bus traffic is observable.
- **NM-originated broadcasts:** suppressed. Any broadcast requiring a
  valid local initiator address is not emitted.

A transport disconnect without a completed rejoin is NOT a fake NM
reset. The NM state machine remains in its current state; it does not
transition to NMInit until a rejoin completes.

## Self-Monitoring

The `self` entry is mandatory in the NM status chart. It is keyed to the
active local address pair and represents the Helianthus gateway's own
bus presence.

### Self Timer

The first lock baseline uses the same provisional 120-second default
for the self timer unless earlier evidence proves a tighter override is
warranted.

### Self Timer Reset

The self timer resets on a successful Helianthus-originated bus
transaction: a poll read, a discovery probe, or an NM broadcast that
completes without error.

### Relationship to Transport Health

NM self-status is NOT the only or fastest transport-health detector.
Existing transport-layer and adapter-layer health surfaces remain
responsible for the low-latency detection path. The NM self timer is a
complementary, higher-level liveness signal operating on a coarser
time scale.

## Broadcast Lane Gating

NM broadcasts are gated on preconditions. Each broadcast surface is
listed below with its gating rule.

### FF 00 (NM Reset)

Emitted only after a valid active local initiator address exists.
Suppressed during transport blindness and before the first valid
address pair is acquired.

### FF 02 (NM Failure)

In scope for the first lock baseline. This is the NM-specific failure
signal broadcast when a monitored node's cycle timer expires.

**Payload-less caveat:** before responder support is available (gated on
M7a feasibility), `FF 02` is emitted without a payload. This means the
broadcast signals failure but is only partially interrogable by peers.
This limitation is accepted for the first lock baseline.

### FF 01 (NM State) -- Optional-Later

Deferred until the broadcast lane is proven stable through operational
experience with `FF 00` and `FF 02`. Not part of the first lock
baseline.

### 07 FF (QueryExistence) -- Optional-Later

Deferred. Subject to the cadence floor defined in the Bus-Load Policy
section below (minimum 10 seconds between successive broadcasts).

`07 FF` is a broadcast (DST = `0xFE`) used for existence queries, not
a targeted discovery probe. Cross-reference:
[nm-discovery.md](./nm-discovery.md) defines the discovery pipeline and
its relationship to NM.

## Responder Lane Gating

ALL responder-mode NM surfaces are gated on the M7a feasibility spike
result. No responder functionality ships until M7a demonstrates that the
transport and adapter stack can reliably handle companion-target
responses.

Gated responder surfaces:

- `07 04` NMQueryExistence response
- `FF 03` NMResolveNodeAddress
- `FF 04` NMQueryNodes
- `FF 05` NMResolveService
- `FF 06` NMUpdateService

Cross-reference: [nm-model.md](./nm-model.md) classifies these services
and defines which are initiator-mode versus responder-mode.

## Transport Capability Matrix

The table below summarizes each transport's expected capability level
for NM-relevant operations.

| Transport | Initiator | Broadcast (`0xFE`) | Responder (companion) | Notes |
|---|---|---|---|---|
| ENH | Yes | Yes | M7a feasibility | Enhanced adapter protocol, full duplex |
| ENS | Yes | Yes | M7a feasibility | Serial variant of ENH |
| ebusd-tcp | Yes (via ebusd) | Limited | Unlikely | ebusd mediates; no direct companion listen |
| UDP-plain | Yes | Yes | M7a feasibility | Raw UDP byte stream |
| TCP-plain | Yes | Yes | M7a feasibility | Raw TCP byte stream |

**ENH/ENS:** Full initiator and broadcast capability. Responder mode
depends on M7a proving the adapter can listen on the companion target
address concurrently.

**ebusd-tcp:** Initiator operations are mediated through ebusd. Broadcast
capability is limited to what ebusd exposes. Responder mode is unlikely
because ebusd does not support companion-target listening.

**UDP-plain / TCP-plain:** Raw byte stream transports with full initiator
and broadcast capability. Responder mode follows the same M7a gate as
ENH/ENS.

## Bus-Load Policy (Frozen Numeric Bounds)

The following numeric bounds are frozen for the first lock baseline.
All NM runtime code must satisfy these bounds as verified by
measurement at implementation time.

### Sustained Load Budget

Helianthus-originated NM traffic must not exceed **0.5% of bus
capacity** outside of reset and rejoin windows.

This is a sustained average measured over a rolling window. The
measurement window length is defined at implementation time but must be
at least 60 seconds.

### Burst Load Budget

Helianthus-originated NM traffic must not exceed **2.0% of bus
capacity** during reset and rejoin windows.

Reset and rejoin windows are bounded by the NMReset-to-NMNormal
transition. Once the state machine enters NMNormal, the sustained
budget applies.

### 07 FF Cadence Floor

A minimum of **10 seconds** must elapse between successive
`07 FF` (QueryExistence) broadcasts originated by Helianthus,
regardless of how many monitored nodes are pending existence
confirmation.

### Measurement and Enforcement

Bus-load compliance is measured using the eBUS specification formula for
bus utilization. The formula accounts for byte-level transmission time
at the eBUS baud rate (2400 baud, 1 start bit, 8 data bits, 1 stop bit
= 4.167 ms per byte) plus inter-frame gaps.

Implementation must provide an internal bus-load estimator that tracks
Helianthus-originated NM bytes per measurement window. The estimator
output is exposed through the observability surface defined in
[architecture/bus-observability-v2.md](./bus-observability-v2.md) for
runtime verification.

## Cycle-Time Policy

### Default

The lock-baseline default cycle time for dynamically enrolled monitored
nodes is provisionally **120 seconds**.

This is a planning default. It is not proven to be appropriate for every
live node class. The value was chosen as a conservative starting point
that balances responsiveness against false-positive risk.

### Evidence-Review Obligation

Implementation MUST collect observed cadence artifacts from live bus
traffic for each monitored node class. The collected evidence must
either:

1. **Justify the default.** Demonstrate that 120 seconds is appropriate
   for the observed traffic pattern of the node class, OR
2. **Attach an explicit override.** Provide a per-node-class cycle time
   that is justified by the observed evidence.

This obligation is a documentation and runtime requirement. Shipping NM
monitoring for a node class without cadence evidence or an explicit
override is a compliance violation.

### Timer-Reset Event Sources

The following events reset a monitored node's NM cycle timer:

**Positive (timer resets):**

1. Passive observation of a CRC-valid, reconstructed,
   sender-attributed application transaction from the monitored node.
2. A successful addressed response to a Helianthus-originated query
   proving the monitored node is alive.
3. For `self`: a successful Helianthus-originated bus transaction (poll
   read, discovery probe, or NM broadcast).

**Negative (timer does NOT reset):**

1. Passive decode faults do NOT reset NM cycle timers. A decode fault
   indicates corrupted or ambiguous data and cannot confirm node
   presence.
2. Passive disconnect/discontinuity events are observability-loss
   signals, distinct from remote-node absence. They freeze timers
   (transport blindness) rather than resetting them.

## Failure and Error Surfaces

### FF 02 -- In Scope

`FF 02` (NMFailure) is the NM-specific failure signal in scope for the
first lock baseline. It is broadcast when a monitored node's cycle timer
expires without a timer-reset event.

Before responder support is available, `FF 02` is emitted payload-less.
This limits its interrogability but still provides a standards-aligned
failure signal to any peer that observes the broadcast.

### FE 01 -- Explicitly Out of Baseline

`FE 01` (general error broadcast) is explicitly OUT of the first lock
baseline. Including it would require defining Helianthus-wide error
semantics that extend beyond the NM domain.

A future doc-gated issue must define the Helianthus-wide semantics for
`FE 01` before it can be included in any implementation work.

## Cross-References

- [architecture/nm-model.md](./nm-model.md) -- NM state machine,
  gateway ownership, wire behaviour lanes, OSI Layer 7 service
  classification
- [architecture/nm-discovery.md](./nm-discovery.md) -- discovery-to-NM
  pipeline, evidence fusion, indirect observation interpretation
- [protocols/ebus-overview.md](../protocols/ebus-overview.md) --
  wire-level formats, address derivation, and frame structure
- [architecture/bus-observability-v2.md](./bus-observability-v2.md) --
  observability surface for bus-load metrics
