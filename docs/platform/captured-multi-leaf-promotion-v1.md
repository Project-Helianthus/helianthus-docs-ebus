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

The exact captured protocol selectors exist only in the `PRIVATE_OPERATOR`
campaign. Each eligible eBUS identity is family-discriminated as `B524` and
binds the catalog-owned target address `0x15`, `(opcode, GG, II, RR)`, group
meaning, instance gate, register category, and unit/scale source together with
the captured target pseudonym and admitted source. A selector from another family or
candidate is not interchangeable even when its decoded value is equal.
The derived `PUBLIC_REDACTED` result retains candidate ids, content hashes,
decisions, terminal outcomes, and replay bindings, but no eBUS addresses or
eeBUS device, entity, feature, service, path, SKI, or SHIP identity. Neither
tier may contain private keys, PEM private material, bearer/basic credentials,
JWT-like tokens, encoded trust-store/private-key bytes, or `candidate_ref`.
Validation recursively scans values as well as enforcing closed schema keys;
operational SKI, SHIP ids, protocol addresses, and selectors are not treated as
cryptographic secrets in the private operator tier.

The eeBUS source contract is grounded by `helianthus-docs-eebus` commit
`657a36d07e52570326384b757a5382a6789f641b`. For every protocol-present leaf,
the registry owns the entity slot and type, feature type and role, complete
description/constraints/value function lists, field path, complete descriptor,
unit, declared minimum/maximum/step, conversion, exact protocol mapping, and
cross-protocol raw-pair mapping. The private eeBUS identity reproduces that
whole profile, binds it with `source_profile_hash`, adds its captured native
service/device/entity/feature selectors, and binds the complete result with
`identity_hash`.

The canonical registry is also an exact byte contract. Its raw SHA-256 is
`d17a66da1919796f57ecd2a515fa4e538c6be8d00a24c8c7e5d38bce7f36e3cd`, exposed
as `registry_sha256=sha256:d17a66da1919796f57ecd2a515fa4e538c6be8d00a24c8c7e5d38bce7f36e3cd`.
`--registry` may name a byte-identical copy; it cannot substitute tolerances,
selectors, mappings, or an eeBUS source profile.

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

Every `ELIGIBLE` candidate has exactly two assessments in window order. Two
`MATCH` outcomes derive `PROMOTED`; otherwise `WITHHELD` and its terminal state
are derived from the first non-`MATCH` outcome in `PRE_RESTART`, then
`POST_RESTART`, order. A campaign or public result cannot assert a different
terminal state. The four catalog-terminal rows retain their exact catalog state
without assessments. The three capability-only rows retain exactly
`NOT_COMPARABLE` without an eBUS identity or assessments.

Each eligible assessment records the observed eBUS selector hash and eeBUS
identity hash independently of the candidate's expected identities. A missing
sample has a null observed identity for that source. `IDENTITY_MISMATCH` is
recomputed from a non-null observed hash that differs from the bound candidate
identity. `GENERATION_CHANGED` is recomputed from sample capture/poll/runtime/
connection generations that differ from the window. `INVALID` requires an
invalid sample, an unmapped protocol value, or a numeric value outside the
declared range. `STALE` requires the recomputed age to exceed the maximum.
`CONFLICT` requires two valid, fresh, same-source samples with different
semantic values: numeric decimals are compared after applying `scale`, while
enum and boolean values use exact normalized equality. Distinct JSON decimal
encodings of the same number do not establish a conflict. `MISMATCH` is reached only after the preceding
conditions are false and the comparator itself fails. A terminal label without
the corresponding observed evidence is rejected.

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

Every non-null sample binds `raw_hash` deterministically to its complete
`raw_value`. Numeric raw and decoded decimals must denote the same number.
Enum and boolean samples instead require the exact eeBUS raw-to-decoded pair
and the exact catalog cross-protocol pair; rehashing a substituted raw value
does not make it comparable.

