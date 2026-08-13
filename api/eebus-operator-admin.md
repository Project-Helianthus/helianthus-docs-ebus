# Post-M9 Shared Consumer Boundary

## Scope And Canonical Ownership

This page freezes only the shared gateway, Portal, Home Assistant, FM5, and
release-version responsibilities required by the post-M9 remediation. The
canonical protocol-specific contract remains exclusively in:

- [`post-m9-operator-pairing-browsers-v1.md`](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/main/architecture/_candidate/post-m9-operator-pairing-browsers-v1.md)
- [`post-m9-operator-admin-v1.md`](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/main/api/_candidate/post-m9-operator-admin-v1.md)

Those documents alone own protocol routes, partner views, certificate and OOB
identity, raw-tree traversal, error vocabulary, persistence, and coordinator
state-machine semantics. This page must not restate them; if a shared consumer
rule conflicts with either canonical document, the protocol repository wins for
that protocol concern.

`eebus.v1.*` remains the only eeBUS MCP namespace. It stays read-only. There is
no v2 namespace, compatibility alias, public pairing tool, GraphQL mutation, or
Portal-private copy of raw protocol truth. Operator mutations use the
separately authenticated gateway admin boundary defined by the canonical API.

## Shared Ownership Boundary

| Component | Shared responsibility | Forbidden responsibility |
| --- | --- | --- |
| eeBUS runtime/coordinator | All protocol-native discovery, identity, connection, trust, persistence, and raw-topology behavior defined by the canonical protocol documents. | Browser or Home Assistant authentication; semantic eBUS projection. |
| Gateway | Authentication, authorization, CSRF enforcement, replay-safe action admission, sanitized audit outcomes, and typed coordinator calls. | Parsing trust-store bytes in an HTTP handler; inventing a second protocol state machine or raw topology. |
| Portal | Owner-only rendering and controlled action submission through the gateway boundary. | Direct filesystem/store access, direct socket access, implicit trust, or semantic promotion of raw data. |
| Home Assistant | Sanitized status, setup/options/repair presentation, and a fixed link to the owner Portal. | Operator-only identity, raw protocol data, any pairing mutation, or delegated authority. |

Portal and Home Assistant never read the trust store, its bytes, or the
owner-only operator socket. They are clients of the gateway boundary. Only the
gateway's typed adapter may reach the coordinator command boundary, and it may
not expose private socket framing or store representations.

## Authentication And Mutation Safety

When the corresponding authenticated boundary cannot be established, all
operator reads and mutations fail closed. No unauthenticated admin-status
fallback exists; authentication and authorization run before object resolution,
request-body processing that could disclose object existence, or coordinator
invocation. Route and error-code definitions remain in the canonical API.

The Portal profile requires an owner-authenticated same-origin session and
CSRF-safe mutation admission. The gateway rejects unauthorized, cross-origin,
stale, malformed, or replay-conflicting actions without invoking the protocol
runtime. The canonical API owns the concrete request fields and admission
vocabulary.

Home Assistant uses a non-cookie, least-privilege credential bound to one
config entry. Ambient browser cookies and browser-origin use of that credential
are rejected. Home Assistant receives no mutation grant, candidate view, raw
view, trust authority, credential exchange, or authority-bearing deep link.
Actions that require pairing or untrust open a fixed Portal path; the owner
authenticates and performs the action there.

Responses, audit data, logs, metrics, traces, crash data, URLs, and shareable
evidence exclude private keys, tokens, private PEM, trust-store bytes,
credentials, private paths, and raw operator-socket frames. Concrete audit and
redaction fields remain owned by the canonical protocol API.

## Raw Operator Inspection Isolation

The shared stack preserves authorized inspection of lossless protocol-native
data through the gateway boundary. Portal may render that data but may not
reinterpret unknown native values, infer semantic facts, or establish a second
protocol truth source. Home Assistant and public formatters receive no raw or
operator-only identity data. Raw protocol data must not enter `ebus.v1`,
GraphQL semantic fields, or the semantic registry. The canonical protocol
documents own all tree shape, paging, identity, action, and live-cardinality
requirements.

## FM5 Behavioral Verdict

