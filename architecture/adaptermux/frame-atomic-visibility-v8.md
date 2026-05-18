# Frame-Atomic Visibility v8 — Surgical Fixes to v7

> Status: design sketch v8. Surgical fixes per round-7 split-verdict.
> Branch: `frame-atomic-visibility` · Date: 2026-05-18

Round 7 verdicts:
  - **Opus: minor-fixes** ("design has converged"); 1 BLOCKER (§1.2 prose) + 1 MAJOR (§1.4 ESCAPE_PENDING bound) + 4 minors.
  - **Codex: major-rethink** with 1 "irreducible blocker" (§1.3 byte ordering) + 7 majors + 4 minors.

v8 applies the surgical fixes both reviewers converged on, plus Codex's unique blocker (real correctness bug, not architecture). It preserves v7's structural design entirely.

## 1. Fixes applied

### 1.1 [Codex IRREDUCIBLE] §1.3 byte ordering — classify under CURRENT phase, then transition

**v7 bug:** Per-byte algorithm in v7 §1.3:
```
for each byte b:
    fsm.feed(b)              # may transition phase
    classify_under(fsm.mode_after_feed, b)
```
This classifies the byte under the POST-transition phase. Example failure: WAIT_MASTER_ACK byte 0x00 (the ACK) advances FSM to SLAVE_LENGTH, then we classify 0x00 under SLAVE_LENGTH (treating it as NN'=0, a zero-length response). The byte was meant to be an ACK, not a length field.

**v8 fix:** classify first, then transition:
```
for each byte b:
    current_phase = fsm.current_phase
    decision = classify_under(current_phase, b)
    apply_decision(decision, b)   # forward/drop/fault
    if decision == FORWARD_TO_ALL or decision == ECHO_OF_OWN_WRITE:
        fsm.consume_byte_in_current_phase(b)
        # consume may complete a phase boundary; transition fires only after consumption:
        if phase_complete(current_phase, b):
            next_phase = fsm.compute_next_phase(current_phase, b)
            fsm.transition_to(next_phase)
```

The byte is interpreted under the phase that expected it. The transition is a consequence of the byte's interpretation, applied AFTER classification commits.

Updated invariant **I9 (v8)**: "Per byte: classify under current phase → forward/drop per classification → if classification was forward/echo, consume byte in current phase → if phase boundary is reached, transition to next phase. All four steps execute atomically within a single goroutine per session."

Special case for IDLE→PASSIVE_TRACKING entry: the entering byte is the FIRST byte of MASTER_HEADER. It is classified under PASSIVE_TRACKING/MASTER_HEADER (not under IDLE), because IDLE has no "what to do with this byte" rule beyond "trigger transition". This is the one phase transition that fires on the byte itself rather than after consumption.

### 1.2 [Opus BLOCKER + Codex MAJOR] §1.2 PASSIVE_TRACKING entry — first-non-SYN is primary, FAILED is rare

**v7 prose:** "ENH adapters surface foreign-arbitration via FAILED(winner_addr) control events that arrive BEFORE the first data byte."

**Both reviewers verified (independently) against ENH spec:** FAILED fires only as response to our own arbitration request, not for foreign-initiator arbitrations where we weren't competing. v7 inverted the architecture under a false premise.

**v8 fix:** Re-order primary/fallback in §1.2:

```
IDLE → PASSIVE_TRACKING entry rule (v8):

  Primary path: first non-SYN byte from adapter when no STARTED-for-us
    is in flight. The byte IS the foreign initiator's QQ. Classify it
    under PASSIVE_TRACKING/MASTER_HEADER byte_index=0.

  Contention edge case: if we happened to issue a START at the same
    moment a foreign initiator won arbitration, ENH adapter emits
    FAILED(winner_addr). Use winner_addr as a validation hint for
    the subsequent QQ byte (validate QQ == winner_addr; on mismatch,
    PROTOCOL_FAULT).

  Most foreign telegrams arrive via the primary path. FAILED-driven
  validation is a sanity check for contention scenarios only.
```

This corrects the prose without changing implementation: §1.6's winner_addr validation rule still applies opportunistically when FAILED was observed. The dominant flow uses the byte itself as entry signal.

### 1.3 [Both MAJOR] §1.4 ESCAPE_PENDING duration bounded

**v7 issue:** Inter-byte timer paused during ESCAPE_PENDING, but ESCAPE_PENDING itself has no max duration. Decoder can sit in ESCAPE_PENDING indefinitely if transport stops delivering bytes.

**v8 fix:** explicit hard cap of 32 ms wall-clock on ESCAPE_PENDING:

```
[ESCAPE_PENDING]
  T_a9_seen = T (monotonic clock)

  on byte b:
    if T_now - T_a9_seen > 32 ms:
      # ESCAPE_PENDING timeout — drop the 0xA9 and absorbed AAs.
      # No emission to classifier; admin log only.
      admin.log("escape_pending_timeout", duration=T_now-T_a9_seen)
      state := NORMAL
      # Re-process current byte b in NORMAL state to preserve it
      # for next-byte resync (chosen over drop-b for data preservation).
      goto NORMAL with input b

    elif b == 0x01: emit (0xAA, was_escaped=true); state := NORMAL
    elif b == 0x00: emit (0xA9, was_escaped=true); state := NORMAL
    elif b == 0xAA and absorbed_count < 8:
      absorbed_count += 1
    else:
      # Malformed escape OR 8 absorptions reached → admin log, emit
      # nothing, state := NORMAL.
      admin.log("escape_decoder_recovery", details)
      state := NORMAL
```

The 32 ms bound is `8 × τ_wire_byte` (the maximum theoretically achievable absorption window) extended slightly for jitter tolerance. Beyond 32 ms, the wire is genuinely broken; better to abandon and let downstream FSM detect protocol fault.

Updated invariant **I4 (v8)**: "Escape decoder budget: absorb up to 8 AAs OR wait up to 32 ms wall-clock in ESCAPE_PENDING, whichever comes first. On either bound: emit nothing, admin log, return to NORMAL state. Inter-byte timer for the classifier-level FSM is paused during ESCAPE_PENDING and resumes from decoded-byte emission."

### 1.4 [Codex MAJOR] §1.7 abandon passive L_rtt sampling

**v7 attempt:** Sample L_rtt during PASSIVE_TRACKING by computing `T_received - (previous_wire_byte_estimate + τ_wire_byte)`.

**Codex correctly identifies:** This estimate includes foreign-initiator inter-byte gaps, target think time, OS/TCP jitter, adapter buffering. Cannot separate link latency from foreign-side cadence variability without adapter wire timestamps (which we don't have). Poisons the EMA.

**v8 fix:** Abandon passive sampling entirely. L_rtt is measured ONLY during active mode (echoes of our own writes). For long idle stretches:

```
v8 L_rtt regime:

  Bootstrap on connect: L_rtt_EMA = 100 ms (conservative).
  α = 0.3.
  Per-byte measurement during ACTIVE mode only: round-trip via echo.
  No measurement during PASSIVE_TRACKING.
  
  On entry to ACTIVE mode after long IDLE (>30 s without active write):
    Use a GRACE_BOOTSTRAP period for the first 3 echoes of the new
    write. During grace, no hard timeout fires — only soft timeout
    (log to admin). After 3 grace samples, L_rtt_EMA has converged
    enough to enable hard timeouts.
```

Echo deadlines:
  - **Grace mode (first 3 echoes after long idle):** soft = `L_rtt_EMA + 500 ms` (very loose); hard disabled.
  - **Normal mode:** soft = `L_rtt_EMA + 100 ms`; hard = `2 × L_rtt_EMA + 200 ms`.

This eliminates Codex's MAJOR §1.7 concern without sacrificing the bootstrap-from-stale issue Opus F-v7-2 raised.

### 1.5 [Codex MAJOR] §1.10 Step A spec citation

**v7 said:** "200 ms is the spec V1.3.1 timeout."

**Codex couldn't find this in spec text.** Honest acknowledgement: 200 ms WAIT_MASTER_ACK is an engineering choice, not strictly mandated by V1.3.1. The spec specifies "respond within AUTO-SYN slot" (which is ~35-45 ms on a healthy bus). 200 ms accommodates slow targets up to ~5× the AUTO-SYN cadence — a defensible engineering choice for tolerance, but not "spec-mandated."

**v8 fix:** Updated §1.10 text:

```
WAIT_MASTER_ACK timeout = 200 ms (engineering choice, not spec-mandated).
Rationale: per spec, the target should respond within the AUTO-SYN slot
(~35-45 ms). 200 ms accommodates targets up to ~5× that envelope while
still bounding stuck-target detection. Gateway-side bus.go aligned to
the same value for FSM coherence.

Step A acceptance criteria:
  - Telegram-completion rate may IMPROVE (latency-class errors hidden
    behind the longer window). Improvement is acknowledged as a
    relaxation artifact, not a pass/fail gate.
  - Pass/fail gate: no NEW error classes appear; pre-existing error
    classes (echo_mismatch, collision, nack) maintain or reduce.
  - Specific tests: scan duration bound, no-ACK behavior, slow-ACK
    (target responding at 100ms), NACK retry sequence, multi-initiator
    contention.
```

This makes the migration step verifiable and avoids the "false positive of improvement" Opus F-v7-5 warned about.

### 1.6 [Codex MAJOR] §1.5 AA-injection filter coverage across all active phases

**Codex finding:** v7's §1.5 retx walk only spells out AA filter in WAIT_MASTER_ACK; retransmitted MASTER_HEADER/DATA/CRC, SLAVE_RETX phases need same provenance-aware SYN policy.

**v8 fix:** explicit in §4 + §1.6:

```
AA-injection filter applies in ALL active and passive non-IDLE phases:
  MASTER_HEADER, MASTER_DATA, MASTER_CRC, MASTER_RETX,
  WAIT_MASTER_ACK,
  SLAVE_LENGTH, SLAVE_DATA, SLAVE_CRC, SLAVE_RETX,
  WAIT_SLAVE_ACK,
  ARBITRATING.

The filter rule is uniform: raw 0xAA (was_escaped=false) bytes that do
not match the phase-expected wire role are dropped as adapter-spurious
AA-injection.

Exempt phases (raw 0xAA forwarded):
  IDLE — wire is genuinely idle; AA is real wire AUTO-SYN
         (residual: cannot distinguish from rare adapter-spurious in idle).
  WAIT_TERMINATOR_SYN — the terminator IS a raw 0xAA byte; forward and
         transition to IDLE.
```

### 1.7 [Codex MAJOR] §1.6 real address validation

**Codex finding:** v7 §1.6 phase validation says "0x00 ≤ QQ ≤ 0xFF" which is tautological.

**v8 fix:** explicit initiator-class and target-class validation:

```
PASSIVE_TRACKING MASTER_HEADER byte_index=0 (QQ):
  validate: QQ is an initiator-class address per eBUS spec
    (low nibble ∈ {0x0, 0x1, 0x3, 0x7, 0xF}; full table per spec V1.3.1
    section "Adressen-Klassen")
  on invalid: PROTOCOL_FAULT (forward + admin event + IDLE)

PASSIVE_TRACKING MASTER_HEADER byte_index=1 (ZZ):
  validate: ZZ is broadcast (0xFE), initiator-class, or target-class
    address per spec
  on invalid: PROTOCOL_FAULT
```

Implementation: a single static lookup table of address-class validity. Cheap constant-time check.

### 1.8 [Codex MAJOR] §1.8 counter gate concrete location

**Codex finding:** "`bus.go.fsm.phase == IDLE`" is not a real exported contract in helianthus-ebusgo. bus.go is call-stack driven.

**v8 fix:** concrete code location:

```
Round-9 absorb predicate (in helianthus-ebusgo/protocol/bus.go):

  if absorb_predicate_matches && in_sendRawWithEcho_active_echo_wait():
    increment helianthus_round9_absorb_fired_proxy_mediated_total

where in_sendRawWithEcho_active_echo_wait() is a boolean that is true
during the inner echo-read loop of sendRawWithEcho, and false elsewhere.
```

This is a concrete implementation surface that exists in the call stack rather than an abstract FSM-state reference.

### 1.9 [Codex MINOR] §1.12 terminology audit — complete pass

**Codex finding:** "Foreign master," "foreign slave," "master-master," "slow-slave" still in v7 prose.

**v8 fix:** thorough audit and replace in prose. Mermaid state names (`MASTER_HEADER`, `SLAVE_LENGTH`, etc.) retain canonical spec-phase labels but are flagged as identifiers in a glossary at the top of the doc. Prose uses initiator/target throughout.

(Note: the v7→v8 prose audit is done in v8; this v8 file uses the corrected terminology throughout.)

### 1.10 [Opus MINOR] §3 mermaid annotation for PASSIVE_TRACKING composite

**Opus finding:** A reader of §3 mermaid alone doesn't see that PASSIVE_TRACKING contains the full MASTER_RETX/SLAVE_RETX sub-FSM.

**v8 fix:** add a textual note immediately under the §3 mermaid:

```
Note: PASSIVE_TRACKING is rendered as a single composite state in the
diagram above. Internally it runs the SAME sub-FSM as the active mode
(MASTER_HEADER through WAIT_TERMINATOR_SYN, including MASTER_RETX and
SLAVE_RETX paths). The only behavioral difference vs active mode is
staging-aware echo matching: PASSIVE_TRACKING has no staging buffer
because the proxy did not originate the bytes.

For the inner sub-FSM, see §3.1 mermaid below (identical to active-
mode FSM modulo the SLAVE→FOREIGN-INITIATOR semantic rename).
```

Plus a second mermaid block in §3.1 showing the inner sub-FSM at full detail.

### 1.11 [Opus MINOR + Codex MINOR] §4 invariants concurrency model

**Opus + Codex both note:** I9/I10 don't specify whether forward/admin/transition happen on the same goroutine.

**v8 fix:** add invariant **I11**:

```
I11 (concurrency model): All FSM transitions, byte classifications,
byte forwards to observer queues, and admin event emissions for a
single session execute on a single goroutine, sequentially. No
concurrent observers see partial state mid-transition.
```

I9 and I10 are derivable from I11.

### 1.12 [Codex MINOR] §1.9 alert deployment ownership

**Codex finding:** alert rule presence should be validated in live-bus phase.

**v8 fix:** explicit in §1.10 / §14:

```
Step C live validation MUST include:
  - HelianthusRound9FiredUnderProxy alert rule present in Prometheus
    config (verify via Prometheus API).
  - Rule owner: operations team; deployed alongside proxy image.
  - Pre-deploy gate: prometheus-rules.yaml audit verifies rule
    presence before proxy rollout.
```

## 2. Items NOT changed from v7

  - Structural design (FSM-driven AA filter, per-session pacer, admin-channel-only faults, round-9 legacy fallback, scoped deletions).
  - Residuals §2.1 slow-target and §2.2 pacer per-session — both correctly framed in v7.
  - The PROTOCOL_FAULT byte-forward + admin-event rule (v7 §1.1 / I10).
  - The deploy order A→B→C→D (v7 §1.10).

## 3. Updated invariants list

  - I0 (clock): monotonic time.
  - I1 (no synthetic events in byte stream; admin channel excluded).
  - I2 (FSM-driven filter).
  - I3 (pacer τ_wire_byte cap, robust under jitter).
  - I4 **v8-revised**: escape decoder 8-AA OR 32-ms bound, whichever first.
  - I5 (FSM autonomy, RESETTED as resync).
  - I6 (retx cap: 1 per phase).
  - I7 (gateway-side bus.go timeout alignment).
  - I8 (round-9 backward compat with gated counter + Prometheus alert).
  - I9 **v8-revised**: classify under current phase BEFORE transition; transition fires only after byte consumption completes phase boundary.
  - I10 (PROTOCOL_FAULT visibility: forward byte + admin event).
  - I11 **NEW**: per-session single-goroutine execution model.

## 4. Mapping v7 findings → v8 resolutions

| v7 finding | v8 resolution |
|---|---|
| Codex IRREDUCIBLE §1.3 byte ordering | §1.1 classify-then-transition; I9 revised. |
| Codex BLOCKER + Opus BLOCKER §1.2 PASSIVE entry | §1.2 first-non-SYN primary, FAILED rare-validation. |
| Codex MAJOR + Opus MAJOR §1.4 ESCAPE_PENDING duration | §1.3 hard 32-ms cap on ESCAPE_PENDING; I4 revised. |
| Codex MAJOR §1.7 passive L_rtt poisoning | §1.4 abandon passive sampling; GRACE_BOOTSTRAP for first 3 echoes after long idle. |
| Codex MAJOR §1.10 spec V1.3.1 citation | §1.5 acknowledged as engineering choice; explicit Step A acceptance criteria. |
| Codex MAJOR §1.5 retx AA filter coverage | §1.6 explicit AA filter list across all active+passive non-IDLE phases. |
| Codex MAJOR §1.6 tautological validation | §1.7 real initiator-class + target-class validation. |
| Codex MAJOR §1.8 bus.go FSM contract | §1.8 concrete code location (`in_sendRawWithEcho_active_echo_wait`). |
| Codex MINOR §1.12 terminology incomplete | §1.9 complete prose audit in v8. |
| Opus MINOR §3 mermaid composite annotation | §1.10 explanatory note + §3.1 inner mermaid. |
| Opus + Codex MINOR concurrency model | §1.11 invariant I11 (per-session single-goroutine). |
| Codex MINOR alert deployment ownership | §1.12 explicit pre-deploy gate. |
| Opus F-v7-2 L_rtt bootstrap recursion | Resolved by §1.4 (abandon passive sampling = no recursion). |
| Opus F-v7-5 Step A acceptance | §1.5 explicit telemetry gate. |

Every v7 finding from both reviewers has explicit v8 resolution.

## 5. v8 status

The five-round trajectory v3→v4→v5→v6→v7→v8 has surfaced and addressed:

  - All structural blockers (telegram-atomic at byte-stream layer impossible for active arbitration; client metadata reception impossible via ENS).
  - All algorithmic correctness bugs (byte ordering, pacer jitter, escape decoder window).
  - All semantic violations (synthetic ENH events, sweeping deletions of cross-mode logic).
  - All observability gaps (counter gating, alert rules, residual documentation).

The design is now ready for **implementation review and live-bus validation**, not further architectural iteration. The next round of adversarial review on v8 is recommended; if it returns minor-fixes from both reviewers, v8 is the architectural spec to land.
