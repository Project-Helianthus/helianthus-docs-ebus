Canonical source: this page.

# Captured Multi-Leaf Promotion V1

Initial issue: `Project-Helianthus/helianthus-docs-ebus#403`
(`MSP-085-LIVE-R2`). This is an additive profile of the unreleased Leaf
Promotion Dossier V1. It does not create a V2, alias, compatibility namespace,
consumer API, or semantic source-precedence policy. The existing
`CAPTURED_RUNTIME_ZERO_PROMOTION` inputs and outputs remain unchanged.

## Purpose And Ownership

`CAPTURED_RUNTIME_MULTI_LEAF_V1` preserves 22 provenance records: four
immutable retired terminal non-leaves and 18 real semantic leaves. The real
leaves are partitioned exactly into 11 cross-protocol equivalence leaves and
seven eeBUS-native leaves. Gateway owns synchronized
capture, source timestamps and generations, sample validity, comparator
evidence, deterministic replay, and dossier assembly. Protocol-independent
freshness, unavailable policy, source precedence, semantic registry ownership,
GraphQL, Portal, Home Assistant, and command routing remain outside this gate.

The exact captured protocol selectors exist only in the `PRIVATE_OPERATOR`
campaign. Each cross-protocol eBUS identity is an exact `B524`/`B555` union.
A `B524` identity binds the catalog-owned target address `0x15`,
`(opcode, GG, II, RR)`, group
meaning, instance gate, register category, and unit/scale source together with
the captured target pseudonym and admitted source. Candidate `0006` retains
that primary B524 provenance but may instead capture one complete B555
`TIMER_READ` identity: the active-controller target pseudonym, `BASV2`, `DHW`,
slot `0`, `MONDAY`, `00:00:00`, `temp_slots_1_shared_setpoint`,
`B555_DHW_TEMPERATURE_RAW_DIV10_C`, `timerSlot.temperature`, `degC`, and
`dhw_temp_slots_1_mirrors_b524_setpoint`. B555 evidence is never serialized or
hashed as B524 evidence. A selector from another family or candidate is not
interchangeable even when its decoded value is equal.
The derived `PUBLIC_REDACTED` result retains candidate ids, content hashes,
decisions, terminal outcomes, and replay bindings, but no eBUS addresses or
eeBUS device, entity, feature, service, path, SKI, or SHIP identity. Neither
tier may contain private keys, PEM private material, bearer/basic credentials,
JWT-like tokens, encoded trust-store/private-key bytes, or `candidate_ref`.
Validation recursively scans values as well as enforcing closed schema keys;
operational SKI, SHIP ids, protocol addresses, and selectors are not treated as
cryptographic secrets in the private operator tier.

The eeBUS source contract is temporarily grounded by the full PR-head commit
`3576a14edbe08aeb757b9e53a03fb6e5be387dfe`; it will be repinned to the source
inventory squash commit. That external binding owns only the SPINE source
profile: entity slot and type, feature type and role, complete
description/constraints/value function lists, field path, descriptor, unit,
declared constraints, and exact SPINE raw mapping. This platform registry owns
the semantic paths, historical hashes, 11/7 partition, validation modes,
comparators, conversions, cross-protocol mappings, restart and promotion
rules, and B555 fallback. The private eeBUS identity reproduces only the SPINE
source profile, binds it with `source_profile_hash`, adds its captured native
service/device/entity/feature selectors, and binds the complete identity with
`identity_hash`.

The four retired ids and fact hashes are verified against the prior published
M8.5 result at `docs/platform/live/msp-085-0.6.38/m8.5-result.json`. They remain
`RETIRED_TERMINAL_NOT_A_LEAF`, retain their historical `CLOUD_ONLY` or
`NOT_TESTED` outcomes, and never enter the real-leaf promotion denominator.

The canonical registry is also an exact byte contract. Its raw SHA-256 is
`3dc531dddb3464c75aca42ccf914d98c7c3e872a2ad925229f2a207586e14b11`, exposed
as `registry_sha256=sha256:3dc531dddb3464c75aca42ccf914d98c7c3e872a2ad925229f2a207586e14b11`.
`--registry` may name a byte-identical copy; it cannot substitute tolerances,
selectors, mappings, or an eeBUS source profile.

