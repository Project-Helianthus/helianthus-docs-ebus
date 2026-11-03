# VRC Explorer Logical Request Deadlines And Evidence Retention

## Status And Evidence Boundary

This is a **planned software contract**, covering the elapsed-deadline remainder
of [Explorer #278](https://github.com/Project-Helianthus/helianthus-vrc-explorer/issues/278).
It does not assert that retry counts are infinite. C12 characterized finite
attempt counts and scripted aggregate costs; it deliberately did not implement
an elapsed deadline across a complete transaction. The original issue's scan
and CLI proposals do not define this contract.

**Observed existing implementation**, as inspected for this documentation:

- [Enhanced TCP](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/src/helianthus_vrc_explorer/transport/enhanced_tcp.py)
  has `timeout_s`, finite retry/reconnect allowances and a local arbitration cap,
  but `EnhancedTcpConfig` has no `max_command_s` field or shared request deadline.
- [ebusd TCP](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/src/helianthus_vrc_explorer/transport/ebusd_tcp.py)
  already has `max_command_s=30.0`; `_send_with_policy` checks elapsed time
  between attempts. This does not cap every framing, response or backoff phase.
- [C12 characterization](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/tests/test_transport_deadline_characterization.py)
  uses scripted reads and reconnect costs. Its disclaimer excludes a bound for
  every phase of a complete protocol transaction.
- The [B524 scanner handler](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/src/helianthus_vrc_explorer/scanner/b524_orchestration.py)
  already retains an incomplete artifact for `TransportRecoveryExhausted`, with
  `transport_recovery_exhausted` and transport diagnostics.

The implementation work remains planned here; this table is not qualification
or release acceptance evidence.

| Companion | Planned implementation responsibility | Status in this contract |
| --- | --- | --- |
| AF02 | Shared absolute deadline and terminal diagnostics, including zero admitted attempts | Planned; not established by the inspected baseline |
| AF03 | Enhanced TCP operation and phase integration | Planned; not established by the inspected baseline |
| AF04 | ebusd TCP operation and phase integration | Planned; not established by the inspected baseline |
| AF05 | Deadline and retained-evidence regression validation | Planned; C12 characterization alone does not establish it |

All requirements below are **planned software behavior** until implemented and
validated. Native facts remain governed by the public [ENH contract](../protocols/enh.md),
[ebusd TCP contract](../protocols/ebusd-tcp.md), and
[B524 contract](../protocols/vaillant/ebus-vaillant-B524.md).
These software budgets add no native timing promise. Evidence labels `Proven`,
`Hypothesis` and `Unknown` remain independent of implementation status and
qualification. No installed-device support, physical timing, completed
qualification or release readiness is asserted. Nothing is stable before 1.0.

## Four Distinct Limits

| Limit | Planned meaning |
| --- | --- |
| `max_command_s` | Finite configurable elapsed budget per logical public transport operation; default `30.0` seconds in both transport configs |
| `timeout_s` and existing shorter phase limits | Local connect, arbitration, framing or response limits; each remains effective and is capped by the remaining root budget |
| Retry and reconnect counts | Independent finite attempt allowances and retry-safety checks; time remaining does not authorize an extra attempt |
| Optional scan request-count budget | Number of requests admitted by a scan; neither a duration nor a replacement for the per-operation deadline |

There is no disable/unlimited sentinel, new CLI flag, scan-wide deadline,
protocol namespace, major or experimental namespace, or revision/profile
inference. The earlier of the elapsed deadline and attempt-count limit wins.
A fresh operation does not reset the scan's request-count budget.

## One Nonrenewable Deadline

Create one absolute monotonic deadline at entry to each logical public transport
operation: `deadline = monotonic_start + max_command_s`. Its attempts,
reconnects, backoff, arbitration, framing and response phases share that same
value. Transport serialization wait counts where a lock exists: start the budget
before waiting for that lock. Preserve reentrant locking and close ordering.
A queued operation that expires before admission must not send when it finally
acquires the lock.

The budget is exhausted at equality: `now >= deadline`. Check before beginning
and after returning from work. No send, hook, retry, reconnect or queued response
may begin or succeed at/after expiry. No response returned at/after expiry may
be accepted as evidence, even if its bytes were already buffered. Keep every
shorter existing phase limit and every retry-safety check; remaining root time
can only shorten a phase, never extend it.

Finite synthetic examples illustrate the planned arithmetic:

- A `1.0`-second root with `0.4` seconds consumed by one phase leaves at most
  `0.6` seconds for the next phase.
- Reconnecting after that phase does not restore `1.0` seconds. The reconnect,
  setup and any next attempt all share the remaining `0.6` seconds.
- A requested `15`-second ebusd backoff with `0.2` seconds remaining may wait
  at most `0.2` seconds under transport control. At expiry it terminates; it
  cannot then admit another attempt.

A new independent operation gets a fresh deadline. Clear request-local deadline
state on every exit, including success, exception and interruption. Standalone
session setup gets its own finite connect/INIT budget; that setup budget does
not consume every later request's budget. Setup or reconnect performed inside a
root operation remains capped by that root. Existing direct private-helper tests
retain their local phase timeout when no root operation is active.

## Terminal Outcome And Retained Evidence

Terminal aggregate expiry uses the existing category:

```python
TransportRecoveryExhausted(
    cause="timeout",
    phase="transaction",
    request_attempts=actually_admitted,
    reconnect_attempts=actually_begun,
)
```

AF02 must permit `request_attempts=0` when expiry precedes admission, including
queued lock wait. Count reconnects actually begun, not merely contemplated.
`retry_count` is never negative: use `max(0, request_attempts - 1)`.
The shared helper's internal `RequestDeadlineExpired` must be caught before
generic retry handling, translated to this terminal outcome, and neither
retried nor leaked into scanner output. This introduces no error cause or
artifact schema.

Reuse the existing `transport_recovery_exhausted` incomplete-artifact path and
its timeout/transaction diagnostics. An unfinished operation remains `Unknown`;
timeout does not prove target absence, unsupported capability or receipt.
Completed siblings, prior observations and partial last-known-good state stay
retained with their raw evidence and provenance. Retention does not qualify an
unfinished result: admission stays fail-closed, and expired responses cannot
replace accepted evidence. For B524, keep native `(opcode, group, instance,
register)` identities distinct, including the separate read namespaces.

Close ambiguous sessions and discard stale parser, message and response buffers
so a later operation cannot accept an earlier response. Clear request-local
state on every exit while preserving prior observations. Recognized writes stay
non-resubmittable; expiry or reconnect never authorizes unsafe retransmission.
A software timeout says nothing about whether a write already took effect.

## Software Budget Limitations And Compatibility

This is a software budget for transport-controlled waits, not a hard real-time
bound for DNS resolution, arbitrary caller hooks, filesystem trace I/O, OS
scheduling or external libraries that ignore timeout. Check expiry before and
after such calls; do not claim they can be interrupted. A call begun before
expiry can return late, but its late result must not become accepted evidence
or authorize another phase. Do not add per-call daemon threads, abandoned
futures, resolver thread pools or dependencies to manufacture a hard bound.

This application contract leaves the [Explorer/Portal coexistence policy](vrc-explorer-migration.md#coexistence-and-failure-handling)
intact. It preserves eBUS MCP envelopes and GraphQL parity and does not redesign
G5: desired-state START/STOP remain idempotent, RESTART executes, gateway
recovery remains intact, and there are no client receipts/keys or authorization
tier before 0.9. AD03 semantic snapshot evaluation coordinates, other
[documentation umbrella #736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736)
contracts, protocol-gap pages and driver-manager validation remain separate.
