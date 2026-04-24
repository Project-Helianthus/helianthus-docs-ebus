# NM-Aligned Device Discovery

Status: Normative
Plan reference: ebus-good-citizen-network-management.locked (M0/ISSUE-DOC-01)

## Purpose

This document freezes the normative interpretation of the eBUS
NM-aligned device discovery model as implemented by the Helianthus
gateway. It defines the realigned discovery approach that replaces
probe-centric scanning with multi-source passive evidence fusion plus
bounded active confirmation.

This must be frozen before any NM runtime implementation lands in
`helianthus-ebusgateway`, because the NM state machine depends on a
populated target configuration, and target configuration depends on
discovery having promoted devices through the evidence pipeline.

## Discovery Is Adjacent to NM, Not Identical

Discovery and NM share evidence but serve different purposes.

- **Discovery** answers: "what devices exist on the bus?"
- **NM** answers: "are monitored devices still communicating within
  their expected cycle times?"

Discovery feeds the NM target configuration. NM does not drive
discovery. A device must first be discovered and promoted before NM
can monitor it. Conversely, NM cycle-time expiry does not remove a
device from the discovery model -- it signals communication loss for
a device whose existence was already established.

The evidence overlap is deliberate: a CRC-valid application
transaction both refreshes discovery freshness and resets an NM cycle
timer. But the two systems interpret that evidence for different
purposes and maintain independent state.

## Passive Evidence Sources

The primary discovery mechanism generates no bus traffic from
Helianthus. All signals below are consumed by observing traffic
originated by other bus participants.

### Passive 07 04 (Identification)

Any identification response observed on the bus from any
initiator/target pair contributes to device-presence evidence.
Helianthus does not need to originate the query -- a VRC700
identifying a BAI, or any other pair exchanging `07 04`, is
equally valid evidence of both participants' existence.

A single observed `07 04` exchange provides strong evidence for two
addresses simultaneously: the initiator (who sent the query) and
the target (who responded).

### Passive FF 00 (NM Reset Broadcast)

A device announcing NM reset/restart is simultaneously a strong
presence signal. The broadcast destination (`0xFE`) means all bus
participants receive it, and Helianthus passively consuming it
requires no bus arbitration.

See [`nm-model.md`](./nm-model.md) for the full `FF 00` semantics
within the NM state machine.

### Passive FF 01 (NM State Broadcast)

A device announcing its NM state (via `FF 01`) is a presence signal.
This broadcast is optional-later in Helianthus's own broadcast lane,
but is always consumed passively from peers when observed.

Like `FF 00`, the broadcast nature of `FF 01` means passive
consumption adds zero bus load.

### New Cyclic Traffic from Unseen Addresses

The appearance of application-layer transactions from a previously
unknown source address is the most general passive discovery signal.
Any CRC-valid reconstructed frame with a new sender address triggers
suspect creation in the evidence buffer.

This is the catch-all that covers devices which do not participate in
NM broadcasts and are never the target of an `07 04` query from
another device. Regular cyclic polling traffic (e.g., a regulator
polling a boiler) is sufficient.

## Bounded Active Confirmation

When passive evidence is insufficient, Helianthus may actively probe,
but with explicit bounds on bus utilization and query rate.

### Active 07 04 (Identification Query)

Rate-limited directed identity query to a specific address. Used to
confirm a suspect or refresh a stale entry. This is the preferred
active confirmation mechanism because:

- it targets a specific address (not a broadcast);
- it provides a definitive response from the target;
- the response payload includes manufacturer and device identity.

Active `07 04` queries are subject to the bus-load policy frozen in
`architecture/nm-participant-policy.md` (ISSUE-DOC-02, planned).

