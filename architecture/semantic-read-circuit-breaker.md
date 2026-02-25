# Semantic Read Circuit Breaker (B524)

This page documents the semantic read circuit breaker used by gateway Vaillant B524 semantic reads.

Goal: suppress repeated failing reads per semantic register target while still allowing bounded recovery probes.

## Scope and Keying

- Applies to semantic B524 reads executed through `SemanticReadScheduler.Get(...)` in the Vaillant semantic poller.
- Circuit scope is per selector key: `b524:<group>:<instance>:<addr>` (hex formatted as `%02x:%02x:%04x`).
- A breaker decision suppresses only that key; other semantic keys continue polling.
- The B524 fetch path still performs bounded internal retries (up to 3 attempts, `75ms` backoff) before returning one success/failure outcome to the breaker.

## State Machine

```mermaid
stateDiagram-v2
  [*] --> closed

  closed --> open: consecutive_failures >= failure_budget
  open --> half-open: open_cooldown elapsed
  half-open --> closed: probe read succeeds
  half-open --> open: probe read fails
  half-open --> open: probe budget exhausted
```

## Transition and Suppression Semantics

| State | Condition | Action |
| --- | --- | --- |
| `closed` | consecutive failures reach `failure_budget` | transition to `open`, start cooldown window |
| `open` | request arrives before cooldown expires | suppress request, return `ErrSemanticReadCircuitOpen` with `retry_after` |
| `open` | cooldown elapsed (or cooldown `<= 0`) | transition to `half-open`, refill probe budget |
| `half-open` | probe succeeds | transition to `closed`, reset consecutive failures |
| `half-open` | probe fails | transition to `open`, restart cooldown |
| `half-open` | request arrives after probe budget is exhausted | transition to `open`, suppress request, restart cooldown |

Notes:

- Half-open probe budget is consumed per allowed fetch call.
- Successful recovery in `half-open` fully closes the breaker and resets the failure counter.
- Suppression means no bus read attempt is made for that key.

## Configuration Knobs and Defaults

| CLI flag | Default | Behavior |
| --- | --- | --- |
| `-semantic-read-breaker-failure-budget` | `2` | Consecutive failed fetch outcomes needed to open the breaker. `<= 0` disables the breaker. |
| `-semantic-read-breaker-open-cooldown` | `15s` | Open-state cooldown before half-open probes are allowed. |
| `-semantic-read-breaker-half-open-probe-limit` | `1` | Number of allowed half-open probes per cooldown window (values `< 1` are normalized to `1`). |

These flags map to runtime config fields:

- `SemanticReadBreakerFailureBudget`
- `SemanticReadBreakerOpenCooldown`
- `SemanticReadBreakerHalfOpenProbeLimit`

## Observability (Transitions and Suppression)

### Expvar Counters

- `semantic_read_breaker_transitions_total` (expvar map): increments on every state change, keyed as `<from>-><to>` (for example `closed->open`, `open->half-open`).
- `semantic_read_breaker_suppressed_total` (expvar map): increments on every suppressed call, keyed by suppression state (`open`).

### Log Markers

- Transition marker:
  - `semantic_read_breaker_transition key="..." from=... to=... consecutive_failures=...`
- Suppression marker:
  - `semantic_read_breaker_suppressed key="..." state=... retry_after=... suppressed_total=...`

## Troubleshooting: Breaker Stuck/Open Cases

1. Check suppression logs for the exact key and retry window:
   - search for `semantic_read_breaker_suppressed`
   - inspect `key`, `retry_after`, `suppressed_total`
2. Verify transition flow for that key:
   - search for `semantic_read_breaker_transition`
   - expected recovery path is `open -> half-open -> closed`
3. If transitions repeatedly bounce `half-open -> open`, investigate underlying read failures first:
   - transport timeout/no-response
   - B524 payload/selector mismatch
4. Tune only after root-cause triage:
   - raise `-semantic-read-breaker-failure-budget` for transient links
   - increase `-semantic-read-breaker-open-cooldown` to reduce pressure during outages
   - increase `-semantic-read-breaker-half-open-probe-limit` for faster recovery attempts
5. Use `-semantic-read-breaker-failure-budget <= 0` only as a temporary diagnostic override (it disables suppression protection).

## Cross-Links

- Runtime architecture context: [`architecture/overview.md`](./overview.md#semantic-startup-runtime)
- Startup phase state machine: [`architecture/startup-semantic-fsm.md`](./startup-semantic-fsm.md)
