# Proxy Wire-Semantics Decisions

Status: Accepted (M0 decision lock for [EPIC #5](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/5))
Plan package: [PLAN-01 #6](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/6)

This document defines the canonical scheduling and timing semantics for proxy-mediated shared eBUS access.

## Scope and intent

The proxy is expected to behave like multiple independent participants sharing one physical eBUS, while acknowledging that software scheduling over one southbound connection cannot reproduce electrical bit-level simultaneity.

This yields a strict distinction:

- Electrical fidelity: bit-simultaneous arbitration and wired-AND effects on the physical wire.
- Wire-semantics fidelity: scheduling and timeout behavior observed at frame/symbol boundaries (`START`, `ACK/NACK`, `SYN`, response windows).

Proxy decisions in this workstream target wire-semantics fidelity.

## Decision 1: `SYN-while-waiting` is a timeout boundary

When an active transaction is waiting for:

- command `ACK/NACK`,
- target response bytes, or
- response confirmation,

and a `SYN` is observed, the transaction is semantically timed out for scheduling.

Proxy consequence:

- the current exchange is closed immediately for bus scheduling,
- arbitration may reopen immediately,
- multi-second host safety timers remain transport/control-path safeguards only and are not authoritative bus handoff timers.

## Decision 2: stale `STARTED` handling for milestone M1

The first proxy milestone uses bounded stale-absorb behavior for `pendingStart`:

- a mismatched stale `STARTED(x)` does not force immediate failure if the expected `STARTED(requested)` arrives within a bounded absorb window,
- absorb success and absorb expiry are both explicitly counted/logged,
- no scheduler redesign is implied by this decision; it is an immediate correctness fix with low blast radius.

## Decision 3: generic child-backed local target passthrough is not timing-faithful by default

For a shared real bus, a target response injected too late appears detached from the initiating request to other participants. Because a generic child-backed responder path includes host/proxy scheduling and transport latency, it is not timing-faithful by default.

Policy:

- do not claim strict timing fidelity for generic child-backed local target passthrough,
- treat strict local target behavior as a separately proven capability,
- keep this capability behind explicit validation before upgrading fidelity claims.

## Operational implications

- Proxy behavior changes that affect scheduling boundaries require doc-gate updates before merge.
- Transport/protocol merge gates remain `T01..T88` plus the dedicated proxy-semantics subset (`PX01..PX12`) defined in the matrix lane.
- Hardware passive proof for strict timing claims remains deferred to the ESERA follow-up milestone and is non-blocking for current code milestones.

## References

- EPIC: [Project-Helianthus/helianthus-execution-plans#5](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/5)
- Execution plan package: [Project-Helianthus/helianthus-execution-plans#6](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/6)
- Matrix runbook: [`../development/smoke-matrix.md`](../development/smoke-matrix.md)
