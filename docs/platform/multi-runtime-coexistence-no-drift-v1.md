Canonical source: this page.

# Multi-Runtime Coexistence No-Drift V1

Issue: `Project-Helianthus/helianthus-docs-ebus#365` (`MSP-08`, M8).

Plan provenance: the locked multi-runtime semantic platform plan, its `MSP-08`
row, and predecessor completion token
`MSP-07@ff511b035b85aef6123fb0853bb3d2f3af6fc01e`. The canonical M7 candidate
graph documentation input is commit
`ea88fef23ecb154b08f70e7f94b36e1738ed08bf`.

## Purpose And Boundary

This language-neutral executable contract proves EEBUS-G18 coexistence no
drift. It freezes a complete eBUS/consumer baseline, captures five compared
runs, derives every result in an offline verifier, and accepts only when the
protected outputs remain byte-equal after the closed normalization procedure.
It is additive documentation and evidence machinery. It does not change a
runtime API.

Existing promoted eBUS leaves remain authoritative. eeBUS candidate and
conflict facts may appear only on the existing internal
`CANDIDATE_DEBUG_REPLAY` evidence channel. They never override, merge into, or
route through `ebus.v1`, GraphQL, Portal, Home Assistant, command routing, or
the promoted semantic registry.

Across every compared state, existing promoted eBUS leaves remain authoritative.

This milestone preserves the stable `eebus.v1` V1 contract and all existing
eBUS/consumer contracts. There is no public V2. M8 does not promote a leaf,
define a protocol translation, add a command route, or authorize a consumer.

EEBUS-G18 is only the no-drift gate. G17 advertisement/discovery and trust
evidence and G19 direct outbound VR940 TCP/TLS/WebSocket/SHIP and first SPINE
data are excluded. A G17 or G19 claim makes this artifact invalid.

The repository positive fixture is synthetic offline evidence. It is not a
canonical positive live VR940 claim and cannot be cited as one. It contains no
vendor-restricted material or private protocol text.

## Closed Machine Contract

The canonical artifacts are:

- `docs/platform/multi-runtime-coexistence-no-drift-v1.md`;
- `docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json`,
  schema ID
  `https://docs.helianthus.local/schemas/multi-runtime-coexistence-evidence-v1.schema.json`;
- `docs/platform/schemas/multi-runtime-coexistence-report-v1.schema.json`,
  schema ID
  `https://docs.helianthus.local/schemas/multi-runtime-coexistence-report-v1.schema.json`;
- `docs/platform/schemas/multi-runtime-coexistence-registry-v1.json`;
- `scripts/validate_multi_runtime_coexistence.py`;
- `scripts/generate_multi_runtime_coexistence_fixture.py`; and
- `docs/platform/fixtures/coexistence-no-drift/v1`.

The evidence contract ID is
`helianthus.platform.multi-runtime-coexistence-evidence.v1`. The derived report
contract ID is
`helianthus.platform.multi-runtime-coexistence-report.v1`. The registry ID is
`helianthus.platform.multi-runtime-coexistence-registry.v1`.

Unknown fields, duplicate JSON keys, malformed UTF-8, non-integer JSON
numbers, negative zero, integers outside the portable JSON safe-integer range,
unknown enum members, missing required objects, and out-of-bound inputs are
rejected. No unknown field is ignored. The input evidence has no verdict
field: `PASS` exists only in the verifier-derived report.

The executable command is:

```text
validate_multi_runtime_coexistence.py verify \
  --evidence <coexistence-evidence.json> \
  --registry <multi-runtime-coexistence-registry-v1.json> \
  --m7-graph <draft-candidate-fact-graph.json> \
  --m7-replay <draft-candidate-fact-replay.json> \
  --m7-registry <draft-candidate-fact-registry-v1.json> \
  --m7-source-bundle <synchronized-evidence-bundle.json> \
  --m7-source-replay <synchronized-evidence-replay.json>
```

Replace `verify` with `report` to emit exact RFC 8785/JCS-subset report bytes.
`verify` emits only `ok`. Failure emits exactly one validation category and no
partial report.

## Frozen Protected Views

The baseline and every compared run contain all eleven views in this exact
order. A caller cannot select a subset.

