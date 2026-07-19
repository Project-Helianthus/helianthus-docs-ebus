Canonical source: this page.

# Draft Candidate Fact Graph V1

Issues: `Project-Helianthus/helianthus-docs-ebus#359` and hardening issue
`Project-Helianthus/helianthus-docs-ebus#361` (`MSP-07`, M7).

Plan provenance: the locked multi-runtime semantic platform plan,
`12-eebus-mcp-first-vr940f.md`, `13-semantic-fact-graph-and-integration.md`, and
the `MSP-07` row in `92-m0-issue-matrix.yaml`.

## Purpose And Boundary

This language-neutral contract consumes an already verified
`helianthus.platform.synchronized-evidence-bundle.v1` result and records a
closed graph of draft semantic claims. It is candidate-only evidence for M7.
It does not promote a leaf, define a stable semantic value, or authorize a
consumer. M8 coexistence and M8.5 per-leaf promotion remain later gates.

The only permitted output channel is `CANDIDATE_DEBUG_REPLAY`. Every graph and
fact carries `NOT_PROMOTED`, `stable_exposure=false`, `command_capable=false`,
and `protocol_translation=false`. No candidate fact is a command. No graph
may initiate acquisition, pair a peer, write a native value, route a command,
or perform protocol-to-protocol translation.

This page does not publish private eeBUS specification text or
vendor-restricted details. eeBUS identifiers in public fixtures are redacted
per-bundle pseudonyms. Native eeBUS protocol meaning remains canonical in
`helianthus-docs-eebus`; this contract owns only the cross-runtime envelope.

## Closed Machine Contract

The canonical machine files are:

- `schemas/draft-candidate-fact-graph-v1.schema.json`;
- `schemas/draft-candidate-fact-replay-v1.schema.json`;
- `schemas/draft-candidate-fact-registry-v1.json`;
- `scripts/validate_candidate_fact_graph.py`; and
- `fixtures/candidate-fact-graph/v1` positive and negative vectors.

Unknown fields, unknown enum members, duplicate JSON keys, malformed UTF-8,
non-integer JSON numbers, negative zero, and integers outside the portable
JSON safe-integer range are rejected. Optional meaning is represented by an
explicit JSON `null`; omission is not another state.

All contract tokens are printable ASCII and at most 256 characters. Proposed
paths, evidence paths, and native observation pointers are at most 512
characters. The schema and executable validator apply the same closed types,
enums, integer ranges, string bounds, required fields, and unknown-field rule.

The root binds the exact synchronized evidence contract, bundle id, bundle
hash, replay hash, immutable evidence refs, candidate registry digest,
visibility flags, hard limits, comparator drafts, and ordered facts. An input
bundle must be verified under the synchronized-evidence v1 contract before the
graph is built. The candidate validator requires the exact source bundle and
source replay as separate inputs; a graph cannot attest its own provenance.

### Exact source consumption

The executable invocation is:

```text
validate_candidate_fact_graph.py verify \
  --graph <candidate-graph.json> \
  --registry <draft-candidate-fact-registry-v1.json> \
  --source-bundle <synchronized-evidence-bundle.json> \
  --source-replay <synchronized-evidence-replay.json>
```

`replay` requires the same four inputs. The validator invokes the existing
MSP-065 synchronized-evidence verifier with the registry pinned by this
contract, regenerates the synchronized replay from the verified bundle, and
requires deep equality with `--source-replay`. It then requires exact equality
for bundle contract/version/id/hash and the complete root evidence-ref set.

Every non-null source/artifact pair on a fact must exist in that verified
bundle with the declared source kind, and every evidence ref of every selected
artifact must be present directly on the fact. A root bundle ref alone is not
fact provenance. eBUS B509/B524/B555 identity must be deep-equal to the
verified artifact identity. A B524 OP=0x02 artifact cannot be relabeled as
OP=0x06. Cloud source/artifact pairs are checked the same way.

An eeBUS service/entity/feature/path is accepted only when the referenced
verified artifact carries that complete path. A service-only artifact may bind
`eebus_service` for `RAW_ONLY` review, but it cannot bind an entity, feature,
numeric observation, or semantic comparison. The current MSP-065 v1
`services.list` evidence carries a service anchor but no entity/feature/value,
so the canonical graph has no evaluated sample and no `CANDIDATE` or
`CONFLICTED` fact. A service anchor never licenses invented entity or feature
selectors.

