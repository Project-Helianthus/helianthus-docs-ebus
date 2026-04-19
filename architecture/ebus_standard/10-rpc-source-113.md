# `rpc.invoke` Source Byte Invariant

Status: Normative
Milestone: M4_GATEWAY_MCP
Plan reference: ebus-standard-l7-services-w16-26.implementing/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Purpose

This chapter freezes the gateway source-byte invariant for live
`ebus.v1.rpc.invoke` traffic produced by `helianthus-ebusgateway` during
`M4_GATEWAY_MCP`.

The canonical plan states:

> Live invocation routes through the existing `ebus.v1.rpc.invoke`. No
> new execution path is introduced.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.implementing/00-canonical.md`,
SHA-256 `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

## Invariant

Every gateway-originated `ebus.v1.rpc.invoke` frame MUST use source byte
`113` (`0x71`).

### Scope: gateway-internal invocation only

This invariant is a **gateway-internal** constraint. It does not change
the public `rpc.invoke` wire shape documented in
[`api/mcp.md`](../../api/mcp.md) ("RPC Method Reference"), where
`source` is defined as a caller-provided required parameter of
`ebus.v1.rpc.invoke`. The `source` parameter continues to exist in the
API exactly as documented.

The invariant narrows caller behaviour along two axes:

1. **Gateway as caller.** When `helianthus-ebusgateway` itself invokes
   `ebus.v1.rpc.invoke` from its own code paths (for example NM
   broadcasts, provider dispatch, internal semantic probes, or any
   other gateway-originated live traffic), the gateway's code MUST set
   `source = 113` (`0x71`). Gateway-internal call sites MUST NOT
   construct, forward, or propagate any other source byte into
   `rpc.invoke` frames.
2. **External callers.** External MCP clients invoking
   `ebus.v1.rpc.invoke` pass `source` per the API contract. The gateway
   verifies and authorizes such calls per its own policy (safety class,
   allow_dangerous, idempotency_key, etc.) and MUST NOT rewrite the
   caller-provided `source`. External callers MUST supply
   `source = 113` (`0x71`); the gateway MUST reject any external
   `ebus.v1.rpc.invoke` request whose `source` is not `0x71` with an
   explicit error before any frame reaches the bus. Silent re-labelling
   of non-`0x71` traffic as `0x71` is forbidden, and silent forwarding
   of non-`0x71` traffic to the bus is equally forbidden.

The effect is that every `rpc.invoke` frame that reaches the bus —
whether constructed internally by the gateway or relayed from an
external MCP caller — carries `0x71` in the source byte. Non-`0x71`
external requests are rejected, not forwarded. The public API wire
shape of `ebus.v1.rpc.invoke` is unchanged; the `source` parameter
remains caller-provided, but its only accepted value is `0x71`.

## Rationale

The live Vaillant topology used by this project assigns the gateway
participant identity to `0x71`. Gateway-originated traffic therefore
uses `0x71` as the source byte by project convention.

Other source bytes are not neutral alternatives:

- They can identify third-party participants on the bus.
- They can describe invalid or unsupported local identities.
- They can hide source attribution errors in audit logs and test
  fixtures.

Using a single fixed gateway source byte keeps `rpc.invoke` traffic
auditable and prevents MCP clients from impersonating other bus
participants.

## Enforcement

Enforcement is mandatory on two construction paths:

1. **Gateway-internal construction.** The implementation MAY choose any
   mechanism that makes the invariant non-bypassable at the
   gateway-internal `rpc.invoke` call sites described above. Acceptable
   mechanisms include:

   - a compile-time constant used by the only frame-construction path
   - a centralized helper that injects `0x71` and rejects conflicting
     input
   - a linter or static check that forbids ad-hoc source-byte
     construction in the gateway invoke path

2. **External caller admission.** The gateway MUST reject any external
   `ebus.v1.rpc.invoke` request whose caller-supplied `source` is not
   `0x71`. Rejection MUST happen at request admission, before the
   request reaches any bus-facing construction path, and MUST surface
   as an explicit typed error to the caller. The gateway MUST NOT
   rewrite a non-`0x71` caller `source` to `0x71`, and MUST NOT
   silently forward non-`0x71` traffic to the bus.

The enforcement mechanism on path 1 is implementation-owned, but the
outcome on both paths is normative: every `rpc.invoke` frame reaching
the bus uses `0x71`, gateway-internal non-`0x71` construction is
rejected before it reaches the bus, and external non-`0x71`
`ebus.v1.rpc.invoke` requests are rejected at admission.

## Test Requirement

Tests MUST plant a non-`113` source at the `rpc.invoke` construction
boundary and prove it is rejected at the call site.

Either of these proof shapes is acceptable:

1. Compile-time proof: no public constructor or typed API exists that
   can express a gateway `rpc.invoke` source other than `0x71`.
2. Runtime sentinel proof: a test injects a non-`113` source into the
   lowest available boundary and receives a stable rejection before any
   frame is sent.

The rejection MUST be observable in tests as a specific failure, not as
a downstream transport timeout.

## Relationship to Execution Policy

The source-byte invariant is separate from safety-class authorization.
A request with source `0x71` can still be denied by the shared execution
policy, and a request that would otherwise pass safety policy MUST still
be rejected if it attempts to use any other gateway source byte.

See [`05-execution-safety.md`](./05-execution-safety.md) for the
default-deny policy and caller-context rules.
