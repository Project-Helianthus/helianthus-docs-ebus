# Frame-Atomic Visibility — SYN Padding and Timing Derivations

> Companion to `frame-atomic-visibility.md`. Status: design sketch.
> Branch: `frame-atomic-visibility` (multi-repo).


<!-- legacy-role-mapping:begin -->
> **Legacy terminology note.** This historical design doc was written before
> the canonical `initiator`/`target` rename completed across the docs corpus.
> Wherever you encounter `m`+`aster` or `sl`+`ave` in this file, read it
> as `initiator`/`target` respectively (per the legacy-role-mapping
> convention used throughout `helianthus-docs-ebus`). Live source code and
> new design docs use the canonical terms exclusively.

This document formalizes the per-session timing model that backs §3 and
§4 of the parent design. The parent doc states *what* the proxy emits;
this one states *exactly when, in what order, and based on which
measurements*. The intent is to be precise enough that an adversarial
reviewer can locate any unsoundness without re-deriving the math from
the parent doc's prose.

---

## 1. Notation

All quantities are in SI units unless otherwise stated. Time is wall
clock as observed on the proxy host.

| Symbol         | Meaning                                                                            | Typical range          |
|----------------|------------------------------------------------------------------------------------|------------------------|
| `T₀`           | wall-clock instant client A submits a write to the proxy                          | —                      |
| `L_up`         | wifi latency proxy → adapter (uplink), per transaction                            | 5–30 ms, spikes >100 ms |
| `L_dn`         | wifi latency adapter → proxy (downlink), per transaction                          | 5–30 ms, spikes >100 ms |
| `W_F`          | wire-time of telegram F on the physical bus                                       | 30–200 ms              |
| `N_F`          | byte count of telegram F (all phases: master + response + ACKs + terminator)      | 6–40 bytes             |
| `σ_global`     | transport-side wire-observed symbol-rate EMA (bytes/sec from adapter)             | 50–240 sym/s           |
| `σ_s`          | per-session symbol-rate EMA (bytes/sec drained to session s)                      | 5–240 sym/s            |
| `τ_byte_wire`  | nominal wire bit-time for one byte at 2400 baud                                   | 4.17 ms                |
| `τ_byte_s`     | per-session emission period per byte = 1 / `σ_s`                                  | 4.17–200 ms            |
| `α`            | EMA smoothing coefficient (applied per observation window)                        | 0.1–0.3                |
| `Δt_obs`       | observation window for instant-rate measurement                                   | 100–1000 ms            |
| `K_s`          | per-session telegram queue depth bound                                            | 4–16                   |

---

## 2. Symbol-rate estimators

### 2.1 Transport-side σ_global

Computed once on the adapter-facing side, shared by all sessions only
as a bootstrap reference (see §2.3). Updated every `Δt_obs`:

```
instant_global = bytes_received_from_adapter(Δt_obs) / Δt_obs
σ_global ← α · instant_global + (1 − α) · σ_global
σ_global clamped to [σ_min, σ_max]   where σ_min = 5, σ_max = 240
```

`σ_global` represents the actual rate at which symbols leave the wire
toward the proxy. It is the upper bound on what any session can
perceive — no session can see more symbols per second than the wire
delivered.

### 2.2 Per-session σ_s

Each cross-proxy session maintains its own EMA, driven by the rate at
which the proxy successfully drains bytes to that session's TCP
egress:

```
instant_s = bytes_emitted_to_session(Δt_obs) / Δt_obs
σ_s ← α · instant_s + (1 − α) · σ_s
σ_s clamped to [σ_min, σ_global]
```

The upper clamp at `σ_global` enforces the physical truth that the
session cannot observe a bus busier than the wire actually is. The
lower clamp prevents divide-by-zero in the pacing math (§4).

### 2.3 Bootstrap

At session connect time, the per-session EMA has no history. Seed:

```
σ_s(t = 0) ← σ_global(t = 0)
```

After bootstrap, σ_s diverges naturally as the session's actual drain
behaviour manifests. After ~3–5 EMA half-lives the per-session value
fully reflects per-session conditions and the bootstrap seed has
decayed out.

### 2.4 Why per-session is the right scope