`source_bundle.replay_hash` is not a file hash. It is lowercase SHA-256 over
ASCII `HELIANTHUS:SYNCHRONIZED-EVIDENCE-REPLAY:V1`, one NUL byte, then RFC
8785/JCS bytes of the regenerated replay object. A trailing newline, JSON
indentation, or object member order therefore cannot change this digest.

## Candidate Fact Nodes

Each node is closed and contains:

- a local `candidate_id` and proposed protocol-agnostic path;
- a draft value and unit, or explicit `null`;
- status, terminal negative state, confidence, and a domain-separated fact
  hash;
- exact native provenance and immutable native evidence refs;
- a comparator draft reference, captured sample inputs, and draft outcome;
- a falsifier with the terminal state produced when observed; and
- a bounded, explicit `retest_trigger`.

The proposed path is a review key, not a stable semantic path. There is no family inheritance
and no sibling inheritance. Device inheritance, nearby-log inference, and
fallback from another candidate are also forbidden. Every non-null native
identity is complete on that node.

### Status And terminal states

The closed statuses are:

- `RAW_ONLY`: provenance is reviewable but no semantic claim is accepted;
- `CANDIDATE`: the draft comparator matched within its declared parameters;
- `CONFLICTED`: valid draft inputs disagree and no precedence is selected; and
- `WITHHELD`: the draft value is unavailable for semantic use.

The terminal negative states are `NO_SIGNAL`, `CLOUD_ONLY`, `CONFLICT`, and
`NOT_TESTED`. A terminal negative state requires status `WITHHELD`, a null
draft value/unit, `debug_only=true`, a falsifier, and a retest trigger. It is
terminal for this evidence bundle only. Retest creates a new candidate graph;
it never mutates or upgrades the old node. `CONFLICTED` is an in-progress
draft disagreement; a concluded negative result is `WITHHELD/CONFLICT`.

Confidence is closed metadata, not promotion authority. It records `level`,
`basis`, and `score_milli`. High confidence cannot bypass M8/M8.5 or make a
candidate stable.

### Fail-closed provenance/status matrix

This fail-closed provenance/status matrix is normative. No unlisted
combination is valid:

| Status / terminal | Required direct provenance | Samples and outcome | Draft value |
| --- | --- | --- | --- |
| `RAW_ONLY` / null | At least one reviewable native or root ref; any selected artifact contributes all of its refs | no samples; `NOT_EVALUATED` | null |
| `CANDIDATE` / null | complete eBUS identity and complete eeBUS service/entity/feature path, with both native artifacts and refs | non-empty, directly bound cross-runtime samples; recomputed `MATCH` | recomputed final rounded eeBUS value and target unit |
| `CONFLICTED` / null | same complete direct eBUS and eeBUS provenance as `CANDIDATE` | non-empty samples; recomputed `CONFLICT` | null |
| `WITHHELD` / `CLOUD_ONLY` | a verified cloud artifact and its refs, and no native substitute | no samples; `NOT_EVALUATED` | null |
| `WITHHELD` / `NO_SIGNAL` | at least one selected native artifact and all its refs | no samples; `NOT_EVALUATED` | null |
| `WITHHELD` / `NOT_TESTED` | bundle provenance only, or incomplete native provenance | no samples; `NOT_EVALUATED` | null |
| `WITHHELD` / `CONFLICT` | complete direct eBUS and eeBUS provenance | non-empty samples; recomputed `CONFLICT` | null |

Cloud-only evidence cannot escape `WITHHELD/CLOUD_ONLY`. Cloud evidence ids
are exactly `public-evidence:sha256:<64 lowercase hex>` and the digest must be
one of the selected verified cloud artifact's evidence-ref digests. An
arbitrary publishable-looking token is invalid.

## Exact Native Provenance

Every provenance record binds its native evidence refs to the root bundle.
References are copied exactly and must be members of the synchronized bundle's
immutable reference set.

eBUS identity is a closed B509/B524/B555 union:

- `B509`: target pseudonym/address/product, register family/id,
  unit/scale source, and evidence role;
