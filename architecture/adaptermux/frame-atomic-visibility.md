# Frame-Atomic Visibility

> Status: implemented design of the gateway adapter multiplexer's session
> view, with per-section implementation labels. The [History](#history)
> section summarizes the revisions that led to it.

## Scope and evidence

This page states how the gateway's adapter multiplexer keeps the byte stream
of each client session faithful to the wire while an adapter injects spurious
`AA` symbols, and how it paces session output. It covers the gateway and the
eBUS library it uses. It describes the implementation, not a native wire
contract: native event identities and encodings stay defined by the public
[ENH reference](../../protocols/enh.md) and
[ENS reference](../../protocols/ens.md). Arbitration among the multiplexer's
own sessions is specified in the
[adapter-direct multiplexer page](../adapter-direct-multiplexer.md#ad06-owner-arbitration-model).

Each section opens with one of four implementation labels:

| Label | Meaning |
|---|---|
| Implemented | The gateway or the library contains the mechanism and applies it. |
| Implemented when the mode is not `off` | The mechanism exists and runs only in the `shadow` and `enforce` [rollout modes](#rollout-modes). |
| Declared but not enforced | The values exist as declarations; no runtime path applies them. |
| Not implemented | The design specifies the rule; no implementation performs it. |

**Proven (implementation evidence):** the sections labelled Implemented, in
either form, describe mechanisms present in the gateway and the library. The
evidence is the implementation and its synthetic tests, for session output
delivery the change in gateway
[issue #1403](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1403)
and [PR #1406](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1406);
it is not a device observation.
**Unknown:** native symbol timing, and qualification of any mode on live
equipment. This page adds no live claim.

## Proxy transparency

**Label: Implemented.** For the arbitration case, see
[AD06](../adapter-direct-multiplexer.md#ad06-owner-arbitration-model).

Every client of the multiplexer should behave as if it had its own ENH or ENS
adapter on the bus. The byte stream a session receives contains only events an
adapter delivered: the multiplexer does not inject health frames, markers or
synthetic ENH events into it. Classifier diagnostics, protocol faults and
telegram aborts go to the multiplexer's admin channel only, which is a separate
diagnostic plane and not part of any client's transport.

The one place where the multiplexer writes a session-local byte is arbitration
among its own sessions: a session that lost locally receives the winner's
source byte, and the multiplexer delivers resynchronization SYNs to the
gateway session after a loss. Those rules are specified in
[AD06](../adapter-direct-multiplexer.md#ad06-owner-arbitration-model) and stay
there.

The observation unit is the byte. Telegram-atomic delivery, synthetic SYN
padding, an idle generator and a per-session symbol rate are not part of the
design; the [History](#history) records why, and the
[SYN padding page](frame-atomic-syn-padding-math.md) is kept as a historical
derivation.

## Rollout modes

**Label: Implemented.**

The classifier runs in one of three modes, read from the environment variable
`HELIANTHUS_V8_CLASSIFIER_MODE`:

| Mode | Classification | Byte drops | Session pacing |
|---|---|---|---|
| `off` | No classifier. | None. | No pacer; session output keeps a FIFO path. |
| `shadow` | Every byte is classified and would-be drops are counted. | None. | Applies. |
| `enforce` | Every byte is classified. | Injected `AA` symbols are dropped. | Applies. |

Two defaults apply:

- **Gateway default:** an unset variable selects `off`.
- **Add-on default:** the Home Assistant add-on option `v8_classifier_mode`
  defaults to `enforce` and exports it to the gateway; an explicit `off` or
  `shadow` is kept.

Promotion from `shadow` to `enforce` rests on the gate documented in
[Prometheus alert rules](../../deployment/prometheus-alerts.md#helianthusv8shadowwouldhavedroppedgrowing):
the shadow divergence counter `helianthus_v8_shadow_would_have_dropped_total`
must stay at zero or be explained by known injection events, and the alert
rules must be loaded before the mode changes. The mitigations that predate the
classifier stay reachable in `off` and `shadow`; see
[Round-9 absorb fallback and alerts](#round-9-absorb-fallback-and-alerts).

## Wire-phase state machine

**Label: Implemented (byte-driven).**

The library's telegram state machine follows each telegram on the wire, one
decoded byte at a time. The gateway classifier embeds it and exposes the
current state and a passive flag. Its states are idle, arbitrating, initiator
header, initiator data, initiator CRC, initiator ACK wait, initiator
retransmission, target length, target data, target CRC, target ACK wait,
target retransmission, terminator SYN wait, aborted, and passive tracking.

| From | Event | To |
|---|---|---|
| idle | STARTED for a multiplexer session | arbitrating |
| idle | first non-SYN byte without a STARTED in flight | passive tracking (see [Passive tracking](#passive-tracking)) |
| arbitrating | grant resolved | initiator header |
| arbitrating | FAILED | idle |
| initiator header | `NN` > 0, or `NN` = 0 | initiator data, or initiator CRC |
| initiator data | `NN` data bytes consumed | initiator CRC |
| initiator CRC | broadcast (`ZZ` = `0xFE`) | terminator SYN wait |
| initiator CRC | any other target | initiator ACK wait |
| initiator ACK wait | ACK, target address of the initiator class | terminator SYN wait |
| initiator ACK wait | ACK, any other target | target length |
| initiator ACK wait | NACK before any retransmission | initiator retransmission, then initiator header |
| initiator ACK wait | NACK after one retransmission | aborted |
| target length | `NN'` > 0, or `NN'` = 0 | target data, or target CRC |
| target data | `NN'` data bytes consumed | target CRC |
| target CRC | CRC byte consumed | target ACK wait |
| target ACK wait | ACK | terminator SYN wait |
| target ACK wait | NACK before any retransmission | target retransmission, then target length |
| target ACK wait | NACK after one retransmission | aborted |
| terminator SYN wait | SYN | idle |
| aborted | reset | idle |

An aborted state machine filters nothing; only a reset revives it. The
multiplexer's
[post-arbitration recovery](../adapter-direct-multiplexer.md#post-arbitration-recovery)
states when it resets the classifier and the wire-phase tracker. Every state
machine instance is autonomous: it reaches its state from the events it
observes, and the only resynchronization signals are events the wire or the
adapter produced (a terminator SYN, a RESETTED from the adapter). Recovery
resets inside the multiplexer are local state changes and never appear to a
client as RESETTED.

### Classify, then transition

Each byte is handled in four steps, in this order:

1. Classify the byte under the phase in force when it arrived.
2. Apply the decision: forward, drop as injected, or report a protocol fault.
3. If the byte was forwarded or was the echo of an own write, consume it in
   that phase.
4. If consuming it completes the phase, transition to the next phase.

The transition is a consequence of the byte's interpretation. An ACK `0x00`
in the initiator ACK wait is therefore read as an ACK, and only then does the
machine move to target length; it is never misread as a zero response length.
The one exception is the entry into passive tracking: the byte that leaves
idle is classified as byte 0 of the initiator header.

### Passive tracking

When the first non-SYN byte arrives in idle and no STARTED for a multiplexer
session is in flight, the byte is the foreign initiator's source address
`QQ`. The machine enters passive tracking and classifies the byte as byte 0 of
the initiator header. Passive tracking runs the same phases as an own
telegram, including both retransmission paths, and leaves to idle on the
terminator SYN. The only difference is that it has no echo matching, because
no session wrote the bytes.

Passive tracking keeps the filter active for foreign telegrams. Without it,
bytes of a foreign telegram would pass unfiltered, and a client parser that
aborts on an extra SYN inside a telegram would lose that telegram.

### Per-phase timeouts

**Label: Declared but not enforced.**

The library declares these constants:

| Phase group | Declared timeout |
|---|---|
| Inter-byte, within header, data, length and CRC phases | 10 ms |
| Initiator ACK wait and target ACK wait | 200 ms |
| Terminator SYN wait | 100 ms |
| Arbitrating | 50 ms |

No code path outside tests refers to them, neither in the library nor in the
gateway. The state machine has no time-based logic, and the library documents
that its read path has no per-phase timeouts. Every transition above is
driven by a byte or by a reset. The 200 ms ACK wait was an engineering choice
of the design, not a value that the eBUS specification mandates. The
alignment of the gateway bus timeouts with these values (invariant I7) is
therefore not in force either.

## AA-injection filter

**Label: Implemented (acts in `enforce`).**

The filter applies in every phase except idle and terminator SYN wait: the
arbitrating phase, the initiator header, data, CRC and retransmission phases,
the initiator ACK wait, the target length, data, CRC and retransmission
phases, and the target ACK wait, both for own telegrams and in passive
tracking. In these phases a raw `AA` (one that did not come out of an escape
pair) that does not match the role the phase expects is classified as
injected by the adapter. In the ACK waits the expected bytes are ACK `0x00`
and NACK `0xFF`.

Two phases are exempt and forward a raw `AA`:

- **Idle.** The bus is idle and an `AA` is a real AUTO-SYN. An injected `AA`
  in idle cannot be told apart from one (see [Residual limits](#residual-limits)).
- **Terminator SYN wait.** The terminator is itself a raw `AA`; it is
  forwarded and the machine returns to idle.

The drop decision applies only in `enforce`. In `shadow` the same decision is
counted as a would-have-dropped byte and the byte is forwarded; the
would-have-dropped counter and the drops-applied counter are kept apart.

## Escape decoder bound

**Label: Implemented.**

The transport's escape decoder absorbs injected `AA` symbols that arrive
between an escape lead `0xA9` and its suffix, and bounds that absorption in
two ways, whichever is reached first:

- at most **8** absorbed `AA` symbols per escape pair;
- at most **32 ms** in the escape-pending state, measured on the monotonic
  clock.

On either bound, and on a malformed suffix, the decoder emits nothing for the
pair, reports the event on the admin channel and returns to normal decoding;
when the time bound expires, the byte that arrived late is decoded again in
the normal state so that it is not lost. The decoder never fabricates a byte
the wire did not send. The classifier mirrors both bounds (invariant I4).

The 32 ms bound is eight wire symbol times (8 × 4.17 ms), so an escape pair
held open longer than that cannot be explained by absorbed symbols alone. The
design also paused the inter-byte timer while an escape pair was pending; with
per-phase timeouts not enforced, that pause has no runtime effect.

## Protocol faults and admin events

**Label: Implemented.**

When a byte cannot belong to the phase in force, the classifier decides a
protocol fault (invariant I10): it forwards the byte to every session, so the
stream stays faithful to the wire, and emits a protocol-fault event on the
admin channel. A telegram abort after retransmission is exhausted is reported
the same way. No ENH event is synthesized for either case: in particular no
RESETTED, which the [ENH reference](../../protocols/enh.md) reserves for an
adapter reset or initialization, and no FAILED. Each client detects the fault
with its own protocol logic, as it would on its own adapter.

## Retransmission cap

**Label: Implemented in the state machine.**

A NACK before any retransmission moves the initiator ACK wait or the target ACK
wait to its retransmission phase, and the telegram restarts at the initiator
header or the target length. A NACK after one retransmission moves to aborted
(invariant I6). The cap is one retransmission per phase.

## Address-class validation

**Label: Not implemented.**

The design checks the first header byte against the initiator address class
and the second against the broadcast, initiator and target classes, and
reports a protocol fault on a mismatch. The library state machine records the
first header byte without validating it; its own documentation defers the
check. No comparison of that byte with a winner named by a FAILED is made in
the state machine either.

## Echo timing and grace bootstrap

**Label: Implemented when the mode is not `off`.**

The session pacer keeps a round-trip latency average (exponential, weight
0.3, starting at 100 ms) for echoes of own writes. It samples only active
echoes: latency inferred from passive traffic would mix foreign inter-byte
gaps, target think time and link jitter into the average.

| Regime | Soft deadline | Hard deadline |
|---|---|---|
| Grace: the first 3 echoes after at least 30 s without an echo | average + 500 ms | none |
| Normal | average + 100 ms | 2 × average + 200 ms |

A missed soft deadline is logged on the admin channel. The pacer is called
before each active write and on each echo arrival, and an echo watchdog checks
the deadlines in between.

## Session output delivery

**Label: Implemented when the mode is not `off`.** Native timing is Unknown.

Pacing applies only where a session pacer exists, so in `shadow` and
`enforce`; in `off` session output keeps a FIFO path without a pacer. These
are host egress scheduling rules of the gateway; the gateway's own
documentation of raw-symbol continuity states the same rules.

### Pacing and the bounded backlog

Invariant I3 (pacing): `RECEIVED` symbols that are on time keep the
per-session wire cadence of one symbol per 4.17 ms (2400 baud, 10 bits per
symbol). The paced backlog is bounded at **2** `RECEIVED` symbols:

- Pacing reserves one slot per `RECEIVED` symbol, independent of its encoded
  ENH length; control frames reserve none.
- The session writer looks ahead over at most three queued frames. When that
  lookahead holds more than two `RECEIVED` frames, the writer takes a snapshot
  of the queue and writes it at once, in FIFO order, without pacing waits.
- When the flush write completes, cadence is rebased to that moment: the next
  ordinary symbol waits one period, instead of replaying the scheduling debt.

The bound limits how much backlog is spread over future pacing slots; it is
not a capacity limit of the session queue. A flush keeps every queued frame
and its order; it never drops a symbol or inserts an event. The gap of at
least one symbol time holds for ordinary paced delivery, not inside a flush.

### STARTED and FAILED keep stream order

`STARTED` and `FAILED` never overtake older queued `RECEIVED` symbols. When an
arbitration result is queued behind them, the writer drains that older prefix
without pacing and writes the result immediately after it, also when the
prefix is within the bound. The result reserves no pacing slot and never
crosses RESETTED or other control frames. A client therefore never sees older
received symbols as echoes after its grant. Immediate means no intentional
pacing wait, not a socket-write or network deadline.

Synthetic examples, in enqueue and delivery order:

| Queued stream | Delivery |
|---|---|
| `RECEIVED(A), RECEIVED(B)` | Normal cadence at the bound. |
| `RECEIVED(A), RECEIVED(B), RECEIVED(C)` | Over the bound: flush A, B, C at once in order, then pace from the end of the flush. |
| `RECEIVED(A), RECEIVED(B), STARTED` | Drain A, B; write STARTED immediately after them. |
| `RECEIVED(A), RECEIVED(B), FAILED` | Drain A, B; write FAILED immediately after them. |

### Flush observability

Each session counts its backlog flushes. The integer expvar
`adaptermux_session_backlog_flushes_total` aggregates them across sessions. It
is kept apart from the latency histogram
`adaptermux_session_frame_latency_us_bucket_total`, which holds no flush
entry. Draining an older prefix for a `STARTED` or `FAILED` does not count as a
backlog flush, and a result delivered inside a counted flush adds no second
count. These diagnostics never enter a client stream.

## Round-9 absorb fallback and alerts

**Label: Implemented.**

The library's bus keeps its round-9 absorb path as a fallback: when the echo
of an own payload `AA` is followed by wire AUTO-SYNs, it absorbs up to three of
them before giving up. The path serves adapter-direct use without a
classifier and stays reachable in `off` and `shadow`, together with the other
mitigations that predate the classifier.

The library exports the entries into that path as
`helianthus_round9_absorb_entered_total`. The counter is gated on the active
echo wait of an own write, so ordinary idle AUTO-SYNs do not move it, and it
does not consult the classifier mode. Invariant I8: in `enforce`, the
classifier filters injected symbols before they reach the gateway's echo
position, so any entry is a violation. The alert rules carry the mode
condition:

| Alert | Counter | Meaning |
|---|---|---|
| [`HelianthusRound9FiredUnderProxy`](../../deployment/prometheus-alerts.md#helianthusround9firedunderproxy) | `helianthus_round9_absorb_entered_total` | A round-9 entry while the classifier is in `enforce`. |
| [`HelianthusV8ShadowWouldHaveDroppedGrowing`](../../deployment/prometheus-alerts.md#helianthusv8shadowwouldhavedroppedgrowing) | `helianthus_v8_shadow_would_have_dropped_total` | Shadow divergence before promotion to `enforce`. |

Both rules must be loaded before the classifier is promoted to `enforce`.

## Invariants

**Concurrency, label: Implemented as a single producer.** The multiplexer's
read loop is the single producer of the classifier: classification,
transitions, forwarding to session queues and admin events for a byte happen
in sequence on that loop, and no session sees a partial transition
(invariant I11).

The numbering I0 to I11 is kept so that existing citations stay valid. I3 is
the pacing guarantee as revised by the bounded backlog.

| Invariant | Statement | Section |
|---|---|---|
| I0 | Scheduling and bounds use the monotonic clock. | [Escape decoder bound](#escape-decoder-bound), [Session output delivery](#session-output-delivery) |
| I1 | No synthetic event enters a client byte stream; the admin channel is outside it. | [Proxy transparency](#proxy-transparency) |
| I2 | The wire-phase state machine is the sole authority for injected-`AA` classification. | [AA-injection filter](#aa-injection-filter) |
| I3 | On-time `RECEIVED` symbols keep the wire cadence; the paced backlog is bounded at 2 symbols and flushed in order beyond it; `STARTED` and `FAILED` never overtake older symbols. | [Pacing and the bounded backlog](#pacing-and-the-bounded-backlog) |
| I4 | The escape decoder absorbs at most 8 `AA` symbols or waits at most 32 ms per pair, whichever comes first, and then emits nothing. | [Escape decoder bound](#escape-decoder-bound) |
| I5 | Each state machine is autonomous and resynchronizes only on events the wire or the adapter produced. | [Wire-phase state machine](#wire-phase-state-machine) |
| I6 | One retransmission per phase; a second NACK aborts. | [Retransmission cap](#retransmission-cap) |
| I7 | Gateway bus timeouts align with the declared per-phase timeouts. | [Per-phase timeouts](#per-phase-timeouts) (declared but not enforced) |
| I8 | Round-9 absorb stays as a fallback; an entry in `enforce` is a violation and alerts. | [Round-9 absorb fallback and alerts](#round-9-absorb-fallback-and-alerts) |
| I9 | Classify under the phase in force, then consume, then transition. | [Classify, then transition](#classify-then-transition) |
| I10 | A protocol-fault byte is forwarded to every session and reported on the admin channel. | [Protocol faults and admin events](#protocol-faults-and-admin-events) |
| I11 | One producer drives classification, transitions, forwarding and admin events in sequence. | This section |

## Residual limits

- **Injected `AA` on an idle bus.** In idle an injected `AA` cannot be told
  apart from a real AUTO-SYN and is forwarded. The window is the gap between
  telegrams.
- **Two adjacent injected `AA` symbols.** Inside a live telegram they are
  indistinguishable from an idle bus; the multiplexer's
  [post-arbitration recovery](../adapter-direct-multiplexer.md#post-arbitration-recovery)
  lists the consequence for its foreign states.
- **Phases without a closing byte.** The design's residual for a target that
  answers after the ACK-wait window assumed an enforced timeout. With
  per-phase timeouts not enforced, how the classifier leaves a phase whose
  expected byte never arrives is covered here only by the multiplexer's
  post-arbitration recovery and is otherwise Unknown.
- **Address classes.** Header addresses are not validated; see
  [Address-class validation](#address-class-validation).
- **Per-session pacing.** The pacer regulates each session's TCP egress, not a
  shared wire; two sessions may receive the same symbol at slightly different
  times, as two clients on separate adapters with different links would.
- **Adapter byte loss.** A byte the adapter transmits but does not report back
  is invisible to every session, as it would be to a client on its own
  adapter.

## Supporting pages

- [First-byte arbitration revalidation](first-byte-arbitration-revalidation.md):
  the accepted implementation contract for the first foreign initiator-class
  byte that arrives during a gateway-owned write; it is forwarded, not
  dropped.
- [SYN padding and timing derivations](frame-atomic-syn-padding-math.md):
  historical; it derives the timing model of the original sketch, which the
  gateway does not implement.
- [Adapter-direct multiplexer](../adapter-direct-multiplexer.md): arbitration
  among the multiplexer's sessions
  ([AD06](../adapter-direct-multiplexer.md#ad06-owner-arbitration-model)) and
  [post-arbitration recovery](../adapter-direct-multiplexer.md#post-arbitration-recovery).
- [Prometheus alert rules](../../deployment/prometheus-alerts.md): the alert
  rules, their counters and the promotion gate.

## History

The design went through a sketch and eight revisions, v2 to v9. The full
revision texts remain in the repository history; this page replaces them.

### Revisions

| Revision | What it changed | Why |
|---|---|---|
| Sketch | Proposed telegram-atomic delivery to observing sessions, with synthetic SYN padding, an idle generator and a per-session symbol rate. | Arbitration is byte-level, so a telegram-atomic byte stream splits an active client's view, and the padding model emitted events the wire did not produce. |
| v2 | Kept the byte as the observation unit; proposed per-byte provenance passed to clients and forwarding gated on the adapter echo; bounded retransmission; required a monotonic clock. | ENS clients cannot receive provenance metadata, and one provenance bit could not separate a terminator SYN from an injected SYN. |
| v3 | Moved the filter into the multiplexer with provenance kept internal and a per-session echo match; added a wire-rate pacer; carried no telegram structure. | Without telegram structure the filter missed injected AA bytes while no session was writing and inside escape pairs, and a retransmission cap needs telegram state. |
| v4 | Added a minimal telegram state machine to drive the filter, an escape decoder that absorbs injected `AA`, a pacer acting as a rate limiter and a cadence threshold for idle. | A cadence threshold at proxy receive time could not separate fast wire SYNs from injected AA bytes, and a time window in the escape decoder lost valid pairs under network jitter. |
| v5 | Filtered only during active phases and passed idle through; bounded the escape decoder by count (8 absorptions); corrected the pacer's scheduling chain; sampled latency per echo; first per-phase timeouts; answered protocol faults with RESETTED. | Idle pass-through was not shown harmless for clients, a synthetic RESETTED on protocol faults contradicted the ENH reference, and a timeout back to idle left later bytes unreconstructable. |
| v6 | Kept the state machine always on with active, passive and idle modes; added passive tracking; moved protocol faults to the admin channel; kept round-9 absorb as a fallback with a regression counter; made malformed escapes emit nothing. | Passive tracking closes the idle gap; the direct-adapter path still needs the round-9 fallback. |
| v7 | Forwarded the protocol-fault byte with an admin event (I10); processed bytes one at a time (I9); added retransmission paths to passive tracking; paused the inter-byte timer during an escape pair; gated the round-9 counter and added its alert rule; set a deployment order. | Localized fixes to v6 without a structural change. |
| v8 | Classified each byte under the phase in force before the transition (I9); made the first non-SYN byte the passive entry; capped the escape-pending time at 32 ms (I4); sampled latency from active echoes only, with a grace bootstrap; extended the filter to all non-idle phases; specified address-class validation; added the single-producer rule (I11). | Byte-ordering and bound fixes to v7 that keep its structure. |
| v9 | Bounded the paced backlog at 2 symbols with an in-order flush and a cadence rebase; kept `STARTED` and `FAILED` behind older symbols; counted flushes outside the latency histogram. | The pacing guarantee of v5 and v8 allowed an unbounded backlog. |

### Section map for earlier citations

Comments and pages, in this repository and others, cite sections and
invariants of the revision pages. They map to this page as follows.

| Earlier citation | Section of this page |
|---|---|
| sketch §0 | [Proxy transparency](#proxy-transparency) |
| sketch §4.5, v8 §4.5 | [Pacing and the bounded backlog](#pacing-and-the-bounded-backlog) |
| v5 I5 / v8 I3 / v9 I5 | [Pacing and the bounded backlog](#pacing-and-the-bounded-backlog); invariant I3 in [Invariants](#invariants) |
| v6 §3, v8 §3 (state machine, idle pass-through), v8 §3.1 | [Wire-phase state machine](#wire-phase-state-machine); timeouts in [Per-phase timeouts](#per-phase-timeouts) |
| v8 §1.1, I9 | [Classify, then transition](#classify-then-transition) |
| v8 §1.2 | [Passive tracking](#passive-tracking) |
| v8 §1.3, I4; v8 §5 | [Escape decoder bound](#escape-decoder-bound) |
| v8 §1.4 | [Echo timing and grace bootstrap](#echo-timing-and-grace-bootstrap) |
| v8 §1.5 | [Per-phase timeouts](#per-phase-timeouts) |
| v8 §1.6, v8 §4 | [AA-injection filter](#aa-injection-filter) |
| v8 §1.7 | [Address-class validation](#address-class-validation) |
| v8 §1.8, v8 §1.9, v8 §10 | [Round-9 absorb fallback and alerts](#round-9-absorb-fallback-and-alerts) |
| v8 §1.12, I8 | [Round-9 absorb fallback and alerts](#round-9-absorb-fallback-and-alerts); invariant I8 in [Invariants](#invariants) |
| v8 §4.7 shadow divergence | [Rollout modes](#rollout-modes) |
| v8 §14 | [Rollout modes](#rollout-modes) |
| v8 §1.11, I11; v8 §3 (invariants list) | [Invariants](#invariants) |
| v7 §1.1, I10; v8 §8 (protocol faults) | [Protocol faults and admin events](#protocol-faults-and-admin-events) |
| v7 §1.5, I6; v8 §8 (abort after retransmission) | [Retransmission cap](#retransmission-cap) |
| v7 §2.1, v7 §2.2, v8 §2 | [Residual limits](#residual-limits) |
| v9 §2 | [Pacing and the bounded backlog](#pacing-and-the-bounded-backlog) |
| v9 §3 | [STARTED and FAILED keep stream order](#started-and-failed-keep-stream-order) |
| v9 §4 | [Flush observability](#flush-observability) |

v5 and v9 called the pacing guarantee I5. In the v8 numbering kept here, I5
is state-machine autonomy and the pacing guarantee is I3.