A worked example: two sessions A and B observe the same bus.

  - Session A is on a fast loopback link. Effective drain rate = 240
    sym/s. σ_s_A → σ_global ≈ 115 sym/s (bounded by wire).
  - Session B is on a congested wifi link. Effective drain rate = 60
    sym/s. σ_s_B → 60 sym/s (drain-limited, below σ_global).

A and B should each see a bus density consistent with their own link
characteristics. A real ENS adapter on B's link would deliver bytes at
60 sym/s — both filler SYNs and telegram bytes alike. Per-session σ_s
reproduces this faithfully.

---

## 3. Latency estimators

### 3.1 L_dn

Measured from the proxy's own outbound exchanges with the adapter.
Existing ENH primitive `RequestInfo` returns a small fixed-size reply
the adapter computes locally (no wire activity). The round-trip is
therefore dominated by `L_up + L_dn`. With symmetry assumption:

```
L_dn_EMA ≈ (T_RequestInfo_reply − T_RequestInfo_sent) / 2
```

Refreshed periodically (e.g., every 30 s) and on transport reset. The
symmetry assumption is approximate but sufficient at SYN-period
resolution (~9 ms granularity at σ ≈ 115).

### 3.2 L_up (per transaction)

Measured per-transaction when the proxy itself originates a write
(token-holder mode). For an outbound first byte sent at `T_write_sent`,
the first echo arrives at `T_first_echo_arrival`. The end-to-end path
is `L_up + τ_byte_wire + L_dn`, so:

```
L_up_estimate(F) = T_first_echo_arrival − T_write_sent
                 − τ_byte_wire
                 − L_dn_EMA
```

Clamped at 0 (cannot be negative; on negative result, assume jitter
absorbed L_up to within measurement noise).

For cross-proxy sessions where THIS session was not the originator,
L_up still applies — but it is the L_up of WHOEVER originated the
telegram. The proxy attributes L_up to the originating session and
propagates it to all cross-proxy observers of the same telegram. (See
§4.2.)

### 3.3 L_up_EMA per-session

The proxy maintains `L_up_EMA[s]` for each session s, updated only on
transactions where s was the token holder. This is the value used as
the "L_up of telegrams originated by s" when computing prefix SYN
counts for other sessions observing s's telegrams.

```
L_up_EMA[s] ← α · L_up_estimate(F) + (1 − α) · L_up_EMA[s]
```

---

## 4. Prefix SYN count derivation

### 4.1 The geometric argument

Consider two cross-proxy observers, B-physical (hypothetical: B
connected directly to an adapter on the same bus) and B-cross-proxy
(actual: B connected through the proxy). Both observe the same
telegram F originated by session A.

B-physical's perceived idle period immediately before F's first
visible byte:

```
idle_before_F (B-physical) = (T_F_wire_start − T_F_prev_end)
                              + L_dn_B-physical
```

The wire was idle from the end of F-prev until A's first byte hit the
wire (at `T_F_wire_start = T₀_A + L_up_A`). B-physical sees this idle
window via its own adapter, length unchanged modulo its own L_dn.

B-cross-proxy's perceived idle period:

```
idle_before_F (B-cross-proxy) = (T_F_emit_start_B − T_F_prev_emit_end_B)
```

For B-cross-proxy to perceive the same idle gap as B-physical (which
is the transparency invariant of §0), the proxy must arrange for
`T_F_emit_start_B − T_F_prev_emit_end_B` to equal the wire-side idle
gap plus L_up_A.

The "plus L_up_A" component is precisely what is invisible in the
cross-proxy timing if no prefix SYNs are inserted: the proxy receives
the first byte of F at `T₀_A + L_up_A + L_dn`, but the wire idle
period actually started L_up_A earlier than that (during the wifi
uplink transit). B-cross-proxy cannot directly witness that gap and
the proxy must reproduce it synthetically.

### 4.2 Prefix count formula

The number of synthetic SYN bytes the proxy prepends to telegram F
when emitting to session s (where s did NOT originate F; if s did
originate F, see §6 below):

```
prefix_filler_count(F → s) = round( L_up_EMA[originator(F)] × σ_s )
```