FM5 interpretation is one runtime result, not a UI label. The provider
publishes the tuple:

```text
fm5_semantic_mode
fm5_semantic_degraded_reason
fm5_semantic_evidence_revision
```

The `fm5_semantic_degraded_reason` and
`fm5_semantic_evidence_revision` fields are inseparable from the mode result.

The closed modes remain `INTERPRETED`, `GPIO_ONLY`, and `ABSENT`:

- `INTERPRETED` means the controller/configuration gate and every required
  acquisition for the currently selected FM5 family completed coherently.
- `GPIO_ONLY` means current or retained admissible FM5 identity evidence exists
  but the current acquisition cannot safely publish interpreted solar/cylinder
  semantics. Its mandatory reason distinguishes a deliberate non-interpretable
  profile from a failed read, including `CONTROLLER_UNREACHABLE` when only
  retained evidence remains.
- `ABSENT` means no current or retained admissible FM5 identity evidence exists.

The closed degraded-reason set is:

```text
CONTROLLER_UNREACHABLE
CONFIGURATION_UNAVAILABLE
CONFIGURATION_NOT_INTERPRETABLE
SOLAR_ACQUISITION_FAILED
CYLINDER_ACQUISITION_FAILED
EVIDENCE_STALE
INCOHERENT_ACQUISITION
```

The named codes are `CONTROLLER_UNREACHABLE`, `CONFIGURATION_UNAVAILABLE`,
`CONFIGURATION_NOT_INTERPRETABLE`, `SOLAR_ACQUISITION_FAILED`,
`CYLINDER_ACQUISITION_FAILED`, `EVIDENCE_STALE`, and
`INCOHERENT_ACQUISITION`; no unlisted reason is accepted.

Reason precedence follows the acquisition pipeline in the order above, except
that `EVIDENCE_STALE` precedes family reads and `INCOHERENT_ACQUISITION` is the
terminal catch for a generation mismatch. The reason is `null` only for
`INTERPRETED` and `ABSENT`. `GPIO_ONLY` always carries exactly one reason:
`CONFIGURATION_NOT_INTERPRETABLE` for a live, known configuration outside the
currently interpretable semantic profile, or the exact acquisition/configuration
failure category that prevented interpretation. The runtime must not collapse
an acquisition or configuration failure into an unexplained `GPIO_ONLY`.

The additive `ebus.v1.semantic.fm5_interpretation.get` MCP tool exposes the
provider tuple first. GraphQL `fm5Interpretation`, Portal, and Home Assistant
then consume that same tuple. They may format the reason but may not recalculate
it. The pre-existing `ebus.v1.semantic.fm5_mode.get` scalar stays stable but is
not sufficient to diagnose degradation. A failed refresh does not publish zero
solar/cylinder values or silently erase last-known data; freshness and the
degraded reason remain explicit. Repair is behavioral at the acquisition/
provider boundary, not a cosmetic Portal change.

## Single Release-Version Authority

Every release starts from a single injected build-time release version. The
release workflow uses that exact input to build/tag the image, generate the
add-on package metadata, and inject the gateway build-info object. The same
release version is reported by runtime health, Portal health, and add-on package metadata.
`build_id` may add immutable revision/digest identity but may
not replace or rewrite the release version.

The gateway constructs build information once at process startup. Every
runtime status and Portal handler receives that object; a hard-coded fallback
release number is forbidden. Development builds may explicitly report `dev`,
but a release binary may not silently fall back to an older numeric version.

The packaging gate compares the injected binary version, image tag, and add-on
metadata before publication. Add-on startup compares the immutable expected
package version with the binary build information before opening listeners;
startup fails closed for a release artifact whose injected version is empty or
mismatched. No UI cache, manifest constant, or independent Portal version is a
version authority.

## Acceptance And Isolation

Implementation acceptance requires focused RED/GREEN tests for gateway-boundary
isolation, CSRF and authorization denial, raw-data non-leakage, FM5 reason
transitions, and version-mismatch startup denial. Protocol-specific identity,
topology, persistence, reconnect, and live-cardinality acceptance comes only
from the canonical protocol documents and the execution plan. Existing eBUS
operation must remain functional throughout eeBUS activity.