The SPINE-declared minimum, maximum, and step are catalog-owned. Both the
converted eBUS value and the eeBUS value must fall inside the inclusive
`[minimum, maximum]` range before either `MATCH` or `MISMATCH` can be asserted;
an out-of-range or sentinel value derives `INVALID`. The step must be finite,
positive, equal to the protocol catalog entry, and present in the same hashed
evidence. A campaign cannot enlarge its own tolerance. The inclusive match
rule is:

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
must remain stable. Each eligible leaf has one assessment in both windows.
Each promoted leaf must pass in both windows with valid
samples, identical source identity, bounded skew and age, and no generation
change within a window.

The campaign also binds the exact bytes and protocol ids/hashes of the M7
graph/status/replay and the complete M8 coexistence evidence/report,
`no_drift=true`, `rollback_exact=true`, and deterministic replay. M8 and M8.5
are separate capture campaigns: their process-instance ids are expected to
differ. They must nevertheless bind the same exact gateway source commit,
binary digest and byte length, and the same persistent trust and peer
identities. M8 must cover all eleven frozen protected views and all four
captured-runtime states with `REPRODUCIBLE_BUILD`; a synthetic fixture or a
narrower coexistence archive cannot substitute for that proof. A
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

The public result records `private_campaign_bytes_hash`, the SHA-256 of the
exact private input bytes from which it was derived. For `LIVE_CAPTURE`,
`verify-public` requires `--private-campaign PATH`, successfully validates that
private campaign against the pinned registry, recomputes the byte hash, and
requires byte-for-object equality with a fresh deterministic public derivation.
A standalone or relabeled public object therefore cannot open M9.

`LIVE_CAPTURE` additionally requires the same external source bundle for
`verify-private`, `derive-public`, and bound `verify-public`: `--m7-graph`,
`--m7-status`, `--m7-replay`, `--m8-evidence`, `--m8-report`, exactly two
`--capture-receipt` arguments in window order, `--deployment-source`, and
`--deployment-binary`. The validator validates the M7 graph/status/replay and
M8 evidence schemas, then requires the supplied M8 report to equal the exact
report regenerated by the predecessor validator. It also validates native
ids/hashes and cross-bindings, the M7 status projection, each exact artifact byte hash, each receipt's
window/generation/process binding, the deployment source commit receipt, and
the deployed binary hash. The M7 graph/replay/status ids, hashes, source
commits, and exact bytes must equal the M8 `m7_binding`, `m7_live_status`, and
immutable inputs. Deployment commit, digest, and size must equal every
non-baseline live M8 runtime and the M8.5 deployment receipt/binary. M8 must use
`REPRODUCIBLE_BUILD`; `SYNTHETIC_FIXTURE` is never live evidence. M8's own
process restart is validated within M8. M8.5 PRE/POST process hashes are
validated independently by its two capture receipts and must differ, while
their trust state and peer binding must equal the unique
`EEBUS_RESTART_PERSISTED` transition. Known
synthetic selector markers fail closed. Numeric SPINE enum ids use the exact
integer representation (`scale=0`); scaled numeric aliases are invalid. The
deployment source receipt is the closed JSON object
`{contract,source_commit,binary_hash}`. Each closed capture receipt binds one
campaign id, the full window hash, and the M7/M8/deployment bindings. It does
not claim that a later leaf window is an M8 run. PRE has no restart event. POST
must carry exactly one
`HA_ADDON_RESTART_COMPLETED` event whose `completed_at` is strictly after the
PRE window and strictly before the POST window. Omitting, splicing, or
substituting any input prevents LIVE derivation and M9 readiness.

The repository fixture is `SANITIZED_CONFORMANCE`; its closed provenance names
the canonical generator and fixture id, while all selector values are synthetic
and make no protocol claim. Relabeling that provenance as `LIVE_CAPTURE` fails
closed. This is an evidence binding, not an execution authorization mechanism.
It proves positive subset derivation
but cannot open M9. Only a private `LIVE_CAPTURE` campaign with at
least one promoted leaf produces `READY_FOR_M9_PLANNING`. That state authorizes
planning for the exact locked leaves only. It does not expose or route them.
