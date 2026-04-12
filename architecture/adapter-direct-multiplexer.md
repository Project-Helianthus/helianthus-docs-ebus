# Adapter-Direct Multiplexer Architecture

Status: Accepted (v0.4.0)
Plan package: [gateway-embedded-proxy](https://github.com/Project-Helianthus/helianthus-execution-plans)

This document defines the canonical architecture of the gateway-embedded adapter
multiplexer introduced in v0.4.0, which replaces the separate proxy for
adapter-direct deployments.

## Problem

The gateway's passive bus tap sees approximately 40% `corrupted_request` events
on a 3-master eBUS (0x71 gateway, 0x31 ebusd, 0x10 VRC700). Root causes:

- Passive reconstruction from a raw byte stream lacks echo matching and frame
  boundary knowledge (structural limitation of passive observation).
- Self-echo noise: the gateway reconstructs its own transmitted frames on the
  passive path -- traffic the active path already has with full fidelity.
- Proxy escape encoding bug: `ownerObserverSeen` accumulates wire-level bytes
  (0xA9 escape sequences), replayed to observers that expect logical bytes.

## Solution: Gateway-Embedded Multiplexer

The gateway embeds an adapter multiplexer (`internal/adaptermux/`) that owns a
single ENH/ENS TCP connection to the adapter hardware. This replaces the
separate proxy for adapter-direct deployments.

### Topology

Gateway connects directly to the adapter. The multiplexer demultiplexes the
single upstream connection into three paths:

- **Active path**: `RawTransport` wrapper for `gateway.Bus` (exclusive write
  access during gateway ownership periods)
- **Passive path**: filtered symbol callback delivering third-party traffic only
  (gateway echo suppressed)
- **Proxy endpoint**: optional TCP listener for external ENH clients (ebusd,
  VRC Explorer) with full master access

The standalone proxy (`helianthus-ebus-adapter-proxy`) remains available as an
independent product for non-gateway deployments.

## Key Architectural Decisions

### AD01: Dual-Transport Pattern

INFO cache population uses a separate transport lifecycle: 2-second deadline
for INIT + INFO retrieval, then the transport is reconfigured with a 50ms
readLoop deadline for normal bus operation. All 8 INFO IDs are cached at
startup and preserved across in-band RESETTED events.

### AD02: Wire Phase Tracking During Gateway Ownership

Wire phase tracking is skipped during gateway ownership periods. The gateway's
active path has full protocol-level awareness through ENH echo matching and does
not need the multiplexer's wire phase tracker. Phase tracking resumes when
ownership is released at a SYN boundary.

### AD03: ArbitrationSendsSource

For both ENH and ENS protocols, the adapter sends the SRC byte during the START
phase of arbitration. The multiplexer accounts for this in echo tracking: the
SRC byte is part of the arbitration handshake, not a data byte to be suppressed
from the passive stream.

### AD04: INFO Cache

All 8 adapter INFO IDs are cached after INIT. The cache is served to the active
path and external sessions without hitting the upstream transport's readMu. The
cache is preserved across in-band RESETTED events (the adapter retains identity
across resets).

### AD05: Re-INIT Suppression on In-Band RESETTED

In-band RESETTED events do not trigger a full re-INIT. The adapter's identity
and INFO are stable across resets. Re-INIT would cause a reset loop on adapters
that RESETTED as part of their normal startup sequence.

### AD06: Owner Arbitration Model

Two-class gateway-priority model. At each SYN boundary:

1. If gateway has a pending START request, gateway wins.
2. Else if an external session has a pending START, external wins (FIFO order).
3. Else bus is idle, no owner.

Gateway requests are never delayed by external contention.

### AD07: Echo Suppression

Internal passive path uses byte-by-byte tracking. External observer sessions
use frame-level tracking. This eliminates the proxy's escape encoding bug by
design -- no wire-level byte accumulation in observer streams.

### AD08: Proxy Listener Compatibility

The optional proxy listener (`--proxy-listen`) provides backward compatibility
for ebusd and VRC Explorer. External sessions get full ENH master access through
the multiplexer's arbitration system.

### AD09: RESETTED Propagation

When the adapter sends ENHResResetted:

1. Active path: transport reset event, clear pending operations
2. Passive path: emit `PassiveEventReset` (discontinuity marker)
3. External sessions: broadcast ENHResResetted frame
4. Wire phase tracker: reset to Idle

### AD10: Connection Management

Single ENH/ENS TCP connection with TCP_NODELAY + KeepAlive. Reconnection loop
on disconnect with exponential backoff (1s initial, 30s cap).

### AD11: Ownership Duration Guard

Hard limit on continuous bus ownership (default 10s, strictly larger than any
request timeout). Idle SYN release after a 200ms grace period following bus
acquisition.

### AD12: Passive Path Delivery

ENH protocol delivers logical bytes (no escape sequences). Passive path
callback receives third-party symbols only. Connected/disconnected/reset
lifecycle events are delivered alongside data symbols.

## Operational Notes

- Adapter-direct transport and proxy-based transport are mutually exclusive at
  the gateway level. Only one may be active at a time.
- Migration and rollback procedures are documented in
  [`../deployment/adapter-direct-migration.md`](../deployment/adapter-direct-migration.md).
- The standalone proxy remains available for users who do not run the gateway.

## Live Validation (v0.4.0)

The adapter-direct multiplexer is running live on production hardware with
verified results:

- Device scan: 4 devices discovered (BAI00, BASV2, VR_71, SOL00)
- B524 register access: coherent responses across all groups
- Semantic planes: zones=2, dhw=true, INFO=7 (all 7 non-reserved IDs cached)
- Passive path: third-party traffic delivered without self-echo corruption

## References

- Implementation: `helianthus-ebusgateway/internal/adaptermux/`
- Migration guide: [`../deployment/adapter-direct-migration.md`](../deployment/adapter-direct-migration.md)
- Execution plan: `helianthus-execution-plans/gateway-embedded-proxy`