- `B524`: target pseudonym, source/target address context, exact
  `(opcode, GG, II, RR)`, group meaning, instance gate, register category, and
  unit/scale source; and
- `B555`: target pseudonym, device family, schedule/program, slot, day, time,
  operation-mode context, and unit/scale source.

For B524, OP=0x02 and OP=0x06 are different namespaces even when `GG`, `II`,
and `RR` are byte-for-byte equal. The complete tuple is compared; the graph
never inherits an opcode or group from a family or sibling record.

An eeBUS provenance record carries a redacted service/entity/feature/path as
three explicit identifiers plus an ordered `feature_path`. Its first three
segments are exactly `SERVICE`, `ENTITY`, and `FEATURE`; optional `FIELD`
segments follow. A service, entity, or feature from another evidence row may
not fill a missing segment. The path is native evidence identity, not a stable
semantic hierarchy and not a publication of restricted feature meaning.

Cloud/app provenance is optional and only accepts a bound publishable evidence id.
It cannot replace missing eBUS or eeBUS identity. A cloud-only observation
ends as `WITHHELD/CLOUD_ONLY`.

## Comparator Draft

V1 has one registry entry, `NUMERIC_WINDOW_V1_DRAFT`. It is a draft, not a
stable comparator API. Every evaluation references the complete root
definition, whose pass/fail parameters are:

- bounded start/end window;
- absolute decimal tolerance and relative parts-per-million tolerance;
- explicit identity or affine unit conversion with decimal scale and offset;
- rounding mode and decimal places;
- `minimum_samples`;
- `maximum_missing_samples`;
- `stale_cutoff_ns`; and
- an absolute and consecutive-sample `conflict_threshold`.

Exact decimals are canonical strings. Every sample has an eBUS left side and
an eeBUS right side. Each side selects one verified source id, artifact id,
artifact evidence ref, recorder ingest offset, native value JSON pointer, and
native unit JSON pointer. The copied decimal/unit must deep-equal the selected
native values. The side ref must occur both on the artifact and directly on the
fact. This is the native observation pointer binding; caller-supplied decimal
text has no authority by itself.

The deterministic evaluator performs these steps in order:

1. reject duplicate canonical samples before any sample can count;
2. resolve both pointers against the verified artifact and require the copied
   value, unit, evidence ref, source kind, ids, and ingest offset to match;
3. derive `MISSING` when either selected value or unit is null, derive `STALE`
   when either age is strictly greater than `stale_cutoff_ns`, otherwise derive
   `PRESENT`, and reject a caller state that differs;
4. for `PRESENT`, compute the left value as `left * scale + offset`, then apply
   the declared rounding to converted left and native right (`HALF_EVEN` uses
   the declared decimal places; `NONE` requires null places);
5. compute `delta = abs(left - right)` and `allowed = absolute tolerance plus relative tolerance`,
   where relative tolerance is `abs(right) * relative_ppm / 1,000,000`; equality
   with `allowed` is a match;
6. count `MISSING` and `STALE` together against `maximum_missing_samples` and
   exclude both from `minimum_samples`;
7. count a conflict when `delta >= conflict_threshold.absolute_decimal` for
   the declared number of consecutive `PRESENT` samples; an unavailable or
   below-threshold sample resets the run; and
8. return `CONFLICT` first, otherwise `INDETERMINATE` when an availability or
   minimum-sample bound fails, otherwise `MISMATCH` when any present delta is
   over tolerance, otherwise `MATCH`. An empty list alone returns
   `NOT_EVALUATED`.

All arithmetic is exact decimal arithmetic with sufficient fixed precision for
the bounded 64-character inputs. Sample offsets are captured monotonic offsets
from the evidence bundle. The evaluator does not read a clock or acquire more
samples. `MATCH`, `MISMATCH`, `CONFLICT`, `INDETERMINATE`, and `NOT_EVALUATED`
are draft outcomes only. The stored outcome must equal the recomputed outcome;
it is never caller-controlled.

## Deterministic Ordering And Hashes

Hash material uses the RFC 8785/JCS subset enforced by the validator: UTF-8,
bytewise UTF-8 object-key ordering, shortest JSON strings, integers only within
the portable JSON safe-integer range, and exact decimals encoded as strings.
Non-finite numbers and negative zero are forbidden.