with floor 0.

Worked example:
  - L_up_EMA[originator] = 18 ms
  - σ_s = 90 sym/s
  - prefix_filler_count = round(0.018 × 90) = round(1.62) = 2 SYNs

The use of σ_s (per-session, not σ_global) is deliberate: it produces
the same proportional idle window for the session, matched to its
density model. A slow session gets fewer prefix SYNs but proportional
to its slower clock.

### 4.3 Postfix accounting

There is no separate postfix count. Once telegram F's last byte is
emitted to session s, the idle generator (§5) resumes for session s
at rate σ_s. The "postfix" is just the natural continuation of the
inter-telegram idle stream.

If the next telegram F+1 starts before the idle generator has emitted
any filler byte to s, that's fine — F+1's emission begins
back-to-back, with F+1's own prefix accounting for the wifi uplink of
F+1's originator. There is no concept of "trailing padding" needed
after a telegram completes.

---

## 5. Idle generator

When session s has no active telegram emission in progress, the proxy
emits one synthetic SYN byte to s every `τ_byte_s = 1/σ_s` ms.

```
schedule_idle_byte(s, T) :
    emit SYN to session s at time T
    schedule next emission at T + τ_byte_s
```

Implementation: a per-session timer with period `τ_byte_s`, refreshed
when `σ_s` changes by more than X% (avoid timer thrash on small
fluctuations).

If a telegram becomes ready to emit during an idle interval, the
pending idle timer is cancelled, the telegram (with its prefix) is
emitted, and the idle timer is rearmed from the end of the telegram
emission.

---

## 6. Intra-telegram pacing

When telegram F is ready to emit to session s, the proxy schedules
each of its `N_F` bytes at:

```
T_byte_i(F, s) = T_F_emit_start + i × τ_byte_s
               where i ∈ [0, N_F − 1]
```

`T_F_emit_start` = wall-clock instant emission of the first byte of F
begins. This is precisely after the prefix SYNs (if any) have been
emitted.

Total emission time:

```
W_F_emit(s) = N_F × τ_byte_s = N_F / σ_s
```

Note `W_F_emit(s)` is NOT equal to `W_F` (the wire time on the actual
bus). On the wire, bytes flow at the bus baud rate (~240 sym/s for
contiguous bytes, but with inter-byte gaps the effective rate is
lower). On session s, bytes flow at `σ_s` which is the
session-perceived rate. The two can differ; the session sees its own
time-base, consistent with §0.

### 6.1 Originator visibility (token-holder case)

When session s IS the originator of F, s is in `token-holder` mode for
F and receives byte-level real-time visibility per §2 of the parent
doc. The pacing math of §6 above does NOT apply to s for this F; s
sees its own echoes byte by byte as they come back from the adapter.

The pacing math applies only to the OTHER sessions (the cross-proxy
observers of F).

---

## 7. Per-session emission queue

### 7.1 Structure

For each session s the proxy maintains:

  - `queue_s`: bounded FIFO of telegrams pending emission, capacity `K_s`.
  - `current_emission_s`: the telegram currently being paced out, plus
    a byte index of next byte to emit.
  - `idle_timer_s`: per-session timer for filler SYN generation.

### 7.2 Enqueue path

When the FSM (§5 of parent doc) reaches `DONE` for telegram F:

```
for each cross-proxy session s :
    if len(queue_s) == K_s :
        drop_oldest_telegram_from(queue_s)
        record_overflow_admin_event(s, F_dropped)
    enqueue F into queue_s with metadata { L_up_EMA[originator(F)], N_F }
```

### 7.3 Drain path

```
loop forever for each session s :
    if current_emission_s is in progress :
        emit next byte at scheduled time
        if telegram fully emitted, set current_emission_s = None
        continue
    if queue_s is non-empty :
        dequeue F
        emit prefix_filler_count(F → s) SYN bytes (paced at τ_byte_s)
        set current_emission_s = (F, byte_index=0)
        continue
    # nothing to emit: idle generator runs at τ_byte_s
    wait until next idle tick
    emit SYN to session s
```

### 7.4 Drop policy

