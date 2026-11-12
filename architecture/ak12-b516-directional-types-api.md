# B516 directional types: Ab20 catalog contract

The [native family supplement](../protocols/vaillant/ebus-b516-directional-types.md)
is the protocol contract for this finite area. Its
[synthetic data](../protocols/vaillant/fixtures/ak12_b516_directional_types.json)
contains implementation-neutral declarations. **Hypothesis:** the five rows
describe candidate relationships. **Unknown:** native support, physical effects,
persistence and delivery. API correctness does not upgrade those grades.

## Local API

**Proven (local API contract):** Package `vaillant` exposes exactly these catalog
entry points. This companion specifies their behavior; it is not runtime test
evidence for the registry implementation.

<!-- api:start -->
| Signature | Result |
| --- | --- |
| Ab20Entries() (json.RawMessage, error) | JSON array of whole rows |
| Ab20Lookup(Ab20Key) (json.RawMessage, bool, error) | One whole row for an exact key |
<!-- api:end -->

<!-- axes:start -->
| Ab20Key field | Go type | Native identity axis | Finite value |
| --- | --- | --- | --- |
| Ab20Family | string | family | vaillant-b516 |
| Ab20Variant | string | variant | generic-system-time, other-system-time, energy-type |
| Ab20Primary | uint8 | primary | 181 (B5) |
| Ab20Secondary | *uint8 | secondary | 22 (16) |
| Ab20Operation | *uint8 | operation | absent |
| Ab20Direction | string | direction | positive, request, read-positive, write-positive |
| Ab20Field | string | field | system-time, energy-type |
| Ab20Alternative | string | alternative | none |
| Ab20Group | *uint8 | group | absent |
| Ab20InstanceScope | string | instance_scope | none |
| Ab20Register | *uint16 | register | absent |
<!-- axes:end -->

All eleven axes participate in identity. Optional absent and explicit zero are
distinct. For example, an absent operation matches a declared row; operation zero
does not match it and no zero operation row is fabricated. The same absence rule
applies independently to secondary, group and register. Non-applicable string
axes use the explicit `none` token. Instance scope is a string: `00` and `dynamic`
are possible explicit scopes in the API, not numeric instances; this finite
slice uses `none`. Semantic variant labels never imply encoded operations.

<!-- behavior:start -->
| Condition | Contract |
| --- | --- |
| Exact hit | One whole row; found=true; error=nil |
| Missing exact key | found=false; error=nil |
| Invalid embedded JSON | error; no admitted result |
| Duplicate complete key | error; no admitted result |
| Lookup policy | All eleven axes; no wildcard or nearest-key lookup; no fallback |
| Entries ownership | Independent deep byte copy on every call |
| Lookup ownership | Independent deep byte copy on every call |
| Return mutation | Changing any row or entries buffer cannot affect a later result |
| Row contents | Ticket-prefixed ID; complete identity; fields and relations; candidate grade; explicit Unknown metadata; retained raw form |
| Admission | Validate embedded JSON and identity uniqueness before exposing any row |
<!-- behavior:end -->

No cross-family, variant, direction, field or alternative fallback is permitted.
The registry companion embeds its owned JSON in its owned Go file and preserves
the existing package name, or uses `vaillant` if no package exists. These docs do
not import a pending API, add shared registration or define another general
family schema. Existing catalog/provider APIs and routability remain unchanged.

## Raw and partial state

**Proven (local representation contract):** Results retain raw input, candidate
grade and explicit Unknowns. Read-positive C1 retains value 1 and two independent
flags. Write-positive C1 retains value 1 and unmodeled C0 without assigning those
flags. Request C1 retains enum token 193 without read-positive bit meanings.
The two system-time states both retain physical reply length Unknown.

An explicitly supplied one-byte energy field slice permits the declared
candidate interpretation. Unknown keys, malformed tokens, short or extra slices
do not admit a new semantic value. Raw evidence and independent last-known-good
state survive those failures; retained state is not fresh evidence. Field
positions and encoded operations remain absent. No byte locator is inferred.
These rules describe local conformance, not a new decoder API or a transmit path.

**Unknown:** Complete enum labels, encoded operation numbers, missing positions,
physical reply length, timeout, broadcast, native support, physical effects,
persistence and delivery. The write-positive upper bits remain unmodeled; no
reserved-zero assertion is made. Neither absent-positive nor header-only-positive
establishes a zero-length physical reply. Candidate grade is not qualification.

The focused checks independently compare all finite native tables and synthetic
cases, and vary each key axis with isolated controls in a local conformance model.
They check this documented API contract, not execution of the companion Go API.
Registry error and byte-copy behavior require companion runtime verification.
eBUS MCP compatibility and GraphQL parity are preserved; no provider, route,
scan default, executor or automatic native qualification changes here.

## Delivery relationship

AK11 must merge before this page in the same delivery cycle. No dependency points
back from that registry companion to this page. Their merge does not establish
native qualification. Refs #1017 and #736; this is a partial parent slice.
Nothing is stable before Helianthus 1.0.