Evidence refs sort by kind, digest algorithm, digest, repository, commit, and
path, with null before a string. Comparator samples sort by offset and then
their canonical bytes. Facts sort by proposed path and candidate id using
bytewise UTF-8 order. Duplicate ids, refs, paths, or samples are rejected.

Fact hashes use ASCII `HELIANTHUS:DRAFT-CANDIDATE-FACT:V1`, one NUL byte, then
JCS of the fact without `fact_hash`. The graph hash uses ASCII
`HELIANTHUS:DRAFT-CANDIDATE-FACT-GRAPH:V1`, one NUL byte, then JCS of the root
without `graph_id` and `graph_hash`. IDs carry the corresponding lowercase
SHA-256 digest.

Offline replay uses captured evidence and stored comparator samples only. It
must not read the network, must not read the wall clock, and must not use
locale, randomness, mutable files, environment-derived identity, or runtime
state. Replay emits facts in graph order and regenerates exact JCS bytes plus
a domain-separated replay hash. Repeated replay of the same verified graph is
byte-identical.

## Bounded Limits

The limits are part of the hash view and must equal the closed registry:

| Limit | V1 value |
| --- | ---: |
| `max_graph_bytes` | 1,048,576 |
| `max_depth` | 32 |
| `max_facts` | 64 |
| `max_evidence_refs_per_fact` | 16 |
| `max_samples_per_comparator` | 1,024 |
| `max_string_bytes` | 4,096 |
| `max_path_segments` | 32 |
| `max_total_members` | 16,384 |
| `max_total_list_items` | 8,192 |

Before `json.loads`, a pre-parse byte scanner enforces graph bytes, nesting
depth, serialized string bytes, total object members, total list items, and
the per-list ceiling. The iterative canonicalization preflight enforces the
same budgets before graph or replay serialization. The serialized graph must
declare exactly the registry ceilings. Limit failure produces no partial graph
or replay and cannot recurse or allocate an unbounded decoded object first.

## Validation Precedence

Validation stops at the first category in this order:

1. `json.syntax` - bytes, duplicate keys, encoding, canonical-number subset;
2. `schema.graph` - closed shape, types, enums, and contract version;
3. `limits.exceeded` - declared and observed resource limits;
4. `registry.binding` - exact registry contract/version/digest;
5. `provenance.binding` - bundle identity and evidence-ref membership;
6. `identity.native` - complete direct B509/B524/B555 and eeBUS path identity;
7. `ordering.invalid` - deterministic ordering and uniqueness;
8. `state.terminal` - status, confidence, falsifier, and terminal-state matrix;
9. `comparator.invalid` - parameters, samples, and outcome consistency;
10. `anti_leak.consumer` - candidate-only channel and all false exposure flags;
11. `hash.fact` - fact content hashes; and
12. `hash.graph` - graph content hash and id.

Unsupported internal combinations are contract violations; validators do not
invent another state or silently normalize an input.

For bounded graph inputs, the CLI parses and validates graph `json.syntax`,
`schema.graph`, `limits.exceeded`, and `registry.binding` before it opens or
verifies either source input. Source bundle/replay syntax, synchronized replay,
and source registry failures map to `provenance.binding`; they cannot preempt
an earlier graph defect. The allocation-safety pre-parse ceilings run before
recursive parsing by necessity and therefore have absolute priority for an
oversized or over-deep byte stream.

## Stable Consumer Anti-Leak

Candidate facts, draft values, native paths, evidence refs, and replay results
must remain absent from every stable surface:

- stable documentation navigation;
- stable documentation search;
- stable sitemap;
- versioned documentation bundle;
- release documentation bundle;
- `ebus.v1.*` MCP outputs;
- GraphQL;
- Portal;
- Home Assistant;
- command routing;
- promoted semantic outputs; and
- stable semantic registry projections.

The repository test vector intentionally flips a stable-exposure bit and must
fail as `anti_leak.consumer`. No Promotion Or Translation occurs in this
milestone. Promotion, GraphQL, Portal, HA, commands, stable semantics, and
protocol translation are outside this contract and require later issues.
