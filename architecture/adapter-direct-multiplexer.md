# Adapter-Direct Multiplexer Architecture

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` → `initiator`, `slave` → `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

Status: Accepted (v0.4.0)
Plan package: [gateway-embedded-proxy](https://github.com/Project-Helianthus/helianthus-execution-plans)

This document defines the canonical architecture of the gateway-embedded adapter
multiplexer introduced in v0.4.0, which replaces the separate proxy for
adapter-direct deployments.

## Problem

The gateway's passive bus tap sees approximately 40% `corrupted_request` events
on a 3-initiator eBUS (0x71 gateway, 0x31 ebusd, 0x10 VRC700). Root causes:

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
  VRC Explorer) with full initiator access

The standalone proxy (`helianthus-ebus-adapter-proxy`) is deprecated and kept
only as a read-only historical reference; its multiplexing role is carried by
this multiplexer. Pages that still describe the proxy-based topology (the
[architecture overview](overview.md#transport-modes) and the UDP-plain
guidance in [full-stack deployment](../deployment/full-stack.md)) describe the
deprecated topology and are superseded by this lifecycle statement until they
are updated.

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
ownership is released, including on transaction failure or a foreign initiator
byte; release does not require waiting for a SYN boundary (see AD11).

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

The embedded mux does not queue START requests. Every session, including
gateway session 0 (used by `gateway.Bus`) and each external session (ebusd or
VRC Explorer clients on the compatibility listener), submits a bid and waits
for the bus to reach an idle SYN. The decision is taken from the initiator
address alone, the way the wire would take it.

#### Selection at an idle SYN

- **Bids accumulate.** A session holds at most one bid. A new bid from the same
  session withdraws the old one; the old waiter is cancelled and receives
  neither STARTED nor FAILED.
- **One winner per SYN.** When the mux observes a SYN, nobody owns the bus and no
  barrier below is outstanding, it selects exactly one bidder and forwards
  exactly one native START, carrying the winner's initiator address, to the
  adapter. Only bids present while that SYN is processed are eligible; a bid
  submitted afterwards, or a replacement, waits for the next SYN.
- **Barriers that postpone selection.** A SYN does not select while an earlier
  START still has an unconsumed adapter response, while a blocking START call
  is in flight, or while an abandoned win is fenced until the next SYN (see
  [Undeliverable wins](#undeliverable-wins)). Bids stay queued and are
  reconsidered at the following SYN.
- **Priority order.** The mux compares the low nibble of the initiator address
  first (smaller wins), then the high nibble (smaller wins). If two sessions bid
  the identical address, the lower session ID wins; this is only a
  deterministic local tie-break, and deployments should give every initiator a
  distinct address. Gateway session 0 has no special rank. For example, a bid
  from `0x31` beats `0x7f` (low nibbles `1` and `f`), and `0x10` beats `0x30`
  (equal low nibble, high nibbles `1` and `3`).
- **Losers.** Every other eligible bidder is told it lost, with the winner's
  address in the FAILED, in the same SYN interval, and re-bids on its own
  schedule. An external loser's FAILED is queued before the next wire byte; if
  the START then cannot be sent to the adapter, that local loss is undone. The
  gateway session's loss is different: the gateway bus cannot take back a
  collision, so it is reported only once the START outcome is known, and the
  mux then delivers the fixed number of resynchronization SYNs the gateway bus
  waits for before it bids again.
- **Source byte.** A losing session is given the winner's source byte once, so
  the telegram that follows parses correctly. After the next observed SYN, a
  later STARTED supplies the source again for losing sessions so their view of
  the telegram stays complete. The synthesized byte is a session-local
  boundary and is never emitted as passive wire evidence.
- **Physical loss.** A selection can still lose on the wire to an initiator
  outside the mux. The adapter then answers the selected bidder with a FAILED
  naming that initiator, and the local losers see the actual winner's source
  instead.
- **Deadlines.** A gateway bid that never sees a SYN expires after the START
  deadline with a timeout error. Once the bid is selected, a separate START
  deadline bounds the adapter response, and expiry of the admission wait never
  cancels a selected win that can still be delivered.

#### Starvation is address priority

The gateway's initiator address is its priority control. The default `0x7f` is in
the lowest priority class, so a higher-priority initiator that bids at every
SYN can legitimately keep the gateway waiting, exactly as it would on a shared
physical bus. This is standard eBUS behaviour, not a scheduling fault, and the
mux adds no rotation, age-based preference or queue to compensate for it. A
deliverable STARTED always reaches its session, however long the bid waited.

This is local selection among the mux's own sessions. It does not change
physical arbitration: initiators outside the mux still arbitrate on the wire.

#### Undeliverable wins

A won STARTED can become undeliverable only when the winner is gone before the
mux commits it: its bid was cancelled or replaced after selection, or its session
closed or disconnected before it received the grant. The mux then:

1. does not deliver STARTED and does not commit (or immediately releases) the
   ownership;
2. fences selection until the next logical structural SYN, so queued bids are
   reconsidered at that SYN without an upstream reconnect;
3. increments `ActiveTxnSnapshot.UndeliverableStarted`.

The same applies when the STARTED arrives after its waiter was already retired
(the outstanding response is absorbed and counted). A lifecycle boundary (reset,
reconnect, close) retires the response without being counted.

#### Post-arbitration recovery

Whenever a START ends without a clean ownership, the mux fences selection until
the next SYN and also has to bring two trackers back in step: the wire-phase
tracker and the AA-injection classifier (see the
[frame-atomic visibility v8 design](adaptermux/frame-atomic-visibility-v8.md)). A fence is raised by
cancellation, replacement or expiry of the selected bid before its result, an
undeliverable STARTED, a STARTED naming a different address than the pending
bid, a FAILED naming a foreign winner or a bit-arbitration artifact, and a START
deadline expiry.

Recovery is a small state machine. It is advanced only by the read loop, which
is the single producer of the classifier; timers and cancellations only request
a state under the mux state lock.

| State | Meaning | Leaves the state when |
| --- | --- | --- |
| none | No recovery pending. | A fence is raised. |
| at SYN | Selection is fenced and no telegram is expected. | The first logical structural SYN arrives. Before the classifier can filter that SYN, the abandoned header and the wire-phase tracker are reset; the SYN is then processed normally and clears the fence. |
| foreign | A telegram is live on the wire and its bytes follow. | See the exits below. |
| foreign after AA | As foreign, and the previous item was an unescaped AA. | See the exits below. |
| reset | A lifecycle boundary ended the stream. | Applied before the next item. |

The foreign states are entered in two cases, and only the first needs the
classifier in enforce mode:

- a response (STARTED or FAILED) named a real foreign winner. A winner counts
  as real when it differs from the selected bidder's own source and is not
  rejected by the configured phantom-initiator predicate (bit-arbitration
  artifacts are not initiators);
- an external owner wrote at least one request byte after its source, then
  cancelled or disconnected. The wire-phase tracker keeps following that
  telegram, so the first SYN of an at-SYN fence could equally be the
  telegram's terminator or an injected AA inside it, and is judged like a
  foreign winner's.

While in a foreign state the AA filter keeps running for the live telegram: an
unescaped AA inside it is subject to the filter and can be dropped as an
injected symbol, because idle repeats SYN and an injected AA is followed by
telegram bytes. A raw-only AA and
an escaped payload AA are never SYNs and never clear a fence.

Exits from the foreign states:

| Exit | Condition | Effect |
| --- | --- | --- |
| Telegram terminator | The classifier completes the telegram and the SYN is not dropped. | The SYN reaches the mux SYN handling, which clears the fence and the recovery state. |
| Second consecutive AA | Two unescaped AA items with nothing between them. | The classifier and wire-phase tracker are reset and the second AA is processed as an idle SYN. |
| First SYN with an aborted classifier | The classifier already aborted the telegram; an aborted classifier filters nothing and only a reset revives it. | The first SYN resets the classifier and wire-phase tracker. |
| Lifecycle reset | Adapter reset, reconnect or close. | State, selection, local-loser bookkeeping and barriers are retired and the classifier reset is requested before the next item. A result from an earlier lifecycle cannot restore ownership, a fence or a synthesized source. |

Recovery resets are local state changes. They are never presented as a RESETTED
observation from the wire.

Known limits:

- **Two adjacent injected AAs look like idle.** Two consecutive unescaped AAs
  inside a live telegram are indistinguishable from an idle bus, so recovery
  ends early and the rest of that telegram is no longer protected by the
  filter.
- **Shadow mode.** The classifier observes and counts but drops nothing, and it
  does not enter the foreign states for a foreign winner. No item is dropped, so
  the first SYN reaches the mux SYN handling and ends the fence.
- **Off mode (the default when no mode is configured).** There is no classifier;
  selection is still fenced until the next SYN, and that SYN ends the fence.
- **Owner telegrams are recognised only for external sessions** that wrote at
  least one request byte; a grant that wrote nothing is not a live telegram.

#### Timing knobs

| Knob | Default | Meaning |
| --- | --- | --- |
| `--adapter-mux-idle-release-grace` | 200 ms | Time after bus acquisition before an idle SYN may release a gateway ownership. The grace is skipped when an external bid is already pending. |
| `--adapter-mux-max-ownership-duration` | 10 s | Hard limit on continuous ownership, measured from the grant. |
| `--adapter-mux-read-timeout` | 50 ms | Adapter read timeout. It is separate from the generic transport `--read-timeout`. |

Each flag must be positive. Three limits are fixed and have no flag: the START
deadline (5 s, for both the gateway admission wait and the adapter response),
the gateway ownership guard (1.5 s, see [AD11](#ad11-ownership-lifecycle-and-duration-guard)),
and the wire-silence grace before an idle SYN releases an external owner (250 ms).
A mux configuration embedded elsewhere that leaves the read timeout unset falls
back to 200 ms; the gateway always supplies the flag value.

The fairness ratio, the external-start staleness budget, the post-external-release
grace and the pending-start TTL no longer exist, neither as configuration
fields nor as flags.

Evidence status: **Proven** as the gateway implementation contract described by
[gateway issue #1402](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1402)
and its code change in gateway
[PR #1410](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1410),
covered by synthetic unit fixtures. These are gateway scheduling rules built on the native
START/STARTED/FAILED contract in [ENH](../protocols/enh.md#start--started--failed);
they are not a native eBUS wire contract. Scanner latency and live-transport
behaviour under this model are **Unknown** here.

### AD07: Echo Suppression

Internal passive path uses byte-by-byte tracking. External observer sessions
use frame-level tracking. This eliminates the proxy's escape encoding bug by
design -- no wire-level byte accumulation in observer streams.

### AD08: Proxy Listener Compatibility

The optional proxy listener (`--proxy-listen`) provides backward compatibility
for ebusd and VRC Explorer. External sessions get full ENH initiator access through
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

### AD11: Ownership Lifecycle and Duration Guard

The gateway releases its own ownership when its transaction fails: on a read
timeout, write error, or context cancellation. A new bid over a live gateway
grant also releases the previous ownership, with reason `abandoned_on_rebid`.
A foreign initiator byte during gateway ownership releases that ownership with
reason `arbitration_collision`. These abnormal endings do not hold ownership
until the next idle SYN or until the duration guard expires.

For a normal transaction, idle SYN release retains the 200 ms grace period
following bus acquisition. The grace is skipped when an external bid is already
pending. The hard limit on continuous ownership defaults to 10 s; gateway grants
are additionally bounded by a 1.5 s guard, and the shorter limit applies. Both
are last-resort guards, rather than the normal release mechanism for a failed
transaction.

Stale active-path bytes belonging to a finished or failed transaction are
discarded and counted. They are never drained into the next grant; the next
transaction must receive only its own active-path bytes.

Mux diagnostics expose these lifecycle counters in `ActiveTxnSnapshot`:

| Field | Meaning |
| --- | --- |
| `InactiveReasonCounts` | Abnormal transaction endings counted by reason, including `abandoned_on_rebid` and `arbitration_collision`. |
| `StaleActiveBytesDiscarded` | Stale active-path bytes discarded after a transaction finishes or fails, rather than carried into the next grant. |
| `ForeignInitiatorReleases` | Gateway ownership releases caused by a foreign initiator byte. |

Evidence status: **Proven** as the gateway implementation contract described by
[gateway issue #1401](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1401)
and its companion [PR #1407](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1407).
These are gateway ownership rules, not a native eBUS wire contract or a device
family qualification claim. Live-equipment validation of this lifecycle is
**Unknown** here.

### AD12: Passive Path Delivery

The multiplexer boundary carries raw wire symbols. An ENH `RECEIVED` event
carries one physical wire byte, so an escaped data or CRC byte arrives as two
symbols (`0xA9 0x00` or `0xA9 0x01`) and only an unescaped `0xAA` is a
structural SYN (see the [ENH receive path](../protocols/enh.md#send)).
Escaping is host-side on both paths: every `SEND`, from the gateway or from an
external session, supplies one physical wire byte that the sending host has
already expanded, and each receiving host decodes the pairs itself.

External ENH sessions receive each raw symbol immediately and in order,
without waiting for an escape suffix. The active `RawTransport` also carries the raw symbol sequence unchanged, so
`gateway.Bus` performs the one escape decoding itself. Only mux-internal
tracking (wire phase tracking, echo tracking) and passive consumers use a
separately decoded logical view that records whether each logical byte came
from an escape pair. That logical view is a host projection, not the wire
contract, and is never fed to the active path.

The passive path callback receives third-party symbols only, from the logical
view. Connected/disconnected/reset lifecycle events are delivered alongside
data symbols.

## Operational Notes

- Adapter-direct transport and proxy-based transport are mutually exclusive at
  the gateway level. Only one may be active at a time.
- Migration and rollback procedures are documented in
  [`../deployment/adapter-direct-migration.md`](../deployment/adapter-direct-migration.md).
- The standalone proxy is deprecated. A return from adapter-direct to a proxy
  topology is not an accepted rollback target; leaving adapter-direct for a
  direct adapter transport or for ebusd-tcp remains a configuration change.

## Live Validation (v0.4.0)

The adapter-direct multiplexer is running live on production hardware with
verified results:

- Device scan: 4 devices discovered (BAI00, BASV2, VR_71, SOL00)
- B524 register access: coherent responses across all groups
- Semantic planes: zones=2, dhw=true, INFO=7 of 8 IDs cached (Bus Voltage unsupported by adapter)
- Passive path: third-party traffic delivered without self-echo corruption

## References

- Implementation: `helianthus-ebusgateway/internal/adaptermux/`
- Migration guide: [`../deployment/adapter-direct-migration.md`](../deployment/adapter-direct-migration.md)
- Execution plan: `helianthus-execution-plans/gateway-embedded-proxy`
