# Frame-Atomic Visibility v5 — Active-Phase FSM Filter, Idle Pass-Through

> Status: design sketch v5. Supersedes v1, v2, v3, v4. Branch: `frame-atomic-visibility` · Date: 2026-05-18


<!-- legacy-role-mapping:begin -->
> **Legacy terminology note.** This historical design doc was written before
> the canonical `initiator`/`target` rename completed across the docs corpus.
> Wherever you encounter `m`+`aster` or `sl`+`ave` in this file, read it
> as `initiator`/`target` respectively (per the legacy-role-mapping
> convention used throughout `helianthus-docs-ebus`). Live source code and
> new design docs use the canonical terms exclusively.

## 1. Convergent findings from v4 review that v5 must resolve

Codex and Opus both returned `major-rethink` on v4 with overlapping findings:

  - Cadence threshold at **proxy receive time** cannot distinguish wire-real fast SYNs from adapter-spurious AA. TCP batching plus normal Vaillant master cadence (~21 ms) breaks the 25 ms heuristic both ways.
  - The AA-aware escape decoder's **10 ms time window** loses legitimate escape pairs under WiFi jitter; widening loses the converse case.
  - **postGrantPreEcho deletion scope is wrong** — it lives in `helianthus-ebusgo/transport/enh_transport.go` and is consumed by direct-adapter clients (no proxy), not deletable by a proxy-side change.
  - **FSM consensus framing as "backstop"** misrepresents the architecture; proxy and active-client FSMs are autonomous observers of the wire, not master/slave.
  - **Initial L_dn hard timeout false positive** during the first 30 s after a degradation onset; tracking-all-samples doesn't help convergence speed.
  - **Pacer algorithm bug** (Codex unique): `last_emit_time` doesn't update until first byte fires, so queued bursts all schedule for the same timestamp → bursts arrive unspaced at the client.
  - **`passive_reconstructor` referenced location is wrong** (`helianthus-ebusgo/protocol/` vs actual `helianthus-ebusgateway/internal/adaptermux/passive_transaction_reconstructor.go`), and active-mode classification is new code, not pure refactor.
  - **Slave-phase classifier** has no value to match against (slave bytes are wire-driven, proxy doesn't know what to expect) → AA-injection in SLAVE_DATA falls through unfiltered.
  - **Per-state FSM timeouts unspecified.**

v5 resolves these by tightening scope and dropping two ideas v4 still carried from earlier rounds.

## 2. v5 scope — what's in, what's out

**In v5:**

  - The proxy maintains an active-session FSM that handles AA-injection filtering **only during phases where the active client is the initiator** (MASTER_HEADER through WAIT_MASTER_ACK and the slave-response phases that follow it). During these phases the proxy knows what bytes the client wrote and can FIFO-match.
  - The proxy maintains an AA-aware escape decoder with a count-bounded (no time-bounded) injection absorber.
  - The proxy paces outbound bytes to **every** client uniformly at a `τ_wire_byte` cap.
  - L_dn EMA bootstraps to a conservative value and is updated per-byte from each echo's measured round-trip.
  - NACK retransmit cap enforced via FSM state.

**Out of v5:**

  - **IDLE-state filtering.** v5 forwards every byte the adapter delivers when the FSM is in IDLE. Wire-real idle SYNs and adapter-spurious AA in idle are indistinguishable at the proxy without wire-time information that we don't have. Honest residual.
  - **Cross-FSM consensus protocol.** v5 reframes the FSMs (proxy, active client, passive observers) as autonomous. They observe the same wire-derived event stream and reach the same state by construction; RESETTED is the only resync signal needed.
  - **Telegram-atomic emission.** Bytes are forwarded as they're classified; no buffering for batch emission.
  - **Scope-violating deletions.** `postGrantPreEcho` is owned by the direct-adapter transport (`helianthus-ebusgo/transport/enh_transport.go`) and stays. v5 only deletes proxy-side gates that the new classifier subsumes.

This is the core scope reduction from v4. The reviewer-flagged ambiguities in v4 evaporate when each sub-problem is solved at exactly the layer that has the necessary information, not at the layer where the intent originated.

## 3. The FSM

Same mermaid as v4 §3 (omitted here for brevity; canonical copy in
`frame-atomic-visibility-v4.md`). Two changes from v4:

  - `IDLE` state has **no filtering rules**. Every received byte during IDLE is forwarded to all sessions. This is the central scope reduction.
  - Per-state timeouts pinned from eBUS V1.3.1 spec:
    - `MASTER_HEADER`, `MASTER_DATA`, `SLAVE_LENGTH`, `SLAVE_DATA`: inter-byte timeout 6.7 ms (≈10 bit times worst-case wire spec).
    - `WAIT_MASTER_ACK`, `WAIT_SLAVE_ACK`: 12.5 ms (slave turnaround window).
    - `WAIT_TERMINATOR_SYN`: 100 ms (allows up to two missed AUTO-SYN slots before declaring abandon).
    - Slave-response-start (ACK → SLAVE_LENGTH transition): 50 ms (typical load tolerance).
    - Per-state timeouts measured against monotonic clock; on expiry, FSM aborts to IDLE.

## 4. Classifier — active phases only

```
classify(ev: ENHEvent, fsm_state: FSM):
  if fsm_state == IDLE or fsm_state == ARBITRATING:
    # Forward unconditionally; no AA filtering possible without
    # wire-time information.
    return FORWARD_TO_ALL

  if fsm_state in (MASTER_HEADER, MASTER_DATA, MASTER_CRC):
    # Active client is writing; staging holds expected bytes.
    expected = staging.peek()  # logical (value, was_escaped) tuple
    if ev.matches(expected):
      staging.pop()
      fsm.advance()
      return FORWARD_TO_ALL
    elif ev.value == 0xAA and ev.was_escaped == false:
      # AA-injection from adapter buffer interference.
      return DROP_AA_INJECTION
    else:
      return PROTOCOL_FAULT

  if fsm_state in (WAIT_MASTER_ACK, WAIT_SLAVE_ACK):
    # ACK phase; expect 0x00 (ACK) or 0xFF (NACK), nothing else.
    if ev.value in (0x00, 0xFF):
      fsm.advance_per_ack_value(ev.value)
      return FORWARD_TO_ALL
    elif ev.value == 0xAA and ev.was_escaped == false:
      return DROP_AA_INJECTION
    else:
      return PROTOCOL_FAULT

  if fsm_state in (SLAVE_LENGTH, SLAVE_DATA, SLAVE_CRC):
    # Slave is writing; proxy does NOT know slave's payload values.
    # Filter the one ambiguous byte (raw 0xAA) — slave does not
    # legitimately emit raw 0xAA mid-frame (it escape-encodes payload
    # 0xAA as 0xA9 0x01). Any raw 0xAA in mid-slave-frame is either
    # adapter buffer artifact or a premature terminator (protocol
    # fault on the slave side, indistinguishable from proxy view).
    if ev.value == 0xAA and ev.was_escaped == false:
      return DROP_AA_INJECTION
    fsm.advance()  # counter-based, value-agnostic
    return FORWARD_TO_ALL

  if fsm_state == WAIT_TERMINATOR_SYN:
    if ev.value == 0xAA and ev.was_escaped == false:
      fsm.advance_to_IDLE()
      return FORWARD_TO_ALL  # terminator IS the SYN, forward it
    return PROTOCOL_FAULT  # any other byte mid-terminator-wait

  # Transient FSM states (MASTER_RETX, SLAVE_RETX, ABORTED_NACK)
  # handled by FSM internal transitions.
```

The key insight: the classifier filters raw 0xAA bytes in ALL non-IDLE
phases. This is sound because:

  - **Master phases:** raw 0xAA only legitimate as terminator. If we're in MASTER_*, terminator hasn't arrived yet, so raw 0xAA mid-master is AA-injection.
  - **ACK phases:** legitimate values are 0x00 or 0xFF only; raw 0xAA is AA-injection.
  - **Slave phases:** payload 0xAA arrives as escape-decoded `(0xAA, was_escaped=true)`; raw 0xAA mid-slave is AA-injection or premature terminator.
  - **WAIT_TERMINATOR_SYN:** raw 0xAA IS the terminator we're waiting for; forward and advance.

This resolves v4's F-v4-9 (slave-phase classifier without predicted value): we filter the **one ambiguous byte** (raw 0xAA), not the entire stream. We don't need to know slave payload values.

## 5. AA-aware escape decoder — count-bounded, no time window

```
[NORMAL]
  on byte b:
    if b == 0xA9: state := ESCAPE_PENDING; absorbed_count := 0
    elif b == 0xAA: emit (0xAA, was_escaped=false)
    else: emit (b, was_escaped=false)

[ESCAPE_PENDING]
  on byte b:
    if b == 0x01: emit (0xAA, was_escaped=true); state := NORMAL
    elif b == 0x00: emit (0xA9, was_escaped=true); state := NORMAL
    elif b == 0xAA and absorbed_count < 8:
      # AA-injection within escape pair. Absorb; stay ESCAPE_PENDING.
      absorbed_count += 1
    elif b == 0xAA and absorbed_count >= 8:
      # 8 consecutive AA absorptions — the wire is genuinely broken
      # or this isn't really an escape sequence.
      emit (0xA9, was_escaped=false)
      state := NORMAL
      # process this 0xAA in NORMAL state:
      emit (0xAA, was_escaped=false)
    else:
      # Genuinely malformed escape — emit 0xA9 as raw, then process b.
      emit (0xA9, was_escaped=false)
      state := NORMAL
      recurse on b
```

No time window. The bound is **8 consecutive AA absorptions** before declaring escape failure. At ~4 ms wire-byte time, 8 AAs = 32 ms of wire activity — more than the slow-slave window, more than realistic adapter buffer drain. If 8 AAs land between `0xA9` and the completion byte, something is genuinely wrong.

This resolves both v4's F-v4-2 (10ms window loses legitimate pairs under jitter) and the counter case (multiple AAs in pair window).

## 6. Pacer — corrected algorithm

```
PER-SESSION pacer state:
  last_scheduled_emit: monotonic time (initially -infinity)
  emit_queue: FIFO of bytes

enqueue(b):
  emit_at = max(now(), last_scheduled_emit + τ_wire_byte)
  emit_queue.push((b, emit_at))
  last_scheduled_emit = emit_at
  if no pacer timer is armed:
    arm_timer(emit_at)

on pacer_timer_fire:
  (b, scheduled) = emit_queue.pop_oldest()
  write_to_session_socket(b)
  if queue not empty:
    arm_timer(queue.head.emit_at)
```

The fix from v4: `last_scheduled_emit` is updated **on enqueue**, not on fire. This means each new byte's `emit_at` is correctly chained from the prior byte's scheduled time, not from whatever the last-actual-emit was. Bursts get correctly spaced.

`τ_wire_byte = 4.17 ms` (2400 baud, 10 bits per byte). All sessions paced uniformly, **including the originator**, eliminating v4's F-v4-5 timing asymmetry.

The pacer is rate-LIMITING: if real bytes arrive slower than 4.17 ms apart (e.g., wire idle SYN at 35 ms cadence), the pacer's `max(now, last_scheduled + τ_byte)` falls back to `now()` and emission is immediate. Natural gaps preserved.

## 7. L_dn — bootstrap conservative, update per byte

```
L_dn_EMA initial = 50 ms     # generous bootstrap; covers WiFi typical
                              # round-trip without false hard timeouts
α = 0.3                       # faster convergence than v4's 0.15

per-byte L_dn measurement:
  on each FSM-classified ECHO_OF_OWN_WRITE event:
    L_dn_sample = T_received_at_proxy - T_sent_to_adapter
                  - τ_byte_wire   # rough wire transit estimate
    if L_dn_sample in [2 ms, 1000 ms]:
      L_dn_EMA = α * L_dn_sample + (1-α) * L_dn_EMA

echo deadlines:
  soft = L_dn_EMA + 100 ms     # log only
  hard = 4 * L_dn_EMA + 200 ms # drop staging, log ADAPTER_DEGRADED

  initial values (L_dn=50 ms):
    soft = 150 ms
    hard = 400 ms

  if L_dn rises to 200 ms (sustained):
    soft = 300 ms
    hard = 1000 ms
```

Per-byte measurement means EMA converges within ~3-5 bytes of any
shift (vs. v4's 30 s RequestInfo cadence). The 50 ms bootstrap and
α=0.3 also mean initial hard timeout is 400 ms — well above typical
echo times — eliminating v4's F-v4-4 first-window false positive.

If L_dn jumps to 500 ms sustained, hard timeout converges to 2200 ms
within ~4 echo cycles (~50 ms of bus activity). Real bytes don't get
dropped because the timeout catches up faster than the degradation.

## 8. FSM autonomy — no consensus protocol

Three FSMs may exist concurrently:

  - **Proxy's FSM** for each active session.
  - **Active client's FSM** (gateway's existing one in `helianthus-ebusgo/protocol/bus.go`).
  - **Passive observer's FSM** (`helianthus-ebusgateway/internal/adaptermux/passive_transaction_reconstructor.go`), one per passive client.

Each FSM observes a wire-derived event stream from its own vantage:

  - Proxy: events directly from adapter, with L_dn=L_dn_proxy_adapter.
  - Active client: events forwarded by proxy (or directly from adapter in non-proxy paths), with L_dn=L_dn_proxy_adapter + L_dn_proxy_client.
  - Passive observer: events forwarded by proxy, with similar latency.

**They are autonomous.** Each FSM independently transitions based on its observed events. No coordination protocol exists.

**Misalignment cases and recovery:**

  - **Same wire, different observed events:** impossible by construction. The proxy forwards all classified `FORWARD_TO_ALL` events to all observers identically. The same FSM logic on the same events produces the same state.
  - **One FSM aborts on timeout, others don't:** the FSM with the shorter timeout aborts to IDLE. Others continue. The proxy's classification continues per its own FSM state. If an active client's FSM is in WAIT_MASTER_ACK and the proxy's FSM is in IDLE (post-abort), the next bytes arrive at the active client in WAIT_MASTER_ACK context — but the bytes are wire-real (forwarded by proxy because proxy is in IDLE which means no filtering). Active client's deadline tracking fires, it aborts independently. Both reach IDLE; recovery complete.
  - **RESETTED event:** forwarded to all observers by the proxy as a real adapter event. All FSMs transition to IDLE. Hard resync.
  - **A non-conforming client emits unexpected bytes:** proxy's FSM detects PROTOCOL_FAULT; reports via admin channel; proxy emits ENH FAILED to that specific client (a real, observable adapter-level error). Other observers see the bytes the proxy already forwarded before the fault; they may also detect fault via their own FSM.

The "proxy backstop" framing from v4 was wrong. v5 frames it correctly: each FSM is a witness, not a controller. RESETTED is the only state-coordination primitive.

This resolves v4's F-v4-1 and F-v4-6.

## 9. PROTOCOL_FAULT contract

When the classifier returns PROTOCOL_FAULT:

  - Toward the **originator** (active session whose write produced the fault): emit `ENH RESETTED` event on the originator's connection. This is a defined ENH-protocol event; receiving clients (gateway, ebusd) treat it as a transport-layer reset and recover via their own FSM's RESETTED-handling.
  - Toward **other sessions:** forward whatever bytes the proxy already classified before the fault. The fault doesn't propagate to non-originator clients in the byte stream (their FSMs may detect the same fault from the wire-real bytes they see).
  - Admin channel: log `PROTOCOL_FAULT` with originator session id, FSM phase, offending byte.

This resolves v4's F-v4-Codex MINOR ("no delivery contract for protocol faults").

`ENH RESETTED` is a real, defined ENH-protocol event — not a proxy-synthesized one. The proxy issues it because the adapter would have issued one in the same situation (RESETTED is the adapter's transport-reset signal). I1 invariant ("no synthetic events") is preserved because RESETTED IS something the adapter would emit on protocol fault.

## 10. NACK retransmit cap — silent drop becomes admin event

v4's design silently dropped client retransmits beyond the cap. v5
makes the drop observable via admin channel AND surfaces an error to
the offending client:

  - On NACK count reaching 2: FSM transitions to `ABORTED_NACK`.
  - Subsequent bytes from same active session in same telegram: NOT forwarded to adapter, NOT silently dropped. Instead: TCP-receive side returns to a per-session "telegram-aborted" state, where any further writes from the client are rejected with explicit `EPIPE`-equivalent at the client's TCP socket (write fails). Client's TCP layer surfaces the error.

This resolves v4's F-v4-6 silent-drop class.

## 11. Layer boundaries — escape decoder explicitly

The escape decoder is a **new sub-component** added to the proxy's
ENH-receive path, NOT a modification of `southbound/enh/codec.go`'s
existing event-emitting logic. Specifically:

```
adapter →[ENH transport bytes]→ codec.go (parses ENH framing) →
   [eBUS escape-encoded bytes] → escape_decoder.go (NEW) →
      [(value, was_escaped) tuples] → FSM classifier (NEW) →
         [classified events] → per-session emission
```

The existing `codec.go` event types stay; the new decoder consumes
the payload bytes and produces a new event type for downstream
consumers. Old consumers of `codec.go` continue to receive
escape-encoded bytes if they need them.

This resolves v4's F-v4-7 layer-boundary critique.

## 12. Scope of deletions

After v5 lands and is validated:

  - Delete from `helianthus-ebusgo/protocol/bus.go`: round-9 `payloadAaAutoSyn*` absorb loop and atomic counters (the active-client side now sees clean echoes from proxy, no absorb needed).
  - Delete from `helianthus-ebusgateway/internal/adaptermux/mux.go`: round-7 `betweenWritesSyn` gate, `queueJustDrained` sentinel.
  - **Do NOT delete** `postGrantPreEcho` from `helianthus-ebusgo/transport/enh_transport.go`. This is direct-adapter transport logic, used by paths that don't go through the proxy. Out of v5's scope.

This resolves v4's F-v4-10 scope-overreach.

## 13. Invariants

  - **I0** (clock): all scheduling on monotonic time.
  - **I1** (no synthetic events): every byte and ENH event forwarded was derived from a real adapter event. `ENH RESETTED` issued on protocol fault is a real ENH-defined event the adapter would issue. Admin channel is NOT part of the byte stream.
  - **I2** (active-phase AA filter): in non-IDLE non-ARBITRATING FSM states, raw 0xAA bytes (was_escaped=false) that don't match expected wire role are dropped. Other bytes forwarded.
  - **I3** (idle pass-through): in IDLE and ARBITRATING states, all bytes forwarded. No filtering, no cadence checks.
  - **I4** (escape decoder): the decoder absorbs up to 8 consecutive AA bytes mid-escape-pair before declaring escape failure.
  - **I5** (pacer correctness): outbound bytes to a session are emitted with `inter-byte gap ≥ τ_wire_byte = 4.17 ms`. Bursts queued faster than this are spread by the pacer using `last_scheduled_emit` accounting.
  - **I6** (FSM autonomy): each FSM instance is independent. Coordination happens only through wire-real events (RESETTED, STARTED, FAILED). No out-of-band sync.
  - **I7** (retx cap): FSM transitions to ABORTED_NACK at retx_count=2; subsequent client writes are rejected at TCP receive with EPIPE.
  - **I8** (memory): per-session FSM + staging + pacer queue ≤ 500 bytes. Total proxy memory O(N × 500) for N sessions.

## 14. What v5 still does not solve

Honest residuals:

  - **Adapter-spurious AA visible during IDLE state.** When no active session is writing, the proxy cannot distinguish adapter-injected AA from wire-real AUTO-SYNs. Both forwarded. Operational impact: clients see occasional extra AA bytes during idle stretches. ebusd handles this natively (its SYN parser tolerates AUTO-SYN cadence variance). vrc-explorer doesn't care (it's not real-time-stream-sensitive).
  - **Inter-session timing skew on different TCP links.** Two clients on links with different L_dn see the same wire byte at slightly different wall-clock times. Inherent to TCP; same as if they were on physically separate adapters with different network paths.
  - **Wire-spec violations (malformed eBUS from third-party master).** Proxy forwards what wire emitted; doesn't try to repair.
  - **Adapter byte loss after physical transmission.** If adapter emits on wire but its reply path drops, proxy doesn't see it. Same residual as if the client had its own adapter on the same bus.

## 15. Migration path

  1. Add escape decoder (new file in `helianthus-ebus-adapter-proxy/internal/southbound/enh/escape_decoder.go`).
  2. Add FSM-per-active-session in proxy (new file; uses logic shared with `passive_transaction_reconstructor.go`).
  3. Implement pacer per §6 algorithm.
  4. Implement L_dn EMA per §7.
  5. Wire classifier per §4.
  6. Live-bus validation: AA-injection metric for active-write phases → 0; cross-client telegram parsing coherent; IDLE-state AA forwarding doesn't break ebusd SYN watchdog.
  7. Delete round-9 (`bus.go`) and round-7 (`mux.go`) layers; verify no regression.
  8. NOT touching `postGrantPreEcho`; it stays.

Each step independently testable and rollback-able. No big-bang migration.

## 16. Summary mapping

| v4 finding | v5 resolution |
|---|---|
| F-v4-1 FSM consensus | §8: FSMs are autonomous, RESETTED is only resync. |
| F-v4-2 Escape decoder 10ms window | §5: count-bounded (8 AAs), no time window. |
| F-v4-3 25ms cadence threshold | §2, §3 IDLE: drop IDLE filter entirely. |
| F-v4-4 L_dn convergence | §7: bootstrap 50ms, per-byte measurement, α=0.3. |
| F-v4-5 Originator timing skew | §6: pacer applies to all sessions including originator. |
| F-v4-6 NACK silent drop | §10: ABORTED_NACK → TCP write rejected with EPIPE, admin event logged. |
| F-v4-7 Escape decoder layer | §11: new sub-component, doesn't modify existing codec.go. |
| F-v4-8 Per-state timeout unspec | §3: pinned from spec. |
| F-v4-9 Slave-phase classifier | §4: filters raw 0xAA in all non-IDLE non-WAIT-TERMINATOR states; value-agnostic FSM advance. |
| F-v4-10 postGrantPreEcho scope | §12: NOT deleted. |
| F-v4-11 Admin channel vs I1 | §13 I1: explicit carve-out for admin channel. |
| Codex pacer queued-burst | §6: `last_scheduled_emit` updated on enqueue. |
| Codex terminator vs idle cadence | §2: no IDLE cadence filter at all. |
| Codex passive_reconstructor location | §8: corrected to `helianthus-ebusgateway/internal/adaptermux/passive_transaction_reconstructor.go`. |
| Codex PROTOCOL_FAULT contract | §9: ENH RESETTED to originator + admin event. |

<!-- legacy-role-mapping:end -->
