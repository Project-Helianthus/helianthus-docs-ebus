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

The source byte is not a caller-provided MCP parameter. User-facing MCP
input MUST NOT be allowed to override it.

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

The implementation MAY choose any enforcement mechanism that makes the
invariant non-bypassable at the `rpc.invoke` call site. Acceptable
mechanisms include:

- a compile-time constant used by the only frame-construction path
- a centralized helper that injects `0x71` and rejects conflicting input
- a linter or static check that forbids ad-hoc source-byte construction
  in the gateway invoke path

The enforcement mechanism is implementation-owned, but the outcome is
normative: gateway `rpc.invoke` traffic uses `0x71`, and non-`0x71`
gateway source construction is rejected before it reaches the bus.

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
