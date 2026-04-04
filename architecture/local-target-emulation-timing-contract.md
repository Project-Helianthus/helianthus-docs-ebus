# Local Target Emulation Timing Contract

Status: Accepted (M4 docs lane for [EPIC #5](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/5), issue [#239](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/239))

This document defines the timing contract for local target emulation in the adapter proxy.

## Scope

The scope is local target handling on a shared physical eBUS where both initiator and target may be represented by sessions behind the same proxy.

The contract defines:

- what local targets are allowed to observe,
- when a local target is allowed to transmit response bytes, and
- when a response must be rejected as detached/late.

## Rule 1: Echo-driven visibility is mandatory

A local target must only observe request bytes after those bytes are observed back from the southbound adapter as wire-visible `RECEIVED` bytes.

Consequences:

- no local target visibility is granted from owner `SEND` intent alone,
- request routing decisions for local target response windows use echoed request state, not pre-wire transmit intent.

Rationale:

- this preserves wire-semantics fidelity for all participants because local target logic is driven by what actually appeared on the bus.

## Rule 2: Target responder window is explicit and bounded

When an echoed request is fully reconstructed and targets a locally emulated target, the proxy opens a target responder window for that target.

During this window:

- global initiator ownership is not transferred,
- only the authorized responder path for that target may emit response bytes for the current transaction,
- non-authorized sends are rejected.

The window closes on terminal boundary conditions, including timeout boundaries.

## Rule 3: Detached late responses are invalid on a shared bus

If a local target response is emitted after the transaction has semantically timed out or after the responder window is closed, the response is detached from the initiating request and must be rejected.

Consequences:

- detached late responses are not injected as valid in-transaction traffic,
- the proxy counts and reports rejected late responses for diagnostics.

Rationale:

- other bus participants observe only wire order and timing; a late detached response is seen as unrelated traffic and can corrupt shared-bus semantics.

## Validation status and claim boundary

Strict timing fidelity claims for local target emulation remain conditional.

- current implementation milestones may merge without on-site hardware proof,
- strict claims remain pending until passive validation is executed in the deferred ESERA follow-up lane ([docs #241](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/241), [plans #7](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/7)).

Until that passive validation is complete, generic external child-backed local responder behavior is considered experimental and not timing-faithful by default.

## References

- Proxy wire-semantics decisions: [`./proxy-wire-semantics.md`](./proxy-wire-semantics.md)
- EPIC: [Project-Helianthus/helianthus-execution-plans#5](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/5)
- Execution plan package: [Project-Helianthus/helianthus-execution-plans#6](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/6)
- Deferred passive validation lane: [Project-Helianthus/helianthus-docs-ebus#241](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/241)
