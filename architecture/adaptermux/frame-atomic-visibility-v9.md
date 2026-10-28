# Frame-Atomic Visibility v9 — Bounded Pacer Backlog and Strict Stream Order

> Status: current session-delivery contract; companion of gateway
> [issue #1403](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1403)
> and [PR #1406](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1406).
> Supersedes the unbounded pacing guarantee in the
> [original sketch §4.5](frame-atomic-visibility.md#45-intra-telegram-pacing),
> [v5 I5](frame-atomic-visibility-v5.md#13-invariants), and the pacer summary in
> [v8 I3](frame-atomic-visibility-v8.md#3-updated-invariants-list).

## 1. Scope and evidence

This contract describes the gateway adapter-mux family's delivery to client
sessions. It is an implementation contract, not a claim about native wire
behavior. Native event identities and encoding remain defined by the public
[ENH reference](../../protocols/enh.md) and
[ENS reference](../../protocols/ens.md); the pacer changes delivery timing,
not those event definitions.

**Proven (implementation evidence):** the companion change implements the
bounded pacer and strict ordering described below. Its session writer and
synthetic backlog tests provide the evidence, rather than device observations.
**Unknown:** qualification on live equipment is not established by this
documentation update. Qualification is separate from the implementation claim.

## 2. Bounded pacing: current I5

**I5 (pacer correctness, restating v5 I5):** outbound `RECEIVED` symbols that
are on time retain the per-session wire cadence `τ_wire_byte`. The default
paced-backlog bound is **2 symbols**. A backlog at the bound remains paced;
when the queued `RECEIVED` symbol count exceeds the bound, write the backlog
immediately in FIFO stream order, without waiting for individual pacing slots.
After the flush completes, resume pacing from the current time, rather than
replaying accumulated scheduling debt.

The bound limits how much backlog is spread across future pacing slots; it is
not a two-symbol capacity limit on the session's delivery queue. The threshold
counts `RECEIVED` symbols, not arbitration or other control events. A backlog
flush preserves queued content and order; exceeding the pacing bound does not
authorize dropping symbols or injecting synthetic events.

Thus `inter-byte gap ≥ τ_wire_byte` applies to normal paced delivery, not to
the immediate flush. The earlier claim that all bursts are spread by the pacer
without a bound is historical. In v8's numbering this revises the pacing
summary I3; v8 I5 continues to mean FSM autonomy.

## 3. STARTED and FAILED preserve stream order

`STARTED` and `FAILED` never overtake earlier queued `RECEIVED` symbols. When
an arbitration result is queued behind a backlog, flush the preceding backlog
first and write that result immediately afterward, without inserting a pacing
delay before the result. This also applies when the preceding backlog is at
or below the two-symbol bound. Both arbitration outcomes use the same rule.

Synthetic examples, with events shown in enqueue and delivery order:

| Queued stream | Delivery |
|---|---|
| `RECEIVED(A), RECEIVED(B)` | Keep normal cadence at the bound. |
| `RECEIVED(A), RECEIVED(B), RECEIVED(C)` | Over the bound: flush A, B, C immediately in order, then resume pacing from now. |
| `RECEIVED(A), RECEIVED(B), STARTED` | Flush A, B first; write STARTED immediately next. |
| `RECEIVED(A), RECEIVED(B), FAILED` | Flush A, B first; write FAILED immediately next. |

The arbitration result is prompt without moving ahead of pre-result traffic.
In particular, a client must not see older received symbols as post-grant
echoes merely because `STARTED` bypassed the queue. Immediate delivery here
means no intentional pacing wait; it does not promise a socket-write or
network-latency deadline.

## 4. Flush observability

Each session keeps a backlog-flush count. The separate integer expvar
`adaptermux_session_backlog_flushes_total` aggregates these threshold-triggered
flushes across sessions. It is not a per-session-labelled histogram bucket.
The latency histogram remains
`adaptermux_session_frame_latency_us_bucket_total`; do not insert a
`backlog_flushes` entry into it or mix counts of flushes with latency samples.

An ordering-driven flush before `STARTED` or `FAILED` alone does not increment
the backlog counter. Exceeding the symbol bound triggers the count; a result
delivered within that flush does not add another count. Diagnostics stay out
of the client event stream.

## 5. Implementation evidence

The companion [PR #1406](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/1406)
contains the session writer, the pacer's output-cadence reset, and synthetic
tests for the bound, steady-stream cadence, both arbitration outcomes, FIFO
delivery during a flush, and separation of the flush metric from the latency
histogram. This addendum changes the delivery guarantee only; the historical
version pages remain available for design traceability.