## Candidate Classes

The catalog is closed and ordered by `m7-candidate-0001` through
`m7-candidate-0022`. Records `0001`-`0004` are the four retired terminal
non-leaves. Records `0005`-`0022` are 18 unique semantic paths. The exact
cross-protocol set is `0005`, `0006`, `0007`, `0009`, `0010`, `0011`, `0012`,
`0014`, `0015`, `0016`, and `0018`. The exact eeBUS-native set is `0008`,
`0013`, `0017`, and `0019`-`0022`. The first three native leaves use
`EEBUS_NATIVE_CAPABILITY`; the last four use `EEBUS_NATIVE_METADATA` and
`STRING_EXACT_STABILITY`.

Every candidate ends in exactly one of these states:

- `PROMOTED` with `terminal_state=null` and
  `visibility=LOCKED_NOT_EXPOSED`;
- `WITHHELD` with one explicit terminal state: `CLOUD_ONLY`, `NOT_TESTED`,
  `MISSING`, `NOT_COMPARABLE`, `IDENTITY_MISMATCH`, `GENERATION_CHANGED`,
  `INVALID`, `STALE`, `CONFLICT`, `MISMATCH`, or `NATIVE_DRIFT`.

A strict subset may be promoted. A withheld sibling does not invalidate an
otherwise complete dossier, and a promoted sibling supplies no inherited
identity, comparator, or evidence.

Every `CROSS_PROTOCOL_EQUIVALENCE` candidate has exactly two assessments in
window order. Two
`MATCH` outcomes derive `PROMOTED`; otherwise `WITHHELD` and its terminal state
are derived from the first non-`MATCH` outcome in `PRE_RESTART`, then
`POST_RESTART`, order. A campaign or public result cannot assert a different
terminal state. The four catalog-terminal rows retain their exact catalog state
without assessments. Native capability and metadata rows have no eBUS identity
but do have exactly two eeBUS-only assessments.

Each cross-protocol assessment records the observed eBUS selector hash and eeBUS
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

Every `EEBUS_NATIVE` candidate also has exactly two assessments in window
order, but each assessment contains only an eeBUS sample. An eBUS sample,
observed eBUS identity, or claim of cross-protocol equality is invalid for this
mode. The sample must bind the exact eeBUS identity, type, raw hash, unit,
capture generation, runtime epoch, connection generation, and age. Capability
values require the exact boolean SPINE raw mapping. Metadata values require a
non-empty `STRING` typed raw and normalized value. PRE and POST normalized
values must be byte-for-object equal. The outcomes are `NATIVE_VALID` and
`NATIVE_DRIFT`; promotion requires exactly two `NATIVE_VALID` outcomes and
exact PRE/POST stability. Any missing, invalid, stale, identity-mismatched,
generation-mismatched, mistyped, or changed native sample terminates the leaf
as `NATIVE_DRIFT`. This establishes restart stability, not eBUS equivalence or
universal immutability across operating states.

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
must remain stable. Each real leaf has one assessment in both windows. Each
promoted cross-protocol leaf must pass in both windows with two valid samples,
identical source identities, bounded skew and age, and no generation change
within a window. Each promoted native leaf must pass the corresponding exact
identity, type, age, generation, and PRE/POST normalized-value stability checks
with no eBUS sample.

