Canonical source: this page.

# Captured Multi-Leaf Promotion V1

Initial issue: `Project-Helianthus/helianthus-docs-ebus#403`
(`MSP-085-LIVE-R2`). This is an additive profile of the unreleased Leaf
Promotion Dossier V1. It does not create a V2, alias, compatibility namespace,
consumer API, or semantic source-precedence policy. The existing
`CAPTURED_RUNTIME_ZERO_PROMOTION` inputs and outputs remain unchanged.

## Purpose And Ownership

`CAPTURED_RUNTIME_MULTI_LEAF_V1` assesses the 18 M7 VR940 facts independently:
11 protocol-comparable observations, three protocol-present observations that
remain withheld without an eBUS capability source, and four terminal facts.
Gateway owns synchronized
capture, source timestamps and generations, sample validity, comparator
evidence, deterministic replay, and dossier assembly. Protocol-independent
freshness, unavailable policy, source precedence, semantic registry ownership,
GraphQL, Portal, Home Assistant, and command routing remain outside this gate.

The exact protocol selectors exist only in the `PRIVATE_OPERATOR` campaign.
The derived `PUBLIC_REDACTED` result retains candidate ids, content hashes,
decisions, terminal outcomes, and replay bindings, but no eBUS addresses or
eeBUS device, entity, feature, service, path, SKI, or SHIP identity. Neither
tier may contain private keys, PEM private material, tokens, trust-store bytes,
or `candidate_ref`.

The eeBUS source contract used to select descriptors is grounded by
`helianthus-docs-eebus` commit
`657a36d07e52570326384b757a5382a6789f641b`. Public documentation names only
publishable descriptors and functions. Exact native selectors and captured
values remain private evidence.

## Candidate Classes

The catalog is closed and ordered by `m7-candidate-0001` through
`m7-candidate-0018`. Four facts are terminal: one `CLOUD_ONLY` fact and the
unavailable B509, B524, and B555 facts. The remaining observations are seven
numeric values, three operation-mode enums, and four booleans. Three of the
booleans describe operation-mode changeability. Such a capability value
describes capability, such as operation-mode changeability, is not inferred
from a successful read or write. It remains `NOT_COMPARABLE` unless an exact
eBUS capability source is captured.

Every candidate ends in exactly one of these states:

- `PROMOTED` with `terminal_state=null` and
  `visibility=LOCKED_NOT_EXPOSED`;
- `WITHHELD` with one explicit terminal state: `CLOUD_ONLY`, `NOT_TESTED`,
  `MISSING`, `NOT_COMPARABLE`, `IDENTITY_MISMATCH`, `GENERATION_CHANGED`,
  `INVALID`, `STALE`, `CONFLICT`, or `MISMATCH`.

A strict subset may be promoted. A withheld sibling does not invalidate an
otherwise complete dossier, and a promoted sibling supplies no inherited
identity, comparator, or evidence.

## Comparator Rules

Numeric leaves use `NUMERIC_DECLARED_GRANULARITY`. Each capture window binds:

- the exact semantic descriptor unconditionally, followed by either the exact
  unit or one closed, catalog-bound affine conversion;
- the raw SPINE decimal value and declared step as `number` plus `scale`;
- the exact eBUS source identity, raw value, decoded value, and poll identity;
- source timestamps, capture generations, runtime epoch, SHIP connection
  generation, admitted eBUS source, the catalog-owned maximum skew of
  `1000000000` ns and maximum age of `10000000000` ns; and
- one comparator outcome.

The SPINE-declared step must be finite, positive, equal to the protocol catalog
entry, and present in the same hashed evidence. A campaign cannot enlarge its
own tolerance. The inclusive match rule is:

```text
abs(convert(eBUS) - eeBUS) <= declared SPINE step
```

This is a protocol-equivalence rule, not a metrological-accuracy claim. Missing,
zero, negative, substituted, or unbound granularity fails closed. Enum and
boolean comparators bind both protocol-native raw values to one exact catalog
pair and require exact equality of the resulting value; a mapping hash without
the matching raw pair is insufficient. Their source identity binds
`unit=null`, because these SPINE fields declare no unit; implementations must
not synthesize a `unitless` token. The current operation-mode catalog maps
only the directly shared `off` and `auto` states. It does not equate eBUS
`heat`/`cool` with SPINE `on`. Numeric tolerance cannot be applied to mapped
values.

## Two-Window Restart Proof

The campaign has exactly two ordered windows, `PRE_RESTART` and
`POST_RESTART`, separated by a completed Home Assistant add-on restart. Their
process-instance hashes must differ. The persistent local eeBUS identity hash,
trust-state hash, admitted eBUS source, and exact candidate identity bindings
must remain stable. Each promoted leaf must pass in both windows with valid
samples, identical source identity, bounded skew and age, and no generation
change within a window.

The campaign also binds the exact M7 graph/status, M8 coexistence evidence and
report, `no_drift=true`, `rollback_exact=true`, and deterministic replay. A
change to source identity, descriptor, unit/conversion, declared step,
generation, validity, comparator, coexistence proof, or replay hash requires a
new dossier.

## Machine Contract

Canonical artifacts are:

- `schemas/leaf-promotion-captured-multi-leaf-v1.schema.json`;
- `schemas/leaf-promotion-captured-multi-leaf-result-v1.schema.json`;
- `schemas/leaf-promotion-captured-multi-leaf-registry-v1.json`;
- `scripts/validate_captured_multi_leaf_promotion.py`;
- `scripts/generate_captured_multi_leaf_promotion_fixture.py`; and
- `fixtures/leaf-promotion-captured-multi-leaf/v1`.

The validator accepts `verify-private`, `derive-public`, and `verify-public`.
`derive-public` is deterministic and emits canonical JSON with a trailing
newline. It reads no network, wall clock, locale, or host identity. Unknown
fields, duplicate JSON keys, malformed UTF-8, non-integer JSON numbers,
negative zero, invalid decimal scales, unordered candidates/windows, and
unregistered candidate ids are rejected.

The repository fixture is `SANITIZED_CONFORMANCE`; its closed provenance names
the canonical generator and fixture id, while all selector values are synthetic
and make no protocol claim. Relabeling that provenance as `LIVE_CAPTURE` fails
closed. This is an evidence binding, not an execution authorization mechanism.
It proves positive subset derivation
but cannot open M9. Only a private `LIVE_CAPTURE` campaign with at
least one promoted leaf produces `READY_FOR_M9_PLANNING`. That state authorizes
planning for the exact locked leaves only. It does not expose or route them.