Telegram drops are always whole-telegram and oldest-first, justified
in §9.4 of the parent doc. The admin-channel `OVERFLOW` record carries
session id, telegram identifier, timestamp; no in-stream notice.

---

## 8. Worked numerical examples

### Example A — fast loopback session

  - Session A on Unix domain socket. σ_s_A = σ_global = 115 sym/s.
  - L_up_EMA[originator] = 12 ms.
  - Telegram F: B5 24 read-by-register, N_F = 22 bytes.

```
τ_byte_A           = 1 / 115 ≈ 8.7 ms
prefix_filler_count = round(0.012 × 115) = round(1.38) = 1 SYN
W_F_emit(A)         = 22 / 115 ≈ 191 ms

emission timeline for A:
  T_F_emit_start (relative)            : 0 ms
  prefix SYN 1                          : 0 ms
  telegram byte 0                       : 8.7 ms
  telegram byte 1                       : 17.4 ms
  …
  telegram byte 21                      : 191.4 ms
  idle generator resumes                : 200.1 ms
```

### Example B — slow congested session

  - Session B on a high-latency WiFi-bridged TCP link.
  - σ_s_B = 60 sym/s (drain-limited).
  - L_up_EMA[originator] = 12 ms (same telegram from same originator).
  - Same telegram F, N_F = 22 bytes.

```
τ_byte_B            = 1 / 60 ≈ 16.7 ms
prefix_filler_count = round(0.012 × 60) = round(0.72) = 1 SYN
W_F_emit(B)         = 22 / 60 ≈ 367 ms

B's view of the bus is slower — telegrams take longer to emerge, idle
intervals stretch by the same factor. A real ENS adapter delivering to
B over its slow link would look identical.
```

### Example C — extreme jitter

  - Session C, same as A's link but bus is mid-burst.
  - σ_global momentarily spikes to 200 sym/s (heavy traffic period).
  - σ_s_C EMA lags, sits at 130 sym/s.
  - L_up spike measured at 80 ms for this transaction (wifi glitch).

```
prefix_filler_count = round(0.080 × 130) = round(10.4) = 10 SYNs
```

The prefix grows large to absorb the unusually long wifi uplink. The
client sees 10 filler SYNs immediately preceding the telegram, which
matches what a physical observer would have seen on the wire during
the L_up window.

---

## 9. Invariants the model must preserve

The math is correct if and only if the following invariants hold at
all times for every cross-proxy session s:

  - **I1 (rate):** The long-term rate of bytes emitted to s equals
    `σ_s`, including filler SYNs and telegram bytes.
  - **I2 (telegram order):** Telegrams are delivered to s in completion
    order (the order in which FSM reached `DONE` for them).
  - **I3 (no inter-leave):** A telegram's bytes are emitted
    contiguously to s — no filler SYN or other telegram bytes
    interpose mid-telegram.
  - **I4 (proxy invisibility):** Diagnostic events, drops, overflows,
    and proxy errors are NEVER emitted in the session byte stream.
  - **I5 (causal):** A byte attributable to telegram F is never emitted
    to s before F reached `DONE` on the proxy FSM.
  - **I6 (bounded buffering):** Per-session memory is `O(K_s × N_F_max)`,
    a small constant.

If any of I1–I6 is violated, the design is wrong, not the
implementation.

---

## 10. Known approximations

These are deliberate simplifications. Each is listed with the
worst-case error it introduces.

| Approximation                                       | Worst-case error                                | Acceptable because                                  |
|-----------------------------------------------------|-------------------------------------------------|----------------------------------------------------|
| L_dn symmetric with L_up                            | ±5 ms on L_up estimate                          | below 1 SYN at σ = 115                              |
| EMA-smoothed σ_s rather than instantaneous          | session-perceived density lags real density     | intentional — clients prefer stable view            |
| τ_byte_s constant within a telegram                 | jitter not modeled per byte                     | telegrams are short (<200 ms); jitter averages out  |
| Single L_up_EMA per originator                      | per-telegram L_up may differ from EMA           | smoothing across telegrams is the point             |
| Prefix only, no postfix                             | inter-telegram idle slightly off if back-to-back | next telegram's prefix handles it                   |

<!-- legacy-role-mapping:end -->
