Canonical source: this page.

# Leaf Promotion Dossier Lock V1

Initial issue: `Project-Helianthus/helianthus-docs-ebus#367` (`MSP-085`,
M8.5). Captured-runtime amendment:
`Project-Helianthus/helianthus-docs-ebus#393` (`MSP-085-LIVE-R1`).

Ordinary provenance dependencies are M7 gateway
`8bcba2107d10b149f984ac9546ea6427a9cda8a1`, M7 docs
`35d2eba256a77b6575a2b45c07e73f054ff74ced`, M8 gateway
`89cf8876a9cd8aa4e6aab9ad21cc05cac523426a`, and M8 docs
`9cede4c61a4f73019142b7418cf6f87537cf645c`. These source commits identify
the reviewed implementations. They are not authorization tokens and do not
cause execution or consumer exposure.

## Purpose And Boundary

This language-neutral contract locks promotion one exact semantic leaf at a
time. It consumes an M7 candidate identity and an M8 coexistence no-drift
proof, records the complete Leaf Promotion Dossier, and derives a deterministic
lock result. Protocol-specific eeBUS meaning, eBUS register meaning, runtime
APIs, GraphQL fields, Portal controls, Home Assistant entities, and command
payloads remain outside this contract.

Protocol source selectors remain opaque identity fields. Their meaning stays
with the protocol-owned documentation. This page owns only the cross-protocol
rules that determine whether one exact canonical semantic path is eligible for
later M9 consumer work.

M8.5 is not a family, device, or runtime approval. A result may validly contain
zero promoted leaves. That result is deterministic, successful validation, and
blocks all M9 consumer work until at least one separately proven leaf is
locked.

V1 has two closed profiles. `SYNTHETIC_CONFORMANCE` retains the four-state
offline fixture and cannot establish a live claim.
`CAPTURED_RUNTIME_ZERO_PROMOTION` consumes the validated private M7 inputs,
their generated public status, the public source-terminal artifacts, and one
captured-runtime M8 evidence/report pair. It assesses every actual M7 fact but
creates no dossier and promotes no leaf. There is one unreleased V1: no V2,
legacy alias, or compatibility namespace exists.

Issue `#403` adds the companion `CAPTURED_RUNTIME_MULTI_LEAF_V1` profile in
[`captured-multi-leaf-promotion-v1.md`](./captured-multi-leaf-promotion-v1.md).
It leaves both profiles and every canonical artifact described on this page
unchanged. The companion contract can promote a strict subset only after two
restart-separated captured windows pass; it is still part of the single
unreleased V1 surface.

## Canonical Machine Contract

The canonical files are:

- `schemas/leaf-promotion-dossier-v1.schema.json`;
- `schemas/leaf-promotion-captured-assessment-v1.schema.json`;
- `schemas/leaf-promotion-lock-result-v1.schema.json`;
- `schemas/leaf-promotion-registry-v1.json`;
- `scripts/validate_leaf_promotion_dossier.py`; and
- `fixtures/leaf-promotion-dossier/v1` positive and negative vectors.

Unknown fields, duplicate JSON keys, malformed UTF-8, non-integer JSON
numbers, negative zero, and integers outside the portable JSON safe-integer
range are rejected. All object shapes and enum sets are closed. Optional
meaning uses explicit JSON `null`; omission is not another state.

The command contract is:

```text
validate_leaf_promotion_dossier.py verify \
  --dossier <dossier.json> \
  --registry <leaf-promotion-registry-v1.json>

validate_leaf_promotion_dossier.py replay \
  --dossier <dossier.json> \
  --registry <leaf-promotion-registry-v1.json>
```

`verify` emits `PASS` and no stderr on success. `replay` emits one
verifier-derived canonical JSON result with a trailing newline. It must not
read the network, wall clock, locale, host identity, or unlisted evidence.

The captured command is:

```text
validate_leaf_promotion_dossier.py derive-captured \
  --registry <leaf-promotion-registry-v1.json> \
  --m7-graph <private-candidate-graph.json> \
  --m7-replay <private-candidate-replay.json> \
  --m7-registry <draft-candidate-fact-registry-v1.json> \
  --m7-source-bundle <private-source-bundle.json> \
  --m7-source-replay <private-source-replay.json> \
  --m7-live-status <generated-public-status.json> \
  --m7-terminal-graph <public-terminal-graph.json> \
  --m7-terminal-replay <public-terminal-replay.json> \
  --m7-terminal-source-bundle <public-terminal-source-bundle.json> \
  --m7-terminal-source-replay <public-terminal-source-replay.json> \
  --m8-evidence <captured-public-redacted-evidence.json> \
  --m8-report <captured-public-redacted-report.json> \
  --m8-registry <multi-runtime-coexistence-registry-v1.json>
```

The command invokes the canonical synchronized-evidence, candidate-graph,
public-status, and M8 coexistence validators. It regenerates both M7 replay and
M8 report and requires exact equality. A caller-authored status or report
cannot substitute. The private assessment exists only in process and has
`export_tier=PRIVATE_OPERATOR`; the generator persists only the derived
`PUBLIC_REDACTED` result. The repository intentionally contains a profile
fixture, not a fabricated captured live result.