| View ID | Frozen meaning |
| --- | --- |
| `mcp.ebus.v1.responses` | Complete selected `ebus.v1` MCP responses |
| `mcp.tool.inventory` | Existing MCP namespace/tool inventory |
| `graphql.schema` | GraphQL schema |
| `graphql.ebus.values` | GraphQL eBUS values |
| `ha.graphql.values` | HA-consumed GraphQL values |
| `ha.identity` | HA identity |
| `debug.ebus` | Existing eBUS debug output |
| `portal.ebus.bootstrap` | Portal bootstrap and eBUS projection |
| `command.routing` | Existing command routing |
| `semantic.registry` | Existing promoted semantic registry |
| `mcp.eebus.v1.contract` | Stable `eebus.v1` V1 contract |

Every view binds its exact capture path, JSON media type, unmodified payload,
raw payload hash, shape hash, and canonical payload hash. Every raw payload is
also an immutable run input with the same digest and exact canonical byte
length. Missing, duplicate, added, or reordered views fail closed.

## Canonicalization And Equality

Hash input uses the RFC 8785/JCS integer subset enforced by the verifier:
UTF-8, bytewise UTF-8 object-key order, shortest JSON string encoding, JSON
integers only, no negative zero, and no locale-dependent formatting.

The exact algorithm for each view is:

1. Verify the unmodified payload's domain-separated raw hash.
2. Derive and verify a domain-separated shape hash. Object keys, array length
   and order, scalar type, and null placement are all retained.
3. Resolve every registry-declared timestamp pointer. The pointer must exist
   and select a string. Perform timestamp replacement with `<TIMESTAMP>`.
4. Resolve every registry-declared mask pointer under the bound mask scope.
   The pointer must exist and select a string. Perform mask replacement with
   `<MASKED>`.
5. Do not delete either field. No wildcard, caller-supplied pointer, or
   recursive field stripping is allowed.
6. Serialize the replaced object to canonical bytes and verify its
   domain-separated canonical payload hash.
7. Require exact shape-hash equality, canonical-hash equality, and canonical
   byte equality with the baseline.

The timestamp and mask pointer sets are part of the hashed normalization
profile and must equal the registry byte-for-byte. This contract cannot pass
by dropping fields. A removed field changes shape and canonical bytes; adding
or dropping a field is drift even when a caller recomputes its own hashes.
In exact terms, the contract cannot pass by dropping fields from any protected
payload.

The raw, shape, and canonical domains are respectively:

```text
HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-RAW-PAYLOAD:V1
HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-PAYLOAD-SHAPE:V1
HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-CANONICAL-PAYLOAD:V1
```

Each digest is lowercase SHA-256 over the ASCII domain, one NUL byte, and the
canonical bytes. Equality is verifier-derived. Caller-asserted hashes,
booleans, or verdicts have no authority.

## Required Scenario Sequence

Runs are ordered by increasing monotonic capture offset. Their IDs, states,
runtime/config provenance, immutable inputs, state evidence, and protected
views are closed.

| State | Required state evidence | Consumer result |
| --- | --- | --- |
| `EEBUS_DISABLED_BASELINE` | eeBUS runtime and candidate graph disabled; zero services/candidates/conflicts | Frozen baseline from gateway parent `ff511b035b85aef6123fb0853bb3d2f3af6fc01e` |
| `EEBUS_DISABLED_CONFIRMED` | New runtime, both features disabled | Exact no drift |
| `EEBUS_ENABLED_NO_SERVICES` | Both features enabled, zero services, explicit `NO_SERVICES_OBSERVED`, degraded true | Expected no-services with exact no drift |
| `EEBUS_CONNECTED_CANDIDATE_ONLY` | At least one service and one synthetic `CANDIDATE` fact on `CANDIDATE_DEBUG_REPLAY` | Candidate confined; exact no drift |
| `EEBUS_CONFLICTED_WITHHELD` | At least one service and one synthetic `WITHHELD/CONFLICT` fact on `CANDIDATE_DEBUG_REPLAY` | Conflict visible internally and withheld; exact no drift |
| `EEBUS_DISABLED_ROLLBACK` | Runtime and graph disabled again | Exact baseline restored |

`empty_success` is always false. The no-service and conflicted states are
explicit outcomes, not generic success. A missing state record, zero-length
run list, generic `PASS`, or no-services run that omits its degraded outcome is
invalid. There is no empty-success path.

## Provenance Binding

Every result binds all of the following:

