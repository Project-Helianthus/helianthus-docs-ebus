Canonical source: this page.

# Multi-Runtime Coexistence No-Drift V1

Issues: `Project-Helianthus/helianthus-docs-ebus#365` (`MSP-08`, M8),
`Project-Helianthus/helianthus-docs-ebus#391` (`MSP-08-LIVE-R1`), and
`Project-Helianthus/helianthus-docs-ebus#407` (stable MCP V1 inventory
alignment).

The historical synthetic predecessor is gateway commit
`ff511b035b85aef6123fb0853bb3d2f3af6fc01e` with candidate-graph docs commit
`ea88fef23ecb154b08f70e7f94b36e1738ed08bf`. The live predecessor is the M7
gateway merge `8bcba2107d10b149f984ac9546ea6427a9cda8a1` with M7 docs merge
`35d2eba256a77b6575a2b45c07e73f054ff74ced`. These are ordinary source
provenance bindings, not execution authorization.

## Purpose And Boundary

This language-neutral executable contract proves EEBUS-G18 coexistence no
drift. Its synthetic profile freezes a complete eBUS/consumer baseline and
captures five compared runs. Its live profile captures four states with the
same exact gateway artifact: connected baseline, raw/withheld evidence,
restart persistence, and connected rollback after the evidence graph is
dropped. Every result is derived in an offline verifier and accepted only when
the protected outputs remain byte-equal after the closed normalization
procedure. It is additive documentation and evidence machinery. It does not
change a runtime API.

Existing promoted eBUS leaves remain authoritative. eeBUS candidate and
conflict facts may appear only on the existing internal
`CANDIDATE_DEBUG_REPLAY` evidence channel. They never override, merge into, or
route through `ebus.v1`, GraphQL, Portal, Home Assistant, command routing, or
the promoted semantic registry.

Across every compared state, existing promoted eBUS leaves remain authoritative.

This milestone preserves the stable `eebus.v1` V1 contract and all existing
eBUS/consumer contracts. There is no public V2. M8 does not promote a leaf,
define a protocol translation, add a command route, or authorize a consumer.

The protected MCP inventory is the exact stable read-only inventory exercised
by coexistence capture. It contains the current eBUS registry and semantic
snapshot reads:

- `ebus.v1.registry.devices.list`;
- `ebus.v1.semantic.snapshot.get`.

It also contains all nine stable raw eeBUS V1 tools, in canonical order:

- `eebus.v1.runtime.status.get`;
- `eebus.v1.services.list`;
- `eebus.v1.services.get`;
- `eebus.v1.sessions.list`;
- `eebus.v1.sessions.get`;
- `eebus.v1.topology.get`;
- `eebus.v1.snapshot.capture`;
- `eebus.v1.snapshot.drop`;
- `eebus.v1.pairing.status.get`.

This is an exact V1 contract assertion, not a compatibility alias set. Missing,
additional, stale, reordered, write-capable, legacy, or V2 entries fail closed.
It is the complete protected inventory declared by this gate, not a copy of an
operator endpoint's larger experimental inventory. Each listed tool must be
derived independently from the effective boundary in every capture window.

EEBUS-G18 is only the no-drift gate. G17 advertisement/discovery and trust
evidence and G19 direct outbound VR940 TCP/TLS/WebSocket/SHIP and first SPINE
data are excluded. A G17 or G19 claim makes this artifact invalid.

The repository positive fixture is synthetic offline evidence. It is not a
canonical positive live VR940 claim and cannot be cited as one. The captured
runtime profile instead validates the supplied M7 graph and source evidence,
regenerates replay, and binds the result to the live M7 source commits above.
Neither profile contains vendor-restricted material or private protocol text.

