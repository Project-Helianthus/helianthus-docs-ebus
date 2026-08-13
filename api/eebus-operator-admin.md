# eeBUS Operator Admin Boundary

## Scope And Canonical Ownership

This page freezes the shared gateway, Portal, Home Assistant, FM5, and release-
version responsibilities required by the post-M9 remediation. The canonical
protocol-specific contract remains exclusively in
`Project-Helianthus/helianthus-docs-eebus`, currently in the candidate
architecture and API documents for post-M9 operator pairing and browsers. This
page does not redefine SHIP, SPINE, certificate identity, trust persistence, or
the eeBUS coordinator state machine.

`eebus.v1.*` remains the only eeBUS MCP namespace. It stays read-only. There is
no v2 namespace, compatibility alias, public pairing tool, GraphQL mutation, or
Portal-private copy of raw protocol truth. Pairing actions use the separately
authenticated gateway admin HTTP boundary under `/admin/eebus/v1/`.

## Shared Ownership Boundary

| Component | Shared responsibility | Forbidden responsibility |
| --- | --- | --- |
| eeBUS runtime/coordinator | Native discovery, selected observation, connection generation, candidate lifecycle, trust commit/revoke, reconnect, and raw topology. | Browser or Home Assistant authentication; semantic eBUS projection. |
| Gateway | Authenticated admin routing, authorization, CSRF enforcement, bounded idempotency/state revision, sanitized audit outcomes, and typed coordinator calls. | Parsing trust-store bytes in an HTTP handler; inventing a second pairing FSM or raw topology. |
| Portal | Owner-only pairing workbench, SHIP partner views, OOB comparison, controlled action submission, and lazy raw SPINE rendering. | Direct filesystem/store access, direct socket access, implicit trust, or semantic promotion of raw data. |
| Home Assistant | Candidate-free sanitized status, setup/options/repair presentation, and a fixed link to the owner Portal. | Candidate identity, raw SPINE, any pairing mutation or delegated authority. |

Portal and Home Assistant never read the trust store, its bytes, or the
owner-only operator socket. They are clients of the gateway boundary. Only the
gateway's typed adapter may reach the coordinator command boundary, and it may
not expose private socket framing or store representations.

## Authentication And Mutation Safety

When the corresponding authenticated boundary cannot be established, all
`/admin/eebus/v1/*` reads and mutations fail closed with
`admin_boundary_unavailable`. No unauthenticated admin status fallback exists;
authentication and authorization run before object resolution, request-body
processing that could disclose object existence, or coordinator invocation.

The Portal profile requires an owner-authenticated same-origin session, a
session-bound CSRF token, strict Origin/Referer validation, JSON content type,
an action-specific scope, the last observed state revision, and a bounded
`Idempotency-Key`. Unknown or duplicate fields and stale bindings are rejected
without an effect. Reusing an idempotency key with different bindings is a
closed conflict, not a second attempt.

Home Assistant uses a non-cookie, least-privilege credential bound to one
config entry. Ambient browser cookies and browser-origin use of that credential
are rejected. Home Assistant receives no mutation grant, candidate view, raw
view, trust authority, credential exchange, or authority-bearing deep link.
Actions that require pairing or untrust open a fixed Portal path; the owner
authenticates and performs the action there.

Audit records contain an opaque request reference, principal class, action,
idempotency outcome, prior/resulting state class, time, and sanitized reason.
Responses, audit data, logs, metrics, traces, crash data, URLs, and shareable
evidence exclude private keys, tokens, private PEM, trust-store bytes,
credentials, candidate nonces, private paths, and raw operator-socket frames.

## SHIP Partner And SPINE Browser Projection

Portal displays the four independent SHIP views `trusted`, `connected`,
`discovered`, and `candidate`. The gateway preserves their distinct source
facts and never infers durable trust from discovery or a live connection.
Complete operational identity and endpoint data are owner-only; public or HA
formatters redact or omit them.

The pairing workbench compares the complete 40-character lowercase certificate
short identifier obtained from the TLS-bound candidate with an independent OOB
source. No discovery event, page load, reconnect, or Home Assistant action may
select, connect, trust, retry, or untrust a peer. Each mutation is an explicit
owner action admitted by the current coordinator state and exact generation.

The SPINE browser is a lazy device/entity/feature/use-case tree over one
immutable raw snapshot. The shared gateway adapter wraps the lossless canonical
raw payload only with tree identity, ordering, snapshot binding, and a fixed
bounded server page size. Parent expansion and continuation remain bound to
the same runtime, partner, authorization, mask tier, snapshot hash, and sort
position. Unknown native values remain typed and inspectable by the authorized
operator; they are never discarded or normalized into invented semantics.

The final VR940 run checks the derived live acceptance target of one device,
eleven entities, twenty features, and use-case claims. Those cardinalities are
a derived live acceptance target, not a generic product or protocol guarantee.
Raw SHIP/SPINE identities, addresses, claims, and opaque values must not enter
`ebus.v1`, GraphQL semantic fields, or the semantic registry.

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
- `GPIO_ONLY` means live FM5 evidence and a known configuration intentionally
  select a supported non-interpreted/GPIO-only profile. It is not a catch-all
  for failed reads.
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
`INTERPRETED` and `ABSENT`; a valid, deliberate `GPIO_ONLY` carries no failure
but uses the explicit reason `CONFIGURATION_NOT_INTERPRETABLE` only when the
configuration is known yet outside the currently interpretable semantic
profile. The runtime must not collapse an acquisition or configuration failure
into an unexplained `GPIO_ONLY`.

Portal, GraphQL, MCP semantic status, and Home Assistant consume the same
provider tuple. They may format the reason but may not recalculate it. A failed
refresh does not publish zero solar/cylinder values or silently erase last-
known data; freshness and the degraded reason remain explicit. Repair is
behavioral at the acquisition/provider boundary, not a cosmetic Portal change.

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

Implementation acceptance requires focused RED/GREEN tests for the admin
boundary, CSRF and authorization denial, exact identity/generation binding,
lazy lossless topology traversal, FM5 reason transitions, and version mismatch
startup denial. Independent add-on and Home Assistant restarts must preserve
only durable trust, rediscover/reconnect, and rebuild raw topology. Existing
eBUS operation must remain functional throughout eeBUS discovery and reconnect.
