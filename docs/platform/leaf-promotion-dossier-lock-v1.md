Canonical source: this page.

# Leaf Promotion Dossier Lock V1

Issue: `Project-Helianthus/helianthus-docs-ebus#367` (`MSP-085`, M8.5).

Dependency: gateway M8 issue
`Project-Helianthus/helianthus-ebusgateway#707`.

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

## Canonical Machine Contract

The canonical files are:

- `schemas/leaf-promotion-dossier-v1.schema.json`;
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
`OFF_LAN`, and `positive_promotion_claim=false`. It makes
no positive promotion claim. Its four leaves close the terminal-state matrix
and produce:

```text
verdict=VALID_ZERO_PROMOTION
promoted=0
m9_consumer_gate=BLOCKED_ZERO_PROMOTED_LEAVES
```

This is a valid M8.5 result, not an error or empty-success shortcut. It blocks
all M9 consumer work.

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

## M9 Handoff

M9 work is considered only for the exact paths listed as promoted by a valid
lock result. It cannot infer permission from a source family, device, sibling,
candidate bundle, M8 coexistence pass, or non-zero candidate count. A
zero-promoted-leaves result leaves every GraphQL, Portal, Home Assistant, and
command-routing task blocked.