For startup on join-capable direct transports, these directed `07 04`
queries are further constrained by
[startup-admission-and-discovery.md §5, "Directed Probe Phase and Bus-Load Budget"](./startup-admission-and-discovery.md#startup-directed-probe-phase):
they occur only in the explicit `startup_directed_probe_phase`, only
against promoted suspects without identity, and have zero intersection
with the legacy full-range `0x01..0xFD` scan.

### 07 FE (QueryExistence) -- Bounded and Indirect Only

**Critical constraint:** `07 FE` is NEVER treated as a direct-answer
discovery query. It is a broadcast (`DST=0xFE`) and responses are
indirect -- they contribute to the evidence buffer but do not
constitute a definitive yes/no answer about a specific device.

Use of `07 FE` is bounded and must be justified on a case-by-case
basis. The broadcast nature means it generates bus traffic visible
to all participants, and indirect responses require correlation with
other evidence before promotion.

When Helianthus does use `07 FE`, responses are fed into the same
evidence pipeline as passive observations -- they do not bypass the
normal promotion path.

### 07 FF (QueryExistence Broadcast) -- Not Discovery

`07 FF` is a good-citizen existence signal that Helianthus may emit
as an optional-later feature, with a cadence floor of >= 10 seconds
between broadcasts. It is NOT a discovery mechanism.

`07 FF` announces Helianthus's own presence to peers. Discovery
consumes `07 FF` passively from other devices (as a presence signal
under the "new cyclic traffic" rule) but does not use it as a probe.

The distinction is directional: Helianthus emits `07 FF` to be
discovered by others, and consumes peers' `07 FF` as passive
evidence of their presence.

## Discovery-to-NM Target-Configuration Pipeline

Discovered devices flow into the NM monitoring model through a
staged pipeline. Each stage has explicit promotion criteria, and
devices cannot skip stages.

### Pipeline Stages

```text
1. Joiner warmup observation
       |
       v
2. Evidence buffer / suspect seeding
       |
       v
3. Normal discovery promotion
       |
       v
4. Target-configuration enrollment
```

**Stage 1 -- Joiner warmup observation.** During transport join
warmup, Helianthus observes bus traffic and collects evidence without
promoting any device. This is a listen-only period where the gateway
builds an initial picture of bus population without injecting any
traffic of its own.

**Stage 2 -- Evidence buffer / suspect seeding.** Passive
observations create suspect entries. Each suspect accumulates
evidence from the sources described above. No suspect is enrolled
in NM target configuration at this stage.

**Stage 3 -- Normal discovery promotion.** Suspects with sufficient
evidence are promoted to confirmed devices. Promotion criteria
include multiple independent observations, successful active
confirmation (when used), or strong single-source evidence such
as a direct `07 04` response.

**Stage 4 -- Target-configuration enrollment.** Confirmed devices
that Helianthus actively polls, depends on semantically, or has
promoted through discovery are enrolled in the NM target
configuration for cycle-time monitoring.

### Enrollment Rules

The gateway target configuration is discovery-fed and self-inclusive.

Population strategy:

- **Always include `self`.** The gateway's own address is
  unconditionally present in the target configuration. For `self`,
  a successful Helianthus-originated bus transaction serves as the
  timer-reset event.
- **Dynamically enroll confirmed devices/faces** that Helianthus
  actively polls, depends on semantically, or promotes through
  discovery.
- **Allow bounded operator/static seed entries** where needed for
  devices that are known to exist but may not be discoverable
  through passive observation alone.
- **Unconfirmed passive suspects do NOT enter target configuration
  directly.** A suspect must be promoted through the normal
  discovery pipeline before it can be monitored by NM.

### Timer-Reset Evidence Bridge

Discovery evidence and NM timer-reset events share a common trigger
but serve different purposes.

**What resets an NM node timer:**

- Passive observation of a CRC-valid reconstructed sender-attributed
  application transaction.
- A successful addressed response to a Helianthus-originated query
  proving the monitored node is alive.
- For `self`, a successful Helianthus-originated bus transaction.

**What does NOT reset an NM node timer:**

- Passive decode faults do NOT reset NM cycle timers. A corrupted
  frame cannot serve as evidence of continued communication.
- Passive disconnect/discontinuity events are observability-loss
  signals, distinct from remote-node absence. They indicate that
  Helianthus lost the ability to observe the bus, not that a
  specific node stopped communicating.

The same CRC-valid transaction that resets an NM cycle timer also
refreshes discovery freshness for the originating address. But the
negative cases diverge: decode faults and disconnect events affect
NM observability accounting without contributing to discovery
evidence.

## Separation from B524 Structural Discovery

This document covers **topology and device-presence discovery** --
which devices exist on the eBUS and their addressing/identity.

[`architecture/semantic-structure-discovery.md`](./semantic-structure-discovery.md)
covers **B524 register-backed structural discovery** -- which
semantic families, instances, and attachments exist within a
discovered device.

These are separate concerns operating at different protocol layers:

- **NM-aligned discovery:** device-level, address-level, eBUS wire
  layer. Answers "who is on the bus?"
- **B524 structural discovery:** register-level, family/instance-level,
  Vaillant application layer. Answers "what does this device contain?"

NM-aligned discovery must succeed first: a device must be present
on the bus before B524 structural discovery can interrogate its
register space. But B524 structural discovery operates independently
once the device is known -- it does not feed back into NM topology.

## Cross-References

- [`architecture/nm-model.md`](./nm-model.md) -- NM state machine, gateway ownership, wire lanes
- [`architecture/semantic-structure-discovery.md`](./semantic-structure-discovery.md) -- B524 structural discovery (separate concern)
- `architecture/nm-participant-policy.md` -- bus-load policy and cycle-time bounds (ISSUE-DOC-02, planned)
- [`protocols/ebus-services/ebus-overview.md`](../protocols/ebus-services/ebus-overview.md) -- wire-level QueryExistence, Identification formats
