Canonical source: this page.

# Draft Candidate Fact Graph V1

Issue: `Project-Helianthus/helianthus-docs-ebus#359` (`MSP-07`, M7).

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
bundle with the declared source kind, and every artifact evidence ref must be
present on the fact. eBUS B509/B524/B555 identity must be deep-equal to the
verified artifact identity. A B524 OP=0x02 artifact cannot be relabeled as
OP=0x06. Cloud source/artifact pairs are checked the same way.

An eeBUS service/entity/feature/path is accepted only when the referenced
verified artifact carries that complete path. The current MSP-065 v1
`services.list` evidence carries a service anchor but no entity/feature path,
so M7 must leave the path null and withhold any claim that needs it. A service
anchor never licenses invented entity or feature selectors.

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

Cloud/app provenance is optional and only accepts a publishable evidence id.
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

Exact decimals are canonical strings. Sample offsets are captured monotonic
offsets from the evidence bundle. The evaluator does not read a clock or
acquire more samples. `MATCH`, `MISMATCH`, `CONFLICT`, `INDETERMINATE`, and
`NOT_EVALUATED` are draft outcomes only. The result is invalid if sample
ordering, bounds, missing/stale accounting, or status/outcome consistency does
not satisfy the validator.

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

An implementation may configure a lower ceiling before capture, but the
serialized graph declares the effective values and cannot exceed or alter the
registry values. Limit failure produces no partial graph or replay.

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