The live M7 graph currently contains inspectable `RAW_ONLY` and `WITHHELD`
facts. M8 preserves those actual statuses and does not fabricate `CANDIDATE`
or `CONFLICTED` facts merely to satisfy a synthetic scenario. M8 does not
authorize M8.5 or M9 and does not promote any leaf.

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
- `docs/platform/schemas/draft-candidate-fact-public-status-v1.schema.json`;
- `scripts/validate_multi_runtime_coexistence.py`;
- `scripts/project_candidate_fact_public_status.py`;
- `scripts/generate_multi_runtime_coexistence_fixture.py`; and
- `docs/platform/fixtures/coexistence-no-drift/v1`.

The evidence contract ID is
`helianthus.platform.multi-runtime-coexistence-evidence.v1`. The derived report
contract ID is
`helianthus.platform.multi-runtime-coexistence-report.v1`. The registry ID is
`helianthus.platform.multi-runtime-coexistence-registry.v1`.

Every accepted evidence and report artifact declares
`export_tier=PUBLIC_REDACTED`. Raw operator captures are inputs to the gateway
harness, not valid instances of this public evidence contract.

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
  --m7-graph <private-draft-candidate-fact-graph.json> \
  --m7-replay <private-draft-candidate-fact-replay.json> \
  --m7-registry <draft-candidate-fact-registry-v1.json> \
  --m7-source-bundle <private-synchronized-evidence-bundle.json> \
  --m7-source-replay <private-synchronized-evidence-replay.json> \
  --m7-terminal-graph <public-source-terminal-graph.json> \
  --m7-terminal-replay <public-source-terminal-replay.json> \
  --m7-terminal-source-bundle <public-source-terminal-bundle.json> \
  --m7-terminal-source-replay <public-source-terminal-source-replay.json> \
  --before-source-manifest <before-source-capture-manifest.json> \
  --after-source-manifest <after-source-capture-manifest.json> \
  --before-source-root <private-before-source-directory> \
  --after-source-root <private-after-source-directory>
