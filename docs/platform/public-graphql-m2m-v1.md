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

Each public provenance row is admitted only when profile ID and version agree,
the complete source identity resolves to the exact registry reference in
`helianthus.source-registry-bindings/v1`, and `originRef` equals the canonical
source observation reference. Origin references are unique within a snapshot;
duplicate or unregistered origins fail closed.

`currentSourceOriginRef` identifies exactly one row in the public provenance
table as the current acquisition's canonical `source_provenance`. Facts may
refer to other rows when retained values originate in older acquisitions, so a
mixed-retention snapshot preserves both current-source identity and per-fact
origin without ambiguity.

The conformance case is rooted in the canonical
`golden-mixed-retention.json`: the current reference must equal that canonical
snapshot's `source_provenance.source_observation_ref`, not merely any unique row
present in the public table.

The positive GraphQL success envelope is generated losslessly from that named
golden. Root identity/time, facts, lifecycle, capability outcome, and every
provenance field are byte-value equivalent after the documented wire-name and
integer-string mapping. The sole omitted canonical field is `source_shadow_ref`,
matching the one declared projection loss. A separate
`capability_satisfied_projection` exercises the complete capability pack without
weakening the golden-bound positive response.

The wire fields `requestedOutputs` and `projectionReport` preserve canonical
projection accounting as opaque digest identities. Every requested identity has
exactly one report row. `MAPPED` rows carry a non-null fact identity and bind
`sourceRef` to that fact's `originRef`; `WITHHELD` and `UNREPRESENTABLE` carry
null fact identity/dimensions and bind to the current source origin. The lists
are closed, duplicate-free, and bounded to 256 rows each.

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

Before semantic decode, the HTTP JSON parser rejects duplicate object keys and
any document nested deeper than 64 arrays/objects. Depth is bounded from raw
bytes before recursive decoding; duplicate keys are rejected by the parser
rather than resolved first-wins or last-wins. The same compact deterministic
JSON encoding used by conformance enforces the 16 KiB request-body and 1 MiB
response-body limits.

The logical client is the authenticated mTLS principal fingerprint. Admission
uses an integer monotonic-millisecond clock and evaluates concurrency before a
token bucket. A request is in flight from admission until its terminal response;
the bucket starts with two tokens, has capacity two, and refills one token every
1000 ms. Fixture order breaks ties at the same timestamp. Rejected requests do
not consume a token. The conformance fixture includes an overlapping request and
a same-client burst/refill sequence, so concurrency and rate limits are
executable contracts rather than prose-only limits. A two-principal sequence
requires simultaneous admission for distinct mTLS identities, then admits the
first principal after its overlap rejection to prove both client isolation and
non-consumption of a rate token.

The request fixture retains both the exact UTF-8 `rawBody` and its decoded
object. The validator measures `rawBody` before parsing, applies depth and
duplicate-key admission to those bytes, and requires the decoded value to equal
the documented body. Whitespace or alternate encoding cannot bypass the 16 KiB
wire limit.

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

Semantic admission is ordered: contract compatibility, asset allowlist, asset
existence, then source-snapshot availability. Conformance binds each of the four
reachable request plus server-state combinations to its exact response. It also
contains an overlapping failure at every precedence boundary, so an earlier
failure cannot leak a later asset/source decision. The fixture additionally
binds every declared request-rejection category to an executable malformed
body, envelope mutation, GraphQL AST mutation, wire-size stimulus, or logical
client event sequence.

The four authenticated semantic failures and ten authenticated request
rejections use HTTP status `200` and the same closed GraphQL error envelope:
`data` is `null`; `errors` contains exactly one row with
the constant message `M2M request failed`, path `m2mCurrentSnapshot`, and only
the applicable code in `extensions.code`. This follows non-null root-field error
propagation while preventing asset, source, or deployment details from leaking
through messages. TLS/client-certificate rejection remains pre-HTTP and returns
no GraphQL envelope.

Authenticated request admission failures use the same envelope and add three
closed codes. Malformed JSON, duplicate keys, and invalid HTTP envelopes map to
`REQUEST_INVALID`; forbidden or non-canonical GraphQL query shapes map to
`QUERY_REJECTED`; body/query/field/concurrency/rate bounds map to
`REQUEST_LIMIT_EXCEEDED`. Static message and path rules are identical to the
semantic failures, so framework parser details and private input are never
reflected to the client.

Conformance binds three wire request examples directly to their exact response
envelopes: duplicate-key JSON to `REQUEST_INVALID`, an aliased query to
`QUERY_REJECTED`, and a raw body over 16 KiB to
`REQUEST_LIMIT_EXCEEDED`. Implementations must preserve these input-to-output
bindings rather than validating request and error examples independently.

Credential rotation permits only the predecessor and replacement certificate
during one operator-bounded overlap: issue replacement, verify it on the
dedicated listener, then revoke the predecessor. Revocation is checked before
asset authorization on every request. A lost credential has no in-band reset;
recovery is an operator-issued replacement through the deployment boundary.

This route is the only public semantic ingress permitted for future private
eeBUS or Matter bindings. It grants neither a private binding implementation
nor access to canonical or source-owned internals.

## Conformance Assets

The conformance boundary is the complete GraphQL HTTP envelope, not an internal
Go or canonical JSON struct. The positive request fixes `POST`, the route,
`operationName`, the full query with inline selections for all three union
members, and the variables object. Its paired response fixes HTTP status and the
`data.m2mCurrentSnapshot` root. Payload fields use the SDL's camelCase names,
dimension lists, and concrete union-member shapes.

The validator checks that envelope and query before applying one mandatory
lossless mapping into canonical field names and value discriminators, then
enforces the canonical catalog and lifecycle invariants. Unknown fields,
duplicate dimension keys, incomplete union members, or a mapping that cannot be
completed fail closed; implementations may not substitute a private normalized
fixture or resolver-only object for this wire-shaped boundary.

- [SDL](../../api/public-graphql-m2m-v1.graphql)
- [machine-readable manifest](./manifests/public-graphql-m2m-v1.json)
- [deterministic cases](./fixtures/public-graphql-m2m/v1/cases.json)
- [`validate_public_graphql_m2m_v1.py`](../../scripts/validate_public_graphql_m2m_v1.py)