## Captured Runtime Zero Promotion

The bound public M7 projection contains 18 actual facts: 14 `RAW_ONLY` and
four `WITHHELD`. The verifier orders the private graph by exact semantic path
and then candidate id and derives one assessment per fact. The public result
preserves candidate id, fact hash, source status, terminal state, withholding
reasons, and bounded retest data. It omits the semantic path and all protocol
identity.

Every current fact remains withheld. `RAW_ONLY` and `WITHHELD` are not positive
comparator results. A promotion dossier is absent unless the exact leaf has all
of the following at once:

- exact B509, B524, or B555 eBUS identity;
- exact eeBUS entity/service/feature/path;
- a complete comparator with eligible captured samples and `MATCH`;
- the exact captured evidence binding; and
- passing M8 coexistence and rollback proof.

Missing data is never inherited from a family, device, sibling, or another
fact. The current derivation therefore emits `dossier_count=0`,
`promoted=0`, `withheld=18`, `verdict=VALID_ZERO_PROMOTION`, and
`m9_consumer_gate=BLOCKED_ZERO_PROMOTED_LEAVES`.

## One Dossier Per Leaf

Every leaf row carries all facts needed to decide that leaf. The exact
canonical semantic path is a rooted path, not a family prefix, device prefix,
or wildcard. The row also carries:

- one exact eBUS source identity;
- one exact opaque eeBUS entity/service/feature/path identity;
- one complete comparator;
- coexistence no-drift and rollback evidence;
- provenance and redacted hashes;
- replay regeneration bindings;
- one explicit retest trigger; and
- mutable proof when the leaf is mutable.

No row may rely on another row to fill missing identity or proof. The machine
form records `family=false`, `device=false`, and `sibling=false`. These booleans
normatively mean no family inheritance, no device inheritance, and
no sibling inheritance. A later family, device, or sibling observation creates a new
dossier; it cannot expand an existing lock.

## Exact Protocol Source Identity

The eBUS identity is selected from exactly one source family:

| Family | Required exact identity |
| --- | --- |
| B509 | target pseudonym and address, target product identity, register family and id, unit/scale source, and authoritative, mirror, or fallback role |
| B524 | target pseudonym, opcode, namespace, group, instance, register, target/source address context, group meaning, instance gate, register category, and unit/scale source |
| B555 | target pseudonym, device family, schedule/program identity, slot, day, time, operation-mode context, and unit/scale source |

B524 identity is opcode-first. `OP=0x02` and `OP=0x06` are separate namespaces.
The tuple `(opcode, group, instance, register)` is exact; the same group,
instance, and register under the other opcode is a different source. The
machine namespace `OP_0X02` must pair only with integer opcode `2`, and
`OP_0X06` must pair only with integer opcode `6`.

The eeBUS identity has exactly four opaque fields: entity, service, feature,
and path. Path is an ordered list of typed opaque selectors. The dossier does
not attach protocol meaning to those selectors and does not publish private or
vendor-restricted specification text.

## Comparator Lock

The comparator is immutable within one dossier hash. Every row requires:

- comparator type;
- bounded window and sample period;
- absolute and relative tolerance policy;
- unit conversion mode, units, scale, and offset;
- rounding mode and decimal places;
- minimum samples;
- maximum missing samples;
- stale cutoff;
- conflict threshold and consecutive-sample count;
- observed and missing sample counts; and
- one closed outcome.

The validator rejects reversed or empty windows, missing samples above the
declared maximum, observations below minimum samples for a positive match,
invalid identity conversions, and incoherent rounding. Comparator changes are
a retest trigger and produce a new dossier hash.

## Terminal Withheld States

`NO_SIGNAL`, `CLOUD_ONLY`, `CONFLICT`, and `NOT_TESTED` are terminal outcomes
for the evaluated dossier version. Every one maps only to:

```text
decision=WITHHELD
visibility=RAW_DEBUG_ONLY
```

Terminal rows remain reviewable as raw debug evidence. They are absent from
promoted semantics, stable registry projections, GraphQL, Portal, Home
Assistant, and command routing. A terminal row cannot be relabeled as promoted
without new evidence and a new dossier generated under its retest trigger.

A promoted row has `terminal_state=null` and remains
`LOCKED_NOT_EXPOSED` at M8.5. Promotion unlocks planning for M9; it does not
itself expose a consumer surface.

## Coexistence, Provenance, And Replay

Each row binds the exact M8 report id and hash, every scenario run id, every
protected-view hash, `no_drift=true`, and `rollback_exact=true`. A root source
binding pins the M7 graph/replay and M8 evidence/report identifiers and
redacted hashes. The V1 registry pins the source artifact files; verification
derives the binding and evidence class from those files instead of trusting a
dossier's self-description.