```

Replace `verify` with `report` to emit exact RFC 8785/JCS-subset report bytes.
`verify` emits only `ok`. Failure emits exactly one validation category and no
partial report. For captured-runtime evidence, both commands require the
private inputs, rederive the public status projection in-process, require exact
bytes, and bind the private graph, replay, source bundle, and source replay as
immutable inputs. They also require both private source-capture manifests and
bind their exact bytes as `source:capture-manifest` /
`SOURCE_CAPTURE_MANIFEST`. `verify-public` checks that the public binding is
well formed but cannot substitute for either private manifest; it emits
`public-only-ok` and cannot establish G18 PASS.

Each source manifest has contract
`helianthus.platform.multi-runtime-source-capture-manifest.v1`, declares
`window_scope=SINGLE_WINDOW_ONLY` and
`projection_policy=M8_PROTECTED_VIEWS_SINGLE_WINDOW_V1`, and binds the
effective auth-scope hash, PRE/POST phase, process instance, distinct window ID,
capture interval, and source timestamp. Its sixteen ordered inputs cover the
complete stable tool inventory visible at the effective read-only M8 test scope,
complete single-window eBUS responses, the eBUS debug view, owner-UNIX eeBUS
state inputs, GraphQL, Portal, command routing, semantic registry, container
identity, and capture timestamp with the exact auth boundary, byte length, and
SHA-256 of each source. The tool inventory must equal the frozen two `ebus.v1`
plus nine stable `eebus.v1` tools in canonical order; an extra write tool,
experimental tool, V2 tool, duplicate, omission, reordering, or paginated
continuation fails closed. The capture is valid only when `tools/list` proves
the complete effective-scope inventory in one terminal response.
Inventory visibility does not grant call authority. The M8 scope may call only
the two eBUS observation tools and the seven eeBUS observation tools. The
stable lifecycle tools `eebus.v1.snapshot.capture` and
`eebus.v1.snapshot.drop` remain visible so contract drift is detectable, but a
`tools/call` request for either must fail before snapshot-store creation,
lookup, or deletion. In particular, `snapshot.drop` cannot destroy evidence
through the read-only scope.
Private verification opens every source as a bounded regular file from a
fixed-name, no-symlink root, rejects devices such as FIFOs, recomputes every
binding, derives all eleven protected views with the closed reference projector,
and compares each derived payload byte-for-byte with the corresponding evidence
payload. Debug, Portal, routing, and semantic-registry inputs are captured
directly; they are not inferred from neighboring views. The complete raw
semantic registry remains bound in the private source manifest. The protected
G18 view is selected by the evidence-bound projection profile. Current M8.5
captures use the exact eleven-leaf cross-protocol core described below; only
the pinned pre-field captures use the legacy projection that excludes the
indexed program/day/slot fields `StartHour`, `StartMinute`, `EndHour`,
`EndMinute`, `TemperatureC`, and `TemperatureRaw`. Array indices use canonical
decimal spelling (`0` or a non-zero digit followed by decimal digits); leading-zero
forms fail closed. Raw leaf paths must arrive in strictly increasing bytewise
order, so the projection cannot normalize an ordering regression. Every raw
leaf is validated before deterministic projection. The complete protected
payload is source-bound: `data` comes from the projector, `meta.captured_at`
comes from the manifest window, and `meta.auth_subject` is the deterministic
public-redacted identifier of the manifest-bound effective auth scope. A
projector invocation receives one window only; consulting the opposite window,
intersecting device sets, dropping fields after comparison, or hard-coding an
observed result is invalid. Reused or swapped PRE/POST manifests, roots,
processes, timestamps, or capture intervals fail closed before no-drift is
evaluated. The protected payloads must be produced independently before
equality is tested.

The protected public projections retain admission and device state but replace
every eBUS address with the constant, non-enumerable
`redacted:opaque-address` placeholder. This includes device `address` and the
address-bearing `selected_source`, `last_successful_source`, and
`companion_target` fields. Device pseudonyms are derived from the ordinal in
the stable projected device list, never from the address or a caller-selected
identity. The public verifier recomputes every device pseudonym, its public
model alias, and its exact HA `model`, `unique_id`, and `via_device`
derivatives. Raw numeric or textual values under an address alias,
address-derived pseudonyms, and caller-chosen identity hashes fail the
public-redaction gate. The three admission fields' declared absent state remains
JSON `null`; it is not an identity value.

PRE and POST source windows require different manifest digests regardless of
their claimed byte lengths. Every source device row remains bound in the raw
private root and manifest. The stable identity projection selects only rows
whose runtime state is `identity_confirmed` and whose manufacturer and device
ID are complete. Incomplete passive observations such as
`corroborated_pending` addresses are retained as raw evidence but are not
promoted into a stable device identity. A malformed address, a confirmed row
with missing identity, or a window with no complete confirmed identity fails
closed. Household zone labels are deterministic public pseudonyms, never
copied from the private MCP or GraphQL source; source device IDs and model
labels are separately pseudonymized. Before return, the complete projected view tree is checked for
unconsumed decimals, so a fractional pass-through field fails with
`provenance.source_capture` rather than reaching canonical serialization.
Capture timestamps are derived exactly from the UTC wall anchor plus the
monotonic nanosecond offset and retain up to nine fractional digits.

An MCP JSON-RPC envelope may carry a `content[0].text` string up to the bounded
source-input ceiling. The verifier then decodes that string as JSON and applies
the ordinary 4,096-byte per-string, depth, member, and list limits independently
to the inner payload. This permits current multi-kilobyte topology responses
without allowing an unbounded semantic scalar.

Private MCP and GraphQL numeric source fields that the closed projector maps to
numeric strings are parsed as exact decimals, with at most 128 significant
digits and an absolute adjusted exponent of at most 1,024. Formatting is
context-independent fixed-point, removes insignificant fractional zeroes, and
never passes through a binary float; every positive zero form maps to `0`, and
negative zero is rejected. These fields accept only JSON integer, decimal, or
`null` values; booleans, strings, arrays, and objects fail closed. A fractional
number in a direct/unmodified protected view is not silently transformed and
fails `provenance.source_capture`.

The public M7 status projection is generated, never hand-authored:

```text
project_candidate_fact_public_status.py \
  --graph <private-draft-candidate-fact-graph.json> \
  --replay <private-draft-candidate-fact-replay.json> \
  --registry <draft-candidate-fact-registry-v1.json> \
  --source-bundle <private-synchronized-evidence-bundle.json> \
  --source-replay <private-synchronized-evidence-replay.json> \
  --source-commit <40-character-gateway-commit> \
  --docs-source-commit <40-character-docs-commit> \
  --expect <committed-public-status.json>
