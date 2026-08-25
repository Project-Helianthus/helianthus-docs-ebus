# eeBUS Northbound External-Integrator Boundary

## Purpose And Scope

This page is the stable, human-readable entry point for an external integrator
of the already merged eeBUS northbound surfaces. It describes ownership and
visibility boundaries only. It does not add a route, a tool, a pairing action,
or a runtime capability.

The underlying SHIP/SPINE protocol discovery design remains in the public
[SHIP/SPINE overview](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/main/protocols/ship-spine-overview.md).
That protocol page does not define a consumer surface; this page does not
replace it with a new protocol contract.

## SHIP Connection State And SPINE Browsing Are Separate

SHIP answers relationship questions: whether a partner is discovered or
trusted, and whether its transport session is connected. SPINE answers
topology questions: the device/entity/feature/use-case tree observed for the
current connected partner generation. Neither state implies the other.

| Observed condition | Integrator-visible meaning | SPINE browsing result |
| --- | --- | --- |
| Trusted and connected | A persisted trust relationship and a current SHIP session are both present. | The gateway may expose the current raw SPINE topology through its typed boundary. |
| Trusted but disconnected | Trust persists, but there is no current SHIP session. This is a connection state, not a missing or revoked trust record. | Do not treat the partner as browseable, reuse an earlier raw tree as current, or infer semantic availability. Present the disconnected state through the existing typed boundary. |
| Connected topology unavailable | A session exists, but a usable current-generation topology is not available. | Show topology as unavailable; do not substitute an old raw snapshot or synthesize a tree. |

SPINE browsing is connected-only and read-only. Raw topology belongs to the
connection generation that produced it. A disconnect or a new generation does
not preserve the previous tree as the current tree. This is distinct from
retained, independently promoted semantic facts.

## Surface Map

| Surface | What an integrator may rely on | What it must not infer or obtain |
| --- | --- | --- |
| Read-only MCP (`eebus.v1.*`) | Bounded protocol-native runtime and raw inspection data exposed by the gateway's read-only MCP boundary. | Pairing mutation, a second eeBUS namespace, a transport write, or automatic semantic promotion of unknown native fields. |
| GraphQL | Only stable, promoted semantic facts suitable for the shared consumer contract. | Raw SHIP/SPINE topology, candidate detail, unknown native fields, or an assertion that every raw observation has a semantic counterpart. |
| Portal | Rendering and operator interaction through the gateway-owned typed boundary, including truthful unavailable or disconnected state. | Direct filesystem, trust-store, private-key, or operator-socket access; a second SHIP/SPINE model; semantic inference from raw data. |
| Home Assistant | Sanitized status and the same gateway-owned typed boundary as Portal. | Transport ownership, direct trust-store or operator-socket access, automatic trust, durable raw retention, or a parallel protocol state machine. |

MCP is the first northbound development surface; GraphQL and consumer rollout
follow only after a fact is stable and promoted. The historical raw-first and
per-leaf promotion boundary is documented in
[eeBUS Raw-First Platform Contract](../docs/platform/eebus-raw-first-contract.md).
The existing MCP, GraphQL, Portal, and shared consumer contracts remain the
authoritative surface-specific references:

- [MCP](./mcp.md)
- [GraphQL](./graphql.md)
- [Portal](./portal.md)
- [Shared consumer boundary](./eebus-operator-admin.md)

## Typed Gateway Boundary And Data Isolation

Portal and Home Assistant are clients of the gateway's typed boundary. They do
not read a trust store, private key material, owner-only operator socket, or
private socket framing. They do not own transport lifecycle, trust decisions,
or a separate SHIP/SPINE state machine.

An active operator view may render bounded raw SPINE inspection data only when
the gateway supplies it through that typed boundary. Public and shareable
output must exclude raw or operator-only identity data. Raw protocol-native
data must not be reinterpreted as a semantic fact by Portal or Home Assistant,
and it must not enter GraphQL semantic fields or the semantic registry without
the separate promotion process.

## Explicit Non-Claims

This reference does not promote candidate documentation into a stable contract.
It does not define pairing mutations, HTTP routes, credentials, a deployment
procedure, a live-device workflow, or an external connection endpoint. Runtime
capability discovery and the surface-specific contracts above remain the source
of truth for what is actually available.