Leaf provenance lists exact source artifact ids, the ordered redacted input
hashes, and the normalized output hash. Raw identifiers, addresses outside the
closed identity shape, credentials, network coordinates, and unredacted
payloads are forbidden.

The captured public result also forbids semantic paths, eBUS addresses, eeBUS
entity/service/feature selectors, SKI, SHIP ID, `candidate_ref`, private-key
material, tokens, trust-store bytes, and vendor-restricted material. Commit
IDs, contract IDs, candidate IDs, and typed content hashes remain ordinary
public provenance. No private assessment is a stable MCP, GraphQL, registry,
or command API.

Replay regeneration hashes the semantic path, exact source identity,
comparator, decision, and terminal state. Expected and actual replay hashes
must match the normalized output hash. The dossier hash and result hash use
domain-separated canonical JSON. Replay is deterministic and offline.

Every row carries a retest trigger with trigger class, changed-input set, and
minimum new samples. Source artifact, identity, comparator, coexistence,
runtime, or lease changes invalidate the prior claim and require a new dossier.

## Mutable Leaf Safety

A mutable leaf requires a complete mutable-proof object even when its current
decision is withheld. The proof requires:

- an explicit lab whitelist entry and non-empty lease;
- one writer and a stable writer identity;
- the gateway/router write path only;
- direct adapter writes disabled;
- the complete closed set of abort conditions;
- rollback after every cycle; and
- exactly three independent perturbation cycles.

Each cycle has a unique cycle id, a distinct perturbation input hash, a
canonical UTC execution time inside the lease window, an observed-state hash,
a rollback-state hash, `independent=true`, and `rollback=EXACT`. Cycle times
are strictly increasing. The writer must abort on lease expiry, writer
conflict, loss of the gateway/router path, stale source evidence,
conflict-threshold breach, or rollback failure. Any abort or failed rollback
withholds the leaf and invalidates that cycle as promotion evidence.

Read-only leaves carry `mutable_proof=null`. A read lock never authorizes a
write.

## Evidence Eligibility

A positive promotion requires `CAPTURED_RUNTIME_EVIDENCE` collected in
`SAME_LAN_LAB`, a passing comparator, exact coexistence proof, and all other
per-leaf locks. The bound M8 source artifact must independently carry the same
captured-runtime evidence class. Current off-LAN evidence and every synthetic
fixture are ineligible for promotion; changing only dossier claims cannot make
them eligible.

The canonical fixture deliberately records `SYNTHETIC_OFFLINE_FIXTURE`,
`OFF_LAN`, `profile=SYNTHETIC_CONFORMANCE`, and
`positive_promotion_claim=false`. It makes
no positive promotion claim. Its four leaves close the terminal-state matrix
and produce:

```text
verdict=VALID_ZERO_PROMOTION
promoted=0
m9_consumer_gate=BLOCKED_ZERO_PROMOTED_LEAVES
```

This is a valid M8.5 result, not an error or empty-success shortcut. It blocks
all M9 consumer work.

The synthetic fixture remains non-live even if a caller changes its evidence
class, source status, predecessor, or M9 field. The captured path rejects a
synthetic graph or M8 artifact before assessment. M8 no-drift by itself is not
a promotion claim.

## Validation Precedence

The first failure category is deterministic:

1. `json.syntax`
2. `schema.dossier`
3. `limits.exceeded`
4. `registry.binding`
5. `identity.native`
6. `comparator.invalid`
7. `inheritance.forbidden`
8. `coexistence.invalid`
9. `provenance.binding`
10. `mutable.safety`
11. `mutable.rollback`
12. `state.terminal`
13. `evidence.ineligible`
14. `hash.replay`
15. `consumer.block`
16. `hash.dossier`

The validator exits `1`, prints exactly that category plus a newline to
stdout, and writes no stderr. Resource use is bounded before and after parse.

Captured derivation additionally preserves fail-closed ordering for wrong M7
or M8 predecessor, source validation, generated-status mismatch,
graph/replay mismatch, synthetic-as-live substitution, assessment ordering,
fabricated dossier or promotion, M9 opening, public identity or secret leak,
unknown fields, and result hash mismatch. Failures from the reused M7 or M8
validators retain their originating category. Captured-only categories are
`captured.input`, `captured.predecessor`, `captured.status`, `captured.coexistence`,
`captured.schema`, `assessment.ordering`, `assessment.derivation`,
`promotion.forbidden`, `consumer.block`, `redaction.public`, and
`hash.result`.

## M9 Handoff

M9 work is considered only for the exact paths listed as promoted by a valid
lock result. It cannot infer permission from a source family, device, sibling,
candidate bundle, M8 coexistence pass, or non-zero candidate count. A
zero-promoted-leaves result leaves every GraphQL, Portal, Home Assistant, and
command-routing task blocked.

This amendment changes no runtime, transport, MCP, GraphQL, Portal, Home
Assistant, command, registry, B509, B524, or B555 behavior. It only defines
the language-neutral M8.5 assessment and public-redacted result contract.