```

The projector first runs the complete synchronized-evidence and candidate-fact
validators, regenerates the candidate replay, and then emits deterministic
public bytes containing only candidate ID, fact hash, status, and terminal
class. `--expect` requires byte-for-byte equality with the committed public
projection. A changed but otherwise valid graph or replay fails
`projection.binding`; invalid private input fails in its originating validator.
Private inputs remain outside git.

## Frozen Protected Views

The baseline and every compared run contain all eleven views in this exact
order. A caller cannot select a subset.

| View ID | Frozen meaning |
| --- | --- |
| `mcp.ebus.v1.responses` | Complete selected `ebus.v1` MCP responses; no post-hoc entity subset |
| `mcp.tool.inventory` | Complete protected eleven-tool inventory derived at the effective boundary |
| `graphql.schema` | GraphQL schema |
| `graphql.ebus.values` | GraphQL eBUS values |
| `ha.graphql.values` | HA-consumed GraphQL values |
| `ha.identity` | HA identity |
| `debug.ebus` | Existing eBUS debug output |
| `portal.ebus.bootstrap` | Portal bootstrap and eBUS projection |
| `command.routing` | Existing command routing |
| `semantic.registry` | Fixed M8.5 cross-protocol eBUS core of 11 promoted leaves; the source capture still retains the complete registry |
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

## Required Scenario Profiles

Runs are ordered by increasing monotonic capture offset. Their IDs, states,
runtime/config provenance, immutable inputs, state evidence, and protected
views are closed.

### Synthetic Offline Fixture

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

### Captured Runtime Evidence

All four states use the same exact gateway artifact and keep the eeBUS runtime
connected. Candidate evidence is an offline harness input and remains confined
to `CANDIDATE_DEBUG_REPLAY`; it does not alter the runtime's public surfaces.
The runtime artifact must use `REPRODUCIBLE_BUILD`. This field is a structural
M8 claim; the downstream M8.5 private verifier closes it by rebuilding the
exact clean source commit with the declared toolchain and comparing the output
byte-for-byte with the deployed binary. A `SYNTHETIC_FIXTURE` build remains
conformance-only, and relabeling arbitrary bytes cannot pass that downstream
rebuild gate even if every caller-controlled hash is recomputed.

| State | Required state evidence | Consumer result |
| --- | --- | --- |
| `EEBUS_CONNECTED_BASELINE` | Runtime connected; graph absent; at least one visible service | Live baseline captured with exact no drift |
| `EEBUS_CONNECTED_RAW_WITHHELD` | Validated M7 graph present; real `RAW_ONLY` and `WITHHELD` counts and facts | Raw-first facts confined; exact no drift |
| `EEBUS_RESTART_PERSISTED` | Same artifact after restart; runtime connected; same validated graph | Trust/session visibility survives restart; exact no drift |
| `EEBUS_CONNECTED_ROLLBACK` | Runtime stays connected; graph evidence removed | Consumer baseline remains exact and authority unchanged |

The live profile proves restart persistence without turning runtime shutdown
into rollback. Its rollback is removal of candidate evidence from the harness,
not disconnection of the paired VR940 runtime.

## Provenance Binding

Every result binds all of the following:

- exact gateway repository, 40-character source commit and milestone
  predecessor commit; `source_parent_commit` names that frozen predecessor and
  does not claim to be the source commit's first Git parent;
- runtime artifact ID, byte digest, byte length, build manifest, and
  domain-separated build-manifest hash;
- exact config payload and domain-separated config hash;
- read-only auth scope, permissions, and domain-separated auth-scope hash;
- normalization/mask scope digest;
- capture clock ID, UTC anchor, monotonic epoch, measured maximum clock error,
  maximum evidence age, verification offset, and clock hash;
- every protected raw payload digest and exact canonical byte length;
- the supplied M7 graph and replay digests and exact canonical byte lengths;
- exact content digests and byte lengths for the M7 registry, synchronized
  source bundle, and synchronized source replay;
- for captured evidence, the exact content digest of the public-redacted M7
  status projection bound to the real graph and replay hashes; and
- evidence ID/hash and registry content digest.

The M7 graph is not accepted from caller attribution alone. The verifier
invokes the existing synchronized-evidence and candidate-fact validators,
regenerates the M7 replay, and requires deep equality with the supplied replay.
The synthetic profile then requires its frozen graph, replay, registry,
source-bundle, and source-replay digests. The captured runtime profile also
requires the frozen public status projection of the real M7 graph. That
projection contains only candidate IDs, fact hashes, statuses, and terminal
classes: 18 facts, including 14 `RAW_ONLY` and 4 `WITHHELD`. It contains no
protocol identities or addresses and binds source graph
`dcfgv1:sha256:a7e4e661b2b78b37ff60f6f5c5b419d9af1cdf1b0f0570a9168b3ecbd3f99be9`.
The separate public source-terminal graph is validated only to supply the
complete anti-leak vocabulary. It cannot supply live fact counts or substitute
for the private graph during `verify` or `report`.
Substituting any otherwise valid synthetic or live input fails
`provenance.m7`. Every supplied M7 input is immutable.

The synthetic baseline runtime source is exact gateway main
`ff511b035b85aef6123fb0853bb3d2f3af6fc01e`; its compared runtime has that
source as parent. The captured runtime profile uses one exact artifact across
all four states and requires source parent
`8bcba2107d10b149f984ac9546ea6427a9cda8a1`. A missing, duplicate, stale,
reordered, mismatched, or unhashed provenance item fails closed. Capture age is
derived only from bound monotonic offsets; replay does not read the wall clock.

## Authority And Anti-Leak Rules

The internal facts prove visibility without publication. Their closed fields
are candidate ID, status, terminal state, and visibility channel. The
synthetic candidate run accepts only `CANDIDATE` with no terminal state and its
conflict run accepts only `WITHHELD` with terminal `CONFLICT`. The live profile
accepts the validated M7 statuses `RAW_ONLY`, `CANDIDATE`, `CONFLICTED`, and
`WITHHELD` but reports only what the supplied graph actually contains.

Every graph-derived candidate ID, the four statuses `RAW_ONLY`, `CANDIDATE`,
`CONFLICTED`, and `WITHHELD`, the terminal-state fields, and
`CANDIDATE_DEBUG_REPLAY` are forbidden in every protected view. This rule also
applies to baseline and rollback views.

The same prohibition covers the complete M7 source-terminal structure,
including its binding kind, source contract and ID, schema version, error
category, and graph-derived terminal vocabulary. Splitting those fields across
adjacent objects does not make them publishable.

Public redaction scans the complete artifact. Qualified or prefixed SHIP/SPINE
address and selector keys are treated as identity fields. A key ending in
`hash`, `digest`, or `commit` is exempt only when its value is a valid typed
SHA-256 digest, namespaced SHA-256 digest, 40-character commit, or null where
the schema permits null. Private IPv4, unique-local/link-local/loopback IPv6,
all supported MAC spellings, SKIs, and private-key PEM labels fail closed.

Protected outputs must contain no candidate, raw-only, conflicted, or withheld
fact field or value. In particular, this internal material cannot appear in:

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

The protected `semantic.registry` view is deliberately narrower than its raw
source input. It contains the fixed `fixed_m85_cross_protocol_ebus_core_v1`
set: four DHW leaves, the system-scheme property, and three operating-mode,
target-temperature, and current-temperature leaves for each of zones 0 and 1.
All eleven must be present and promoted in every run. Other promoted eBUS
leaves remain byte-bound in the immutable source capture, but their asynchronous
TTL and warm-up materialization is not interpreted as cross-runtime drift.
Exact candidate selectors and values are compared by the M8.5 campaign rather
than inferred from this coexistence projection.

The projection rule is evidence-bound through
`normalization.semantic_registry_projection` and therefore participates in the
normalization profile digest. Captures that predate this field replay with
`all_promoted_ebus_leaves_outside_volatile_schedule_slot_materialization`;
captures that declare
`fixed_m85_cross_protocol_ebus_core_v1` replay with the fixed eleven-path set.
The missing-field fallback is restricted to the pinned, already-published
pre-field evidence IDs; a new captured artifact cannot select the legacy rule
by omission. Changing or removing the declared profile invalidates the
evidence hashes.

## Rollback

Synthetic rollback disables the eeBUS runtime and candidate graph in the same
compared artifact. The verifier requires `EEBUS_DISABLED_ROLLBACK`, disabled
config bits, explicit `ROLLBACK_BASELINE_RESTORED`, zero service and fact
counts, and exact shape and canonical bytes for all protected views. Live
rollback keeps the runtime connected, drops only the candidate graph, requires
`EEBUS_CONNECTED_ROLLBACK` and `GRAPH_EVIDENCE_DROPPED`, and retains at least
one visible service. In either profile, restart success or an empty response is
not rollback evidence.

Live restart persistence requires two distinct process instances. The restart
state carries domain-hashed immutable inputs for the observed process event,
the redacted pre/post state snapshots, and the observed reconnection event.
The verifier derives process, trust, peer-binding, and session continuity from
those captures. Relabeling a state in one process, changing a capture without
its input digest, reusing the same process instance ID, changing either
persisted binding, reusing the old session, or omitting reconnection fails.

## Validation Precedence

Validation stops at the first category in this exact order:

1. `json.syntax`
2. `limits.exceeded`
3. `schema.evidence`
4. `registry.binding`
5. `provenance.m7`
6. `provenance.runtime`
7. `provenance.source_capture`
8. `provenance.config`
9. `provenance.auth_mask`
10. `provenance.clock`
11. `ordering.duplicate`
12. `state.evidence`
13. `view.coverage`
14. `canonicalization.invalid`
15. `hash.payload`
16. `anti_leak.candidate`
17. `redaction.public`
18. `authority.ebus`
19. `gate.scope`
20. `drift.consumer`
21. `rollback.drift`
22. `hash.evidence`

Allocation-driving byte, nesting, string, member, and list limits run before
recursive parsing by necessity. They still report `limits.exceeded`.
Source-manifest paths are not opened until step 7 and all immutable runtime
inputs have passed, so a missing, unsafe, or oversized source cannot mask an
earlier schema, registry, M7, or runtime failure. Captured-runtime evidence has
exactly four ordered runs; synthetic evidence has exactly six.
Validation emits no partial success or report.

## Resource Bounds

| Limit | V1 value |
| --- | ---: |
| `max_evidence_bytes` | 2,097,152 |
| `max_depth` | 32 |
| `max_runs` | 8 |
| `max_views_per_run` | 16 |
| `max_inputs_per_run` | 27 |
| `max_internal_facts_per_run` | 64 |
| `max_payload_bytes` | 262,144 |
| `max_string_bytes` | 4,096 |
| `max_total_members` | 65,536 |
| `max_total_list_items` | 32,768 |
| `max_source_input_bytes` | 2,097,152 |
| `max_source_total_bytes` | 16,777,216 |

The evidence declares these exact values and the verifier hard-codes the same
ceilings. Raising, lowering, omitting, or exceeding a ceiling is invalid.

## EEBUS-G18 Evidence Artifact

The transport-gate evidence artifact is the closed evidence JSON plus its
verifier-derived report. It proves coexistence only and is suitable for the
`eebus_v0` G18 row. Synthetic evidence does not satisfy G17 or G19 and does not
require a live outbound connection. Captured runtime evidence may use the
already-proven outbound connection, but this contract still makes no new G17
or G19 claim.

Runtime/operator captures may inspect local raw eeBUS facts. Any evidence
published from this gate must use the explicit `public-redacted` export path:
stable device identity and protocol addresses are removed, while all
cryptographic secrets remain forbidden in every tier. The protected-view
comparison binds the effective auth and mask scope and never permits a tier
change on dereference.

The public verifier scans the complete evidence artifact, not only protected
payloads. It normalizes snake-case, kebab-case, and camel-case field names and
fails closed on private-key or key-material fields; encrypted, DSA, and other
private-key PEM labels; credential, secret, password, token, or trust-store
fields; private IPv4 addresses; colon, hyphen, dotted, or compact MAC
addresses; raw 40-hex-character SKIs; and unredacted stable device, entity,
feature, peer, SHIP, authentication-subject, endpoint, source, target, or other
protocol addresses. Only typed commits, hashes, and digests bypass scalar
secret-pattern inspection. A retained secondary identifier must use the
deterministic `redacted:sha256:<12-hex>` form. This rule does not redefine SKI,
SHIP ID, or SPINE addresses as cryptographic secrets in the local authorized
operator view.

The positive fixture IDs are:

- `MSP08-G18-SYNTHETIC-POSITIVE-001`; and
- `MSP08-G18-SYNTHETIC-REPORT-001`.

The generated report includes the exact baseline runtime identity and eleven
view hashes, every scenario result and view hash, the profile-specific
acceptance matrix, the exact M7 binding, and the rollback result. `PASS` is
emitted only after every validation stage completes.

Live evidence reserves the seven-character `-REPORT` suffix within the
121-character evidence fixture-ID limit, so every accepted evidence ID yields
a report fixture ID within the report schema's 128-character ceiling.

The report schema enforces profile-specific cardinality: synthetic evidence
produces five scenario results and six acceptance rows, while captured live
evidence produces three scenario results and four acceptance rows. Both
profiles carry the same `PUBLIC_REDACTED` export tier as their source evidence.

## Acceptance Matrix

Each state must pass every listed check. No cell is caller-provided. The table
below is the synthetic profile; the captured profile applies the same checks
to its four live states, including restart persistence.

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
`CANDIDATE_CONFINED`, `PUBLIC_REDACTION_ENFORCED`,
`V1_SURFACES_PRESERVED`, and `G18_SCOPE_ONLY`.

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
| `SOURCE_CAPTURE_MALFORMED` | `provenance.source_capture` |
| `SOURCE_CAPTURE_RESOURCE_LIMIT` | `limits.exceeded` |
| `SOURCE_CAPTURE_UNSAFE_FILE` | `provenance.source_capture` |
| `RESOURCE_LIMIT_EXCEEDED` | `limits.exceeded` |
| `ROLLBACK_DRIFT` | `rollback.drift` |
| `RUNTIME_ARTIFACT_MISMATCH` | `provenance.runtime` |
| `STALE_CAPTURE` | `provenance.clock` |
| `TIMESTAMP_EXCLUSION_MISMATCH` | `canonicalization.invalid` |
| `UNKNOWN_FIELD` | `schema.evidence` |

## Gateway RED Handoff

The next gateway RED test should vendor or fetch these exact docs artifacts by
immutable docs commit, then emit one captured-runtime evidence JSON conforming
to the evidence schema. It must supply all five M7 validation inputs to the
verifier. Expected runtime output paths are the registry `capture_path` values
under `artifacts/protected/`; raw and withheld facts remain in the separate
internal capture for `CANDIDATE_DEBUG_REPLAY`.

Gateway synthetic conformance must retain the six synthetic scenario IDs and
all mutation classes. Live acceptance must exercise the four captured-runtime
states in order with one artifact and the eleven protected view IDs without
substitution. Its G18 artifact is the input evidence plus exact report bytes.
A gateway test must not replace the verifier with a caller comparison, drop
fields before capture, extend masking, infer a state from missing data, or
claim G17/G19 from this contract. Passing M8 does not authorize M8.5 or M9.