The campaign also binds the exact bytes and protocol ids/hashes of the M7
graph/status/replay and the complete M8 coexistence evidence/report,
`no_drift=true`, `rollback_exact=true`, and deterministic replay. M8 and M8.5
are separate capture campaigns: their process-instance ids are expected to
differ. They must nevertheless bind the same exact gateway source commit,
binary digest and byte length, and the same persistent trust and peer
identities. The PRIVATE_OPERATOR M8.5 digest binds to M8's public-redacted
identity through its exact first twelve lowercase hexadecimal characters. The
private verifier also requires the full 256-bit M8 trust-state and peer-binding
hashes and compares them byte-for-byte with both M8.5 windows; the truncated
public ids are correlation labels only. The M8 transition still validates its
own domain-separated trust and peer hashes.
M8 must cover all eleven frozen protected views and all four
captured-runtime states with `REPRODUCIBLE_BUILD`. The private verifier creates
a fresh local clone, checks out the exact gateway source commit detached, and
rebuilds it with the declared Go toolchain, target,
`CGO_ENABLED=0`, `-trimpath`, and VCS stamping, then requires byte equality with
the deployed binary. A synthetic fixture, relabeled arbitrary binary, or a
narrower coexistence archive cannot substitute for that proof. Untracked or
ignored files in the operator's supplied checkout cannot enter this build. A
filesystem-backed Go module replacement is rejected; versioned module
replacements remain admissible under the committed module graph. The rebuild
also rejects tracked symlinks and gitlinks, so a tracked source path cannot
escape the materialized checkout. Git checkout ignores global and system
configuration, rejects active content filters, and verifies every materialized
regular file against its committed blob without filters. Go build disables
persisted `GOENV` configuration and fixes the baseline architecture tuning for
the declared target (`GO386=sse2`, `GOAMD64=v1`, `GOARM64=v8.0`, or the
declared `GOARM=v6/v7`). A
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
Public counts are exactly `records=22`, `total=18`, and `retired=4`;
`promoted` and `withheld` partition only the 18 real leaves. Candidate output
contains ids, hashes, disposition and terminal/window outcomes, visibility,
and dossier hashes. It contains no semantic paths, selectors, identities,
addresses, raw values, metadata strings, or secrets.

`LIVE_CAPTURE` additionally requires the same external source bundle for
`verify-private`, `derive-public`, and bound `verify-public`: `--m7-graph`,
`--m7-status`, `--m7-replay`, `--m7-registry`, `--m7-source-bundle`,
`--m7-source-replay`, all four corresponding `--m7-terminal-*` inputs,
`--m8-evidence`, `--m8-report`, `--m8-before-source-manifest`,
`--m8-after-source-manifest`, `--m8-before-source-root`,
`--m8-after-source-root`, `--m8-trust-state-hash`,
`--m8-peer-binding-hash`, exactly two `--capture-receipt` arguments in window
order, `--deployment-source`, `--deployment-binary`, and
`--deployment-source-tree`. The validator invokes the complete M8 verifier,
including all immutable M7 inputs, and requires the supplied M8 report to equal
the exact report regenerated by the predecessor validator. It also validates
native ids/hashes and cross-bindings, the M7 status projection, each exact
artifact byte hash, each receipt's window/generation/process binding, the
deployment source commit receipt, the deployed binary hash, and the full
private trust/peer hashes. The M7 graph/replay/status ids, hashes, source
commits, and exact bytes must equal the M8 `m7_binding`, `m7_live_status`, and
immutable inputs. Deployment commit, digest, and size must equal every
non-baseline live M8 runtime and the M8.5 deployment receipt/binary. M8 must use
`REPRODUCIBLE_BUILD`, and a fresh detached checkout materialized from the exact
source commit must rebuild to the same bytes with matching embedded VCS
revision and `vcs.modified=false`;
`SYNTHETIC_FIXTURE` is never live evidence. M8's own
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

These checks establish deterministic closed-bundle consistency and reject
partial splices, provenance substitution, and build relabeling. They do not
authenticate that the operator performed a capture or that a coherently
regenerated archive came from independent physical executions. Such origin
authentication would require a signer, trusted capture service, hardware root,
or append-only log and is outside this contract's declared threat model.

The repository fixture is `SANITIZED_CONFORMANCE`; its closed provenance names
the canonical generator and fixture id, while all selector values are synthetic
and make no protocol claim. Relabeling that provenance as `LIVE_CAPTURE` fails
closed. This is an evidence binding, not an execution authorization mechanism.
It proves positive subset derivation
but cannot open M9. Only a private `LIVE_CAPTURE` campaign with at
least one promoted leaf produces `READY_FOR_M9_PLANNING`. That state authorizes
planning for the exact locked leaves only. Every promotion emitted by this
contract remains `LOCKED_NOT_EXPOSED`; the contract never exposes, routes, or
publishes an M9 consumer surface.
