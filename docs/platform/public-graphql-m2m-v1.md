# Public GraphQL M2M V1

`PUBLIC_GRAPHQL_M2M_V1` is the pre-implementation public semantic contract at
`/graphql/m2m/v1`. It is structurally separate from the gateway's generic
GraphQL route. Its only operation is the query `m2mCurrentSnapshot`; it has no
write, event-stream, historical, or generic fallback surface.

## Source And Projection

The only semantic source is the locked `helianthus.canonical-pv/v1` contract,
owned by `helianthus-ebusreg`. One request names one opaque `assetRef` and
returns one current, bounded snapshot: at most 256 dimensioned fact instances
drawn only from the 17 fact IDs in the locked V1 catalog. The response
identifies both `PUBLIC_GRAPHQL_M2M_V1` and its exact
source contract `helianthus.canonical-pv/v1`. Publication time, source-time
state, fact identity, exact decimal coefficient/scale, dimensions, unit,
quality, availability, freshness, receipt temporal fields, freshness policy,
continuity, capability outcome, and the public-safe provenance members are
preserved exactly.

GraphQL encodes the canonical value-kind discriminator as the closed union
mapping `decimal -> M2MDecimalValue`, `enum -> M2MEnumValue`, and `bitfield ->
M2MBitfieldValue`; the concrete type is the discriminator, so an independent
kind field cannot contradict its payload. Bitfield values retain the canonical
`symbols` field. Decimals are not JSON numbers: coefficients are canonical
integer strings and scale is a base-10 integer. Facts represented as unavailable remain explicitly
unavailable, while absent catalog members are not synthesized as zero or
inferred from another field. The public provenance table exposes at most 256
rows containing opaque origin, source protocol/profile/version/validity,
registry, observation, and evidence references. `source_shadow_ref` is the one
explicit projection loss: it is classified as
`WITHHELD_SOURCE_SHADOW_REFERENCE` because the public route must not provide a
navigation handle into source-owned shadow data. It never exposes source-shadow
content, registers, addresses, credentials, paths, or endpoints.

V1's catalog is closed. Any additive or breaking semantic change, including a
new fact, enum value, dimension meaning, capability requirement, or lifecycle
meaning, requires a successor contract identifier. The M2M route must reject
unknown fields and incompatible contracts rather than proxying to generic
GraphQL.

## Negotiation, Access, And Recovery

Every request supplies `contractId=PUBLIC_GRAPHQL_M2M_V1`; an absent or
incompatible value fails closed before a snapshot is returned. The request is
also constrained by the deployment/operator asset allowlist.

The wire surface accepts POST only, one operation named
`M2MCurrentSnapshot`, one asset, and one current snapshot. The request body is
limited to 16 KiB, query depth to 8, selected fields to 256, concurrency to one
request per client, and rate to one request per second with burst two. GraphQL
batching, aliases, named fragments, directives, introspection, GET,
subscriptions, and multi-operation documents are rejected before resolver
execution. Inline type conditions are allowed only to select the closed
decimal, enum, or bitfield member of the `M2MValue` union. The response is
limited to 1 MiB.

The route is registered only on a dedicated TLS listener; it is absent from the
generic HTTP listener that serves `/graphql` and subscriptions. The channel
requires HTTPS with verified server identity and mandatory per-client mTLS.
The deployment/operator boundary owns the listener configuration, server
identity, CA/trust root, client issuance, allowed assets, rotation, and
revocation. Cookies, shared credentials, and interactive credentials are not
accepted.

Unknown, revoked, expired, or lost client certificates; server-identity
failure; and contract incompatibility all fail closed. Reconnect retries are
bounded, and a successful reconnect obtains a fresh full snapshot rather than
merging a partial response into prior state. Monotonic receipt times are local
to one process lifetime and are not comparable across restart.

An invalid client certificate fails during the TLS handshake and receives no
GraphQL response. For an authenticated principal, contract mismatch returns
`CONTRACT_INCOMPATIBLE`, a disallowed asset returns `ASSET_FORBIDDEN`, an
unknown allowed asset returns `ASSET_NOT_FOUND`, and a provider with no retained
canonical snapshot returns `SOURCE_UNAVAILABLE`. These errors return no
partial snapshot and never fall back to generic GraphQL. A retained stale or
expired canonical snapshot is data, not a transport error, and keeps its
canonical availability/freshness state.

Credential rotation permits only the predecessor and replacement certificate
during one operator-bounded overlap: issue replacement, verify it on the
dedicated listener, then revoke the predecessor. Revocation is checked before
asset authorization on every request. A lost credential has no in-band reset;
recovery is an operator-issued replacement through the deployment boundary.

This route is the only public semantic ingress permitted for future private
eeBUS or Matter bindings. It grants neither a private binding implementation
nor access to canonical or source-owned internals.

## Conformance Assets

The conformance boundary is the GraphQL operation payload, not an internal Go
or canonical JSON struct. Fixtures therefore use the SDL's camelCase names,
dimension lists, and concrete union-member payloads. The validator first applies
one mandatory lossless mapping into canonical field names and value
discriminators, then enforces the canonical catalog and lifecycle invariants.
Unknown fields, duplicate dimension keys, incomplete union members, or a mapping
that cannot be completed fail closed as structural errors; implementations may
not substitute a private normalized fixture for this wire-shaped boundary.

- [SDL](../../api/public-graphql-m2m-v1.graphql)
- [machine-readable manifest](./manifests/public-graphql-m2m-v1.json)
- [deterministic cases](./fixtures/public-graphql-m2m/v1/cases.json)
- [`validate_public_graphql_m2m_v1.py`](../../scripts/validate_public_graphql_m2m_v1.py)
