# Local eBUS responder registration contract

Status: **Hypothesis** — proposed software contract, tracked by
[docs issue #770](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/770).
This is a partial slice of
[gateway issue #991](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/991);
the parent remains open. This page delivers no mux responder, endpoint or
real-bus transmit path. Interfaces remain pre-stable until Helianthus 1.0.

## Authority and evidence

Native facts come first from the public
[eBUS wire contract](../protocols/ebus-services/ebus-overview.md) and
[identification service contract](../protocols/ebus-services/ebus-service-07h.md#service-0x07-0x04--identification).
Those references own frame types, escaping, CRC coverage and ACK/response phases;
this application contract cannot redefine them. **Proven** means supported by
those public contracts, not physical qualification. Proposed behavior below is
**Hypothesis**. Production timing, error rates, host suitability and physical
fault containment are **Unknown**. Evidence labels do not confer qualification,
freshness, readiness or authority.

The [bidirectional driver boundary](../architecture/bidirectional-driver-registration.md)
continues to own driver lifecycle and source/sink separation. The
[offline worker contract](../architecture/local-worker-transport.md) owns local
message transport and safe reclamation. Registration grants neither source
ownership nor permission to initiate a telegram.

## Exact identities and bounded inputs

All comparisons use complete tuples, without matching by address alone.
Numbers below are unsigned; identity counters start at one and zero is invalid.
The host allocates subscriber and worker identities without reuse while any old
handle, mapping or retained record can exist. Missing allocator recovery proof
keeps admission closed.

| Identity or field | Exact meaning |
| --- | --- |
| `subscriber` | Host-assigned subscriber incarnation, not a display name or reusable connection slot |
| `address` | One target address octet admitted by the native frame-type rules; no broadcast, initiator address, escape or SYN address |
| `registration_epoch` | Strictly advancing incarnation of this subscriber's registration; never reused after cleanup |
| Registration key | `(subscriber, address, registration_epoch)` |
| `worker` | Host-assigned worker incarnation; a replacement cannot inherit the predecessor's authority |
| `stream_generation` | Generation of one uninterrupted raw observation stream within that worker |
| `transaction` | Ordinal assigned at request collection start within the stream; never inferred from equal payloads |
| `plan_generation` | Strictly advancing immutable publication identity within a worker, including across stream changes |
| Wire key | `(worker, stream_generation, transaction, plan_generation)` |
| `owner_token` | Nonzero, nonreused command-owner reservation scoped to the exact registration and wire keys |
| `owner_expiry` | Exclusive deadline of that token in the injected worker monotonic clock |
| `capture_sequence` | Strictly increasing ordinal for every raw symbol and control observation in the stream |
| `capture_time` | Nondecreasing injected monotonic capture time, recorded at observation, never replaced with delivery time |

All u64 counters refuse the increment that would wrap; no modulo generation or
sequence comparison is permitted. Exhaustion closes affected admission and
requires a new isolated incarnation after predecessor retirement proof.
Expiry equality is expired: admission requires `now < owner_expiry`,
`now < plan_expiry` and `now < request_deadline`. Checked deadline addition must
refuse overflow. Clock regression or an incomparable clock domain invalidates
admission; wall clock is never substituted.

Before registration, an offline fixture supplies positive finite parameters:
maximum subscribers, registrations, plans, entries per plan, retained events,
raw prefix bytes, request bytes, response bytes, plan bytes, each lane's slot
count and payload bytes, and lease/request durations in injected ticks. Values
must fit the ABI widths and all checked allocation sums/products. A zero,
missing, overflowing or inconsistent limit refuses configuration before effects.
No unbounded list, queue, capture buffer or callback backlog is allowed. A full
resource refuses new admission without evicting an active lease. These limits
and deadlines are fixture inputs, never product timing or error acceptance.

## Register, replace and clean up

Validate the entire detached registration and plan before publishing either.
One address has at most one admitted registration across all subscribers.
An exact retry of a registration key with byte-identical detached content
returns its current state, allocating nothing. The same key with different
content is a conflict. Any different key claiming an occupied address is a
conflict, including a later epoch from the same subscriber: replacement requires
explicit retirement of the incumbent first. No last-writer-wins selection.
Rejection changes no incumbent, unrelated registration or retained evidence.

Unregister takes the full registration key. Repeating cleanup is harmless;
cleanup of a stale epoch cannot remove a successor. Disconnect, cancellation,
STOP, stream invalidation or expired registration authority fences new work,
revokes affected command tokens and retires affected plans. Cleanup completes
only after the worker's observed revocation acknowledgement or lease expiry,
and the reclamation conditions below. Desired STOP alone proves no close.
No successor is admitted to the address while predecessor wire authority is
uncertain. Unaffected last-known-good state keeps its original provenance and
aging; retained state cannot bypass a closed admission gate.

## Immutable publication and leases

A plan is a detached, bounded table of exact accepted request bytes and prepared
response bytes, bound to the full registration key, worker, stream generation,
plan generation and exclusive `plan_expiry`. Entries include source constraints,
destination, PB/SB, request length/data, response length/data and allowed phase.
Ambiguous or overlapping match entries refuse the whole candidate. A complete
replacement publishes atomically; omitted registrations and unrelated plans
retain their original state. An invalid candidate replaces nothing. Published
bytes never change, including through caller-owned buffers.

The worker records a lease before retaining a plan reference. A publication
replacement prevents new selection of the predecessor but cannot redirect an
already selected transaction into newer bytes. A selected plan can finish only
while every original lease/token/deadline remains valid and it has not been
revoked. Renewal requires a fresh plan generation and new selection, never
in-place extension of a selected lease.

The publisher retains retired storage until it has observed an acknowledgement
for the exact worker/stream/plan and registration identity, or the original lease
has expired in the same comparable clock domain. An acknowledgement must mean
that no reader or deferred output still references the plan. At expiry the
worker must synchronously drop references and cancel deferred output before
further access; the publisher must also establish no in-flight access remains.
Uncertain clock progress, worker pause, lost acknowledgement or unproven quiescence
quarantines storage instead of freeing or reusing it. Expiry is not a claim that
a stopped process has executed cleanup. The transport page specifies the
reclamation barrier. No address or token reuse can bypass this barrier.

## Destination-time selection and phase admission

1. Record the complete ordered raw prefix from request start, including source,
   destination and both octets of every escape pair, with each event's sequence,
   capture time and direction. Do not reconstruct raw bytes from decoded data.
2. When the destination becomes available, provisionally select at most one
   eligible registration and immutable plan. Deliver the full prefix, then every
   subsequent raw event exactly once in capture order. A subscriber must not
   miss bytes received before destination selection. Freeze the registration,
   wire key and owner token; provisional selection emits nothing.
3. Collect and validate the complete command against that selected plan:
   contiguous sequence, well-formed escapes, exact lengths and bytes, source
   constraint, destination, PB/SB, native request CRC and correct target phase.
   Recheck exact keys, revocation, authority and all deadlines at the actual
   output boundary for each symbol, not only at enqueue time.
4. Only a valid matching initiator/target command may enter target ACK and
   response phases. Broadcast, initiator/initiator, unsupported requests, bad
   CRC, wrong phase, stale identity, gap, overflow or expired lease produce no
   synthetic answer. Refusal is not a universal NACK policy. Any later NACK or
   retransmission behavior needs explicit native phase support and independent
   evidence; the minimal fixture does not implement it.
5. Preserve the native distinction between raw SYN boundaries and escaped data.
   SYN ending an active wait, echo mismatch, malformed escape or lost stream
   continuity aborts selected work. A fresh boundary may resynchronize collection
   only after invalidation; old tokens and partial prefixes cannot be revived.

The sole wire authority serializes ordinary initiator ownership and selected
target output. It cannot grant both simultaneously. A target reservation cannot
arbitrate, send initiator `START`, initiate a command, or release another owner's
transaction. Conflicting initiator ownership withholds the target answer;
neither subscriber priority nor a late callback can steal the wire. Observers
may receive raw evidence without gaining transmit authority.

## Minimal synthetic read-only scope and ordinary surfaces

The only planned response fixture is a directed identification read:
`PB=0x07, SB=0x04, LEN=0`, using the native fixed ten-byte response layout.
Its manufacturer byte, five ASCII family bytes and four valid BCD bytes are
explicit synthetic inputs, not copied device identities or a compatibility
claim. The response is precomputed with native CRC/escaping. Empty, malformed,
unsupported or broadcast requests stay silent. No register write, spontaneous
broadcast, live discovery or real-device emulation is included. A target answer
on a real bus is a live write; this offline contract authorizes none.

No default configuration reaches a new real-bus transmit path and no production
eBUS arming switch is introduced. Existing eBUS MCP names, envelopes and behavior
remain compatible. Any future ordinary GraphQL/MCP read view must use the same
detached snapshot, ordering, evidence labels and loss/withholding reasons under
its documented mapping. This proposal adds no endpoint, lifecycle principal,
authorization gate, new major namespace or experimental namespace.

## Eight-criterion acceptance trace

The rows trace this partial slice's eight acceptance areas; they are not claims
of executed parent acceptance. This table is a contract coverage index; exact
matching to the parent criterion text remains unverified.

| Criterion | Contract obligation and planned deterministic evidence | Current evidence |
| --- | --- | --- |
| 1 | Exact registration, duplicate refusal and bounded inputs; retry/conflict fixture with unchanged incumbent | Contract only; runtime **Unknown** |
| 2 | Exact-key cleanup and disconnected subscriber retirement; late old-epoch cleanup cannot remove a successor | Contract only; runtime **Unknown** |
| 3 | Detached immutable plans and lease reclamation; caller mutation, replacement, held reader, acknowledgement loss and expiry equality | Contract only; runtime **Unknown** |
| 4 | Destination-time provisional selection; escaped source/destination prefix and later bytes delivered once in order | Contract only; runtime **Unknown** |
| 5 | CRC, frame type, phase and deadline admission; valid identification positive control and one invalid condition at a time | Contract only; runtime **Unknown** |
| 6 | One wire authority, no initiator START, independent bounded control lane; saturated data cannot hide revocation, neither role steals ownership | Contract only; runtime **Unknown** |
| 7 | Gap/restart invalidation and ABI validation; stale key fields, malformed regions, wrap refusal, snapshot parity and unaffected last-known-good state | Contract only; runtime **Unknown** |
| 8 | Production timing/error acceptance, platform atomics/MMIO, physical fault containment and hardware suitability | **Unknown**; hardware/owner decisions remain open |

Future runtime identity tests must vary subscriber, address and registration
epoch independently, then worker, stream generation, transaction and plan
generation independently, and separately owner token, owner expiry, capture
sequence and capture time while all other fields remain valid. Each needs an
independent expected result, valid positive control, joined cleanup and a named
production mutation removing that field's check. Planned mappings are not
executed mutant kills. Document publication checks prove only document properties,
not runtime identity enforcement, transport conformance or physical acceptance.