- exact gateway repository, 40-character source commit and parent commit;
- runtime artifact ID, byte digest, byte length, build manifest, and
  domain-separated build-manifest hash;
- exact config payload and domain-separated config hash;
- read-only auth scope, permissions, and domain-separated auth-scope hash;
- normalization/mask scope digest;
- capture clock ID, UTC anchor, monotonic epoch, measured maximum clock error,
  maximum evidence age, verification offset, and clock hash;
- every protected raw payload digest and exact canonical byte length;
- the supplied M7 graph and replay digests and exact canonical byte lengths;
  and
- evidence ID/hash and registry content digest.

The M7 graph is not accepted from hashes alone. The verifier invokes the
existing synchronized-evidence and candidate-fact validators, regenerates the
M7 replay, requires deep equality with the supplied replay, and then requires
the exact frozen graph and replay IDs/hashes. The supplied graph, replay,
registry, synchronized bundle, and synchronized replay are immutable inputs.

The baseline runtime source is exact gateway main
`ff511b035b85aef6123fb0853bb3d2f3af6fc01e`. All compared and rollback runs
must use one exact new runtime identity whose parent is that baseline. A
missing, duplicate, stale, reordered, mismatched, or unhashed provenance item
fails closed. Capture age is derived only from bound monotonic offsets; replay
does not read the wall clock.

## Authority And Anti-Leak Rules

The internal candidate facts prove visibility without publication. Their
closed fields are candidate ID, status, terminal state, and visibility
channel. The candidate run accepts only `CANDIDATE` with no terminal state.
The conflict run accepts only `WITHHELD` with terminal `CONFLICT`.

Protected outputs must contain no candidate/conflict field or value. In
particular, candidate or conflict material cannot appear in:

- `ebus.v1` MCP responses;
- the MCP public inventory;
- GraphQL schema or values;
- HA-consumed GraphQL values or HA identity;
- eBUS debug output;
- Portal bootstrap;
- command routing; or
- the promoted semantic registry.

The semantic registry authority remains `ebus.promoted`, and every existing
command route remains sourced from eBUS. The stable `eebus.v1` namespace stays
version 1. No `.v2` tool or public contract is permitted. Separate eeBUS raw,
debug, or candidate evidence does not become an `ebus.v1` value and does not
authorize protocol translation.

## Rollback

Rollback disables the eeBUS runtime and candidate graph in the same compared
runtime artifact. The verifier requires `EEBUS_DISABLED_ROLLBACK`, disabled
config bits, explicit `ROLLBACK_BASELINE_RESTORED`, zero service/candidate/
conflict counts, and exact shape and canonical bytes for all protected views.
Rollback succeeds only when it demonstrates restoration of the exact
baseline. Restart success or an empty response is not rollback evidence.

## Validation Precedence

Validation stops at the first category in this exact order:

1. `json.syntax`
2. `limits.exceeded`
3. `schema.evidence`
4. `registry.binding`
5. `provenance.m7`
6. `provenance.runtime`
7. `provenance.config`
8. `provenance.auth_mask`
9. `provenance.clock`
10. `ordering.duplicate`
11. `state.evidence`
12. `view.coverage`
13. `canonicalization.invalid`
14. `hash.payload`
15. `anti_leak.candidate`
16. `authority.ebus`
17. `gate.scope`
18. `drift.consumer`
19. `rollback.drift`
20. `hash.evidence`

Allocation-driving byte, nesting, string, member, and list limits run before
recursive parsing by necessity. They still report `limits.exceeded`.
Validation emits no partial success or report.

## Resource Bounds

| Limit | V1 value |
| --- | ---: |
| `max_evidence_bytes` | 2,097,152 |
| `max_depth` | 32 |
| `max_runs` | 8 |
| `max_views_per_run` | 16 |
| `max_inputs_per_run` | 16 |
| `max_internal_facts_per_run` | 64 |
| `max_payload_bytes` | 262,144 |
| `max_string_bytes` | 4,096 |
| `max_total_members` | 65,536 |
| `max_total_list_items` | 32,768 |

The evidence declares these exact values and the verifier hard-codes the same
ceilings. Raising, lowering, omitting, or exceeding a ceiling is invalid.

## EEBUS-G18 Evidence Artifact

The transport-gate evidence artifact is the closed evidence JSON plus its
verifier-derived report. It proves coexistence only and is suitable for the
`eebus_v0` G18 row. It does not satisfy G17 or G19 and does not require a live
outbound connection.

