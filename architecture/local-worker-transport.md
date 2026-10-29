# Offline local-worker transport contract

Status: **Hypothesis** — proposed software ABI version 1, pre-stable until
Helianthus 1.0. Companion to the
[local responder registration contract](../api/ebus-local-responder.md), tracked by
[docs issue #770](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/770)
as a partial slice of
[gateway issue #991](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/991).
No worker, shared-memory implementation, mux responder or live transport is
implemented by this document.

## Authority and scope

The public [eBUS wire contract](../protocols/ebus-services/ebus-overview.md) owns
native framing and phases. The registration companion owns exact identities,
immutable plans, half-open deadlines and destination-time selection. The
[bidirectional driver boundary](bidirectional-driver-registration.md) continues
to own lifecycle and ordinary eBUS MCP/GraphQL compatibility. This page defines
application transport, not native eBUS semantics; it belongs outside CC0 trees.

**Proven** denotes support from the linked public contracts only. The proposed
ABI and behaviors are **Hypothesis**. Runtime implementation, production timing,
error rates, Linux arm64 performance, MMIO/atomic suitability and physical fault
containment remain **Unknown**, independently of evidence labels and qualification.
Only synthetic/public fixtures, in-memory loopback and injected monotonic time
are in scope. No device access, real-bus answer, new production arming switch or
reachable-by-default real-bus transmit path follows from this contract.

## ABI version 1: bytes, regions and validation

Use pointer-free little-endian serialization with unsigned fixed-width fields;
no native struct layout, pointers, Go objects, native-size integers or implicit
padding. The following layout is the proposed offline interchange contract,
not a published SDK or a claim that a platform supports shared atomics.
All offsets below are bytes from the beginning of their containing structure.

The mapping header is 64 bytes, aligned to 8 bytes:

| Offset | Type | Field and requirement |
| --- | --- | --- |
| 0 | u32 | Magic: ASCII bytes `LWB1` in increasing offset order |
| 4 | u32 | ABI version, exactly 1 |
| 8 | u32 | Header bytes, exactly 64 |
| 12 | u32 | Total mapping bytes, finite and equal to the supplied buffer length |
| 16 | u64 | Nonzero worker incarnation |
| 24 | u64 | Nonzero stream generation |
| 32 | u32 | Lane count, exactly 4 |
| 36 | u32 | Lane descriptor bytes, exactly 64 |
| 40 | u64 | Descriptor table offset, 8-byte aligned |
| 48 | u64 | Immutable plan arena offset, 8-byte aligned |
| 56 | u64 | Immutable plan arena bytes, positive and finite |

Each 64-byte lane descriptor has the following layout:

| Offset | Type | Field and requirement |
| --- | --- | --- |
| 0 | u32 | Lane kind: 1 host control, 2 worker control, 3 host data, 4 worker data; each occurs once |
| 4 | u32 | Slot bytes, at least 128 and a multiple of 8 |
| 8 | u32 | Capacity in slots, positive fixture parameter |
| 12 | u32 | Reserved, zero |
| 16 | u64 | Slot region offset, 8-byte aligned |
| 24 | u64 | Producer index, aligned, initialized to zero |
| 32 | u64 | Consumer index, aligned, initialized to zero |
| 40 | 24 bytes | Reserved, all zero |

Check every addition, multiplication and conversion before dereference. Header,
descriptor table, four slot regions and plan arena must all be in bounds and
pairwise disjoint, with positive lengths. Reject overlapping regions, duplicate
lane kinds, unknown version, wrong magic, unsupported flags, nonzero reserved
bytes, misalignment or impossible sizes before accepting any record. No
unchecked offset from a peer becomes an address. An invalid replacement leaves
the previous valid mapping's unaffected state intact and admits no new output.

A slot starts with the following 128-byte envelope; any payload follows at 128.
Remaining slot padding is zero. There are no out-of-mapping references.

| Offset | Type | Field |
| --- | --- | --- |
| 0 | u32 | Kind: 1 publish plan, 2 revoke plan, 3 revocation acknowledgement, 4 gap, 5 stop, 6 command, 7 raw event, 8 completion |
| 4 | u32 | Payload bytes, at most slot bytes minus 128 and the fixture payload limit |
| 8 | u64 | Worker incarnation |
| 16 | u64 | Stream generation |
| 24 | u64 | Transaction ordinal |
| 32 | u64 | Plan generation |
| 40 | u64 | Subscriber incarnation |
| 48 | u64 | Registration epoch |
| 56 | u64 | Command owner token |
| 64 | u64 | Owner expiry in injected ticks |
| 72 | u64 | Capture sequence |
| 80 | u64 | Capture time in injected ticks |
| 88 | u64 | Plan expiry in injected ticks |
| 96 | u64 | Request deadline in injected ticks |
| 104 | u64 | Plan arena offset relative to mapping start |
| 112 | u32 | Plan bytes |
| 116 | u32 | Status: 0 proposed/pending, 1 accepted, 2 refused, 3 retired |
| 120 | u8 | Target address |
| 121 | u8 | Raw octet, used only for a raw event |
| 122 | u8 | Direction: 0 control, 1 observed receive, 2 observed transmit echo |
| 123 | u8 | Phase: 0 none, 1 request, 2 target ACK, 3 response, 4 initiator ACK, 5 ended |
| 124 | u32 | Flags, exactly zero in version 1 |

Command, selected raw-event and completion records carry the entire
registration key, wire key and token/deadlines. Before selection, or for an
unselected observed transaction, raw events carry worker/stream/transaction
identity with registration, plan and token/deadline fields zero. Prefix delivery
may attach the frozen selected identity without changing any captured bytes,
sequence, time or direction. A raw event has zero payload;
it carries one octet plus its original sequence, capture time, direction and
phase. Control records have direction/phase zero. Publish, revoke and revocation
acknowledgement carry the exact registration key, worker/stream/plan identity
and original plan expiry; their transaction/token fields are zero. Gap is a
worker-originated stream-wide control with worker, stream and capture
sequence/time; its registration/plan/transaction/token fields are zero. Stop is a
host-originated stream-wide control with worker and stream identity; its capture
sequence/time and registration/plan/transaction/token fields are zero.
Other unused fields are zero;
unknown kind/status/direction/phase values refuse. Host control accepts publish,
revoke and stop; worker control accepts acknowledgement and gap; host data
accepts command; worker data accepts raw event and completion. Wrong-lane kinds
refuse. A publish record has an in-bounds immutable plan arena reference;
other records carry zero arena offset/length. Kind-specific payloads beyond
raw events are bounded opaque bytes for offline fixtures, not a new public
application schema. Implementation of a plan codec remains separate work;
unsupported codecs refuse, never interpret opaque bytes as native instructions.

## SPSC ownership and bounded independent control

Each lane is single-producer/single-consumer (SPSC). One serialized host producer
owns host-control and host-data indices; one worker consumer owns their consumer
indices. The worker alone produces worker-control and worker-data; the host
alone consumes them. No subscriber, callback or second thread writes those
indices directly. Host and worker control lanes have independent positive
capacities, storage and service budgets; data saturation cannot consume their
slots or prevent a control poll before any next output decision.

Indices are aligned u64 monotonically increasing counts, not wrapping counters.
Validate `consumer <= producer` and `producer - consumer <= capacity`. The slot
is selected by `index % capacity`, but the count itself never wraps. A producer
writes a whole slot then release-publishes its index; the consumer acquire-loads
that index before reading, then release-publishes its consumer index. The
producer acquire-loads the consumer index before reuse. A platform without
qualified aligned atomic u64 loads/stores and these memory-order guarantees
cannot use shared memory; an offline serialized loopback may model the order,
but proves no atomic/platform suitability. Wire little-endian encoding does not
itself provide synchronization.

Full lanes never overwrite unread slots or block the output loop indefinitely.
Refuse new host data. A dropped worker observation is a gap: close admission
immediately, cancel the transaction, and post a gap through worker control.
If a control lane is full or its finite injected service deadline expires,
the detecting side closes its own admission and invalidates its stream view.
A worker detecting worker-control saturation stops output without awaiting host
delivery. Host-control saturation fences new host commands but cannot prove
remote wire cessation: keep the predecessor quarantined until observed
revocation or original lease expiry plus quiescence proof. The worker independently
enforces its finite control-service deadline and every output lease. A
publish/revoke enqueue is not worker acknowledgement. No shutdown or control
delivery relies on draining the saturated data lane. Counters at their maximum
refuse advancement and invalidate instead of aliasing old slots.

## Revocation, expiry and reclamation barrier

The worker is the only wire authority and must inspect pending control before
any next output decision, then revalidate the exact keys and `now < expiry`
conditions immediately before every symbol. Host commands cannot perform initiator
START through a target reservation or create a second UART writer. A synchronous
offline output step must not retain references or queued symbols after it
returns. Asynchronous hardware/DMA writes are outside this offline ABI contract.

A revocation acknowledgement is emitted only after selection is fenced, active
readers have left the plan, pending symbols are discarded and no future access
can use that plan identity. The host observes and validates that exact
acknowledgement before reclaiming. A stale acknowledgement cannot retire a
successor or clear another registration.

Without acknowledgement, expiry can close admission but reclamation also needs
an observed reader-quiescence barrier: the worker has completed a processing
step at or after the original plan expiry and reported retirement for that
identity, or the predecessor worker has demonstrably terminated and all access
to its mapping has ceased. Only then may the host free/reuse storage. Expiry
with a paused or unreachable worker quarantines memory until that proof exists.
Every plan access checks expiry before borrowing; no borrow may span an offline
processing step. The original expiry cannot be extended by message retries,
replacement publication or clock reset. A finite plan/count budget bounds
quarantine growth; exhaustion refuses publication, rather than unsafe reuse.

## Capture gaps, restart and retained state

A raw event records observation-time sequence/time before queueing, preserving
all wire octets, including escape prefixes and echoes. The full prefix crosses
destination-time selection as specified by the registration companion. Captured
control and raw observations share the stream's sequence domain, allocated only
by the worker. Host stop records consume no capture sequence. Lane delivery
may interleave; merge by capture sequence using a finite fixture reorder buffer
and deadline. An unexplained discontinuity, duplicate, time regression or reorder
bound/deadline breach is a gap, never silent omission. Host-origin commands have
zero capture fields; they cannot fabricate observed continuity. Control affecting
admission takes effect immediately even while older data awaits ordered delivery.

Gap, corruption, restart or worker replacement fences current output, revokes
all affected tokens, abandons partial CRC/escape/phase state and invalidates
provisional selection. Drain/drop old messages by their full identity, not their
payload equality. Restart advances worker incarnation; resynchronization after
a gap advances stream generation. Rejoin requires a fresh validated mapping,
explicit boundary synchronization and newly published plans/tokens after old
wire authority is settled. Never replay a queued command into a fresh stream.
Nonwrapping allocation failure or missing retirement proof keeps admission closed.

Retain raw evidence and unaffected last-known-good semantic state with original
provenance/aging. Affected retained facts may be available as historical evidence,
but cannot be represented as fresh output or used to reopen admission. Ordinary
MCP and GraphQL detached reads must preserve equivalent ordering, loss reasons
and evidence labels. The transport adds no semantic authority or public API.

## Planned offline evidence and remaining edge

Use explicit finite capacities, deadlines and injected time. Deterministic tests
must cover valid publication/identification first, then one invalid region,
identity field, CRC/phase condition or deadline boundary at a time; held-reader
revocation, paused-worker expiry, lost acknowledgement, full data/control lanes,
escape split across destination selection, gap, restart and counter exhaustion.
Each runtime test needs independent expectations and joined cleanup. Each
identity field varied must name the production comparison it detects when
removed; reasoned mappings are separate from executed mutations. No tests or
mutation kills are delivered by this contract page.

The companion's eight-criterion trace records criteria 1–7 as contract plus
planned evidence only. Criterion 8 remains **Unknown**: production timing/error
thresholds, platform/MMIO/atomic qualification and physical containment require
separate owner decisions and hardware evidence. Reserved mux pages are unchanged.
No transport matrix, passive capture, hosted/SDK acceptance, Matter conformance
or certification follows from offline publication checks.