The positive fixture IDs are:

- `MSP08-G18-SYNTHETIC-POSITIVE-001`; and
- `MSP08-G18-SYNTHETIC-REPORT-001`.

The generated report includes the exact baseline runtime identity and eleven
view hashes, all five scenario results and view hashes, the six-row acceptance
matrix, the exact M7 binding, and the rollback result. `PASS` is emitted only
after every validation stage completes.

## Acceptance Matrix

Each state must pass every listed check. No cell is caller-provided.

| State | Provenance | Explicit state | Complete views | Hashes | Shape | Canonical bytes | eBUS authority | Candidate confined | V1 only | G18 only |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Disabled baseline | required | required | required | required | anchor | anchor | required | required | required | required |
| Disabled confirmed | required | required | required | required | equal | equal | required | required | required | required |
| Enabled/no services | required | required, degraded | required | required | equal | equal | required | required | required | required |
| Connected/candidate | required | required | required | required | equal | equal | required | required | required | required |
| Conflicted/withheld | required | required, degraded | required | required | equal | equal | required | required | required | required |
| Disabled rollback | required | required | required | required | equal | equal | required | required | required | required |

The machine check IDs are `PROVENANCE_BOUND`,
`STATE_EVIDENCE_EXPLICIT`, `PROTECTED_VIEW_SET_COMPLETE`,
`PAYLOAD_HASHES_VERIFIED`, `SHAPE_IDENTICAL`,
`CANONICAL_BYTES_IDENTICAL`, `EBUS_AUTHORITY_PRESERVED`,
`CANDIDATE_CONFINED`, `V1_SURFACES_PRESERVED`, and
`G18_SCOPE_ONLY`.

## Mutation Classes

The negative fixtures are descriptors; tests apply each mutation to the
positive evidence and require one precedence category.

| Fixture mutation | Required category |
| --- | --- |
| `CANDIDATE_LEAK_EBUS_MCP` | `anti_leak.candidate` |
| `CANONICAL_HASH_MISMATCH` | `hash.payload` |
| `CLOCK_MISMATCH` | `provenance.clock` |
| `CONFIG_HASH_MISMATCH` | `provenance.config` |
| `CONFLICT_LEAK_GRAPHQL` | `anti_leak.candidate` |
| `DROPPED_PAYLOAD_FIELD` | `drift.consumer` |
| `DUPLICATE_PROVENANCE` | `ordering.duplicate` |
| `G17_CLAIM` | `gate.scope` |
| `G19_CLAIM` | `gate.scope` |
| `INPUT_HASH_MISMATCH` | `provenance.runtime` |
| `M7_GRAPH_MISMATCH` | `provenance.m7` |
| `MASK_SCOPE_MISMATCH` | `provenance.auth_mask` |
| `MISSING_PROVENANCE` | `schema.evidence` |
| `MISSING_REQUIRED_VIEW` | `view.coverage` |
| `NO_SERVICES_EMPTY_SUCCESS` | `state.evidence` |
| `PUBLIC_V2_SURFACE` | `gate.scope` |
| `RESOURCE_LIMIT_EXCEEDED` | `limits.exceeded` |
| `ROLLBACK_DRIFT` | `rollback.drift` |
| `RUNTIME_ARTIFACT_MISMATCH` | `provenance.runtime` |
| `STALE_CAPTURE` | `provenance.clock` |
| `TIMESTAMP_EXCLUSION_MISMATCH` | `canonicalization.invalid` |
| `UNKNOWN_FIELD` | `schema.evidence` |

## Gateway RED Handoff

The next gateway RED test should vendor or fetch these exact docs artifacts by
immutable docs commit, then emit one evidence JSON conforming to the evidence
schema. It must supply all five M7 validation inputs to the verifier. Expected
runtime output paths are the registry `capture_path` values under
`artifacts/protected/`; candidate-only facts remain in the separate internal
capture for `CANDIDATE_DEBUG_REPLAY`.

Gateway acceptance must exercise the six registry scenario IDs in order, use
the eleven protected view IDs without substitution, and run all twenty-two
mutation classes. Its G18 artifact is the input evidence plus exact report
bytes. A gateway test must not replace the verifier with a caller comparison,
drop fields before capture, extend masking, infer a state from missing data,
or claim G17/G19 from this contract.
